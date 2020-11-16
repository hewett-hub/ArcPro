import datetime
import logging
import argparse
import sys
import copy

from arcgis.gis import GIS
from arcgis.features import FeatureLayer

from graphc.covid.source.NSW_SourceData import NswTestData
from graphc.da import da_arcpy
from graphc.data.abs2016 import POA2016


default_service_url = r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Tests_by_Date_and_Postcode/FeatureServer/0'


class Covid19TestsByDateAndPostcode(object):
    """
    A feature service wrapper class that supports common operations.
    """
    def __init__(self, service_url=default_service_url):
        self.service_url = service_url
        self.id_field = 'ID'
        self.postcode_field = 'Postcode'
        self.date_field = 'Date'
        self.tests_field = 'Tests'
        self.date_code_format = '%Y%m%d'

    def layer(self):
        return FeatureLayer(self.service_url)

    def query(self, where_clause='1=1'):
        return self.layer().query(where=where_clause)

    def update(self, update_values, allow_deletes=False):
        """
        updates the feature service by updating or adding the submitted rows.  Rows are identified by date_code and postcode.
        Date values are derived from the date_code values.
        Existing XYs are not updated, submitted xys are used if rows are added.
        :param update_values: {id: {'tests': int, 'xy': {'x': float, 'y': float}}} with id in format yyyymmdd_pppp where:
        - yyyy is the 4 digit year
        - mm is the 2 digit month, with leading zeros if required (ie 02 for February)
        - dd is the 2 digit day of the month, with leading zeros as needed.
        - pppp is the 4 digit postcode, or 'UNK' if the postcode is unknown.
        :type update_values: dict
        :param allow_deletes: If set to True any records not found in the source rows will be deleted.  Default=False
        :type allow_deletes: bool
        :return:
        :rtype:
        """

        copied_values = copy.deepcopy(update_values)
        deletes = []
        updates = []
        target_layer = self.layer()
        update_fields = [self.id_field, self.postcode_field, self.date_field, self.tests_field]
        query_result = target_layer.query(out_fields=update_fields)
        for row in query_result:
            key = row.attributes[self.id_field]
            if allow_deletes and key not in copied_values:
                deletes.append(row.attributes[query_result.object_id_field_name])

            item = copied_values.pop(key, None)
            if item:
                if row.attributes[self.tests_field] != item['tests']:
                    row.attributes[self.tests_field] = item['tests']
                    updates.append(row)

        # any remaining data_models items are new records
        adds = []

        for key, new_item in copied_values.items():
            date_code, postcode = key.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            row = {"attributes":
                       {self.id_field: key,
                        self.date_field: date,
                        self.postcode_field: postcode.upper(),
                        self.tests_field: new_item['tests']},
                   "geometry": new_item['xy']}
            adds.append(row)

        logging.info('Updating: {}'.format(self.service_url))
        logging.info('ADDS: {}'.format(len(adds)))
        logging.info('DELETES: {}'.format(len(deletes)))
        logging.info('UPDATES: {}'.format(len(updates)))
        if updates or adds or deletes:
            return target_layer.edit_features(updates=updates, adds=adds, deletes=str(deletes))
        else:
            return None

    def format_date_string(self, date_string, in_format):
        """
        Reformats the submitted date or datetime string to the correct format for the date_code field
        :type date_string: str
        :param in_format: the format string of the submitted date_string.  eg: '%Y-%m-%d'
        :type in_format: str
        :return: The reformatted date_string
        :rtype: str
        """

        dt = datetime.datetime.strptime(date_string, in_format)
        return dt.strftime(self.date_code_format)


class UpdateFromSourceTask(object):
    """
    An update task encapsulating all of the required input parameters and structures.
    Upon initial creation the defaults are set.
    Defaults can be modified after creation using the class properties.
    """
    def __init__(self):
        self.feature_service = Covid19TestsByDateAndPostcode()
        self.nsw_tests_source = NswTestData()
        self.postcode_feature_source = POA2016.centroids()

    def full_update(self):
        """
        Performs a full update from the source data, including adds, deletes and updates.
        :return:
        :rtype:
        """
        # get the source data
        source_data = self.nsw_tests_source.source_data()

        # sort rows by date and postcode.
        # sorted_data = sorted(source_data, key=lambda x: (x[self.nsw_tests_source.postcode_field], x[self.nsw_tests_source.date_field]))

        # get postcode xys
        xys = da_arcpy.load_xy_geometries(source=self.postcode_feature_source.source,
                                          id_field=self.postcode_feature_source.poa_code_field)

        # convert to input rows
        wkg = {}
        for row in source_data:
            date_str = self.feature_service.format_date_string(date_string=row[self.nsw_tests_source.date_field],
                                                               in_format=self.nsw_tests_source.out_date_format)
            postcode = row[self.nsw_tests_source.postcode_field]
            if not postcode:
                postcode = 'UNK'

            key = '{}_{}'.format(date_str, postcode)
            wkg_item = wkg.get(key, None)
            if wkg_item:
                wkg_item['tests'] += 1
            else:
                xy = xys.get(postcode, None)
                wkg[key] = {'tests': 1, 'xy': xy}

        return self.feature_service.update(update_values=wkg, allow_deletes=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile",
                        required=False,
                        default='agol_graphc',
                        help="Local Profile used to access the ArcGIS Online instance.")
    parser.add_argument("-l", "--log",
                        required=False,
                        default=r'E:\Documents2\tmp\DailyCovid19TestsByDateAndPostcode.log',
                        help='Log file to be created or used.')
    parser.add_argument("-u", "--update",
                        action='store_true',
                        help='If specified, update from source will be performed using system defaults.')
    parser.add_argument("-t", "--target",
                        required=False,
                        default=default_service_url,
                        help='The full url to the target feature service layer(including layer id).')

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        filename=args.log
    )

    try:
        log_entry = '"{}" -p "{}" -l "{}" -t "{}"'.format(sys.argv[0], args.profile, args.log, args.target)
        if args.update:
            log_entry += ' -u'

        logging.info(log_entry)
        # create GIS connection
        logging.info('Start signin using profile credentials')
        gis = GIS(profile=args.profile)
        logging.info('End signin using profile credentials')

        if args.update:
            task = UpdateFromSourceTask()
            task.feature_service.service_url = args.target
            task.full_update()

    except Exception as e:
        print(e)
        logging.error(e, exc_info=True)
        raise
