import datetime
import logging
import argparse
import sys
import copy

from arcgis.gis import GIS
from arcgis.features import FeatureLayer

from graphc.covid.layers.Covid19NotificationsByDateAndPostcode import Covid19NotificationsByDateAndPostcode


default_service_url = r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/Case_Locations_By_Postcode/FeatureServer/0'


class Covid19CaseLocationsByPostcode(object):
    """
    A feature service wrapper class that supports common operations.
    """
    def __init__(self, service_url=default_service_url):
        self.service_url = service_url
        self.date_string_field = 'DateString'
        self.postcode_field = 'PostCode'
        self.date_field = 'ReportDate'
        self.date_code_format = '%Y%m%d'

    def layer(self):
        return FeatureLayer(self.service_url)

    def query(self, where_clause='1=1'):
        return self.layer().query(where=where_clause)

    def update(self, update_values):
        """
        updates the feature service by adding or removing records so that the number of items for each date/postcode combination match
        number of notifications in the update values for that date/postcode combination.  This update assumes a full update set is submitted.
        Existing XYs are not updated, submitted xys are used if rows are added.
        :param update_values: {id: {'notifications': int, 'xy': {'x': float, 'y': float}}} with id in format yyyymmdd_pppp where:
        - yyyy is the 4 digit year
        - mm is the 2 digit month, with leading zeros if required (ie 02 for February)
        - dd is the 2 digit day of the month, with leading zeros as needed.
        - pppp is the 4 digit postcode, or 'UNK' if the postcode is unknown.
        :type update_values: dict
        :return:
        :rtype:
        """

        copied_values = copy.deepcopy(update_values)
        deletes = []
        adds = []
        target_layer = self.layer()
        query_result = target_layer.query()
        for row in query_result:
            key = '{}_{}'.format(row.attributes[self.date_string_field], row.attributes[self.postcode_field])
            update_item = copied_values.get(key, None)
            if update_item:
                # if an update item was found, subtract 1 from the notifications total.
                update_item['notifications'] -= 1
                if update_item['notifications'] < 1:
                    # If the new notifications total is less than 1, then this was the last notification for the postcode/date.
                    # Remove the postcode/date item from the collection of update items so any additional records associated with
                    # this date/postcode combo will be deleted from the online data.
                    copied_values.pop(key, None)
            else:
                # if no matching update item was found, delete the record from online.
                deletes.append(row.attributes[query_result.object_id_field_name])

        # any remaining data_models items are new records
        adds = []

        for key, new_item in copied_values.items():
            date_code, postcode = key.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            for i in range(new_item['notifications']):
                row = {"attributes":
                           {self.date_string_field: date_code,
                            self.date_field: date,
                            self.postcode_field: postcode.upper()},
                       "geometry": new_item['xy']}
                adds.append(row)

        logging.info('Updating: {}'.format(self.service_url))
        logging.info('ADDS: {}'.format(len(adds)))
        logging.info('DELETES: {}'.format(len(deletes)))
        if adds or deletes:
            return target_layer.edit_features(adds=adds, deletes=str(deletes))
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


class UpdateTask(object):
    """
    An update task encapsulating all of the required input parameters and structures.
    Upon initial creation the defaults are set.
    Defaults can be modified after creation using the class properties.
    """
    def __init__(self):
        self.feature_service = Covid19CaseLocationsByPostcode()
        self.source_data = Covid19NotificationsByDateAndPostcode()

    def update(self):
        """
        Performs a full update from the source data, including adds, deletes and updates.
        :return:
        :rtype:
        """

        update_data = {}
        # get all source rows
        source_rows = self.source_data.query(where_clause="1=1")
        # parse source rows to required update data format.
        for row in source_rows:
            key = row.attributes[self.source_data.id_field]
            notifications = row.attributes[self.source_data.notifications_field]
            geometry = row.geometry
            update_data[key] = {'notifications': notifications, 'xy': geometry}

        return self.feature_service.update(update_values=update_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile",
                        required=False,
                        default='agol_graphc',
                        help="Local Profile used to access the ArcGIS Online instance.")
    parser.add_argument("-l", "--log",
                        required=False,
                        default=r'E:\Documents2\tmp\Covid19CaseLocationsByPostcode.log',
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
            task = UpdateTask()
            task.feature_service.service_url = args.target
            task.update()

    except Exception as e:
        print(e)
        logging.error(e, exc_info=True)
        raise
