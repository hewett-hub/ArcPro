import datetime
import logging
import argparse
import sys

from arcgis.gis import GIS
from arcgis.features import FeatureLayer

from graphc.covid.source.NSW_SourceData import NswTestData
from graphc.da import da_arcpy
from graphc.data.abs2016 import POA2016


default_service_url = r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/Daily_COVID_19_Testing_by_Postcode/FeatureServer/0'


class DailyCovid19TestingByPostcode(object):
    def __init__(self, service_url=default_service_url):
        self.layer = FeatureLayer(service_url)
        self.postcode_field = 'Postcode'
        self.date_field = 'Date'
        self.date_code_field = 'DateCode'
        self.tests_field = 'Tests'
        self.total_tests_field = 'TotalTests'
        self.date_code_format = '%Y%m%d'

    def query(self, where_clause):
        return self.layer.query(where=where_clause)

    def update(self, rows, allow_deletes=False):
        """
        updates the feature service by updating or adding the submitted rows.  Rows are identified by date_code and postcode.
        Date values are derived from the date_code values.
        Existing XYs are not updated, submitted xys are used if rows are added.
        :param rows: [{'postcode': str, 'date_code': str, 'tests': int, 'total_tests': int, 'xy': {'x': float, 'y': float}}]
        :type rows: [dict]
        :param allow_deletes: If set to True any records not found in the source rows will be deleted.  Default=False
        :type allow_deletes: bool
        :return:
        :rtype:
        """

        # build lookup from submitted rows:
        items = {}
        for row in rows:
            key = '{}_{}'.format(row['postcode'], row['date_code'])
            items[key] = row

        deletes = []
        updates = []
        query_result = self.layer.query()
        for row in query_result:
            poa = row.attributes[self.postcode_field]
            date_code = row.attributes[self.date_code_field]
            key = '{}_{}'.format(poa, date_code)
            if allow_deletes and key not in items:
                deletes.append(row.attributes[query_result.object_id_field_name])

            item = items.pop(key, None)
            if item:
                update_required = False
                if row.attributes[self.tests_field] != item['tests']:
                    row.attributes[self.tests_field] = item['tests']
                    update_required = True
                if row.attributes[self.total_tests_field] != item['total_tests']:
                    row.attributes[self.total_tests_field] = item['total_tests']
                    update_required = True
                if update_required:
                    updates.append(row)

        # any remaining data_models items are new records
        adds = []
        new_items = items.values()
        if new_items:
            for new_item in new_items:
                date = datetime.datetime.strptime(new_item['date_code'], '%Y%m%d')
                row = {"attributes":
                           {self.date_field: date,
                            self.postcode_field: new_item['postcode'],
                            self.date_code_field: new_item['date_code'],
                            self.total_tests_field: new_item['total_tests'],
                            self.tests_field: new_item['tests']},
                       "geometry": new_item['xy']}
                adds.append(row)

        logging.info('Updating: {}'.format(self.layer.url))
        logging.info('ADDS: {}'.format(len(adds)))
        logging.info('DELETES: {}'.format(len(deletes)))
        logging.info('UPDATES: {}'.format(len(updates)))
        if updates or adds or deletes:
            return self.layer.edit_features(updates=updates, adds=adds, deletes=str(deletes))
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

        if in_format == self.date_code_format:
            return date_string

        dt = datetime.datetime.strptime(date_string, in_format)
        return dt.strftime(self.date_code_format)


class UpdateFromSourceTask(object):
    """
    An update task encapsulating all of the required input parameters and structures.
    Upon initial creation the defaults are set.
    Defaults can be modified after creation using through the class properties.
    """
    def __init__(self, service_url=default_service_url):
        self.target = DailyCovid19TestingByPostcode(service_url)
        self.nsw_source = NswTestData()
        self.geometry_source = POA2016.centroids()

    def full_update(self):
        """
        Performs a full update from the source data, inculding adds, deletes and updates.
        A combination of the date_code and postcode are used as the full identifier.
        :return:
        :rtype:
        """
        # get the source data
        source_data = self.nsw_source.source_data()

        # sort rows by date and postcode.
        sorted_data = sorted(source_data, key=lambda x: (x[self.nsw_source.postcode_field], x[self.nsw_source.date_field]))

        # get postcode xys
        xys = da_arcpy.load_xy_geometries(source=self.geometry_source._source,
                                          id_field=self.geometry_source.poa_code_field)

        # convert to input rows
        totals = {}
        wkg = {}
        for row in sorted_data:
            date_str = self.target.format_date_string(date_string=row[self.nsw_source.date_field], in_format=self.nsw_source.out_date_format)
            postcode = row[self.nsw_source.postcode_field]
            if not postcode:
                postcode = 'UNK'

            total = totals.get(postcode, 0) + 1
            totals[postcode] = total

            key = '{}_{}'.format(postcode, date_str)
            wkg_item = wkg.get(key, None)
            if wkg_item:
                wkg_item['tests'] += 1
                wkg_item['total_tests'] = total
            else:
                xy = xys.get(postcode, None)
                wkg_item = {'postcode': postcode,
                            'date_code': date_str,
                            'tests': 1,
                            'total_tests': total,
                            'xy': xy}
                wkg[key] = wkg_item

        return self.target.update(rows=wkg.values(), allow_deletes=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile",
                        required=False,
                        default='agol_graphc',
                        help="Local Profile used to access the ArcGIS Online instance.")
    parser.add_argument("-l", "--log",
                        required=False,
                        default=r'E:\Documents2\tmp\DailyCovid19TestingByPostcode.log',
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
            task = UpdateFromSourceTask(args.target)
            task.full_update()

    except Exception as e:
        print(e)
        logging.error(e, exc_info=True)
        raise
