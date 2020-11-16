import csv
import copy
import datetime
import urllib.request
import io
import logging


# https://github.com/M3IT/COVID-19_Data/tree/master/Data


class COVID_AU_state(object):
    def __init__(self, source_url=r'https://raw.githubusercontent.com/M3IT/COVID-19_Data/master/Data/COVID_AU_state.csv'):
        self.source_url = source_url
        self.fields = COVID_AU_state.Fields()

        self._source_data = None

    def load(self):
        """
        Loads or reloads the NswTestData.source_data element from the source url and returns a copy of the loaded data.
        :return: [{},{}]
        :rtype: list[dict]
        """
        logging.info('Loading: ' + self.source_url)
        with urllib.request.urlopen(self.source_url) as response:
            content = response.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))

            data = []
            for row in reader:
                date_string = row[self.fields.date]
                row[self.fields.date] = datetime.datetime.strptime(date_string, '%Y-%m-%d')
                for numeric_field in self.fields.numeric_fields():
                    numeric_val = row[numeric_field]
                    if numeric_val in ['NA']:
                        row[numeric_field] = 0
                    else:
                        row[numeric_field] = int(row[numeric_field])
                data.append(row)

        self._source_data = data
        # return a copy so that the original loaded source is not altered by downstream processes.
        return copy.deepcopy(data)

    def source_data(self):
        """
        Returns a copy of the source data.  If not previously loaded, a load is performed first.
        :return: [{}]
        :rtype: list[dict]
        """
        if not self._source_data:
            return self.load()  # load already returns a copy, no need to re-copy

        # return a copy so that the original loaded source is not altered by downstream processes.
        return copy.deepcopy(self._source_data)

    def by_date_and_state(self):
        result = {}
        for item in self.source_data():
            date_code = item[self.fields.date].strftime('%Y%m%d')
            key = '{}_{}'.format(date_code, item[self.fields.state_abbrev])
            result[key] = item

    class Fields(object):
        def __init__(self):
            self.date = 'date'
            self.state = 'state'
            self.state_abbrev = 'state_abbrev'
            self.confirmed = 'confirmed'
            self.total_confirmed = 'confirmed_cum'
            self.deaths = 'deaths'
            self.total_deaths = 'deaths_cum'
            self.tests = 'tests'
            self.total_tests = 'tests_cum'
            self.positives = 'positives'
            self.total_positives = 'positives_cum'
            self.recovered = 'recovered'
            self.total_recovered = 'recovered_cum'
            self.hospitalised = 'hosp'
            self.total_hospitalised = 'hosp_cum'
            self.icu = 'icu'
            self.total_icu = 'icu_cum'
            self.vent = 'vent'
            self.total_vent = 'vent_cum'

        def numeric_fields(self):
            return [self.confirmed, self.total_confirmed, self.deaths, self.total_deaths, self.tests, self.total_tests,
                    self.positives, self.total_positives, self.recovered, self.total_recovered, self.hospitalised, self.total_hospitalised,
                    self.icu, self.total_icu, self.vent, self.total_vent]