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
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from arcgis.features import FeatureSet

# Windows profile holding the credentials to be used to connect to the national_time_series_target
profile = 'agol_graphc'

# file path to log file.
logfile = r'E:\Documents2\tmp\UpdateNationalTimeSeries_AppendOnly.log'

jhu_cases = r'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/' \
            r'time_series_covid19_confirmed_global.csv'
jhu_deaths = r'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/' \
             r'time_series_covid19_deaths_global.csv'
jhu_recovered = r'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/' \
                r'time_series_covid19_recovered_global.csv'

national_time_series_target = r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/National_Time_Series/FeatureServer/0'

state_coords = {'Australian Capital Territory':  {"x": 16601000, 'y': -4202000},
                'New South Wales': {"x": 16833000, 'y': -4011000},
                'Northern Territory': {"x": 14566000, 'y': -1398000},
                'Queensland': {"x": 17034000, 'y': -3182000},
                'South Australia': {"x": 15429000, 'y': -4154000},
                'Tasmania': {"x": 16400000, 'y': -5294000},
                'Victoria': {"x": 16137000, 'y': -4553000},
                'Western Australia': {"x": 12897000, 'y': -3757000},
                'Australia': {"x": 15000000, 'y': -2900000}}


def parse_john_hopkins_time_series(source_url):
    with urllib.request.urlopen(source_url) as response:
        content = response.read().decode('utf-8')
        reader = csv.reader(io.StringIO(content))

        broken_date = datetime.datetime(2020, 4, 14)
        australia = {}
        result = {'Australia': australia}
        headers = None
        row_length = 0
        for row in reader:
            # get the headers from the first row.
            if not headers:
                headers = row[:]
                row_length = len(headers)
                for i in range(4, row_length):
                    date_string = headers[i]
                    # m, d, y = date_string.split('/')
                    # date = datetime.datetime(int('20' + y), int(m), int(d))
                    date = datetime.datetime.strptime(date_string, "%m/%d/%y")

                    if date > broken_date:
                        date += datetime.timedelta(days=1)

                    headers[i] = date

            aus_data = []
            # if the record is associated with Australia
            if row[1] == 'Australia':
                aus_data.append(row)
                # create a value dictionary for the region
                region_values = {}

                # for each date column in the table
                for i in range(4, row_length):
                    date = headers[i]  # date from headers
                    cases = int(row[i])  # case count from row
                    region_values[date] = cases  # add item to regional values

                    # add counts to Australian total for date.
                    if date in australia:
                        australia[date] += cases
                    else:
                        australia[date] = cases

                result[row[0]] = region_values

        return result


def pre_process(data, totals_name, deltas_name, target_dict):
    """
    Appends or updates the target_dict to include the new source_data values.
    - If a region/date combo does found in the source_data does not exist in the target_dict, then a new item will be created.
    - If totals_name and/or deltas_name does not exist in an item, then they will be added using the source_data values.
      If they do exist, then the values will be updated to match the source_data values.
    :param data: {region: {date: total_cases}}
    :type data:
    :param totals_name:
    :type totals_name:
    :param deltas_name:
    :type deltas_name:
    :param target_dict: A dict to be updated.  May optionally already contain items in the format:
           {regionyyyymmdd: {'date': datetime.date, 'region': string, ....}}, where .... are optional other key: value pairs.
    :type target_dict: dict
    :return: {regionyyyymmdd: {totals_name: int, deltas_name: int, 'date': datetime.date, 'region': string, ....}}
    :rtype:
    """

    for region, daily_totals in data.data():
        last_total = 0
        sorted_dates = sorted(daily_totals.keys())
        for date in sorted_dates:
            key_val = region + date.strftime('%Y%m%d')
            this_total = daily_totals[date]
            daily_stats = target_dict.get(key_val, None)
            if daily_stats:
                daily_stats[totals_name] = this_total
                daily_stats[deltas_name] = this_total - last_total
            else:
                target_dict[key_val] = {'region': region, 'date': date, totals_name: this_total, deltas_name: this_total-last_total}

            last_total = this_total

    return target_dict


def get_source_data():
    """
    Parses the source source_data and returns a dict of values indexed by a regiondate string key.
    :return: {regionyyyymmdd: {'NewCases': int, 'NewDeaths': int, 'NewRecovered': int, 'TotalCases': int, 'TotalDeaths': int,
                      'TotalRecovered': int, 'date': datetime.date, 'region': string}
    :rtype: dict
    """
    cases_data = parse_john_hopkins_time_series(jhu_cases)
    deaths_data = parse_john_hopkins_time_series(jhu_deaths)
    recovered_data = parse_john_hopkins_time_series(jhu_recovered)

    result = pre_process(cases_data, 'TotalCases', 'NewCases', {})
    pre_process(deaths_data, 'TotalDeaths', 'NewDeaths', result)
    pre_process(recovered_data, 'TotalRecovered', 'NewRecovered', result)

    for item in result.values():
        item['ActiveCases'] = item['TotalCases'] - (item['TotalDeaths'] + item['TotalRecovered'])

    return result


class NationalTimeSeries(object):
    def __init__(self, service_url: str,
                 date_field: str = 'Date',
                 region_field: str = 'Region',
                 new_cases_field: str = 'NewCases',
                 new_deaths_field: str = 'NewDeaths',
                 new_recoveries_field: str = 'NewRecoveries',
                 total_cases_field: str = 'TotalCases',
                 total_deaths_field: str = 'TotalDeaths',
                 total_recoveries_field: str = 'TotalRecoveries',
                 active_cases_field: str = 'ActiveCases'):
        self.layer = FeatureLayer(service_url)
        self.region_field = region_field
        self.date_field = date_field
        self.new_cases_field = new_cases_field
        self.new_deaths_field = new_deaths_field
        self.new_recoveries_field = new_recoveries_field
        self.total_cases_field = total_cases_field
        self.total_deaths_field = total_deaths_field
        self.total_recoveries_field = total_recoveries_field
        self.active_cases_field = active_cases_field

    def _get_adds(self, target_features: FeatureSet, update_values: dict):

        # Make a copy so no items are removed from the source update_values item.
        update_copy = copy.deepcopy(update_values)

        # remove all items with matching key value.
        for target_feature in target_features:
            region = target_feature.attributes[self.region_field]
            date = datetime.datetime.fromtimestamp(target_feature.attributes[self.date_field]/1000)
            key_val = region + date.strftime('%Y%m%d')
            update_copy.pop(key_val, None)

        # only new items remain.  Create adds for new items.
        new_features = []
        for new_item in update_copy.values():
            # Create new item for service adds.  Explicitly assigning the values to a new item prevents any possible errors
            # if the item has additional fields.
            item = {"attributes":
                        {self.date_field: new_item['date'],
                         self.region_field: new_item['region'],
                         self.new_cases_field: new_item['NewCases'],
                         self.total_cases_field: new_item['TotalCases'],
                         self.new_deaths_field: new_item['NewDeaths'],
                         self.total_deaths_field: new_item['TotalDeaths'],
                         self.new_recoveries_field: new_item['NewRecovered'],
                         self.total_recoveries_field: new_item['TotalRecovered'],
                         self.active_cases_field: new_item['ActiveCases']},
                    "geometry": state_coords.get(new_item['region'], {"x": 17100000, "y": -4600000})}

            new_features.append(item)

        return new_features

    def update(self, update_values):
        # get featureset from target service
        query_result = self.layer.query()
        target_features = query_result.features

        # get new values (adds)
        adds = self._get_adds(target_features=target_features, update_values=update_values)

        # update feature layer
        if adds:
            self.layer.edit_features(adds=adds)

        return len(adds)


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        filename=logfile
    )

    try:

        source_data = get_source_data()

        # create GIS connection
        logging.info('Start signin using profile credentials')
        gis = GIS(profile=profile)
        logging.info('End signin using profile credentials')

        logging.info('Updating National Statistics: ' + national_time_series_target)
        total_cases_by_postcode = NationalTimeSeries(service_url=national_time_series_target)
        add_count = total_cases_by_postcode.update(update_values=source_data)
        logging.info('SUCCESS - Records Added: {}'.format(add_count))

    except Exception as e:
        print(e)
        logging.error(e, exc_info=True)
