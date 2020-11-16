import os
import urllib.request
import json
from datetime import datetime


class DataEngine(object):
    """A factory class to create DataEngine objects"""
    def __init__(self, url=r'http://130.56.246.102/'):
        self._url = url
        self._cases_by_date_and_state = None
        self._cases_by_date_and_postcode = None
        self._cases_by_date_postcode_and_source = None
        self._deaths_by_date_and_state = None
        self._tests_by_date_and_state = None
        self._tests_by_date_and_postcode = None

    def cases_by_date_and_state(self):
        if not self._cases_by_date_and_state:
            url_value = os.path.join(self._url, 'casesbydateandstate')
            self._cases_by_date_and_state = CasesByDateAndState(url=url_value)
        return self._cases_by_date_and_state

    def deaths_by_date_and_state(self):
        if not self._deaths_by_date_and_state:
            url_value = os.path.join(self._url, 'deathsbydateandstate')
            self._deaths_by_date_and_state = DeathsByDateAndState(url=url_value)
        return self._deaths_by_date_and_state

    def tests_by_date_and_state(self):
        if not self._tests_by_date_and_state:
            url_value = os.path.join(self._url, 'testsbydateandstate')
            self._tests_by_date_and_state = TestsByDateAndState(url=url_value)
        return self._tests_by_date_and_state

    def tests_by_date_and_postcode(self):
        if not self._tests_by_date_and_postcode:
            url_value = os.path.join(self._url, 'testsbydateandpostcode')
            self._tests_by_date_and_postcode = TestsByDateAndPostcode(url=url_value)
        return self._tests_by_date_and_postcode

    def cases_by_date_and_postcode(self):
        if not self._cases_by_date_and_postcode:
            url_value = os.path.join(self._url, 'casesbydateandpostcode')
            self._cases_by_date_and_postcode = CasesByDateAndPostcode(url=url_value)
        return self._cases_by_date_and_postcode

    def cases_by_date_postcode_and_source(self):
        if not self._cases_by_date_postcode_and_source:
            url_value = os.path.join(self._url, 'nsw_postcode_cases')
            self._cases_by_date_postcode_and_source = CasesByDatePostcodeAndSource(url=url_value)
        return self._cases_by_date_postcode_and_source


class CasesByDateAndState(object):
    def __init__(self, url=r'http://130.56.246.102/casesbydateandstate'):
        self.url = url
        self.date_index = 1
        self.state_index = 2
        self.cases_index = 3
        self._data = None

    def load(self):
        """
        Loads the data from the data engine
        :return: [{'State': state, 'Date': datetime, 'Cases': int},...]
        :rtype:
        """
        with urllib.request.urlopen(self.url) as response:
            content = response.read().decode('utf-8')
            data = json.loads(content)

        result = []
        for item in data:
            date_value = datetime.strptime(str(item[self.date_index]), '%Y%m%d')
            result.append({'Date': date_value,
                           'State': item[self.state_index],
                           'Cases': item[self.cases_index]})

        self._data = result
        return result

    def records(self):
        """
        Returns the Cases by Date and State records from the data engine.  Uses loaded records if they have been previously loaded.
        :return:  [{'State': state, 'Date': datetime, 'Cases': int},...]
        :rtype:
        """
        if self._data is None:
            self.load()

        return self._data


class CasesByDateAndPostcode(object):
    def __init__(self, url=r'http://130.56.246.102/casesbydateandpostcode'):
        self.url = url
        self.date_index = 1
        self.postcode_index = 2
        self.cases_index = 3
        self._data = None

    def load(self):
        """
        Loads the data from the data engine
        :return: [{'Postcode': str, 'Date': datetime, 'Cases': int},...]
        :rtype:
        """
        with urllib.request.urlopen(self.url) as response:
            content = response.read().decode('utf-8')
            data = json.loads(content)

        result = []
        for item in data:
            date_value = datetime.strptime(str(item[self.date_index]), '%Y%m%d')
            result.append({'Date': date_value,
                           'Postcode': item[self.postcode_index],
                           'Cases': item[self.cases_index]})

        self._data = result

        return result

    def records(self):
        """
        Returns the Cases by Date and Postcode records from the data engine.  Uses loaded records if they have been previously loaded.
        :return:  [{'Postcode': str, 'Date': datetime, 'Cases': int},...]
        :rtype:
        """
        if self._data is None:
            self.load()

        return self._data


class CasesByDatePostcodeAndSource(object):
    def __init__(self, url=r'http://130.56.246.102/nsw_postcode_cases'):
        self.url = url
        self.date_index = 1
        self.postcode_index = 2
        self.likely_source_index = 3
        self._data = None

        self.source_conversions = {'Overseas': 'Overseas',
                                   'Locally acquired - source not identified': 'Locally Acquired - Unknown Source',
                                   'Locally acquired - contact of a confirmed case and/or in a known cluster': 'Locally Acquired - Known Source',
                                   'Interstate': 'Interstate'}

    def load(self):
        """
        Loads the data from the data engine
        :return: [{'Postcode': str, 'Date': datetime, 'Cases': int},...]
        :rtype:
        """
        with urllib.request.urlopen(self.url) as response:
            content = response.read().decode('utf-8')
            data = json.loads(content)

        wkg = {}
        for item in data:
            date_value = datetime.strptime(str(item[self.date_index]), '%Y-%m-%d')
            postcode_value = item[self.postcode_index]
            if not postcode_value:
                postcode_value = 'UNK'

            likely_source_value = item[self.likely_source_index]
            likely_source_value = self.source_conversions[likely_source_value]  # convert to tidier source names
            key = '{}_{}_{}'.format(date_value, postcode_value, likely_source_value)
            record = wkg.get(key, None)
            if record:
                record['Cases'] += 1
            else:
                wkg[key] = {'Date': date_value,
                            'Postcode': postcode_value,
                            'Cases': 1,
                            'LikelySource': likely_source_value}

        self._data = list(wkg.values())

        return self._data

    def records(self):
        """
        Returns the Cases by Date and Postcode records from the data engine.  Uses loaded records if they have been previously loaded.
        :return:  [{'Postcode': str, 'Date': datetime, 'Cases': int},...]
        :rtype:
        """
        if self._data is None:
            self.load()

        return self._data


class DeathsByDateAndState(object):
    def __init__(self, url=r'http://130.56.246.102/deathsbydateandstate'):
        self.url = url
        self.date_index = 1
        self.state_index = 2
        self.deaths_index = 3
        self._data = None

    def load(self):
        """
        Loads the data from the data engine
        :return: [{'State': state, 'Date': datetime, 'Deaths': int},...]
        :rtype:
        """
        with urllib.request.urlopen(self.url) as response:
            content = response.read().decode('utf-8')
            data = json.loads(content)

        result = []
        for item in data:
            date_value = datetime.strptime(str(item[self.date_index]), '%Y%m%d')
            result.append({'Date': date_value,
                           'State': item[self.state_index],
                           'Deaths': item[self.deaths_index]})

        self._data = result
        return result

    def records(self):
        """
        Returns the Deaths by Date and State records from the data engine.  Uses loaded records if they have been previously loaded.
        :return:  [{'State': state, 'Date': datetime, 'Deaths': int},...]
        :rtype:
        """
        if self._data is None:
            self.load()

        return self._data


class TestsByDateAndState(object):
    def __init__(self, url=r'http://130.56.246.102/testsbydateandstate'):
        self.url = url
        self.date_index = 1
        self.state_index = 2
        self.tests_index = 3
        self._data = None

    def load(self):
        """
        Loads the data from the data engine
        :return: [{'State': state, 'Date': datetime, 'Tests': int},...]
        :rtype:
        """
        with urllib.request.urlopen(self.url) as response:
            content = response.read().decode('utf-8')
            data = json.loads(content)

        result = []
        for item in data:
            date_value = datetime.strptime(str(item[self.date_index]), '%Y%m%d')
            result.append({'Date': date_value,
                           'State': item[self.state_index],
                           'Tests': item[self.tests_index]})

        self._data = result
        return result

    def records(self):
        """
        Returns the Tests by Date and State records from the data engine.  Uses loaded records if they have been previously loaded.
        :return:  [{'State': state, 'Date': datetime, 'Tests': int},...]
        :rtype:
        """
        if self._data is None:
            self.load()

        return self._data


class TestsByDateAndPostcode(object):
    def __init__(self, url=r'http://130.56.246.102/testsbydateandpostcode'):
        self.url = url
        self.date_index = 1
        self.postcode_index = 2
        self.tests_index = 3
        self._data = None

    def load(self):
        """
        Loads the data from the data engine
        :return: [{'Postcode': postcode, 'Date': datetime, 'Tests': int},...]
        :rtype:
        """
        with urllib.request.urlopen(self.url) as response:
            content = response.read().decode('utf-8')
            data = json.loads(content)

        result = []
        for item in data:
            date_value = datetime.strptime(str(item[self.date_index]), '%Y%m%d')
            result.append({'Date': date_value,
                           'Postcode': item[self.postcode_index],
                           'Tests': item[self.tests_index]})

        self._data = result
        return result

    def records(self):
        """
        Returns the Tests by Date and Postcode records from the data engine.  Uses loaded records if they have been previously loaded.
        :return:  [{'Postcode': str, 'Date': datetime, 'Tests': int},...]
        :rtype:
        """
        if self._data is None:
            self.load()

        return self._data


class QldData(object):
    def __init__(self, url=r'http://130.56.246.102/qld'):
        self.url = url
