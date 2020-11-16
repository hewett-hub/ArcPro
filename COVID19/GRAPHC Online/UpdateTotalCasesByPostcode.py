"""
Note:  This script is intended to be run as a scheduled task.  Parameters are hard coded into the script to remove the need
to configure parameters in the task scheduler.  You should take a copy of this script and configure parameters to meet your needs, then
use Task Scheduler to run your copy.

Credentials:
In order to protect your credentials (ie, not have them visible in the script or in the Task Manager parameters) the script uses a
Profile to access your credentials.  If you haven't already created a profile to hold these credentials on your computer you must
create one before running this script.  You can do this by copying the following snippet into the python window of ArcGIS Pro,
replacing the **** placeholders with values appropriate to you, and running the snippet.

from arcgis.gis import GIS
my_new_profile =  GIS(url="https://graphc.maps.arcgis.com/", username='****', password='****', profile='****')



Once you have run the snippet your profile will be created on the computer you ran the snippet on.

See the 'Storing your credentials locally' section on the following web-page for more information:
https://developers.arcgis.com/python/guide/working-with-different-authentication-schemes/

Refs:
https://developers.arcgis.com/python/guide/editing-features/
https://developers.arcgis.com/python/guide/working-with-different-authentication-schemes/
"""

import csv
import urllib.request
import io
import logging
import datetime
import copy
import argparse
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from arcgis.features import FeatureSet


# Windows profile holding the credentials to be used to connect to the national_time_series_target
profile = 'agol_graphc'

# file path to log file.
logfile = r'E:\Documents2\tmp\UpdateTotalCasesByPostcode.log'

# NSW case information source.
nsw_source = r'https://data.nsw.gov.au/data/dataset/aefcde60-3b0c-4bc0-9af1-6fe652944ec2/resource/21304414-1ff1-4243-a5d2-f52778048b29/download' \
             r'/covid-19-cases-by-notification-date-and-postcode-local-health-district-and-local-government-area.csv'
postcode_index = 1
date_index = 0

count_by_postcode_target = r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/Total_Cases_By_Postcode/FeatureServer/0'
individual_cases_by_postcode_target = 'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/Case_Locations_By_Postcode/FeatureServer/0'

date_now = datetime.datetime.now()


class CaseList(object):
    def __init__(self):
        self.items = []  # [{'date_string': str, 'date': datetime, 'postcode': int, 'report_age': int}]
        self._counts_by_postcode = None
        self._counts_by_date_and_postcode = None

    @staticmethod
    def parse_date(date_value):
        """
        Parses a date in format "dd-mm-yy" or "dd-mm-yyyy" into a date string and a datetime object.
        :param date_value: The date string to be parsed.
        :type date_value: str
        :return: a date string (yyyymmdd), a datetime object and the number of days since the report date.
        :rtype: str, datetime, int
        """
        if '-' in date_value:
            year_part, month_part, day_part = date_value.split('-')
        else:
            day_part, month_part, year_part = date_value.split('/')

        year_length = len(year_part)
        if year_length == 2:
            year_part = '20' + year_part
        elif year_length != 4:
            raise RuntimeError('Invalid year value: ' + date_value)

        date_string = year_part + month_part.zfill(2) + day_part.zfill(2)
        date_result = datetime.datetime(int(year_part), int(month_part), int(day_part))
        days_since_report = (date_now - date_result).days

        return date_string, date_result, days_since_report

    def append_nsw_data(self, source_url):
        """
            Parses the NSW source source_data and appends it to the CaseList.items.
            :return: the number of items appended to the items list.
            :rtype: int
            """
        result = 0
        # reset derivatives before appending source_data.
        self._counts_by_postcode = None
        self._counts_by_date_and_postcode = None

        with urllib.request.urlopen(source_url) as response:
            content = response.read().decode('utf-8')
            reader = csv.reader(io.StringIO(content))
            for row in reader:
                postcode = row[postcode_index]
                if postcode:
                    postcode = postcode.strip()
                if len(postcode) <= 4:
                    date_string, date_value, days_since_date = self.parse_date(row[date_index])
                    result_item = {'date_string': date_string, 'date': date_value, 'postcode': postcode, 'report_age': days_since_date}
                    self.items.append(result_item)
                    result += 1

        return result

    def counts_by_postcode(self):
        """Calculates the number of cases, date of last case and days since last case for each postcode
        in the CaseList.items
        :return: {postcode: {'Postcode': str, 'Total Cases': int, 'DateOfLastCase': date, 'DaysSinceLastCase': int}}
        :rtype: dict
        """

        # if the counts by postcode have been calculated since last case added to items
        # there is no need to re-calculate - return stored values.
        if self._counts_by_postcode:
            return copy.deepcopy(self._counts_by_postcode)

        # make a local copy so we do not alter the case_list
        local_copy = copy.deepcopy(self.items)

        # sort the input postcode items by report age.  This means that the first
        # item found for each postcode will be the most recent, avoiding the need for repeated checks
        # to test if the current item is the most recent when updating count items.
        sorted_items = sorted(local_copy, key=lambda k: k['report_age'])

        result = {}

        for postcode_item in sorted_items:
            postcode = postcode_item['postcode']
            result_item = result.get(postcode, None)
            if result_item:
                result_item['Total Cases'] += 1
            else:
                result[postcode] = {'Postcode': postcode,
                                    'Total Cases': 1,
                                    'DateOfLastCase': postcode_item['date'],
                                    'DaysSinceLastCase': postcode_item['report_age']}

        self._counts_by_postcode = result

        return copy.deepcopy(result)

    def counts_by_date_and_postcode(self):
        """

        :return: {yyyymmddpppp: {'date_string': str, 'date': datetime, 'postcode': int, 'report_age': int, 'count': int}
        :rtype: dict
        """
        if self._counts_by_date_and_postcode:
            return copy.deepcopy(self._counts_by_date_and_postcode)

        result = {}
        for item in self.items:
            key_val = item['date_string'] + item['postcode']
            result_value = result.get(key_val, None)
            if result_value:
                result_value['count'] += 1
            else:
                result_value = copy.deepcopy(item)
                result_value['count'] = 1
                result[key_val] = result_value

        self._counts_by_date_and_postcode = result

        return copy.deepcopy(result)


class UpdateResultCounts(object):
    """A class to return UpdateResult counts."""
    def __init__(self, adds=0, deletes=0, updates=0, unchanged=0):
        self.adds = adds
        self.deletes = deletes
        self.updates = updates
        self.unchanged = unchanged


class TotalCasesByPostcodeFeatureLayer(object):
    def __init__(self, service_url: str,
                 postcode_field: str = 'PostCode',
                 total_cases_field: str = 'TotalCases',
                 date_of_last_case_field: str = 'DateOfLastCase',
                 days_since_last_case_field: str = 'DaysSinceLastCase'):
        self.layer = FeatureLayer(service_url)
        self.postcode_field = postcode_field
        self.totalCases_field = total_cases_field
        self.dateOfLastCase_field = date_of_last_case_field
        self.daysSinceLastCase_field = days_since_last_case_field

    def _get_updates(self, postcode_features: FeatureSet, update_values: dict):
        """

        :param postcode_features: The postcodes featureset to be updated
        :type postcode_features: FeatureSet
        :param update_values: The current count values to be applied.
        :type update_values:
        :return:
        :rtype:
        """
        updates = []
        no_change = 0

        for postcode_feature in postcode_features:
            postcode = postcode_feature.attributes[self.postcode_field]
            updated_counts = update_values.pop(postcode, None)
            if updated_counts:
                total_cases = updated_counts['Total Cases']
                date_last = updated_counts['DateOfLastCase']
                days_since = updated_counts['DaysSinceLastCase']
            else:
                total_cases = None
                date_last = None
                days_since = None

            current_cases = postcode_feature.attributes[self.totalCases_field]
            current_days_since = postcode_feature.attributes[self.daysSinceLastCase_field]
            if current_cases != total_cases or days_since != current_days_since:
                postcode_feature.attributes[self.totalCases_field] = total_cases
                postcode_feature.attributes[self.dateOfLastCase_field] = date_last
                postcode_feature.attributes[self.daysSinceLastCase_field] = days_since
                updates.append(postcode_feature)
            else:
                no_change += 1

        return updates, no_change

    def _get_adds(self, update_values):
        new_postcodes = []
        for new_item in update_values:
            # Create new item for service adds.  Explicitly assigning the values to a new item prevents any possible errors
            # if the item has additional fields.
            item = {"attributes":
                    {self.postcode_field: new_item['Postcode'],
                     self.totalCases_field: new_item['Total Cases'],
                     self.dateOfLastCase_field: new_item['DateOfLastCase'],
                     self.daysSinceLastCase_field: new_item['DaysSinceLastCase']},
                    "geometry":
                        {"x": 17100000, "y": -4600000}}

            new_postcodes.append(item)

        return new_postcodes

    def update_from_case_list(self, case_list: CaseList):
        """
        Updates the layer using the values in the case_list parameter.

        If a postcode in the service is not found in the case_list then the value for that postcode is set to None.
        Postcodes are never deleted from the service.

        If postcodes are found in the case_list that are not in the table, then those postcodes are added to the service.

        This function does not alter the case_list object.

        :param case_list: The case list to be used to update the feature layer.
        :type case_list: CaseList
        :return:
        :rtype: UpdateResultCounts
        """
        # make a local copy of postcode_counts so we don't inadvertently change the source dictionary for other uses.
        update_values = case_list.counts_by_postcode()

        # get featureset from target service
        query_result = self.layer.query()
        postcode_features = query_result.features

        updates, no_change = self._get_updates(postcode_features, update_values)
        adds = self._get_adds(update_values)

        if updates or adds:
            self.layer.edit_features(updates=updates, adds=adds)

        return UpdateResultCounts(adds=len(adds),
                                  updates=len(updates),
                                  unchanged=no_change)

    def get_geometry_lookups(self, where_clause: str = None):
        """
        Gets a dictionary of {key: geometry pairs}
        :param where_clause:
        :type where_clause:
        :return:
        :rtype:
        """
        result = {}
        if where_clause:
            query_result = self.layer.query(out_fields=[self.postcode_field], where=where_clause)
        else:
            query_result = self.layer.query(out_fields=[self.postcode_field])

        postcode_features = query_result.features
        for postcode_feature in postcode_features:
            postcode = postcode_feature.attributes[self.postcode_field]
            geometry = postcode_feature.geometry
            result[postcode] = geometry

        return result


class IndividualCasesByPostcodeFeatureLayer(object):
    def __init__(self, service_url: str, date_string_field='DateString', postcode_field='PostCode', report_date_field='ReportDate',
                 report_age_field='ReportAge', oid_field='OBJECTID'):
        self.layer = FeatureLayer(service_url)
        self.oid_field = oid_field
        self.dateString_field = date_string_field
        self.postcode_field = postcode_field
        self.reportAge_field = report_age_field
        self.reportDate_field = report_date_field

    @staticmethod
    def _get_source_values(case_list, postcode_centroids, default_xy=(17100000, -4600000)):
        """
        Generates the update values by combining counts by date and postcode from the case list
        and postcode centroids from the geometry source.

        :param case_list: The CaseList containing the cases to be used to update the FeatureLayer
        :type case_list: CaseList
        :param postcode_centroids: A lookup of postcode centroid geometries
        :type postcode_centroids: dict
        :param default_xy: Optional - The xy tuple to be used if no matching postcode geometry is found.
        Default is (17100000, -4600000), a WGS84-WMAS coordinate that falls of the NSW/VIC coast.
        :type default_xy: tuple (float, float)
        :return: {yyyymmddpppp: {'date_string': str, 'date': datetime, 'postcode': int, 'report_age': int, 'count': int, 'xy': (float, float)}
        :rtype: dict
        """

        result = case_list.counts_by_date_and_postcode()

        # add the coordinate values to each item.
        for item in result.values():
            postcode_centroid = postcode_centroids.get(item['postcode'], None)
            if postcode_centroid:
                item['xy'] = postcode_centroid
            else:
                item['xy'] = {'x': default_xy[0], 'y': default_xy[1]}

        return result

    def update(self, case_list, postcode_centroids, default_xy=(17100000, -4600000)):

        source_values = self._get_source_values(case_list, postcode_centroids, default_xy)

        # get featureset from target service
        query_result = self.layer.query()
        postcode_features = query_result.features

        adds = []
        deletes = []
        updates = []
        unchanged = 0

        for postcode_feature in postcode_features:
            postcode = postcode_feature.attributes[self.postcode_field]
            datestring = postcode_feature.attributes[self.dateString_field]
            key_value = datestring + postcode
            item = source_values.get(key_value, None)
            if item:
                if item['count'] == 1:
                    """ Remove the item from source if all source items have been matched.
                    Additional items in the feature layer with the same key will be deleted."""
                    source_values.pop(key_value)
                item['count'] -= 1
                if item['report_age'] != postcode_feature.attributes[self.reportAge_field]:
                    """If the report age values are not equal, updates are required.
                    We do not need to compare postcode or date values because they are defined
                    at record creation and do not change. A source record where the postcode or date changes
                    will result in a deletion of the current record and a creation of a new record with the
                    new date/postcode key."""
                    postcode_feature.attributes[self.reportAge_field] = item['report_age']
                    updates.append(postcode_feature)
                else:
                    unchanged += 1

            else:  # if no match found in source, add the OID to the deletes
                deletes.append(postcode_feature.attributes[self.oid_field])

        # any items left in the source_values represent new records.  Append them to the Adds list.
        for source_value in source_values.values():
            item = {"attributes": {
                        self.postcode_field: source_value['postcode'],
                        self.dateString_field: source_value['date_string'],
                        self.reportDate_field: source_value['date'],
                        self.reportAge_field: source_value['report_age']
                     },
                    "geometry": source_value['xy']}

            for i in range(source_value['count']):
                adds.append(item)

        if updates or adds or deletes:
            self.layer.edit_features(updates=updates, adds=adds, deletes=str(deletes))

        return UpdateResultCounts(adds=len(adds), deletes=len(deletes), updates=len(updates), unchanged=unchanged)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile", required=False, help="Local Profile used to access the ArcGIS Online instance.")
    parser.add_argument("-l", "--log", required=True, help='Log file to be created or used.')

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        handlers=[
            logging.FileHandler(args.log),
            logging.StreamHandler()
        ]
    )

    try:
        # parse source source_data
        case_data = CaseList()
        case_data.append_nsw_data(nsw_source)

        # create GIS connection
        logging.info('Start signin using profile credentials')
        gis = GIS(profile=args.profile)
        logging.info('End signin using profile credentials')

        logging.info('Updating Postcode Counts: ' + count_by_postcode_target)
        total_cases_by_postcode = TotalCasesByPostcodeFeatureLayer(service_url=count_by_postcode_target)
        update_results = total_cases_by_postcode.update_from_case_list(case_list=case_data)
        logging.info('SUCCESS - Updates: {}, Inserts: {}, Deletes: {}, Unchanged: {}'.format(update_results.updates, update_results.adds,
                                                                                             update_results.deletes, update_results.unchanged))

        logging.info('Updating Individual Cases by Postcode: ' + count_by_postcode_target)
        postcode_centroid_source = total_cases_by_postcode.get_geometry_lookups()
        case_locations = IndividualCasesByPostcodeFeatureLayer(service_url=individual_cases_by_postcode_target)
        update_results = case_locations.update(case_list=case_data, postcode_centroids=postcode_centroid_source)
        logging.info('SUCCESS - Updates: {}, Inserts: {}, Deletes: {}, Unchanged: {}'.format(update_results.updates, update_results.adds,
                                                                                             update_results.deletes, update_results.unchanged))

    except Exception as e:
        logging.error(e, exc_info=True)
