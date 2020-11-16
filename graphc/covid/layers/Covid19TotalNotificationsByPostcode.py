import logging
import argparse
import sys
import copy

from arcgis.gis import GIS
from arcgis.features import FeatureLayer

from graphc.covid.layers.Covid19NotificationsByDateAndPostcode import Covid19NotificationsByDateAndPostcode


default_service_url = r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Total_Notifications_by_Postcode/FeatureServer/0'


class Covid19TotalNotificationsByPostcode(object):
    """
    A feature service wrapper class that supports common operations.
    """
    def __init__(self, service_url=default_service_url):
        self.service_url = service_url
        self.postcode_field = 'Postcode'
        self.total_notifications_field = 'TotalNotifications'
        self.most_recent_notification_field = 'MostRecentNotification'

    def layer(self):
        return FeatureLayer(self.service_url)

    def query(self, where_clause='1=1'):
        return self.layer().query(where=where_clause)

    def update(self, update_values):
        """
        updates the feature service by updating or adding the submitted rows.  Rows are identified by postcode.
        Existing XYs are not updated, submitted xys are used if rows are added.
        :param update_values: {postcode: {'total_notifications': int, 'most_recent_notification': date,
                                          'xy': {'x': float, 'y': float}}}
        :type update_values: dict
        :return:
        :rtype:
        """

        copied_values = copy.deepcopy(update_values)
        updates = []
        target_layer = self.layer()
        query_result = target_layer.query()
        for row in query_result:
            postcode = row.attributes[self.postcode_field].upper()
            current_date = row.attributes[self.most_recent_notification_field]
            current_total = row.attributes[self.total_notifications_field]

            update_values = copied_values.pop(postcode, None)
            if update_values:
                new_date = update_values['most_recent_notification']
                new_total = update_values['total_notifications']
            else:
                new_date = None
                new_total = None

            if current_total != new_total or current_date != new_date:
                row.attributes[self.total_notifications_field] = new_total
                row.attributes[self.most_recent_notification_field] = new_date
                updates.append(row)

        # any remaining data_models items are new records
        adds = []

        for postcode, new_values in copied_values.items():
            row = {"attributes":
                   {self.postcode_field: postcode.upper(),
                    self.total_notifications_field: new_values['total_notifications'],
                    self.most_recent_notification_field: new_values['most_recent_notification']},
                   "geometry": new_values['xy']}
            adds.append(row)

        logging.info('Updating: {}'.format(self.service_url))
        logging.info('ADDS: {}'.format(len(adds)))
        logging.info('UPDATES: {}'.format(len(updates)))
        if updates or adds:
            return target_layer.edit_features(updates=updates, adds=adds)
        else:
            return None


class UpdateTask(object):
    """
    An update task encapsulating all of the required input parameters and structures.
    Upon initial creation the defaults are set.
    Defaults can be modified after creation using the class properties.
    """
    def __init__(self):
        self.feature_service = Covid19TotalNotificationsByPostcode()
        self.source_data = Covid19NotificationsByDateAndPostcode()

    def update(self):
        """
        Performs a full update from the source data, including adds, deletes and updates.
        :return:
        :rtype:
        """
        # get all postcode notification records.
        source_values = self.source_data.query()

        update_values = {}

        for row in source_values:
            postcode = row.attributes[self.source_data.postcode_field].upper()
            row_date = row.attributes[self.source_data.date_field]
            notifications = row.attributes[self.source_data.notifications_field]

            postcode_values = update_values.get(postcode, None)
            if postcode_values:
                postcode_values['total_notifications'] += notifications
                if row_date > postcode_values['most_recent_notification']:
                    postcode_values['most_recent_notification'] = row_date
            else:
                update_values[postcode] = {'total_notifications': notifications,
                                           'most_recent_notification': row_date,
                                           'xy': row.geometry}

        return self.feature_service.update(update_values=update_values)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile",
                        required=False,
                        default='agol_graphc',
                        help="Local Profile used to access the ArcGIS Online instance.")
    parser.add_argument("-l", "--log",
                        required=False,
                        default=r'E:\Documents2\tmp\DailyCovid19NotificationsByDateAndPostcode.log',
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
