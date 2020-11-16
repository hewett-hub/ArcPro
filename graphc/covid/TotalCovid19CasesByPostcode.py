import datetime
import logging
import argparse
import sys

from arcgis.gis import GIS
from arcgis.features import FeatureLayer

from graphc.covid.source.NSW_SourceData import NswNotificationData
from graphc.da import da_arcpy
from graphc.data.abs2016 import POA2016


default_service_url = r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/Total_Cases_By_Postcode/FeatureServer/0'


class TotalCovid19CasesByPostcode(object):
    """
    A data access class to support the corresponding feature service layer.
    - Each postcode is represented by a single record.  There should be no duplicate postcodes in this feature layer.
    """
    def __init__(self, service_url=default_service_url):
        self.layer = FeatureLayer(service_url)
        self.postcode_field = 'PostCode'
        self.total_cases_field = 'TotalCases'
        self.date_of_last_case_field = 'DateOfLastCase'
        self.days_since_last_case_field = 'DaysSinceLastCase'

    def query(self, where_clause):
        return self.layer.query(where=where_clause)

    def update(self, updates_items=None):
        """
        Updates the feature service:
        - recalculates the date_of_last_case values and updates as required.
        - if update_items are submitted, updates or adds the submitted rows.

        Rows are identified by postcode.
        Rows are only added if the postcode does not already exist in the table.
        Rows are never deleted by this process.  In order to prevent accidental deletions they must be performed as a separate task.
        Existing XYs are not updated, submitted xys are used if rows are added.
        Use 'xy': None if location is not known for new records

        :param updates_items: A dictionary of named row values indexed by postcode.
        {postcode: {
          'postcode': str,
          'total_cases': int,
          'date_of_last_case': datetime,
          'xy': {
            'x': float,
            'y': float}
          }
        }
        :type updates_items: dict
        :return:
        :rtype:
        """

        updates = []
        if not updates_items:
            updates_items = {}

        # identify updates to be performed for existing rows.
        query_result = self.layer.query()
        for row in query_result:
            update_required = False
            poa = row.attributes[self.postcode_field]
            item = updates_items.pop(poa, None)
            if item:
                if row.attributes[self.total_cases_field] != item['total_cases']:
                    row.attributes[self.total_cases_field] = item['total_cases']
                    update_required = True
                if row.attributes[self.date_of_last_case_field] != item['date_of_last_case']:
                    row.attributes[self.date_of_last_case_field] = item['date_of_last_case']
                    update_required = True

            report_age = self.calc_days_since(row.attributes[self.date_of_last_case_field])
            if report_age != row.attributes[self.days_since_last_case_field]:
                row.attributes[self.days_since_last_case_field] = report_age
                update_required = True

            if update_required:
                updates.append(row)

        # any remaining data_models items are new records
        adds = []
        new_items = updates_items.values()
        if new_items:
            for new_item in new_items:
                days_since_last_case = self.calc_days_since(new_item['date_of_last_case'])
                row = {"attributes":
                       {self.postcode_field: new_item['postcode'],
                        self.total_cases_field: new_item['total_cases'],
                        self.date_of_last_case_field: new_item['date_of_last_case'],
                        self.days_since_last_case_field: days_since_last_case},
                       "geometry": new_item['xy']}
                adds.append(row)

        logging.info('Updating: {}'.format(self.layer.url))
        logging.info('ADDS: {}'.format(len(adds)))
        logging.info('UPDATES: {}'.format(len(updates)))
        if updates or adds:
            return self.layer.edit_features(updates=updates, adds=adds)
        else:
            return None

    @staticmethod
    def calc_days_since(reference_date):
        if reference_date:
            return (datetime.datetime.now() - reference_date).days
        else:
            return None


class UpdateFromSourceTask(object):
    """
    An update task encapsulating all of the required input parameters and structures.
    Upon initial creation the defaults are set.
    Defaults can be modified after creation using through the class properties.
    """
    def __init__(self, service_url=default_service_url):
        self.target = TotalCovid19CasesByPostcode(service_url)
        self.nsw_source = NswNotificationData()
        self.geometry_source = POA2016.centroids()

    def full_update(self):
        """
        Performs a full update from the source data, inculding adds, deletes and updates.
        A combination of the date_code and postcode are used as the full identifier.
        :return:
        :rtype:
        """

        update_data = {}
        self.append_nsw_cases_to_totals(update_data)

        self.apply_xys(update_data)

        return self.target.update(updates_items=update_data)

    def append_nsw_cases_to_totals(self, postcode_items):
        """
        Adds NSW cases to total_cases and updates date_of_last_case where case date is more recent than existing value.
        Creates new postcode items where needed.
        :param postcode_items: {postcode: {'postcode': str, 'total_cases': int, 'date_of_last_case': datetime}}
        :type postcode_items: dict
        :return: {postcode: {'postcode': str, 'total_cases': int, 'date_of_last_case': datetime}}
        :rtype: dict
        """

        # get the source data
        source_data = self.nsw_source.source_data()

        for case in source_data:
            date_string = case[self.nsw_source.date_field]
            date = datetime.datetime.strptime(date_string, self.nsw_source.csv_date_format)
            postcode = case[self.nsw_source.postcode_field]

            postcode_item = postcode_items.get(postcode, None)
            if postcode_item:
                postcode_item['total_cases'] += 1
                # if this case is more recent that the current date of last case, update the date of last case.
                if postcode_item['date_of_last_case'] < date:
                    postcode_item['date_of_last_case'] = date
            else:
                postcode_items[postcode] = {'postcode': postcode, 'total_cases': 1, 'date_of_last_case': date}

        return postcode_items

    def apply_xys(self, postcode_items):
        """
        Applys the xy geometries to each postcode using the geometry_source.  If no geometry for the postcode is found, the output
        'xy' value will be None for that item.

        :param postcode_items: {postcode: {}}
        :type postcode_items: dict
        :return: {postcode: {'xy': {'x': float, 'y': float}}
        :rtype: dict
        """

        # get postcode xys
        xys = da_arcpy.load_xy_geometries(source=self.geometry_source._source,
                                          id_field=self.geometry_source.poa_code_field)

        for postcode, postcode_item in postcode_items.items():
            postcode_item['xy'] = xys.get(postcode, None)

        return postcode_items


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile",
                        required=False,
                        default='agol_graphc',
                        help="Local Profile used to access the ArcGIS Online instance.")
    parser.add_argument("-l", "--log",
                        required=False,
                        default=r'E:\Documents2\tmp\TotalCovid19CasesByPostcode.log',
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
