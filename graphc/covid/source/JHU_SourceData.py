import csv
import urllib.request
import io
import datetime
import logging


class JhuCasesData(object):
    def __init__(self):
        self.source_url = r'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/' \
                          r'time_series_covid19_confirmed_global.csv'

        self._source_data = None

    def load(self):
        logging.info('Loading JHU data from source: ' + self.source_url)
        self._source_data = _parse_john_hopkins_time_series(self.source_url)
        return self._source_data

    def source_data(self):
        """
        The number of cases for each state and date.
        :return: {region: {date_code: cases}}
        :rtype: {str: {str: int}}
        """
        if not self._source_data:
            self.load()

        return self._source_data

    def counts_by_date_and_state(self, use_abbreviation: bool = True):
        """
        Returns counts by date and state, with a key in the form datecode_state
        :param use_abbreviation: If True, the state abbreviations are used as the state values, otherwise the state name is used.
        :return: {key: count}
        :rtype: dict
        """
        result = {}
        data = self.source_data()

        state_abbreviations = _state_abbreviations()

        for state, values in data.items():
            if use_abbreviation:
                state = state_abbreviations[state.upper()]

            previous_count = 0
            for date_code, count in values.items():
                if count != previous_count:
                    cases = count - previous_count
                    key = '{}_{}'.format(date_code, state)
                    result[key] = cases
                    previous_count = count

        return result


class JhuDeathsData(object):
    def __init__(self):
        self.source_url = r'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/' \
                          r'time_series_covid19_deaths_global.csv'

        self._source_data = None

    def load(self):
        logging.info('Loading JHU data from source: ' + self.source_url)
        self._source_data = _parse_john_hopkins_time_series(self.source_url)
        return self._source_data

    def source_data(self):
        """
        The number of deaths for each state and date.
        :return: {region: {date_code: deaths}}
        :rtype: {str: {str: int}}
        """
        if not self._source_data:
            self.load()

        return self._source_data

    def counts_by_date_and_state(self, use_abbreviation: bool = True):
        """
        Returns counts by date and state, with a key in the form datecode_state
        :param use_abbreviation: If True, the state abbreviations are used as the state values, otherwise the state name is used.
        :return: {key: count}
        :rtype: dict
        """
        result = {}
        data = self.source_data()

        state_abbreviations = _state_abbreviations()

        for state, values in data.items():
            if use_abbreviation:
                state = state_abbreviations[state.upper()]

            previous_count = 0
            for date_code, count in values.items():
                if count != previous_count:
                    deaths = count - previous_count
                    key = '{}_{}'.format(date_code, state)
                    result[key] = deaths
                    previous_count = count

        return result


class JhuRecoveredData(object):
    def __init__(self):
        self.source_url = r'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/' \
                          r'time_series_covid19_recovered_global.csv'

        self._source_data = None

    def load(self):
        """
        Forces a load or reload from the csv source.  The loaded data is stored internally for later used and can be accessed by calling
        the source_data method.  If you do not need to explicitly force a reload, you should call source_data instead of this method.
        :return: {region: {date_code: recovered}}
        :rtype: {str: {str: int}}
        """
        logging.info('Loading JHU data from source: ' + self.source_url)
        self._source_data = _parse_john_hopkins_time_series(self.source_url)
        return self._source_data

    def source_data(self):
        """
        The number of recoveries for each state and date.
        :return: {region: {date_code: recovered}}
        :rtype: {str: {str: int}}
        """
        if not self._source_data:
            self.load()

        return self._source_data


def _parse_john_hopkins_time_series(source_url):
    """
    Parses the time series data found at the source url and returns the data as a dictionary
    :param source_url: The URL of the source John Hopkins Time Series csv.
    :type source_url: str
    :return: {region: {date_code: value}}
    :rtype: dict
    """
    with urllib.request.urlopen(source_url) as response:
        content = response.read().decode('utf-8')
        reader = csv.reader(io.StringIO(content))

        broken_date = datetime.datetime(2020, 4, 14)
        result = {}
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

                    headers[i] = date.strftime('%Y%m%d')

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

                result[row[0]] = region_values

        return result


def _state_abbreviations():
    return {'AUSTRALIAN CAPITAL TERRITORY': 'ACT',
            'NEW SOUTH WALES': 'NSW',
            'VICTORIA': 'VIC',
            'TASMANIA': 'TAS',
            'QUEENSLAND': 'QLD',
            'SOUTH AUSTRALIA': 'SA',
            'NORTHERN TERRITORY': 'NT',
            'WESTERN AUSTRALIA': 'WA'}
