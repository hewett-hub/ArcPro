import csv
import datetime
import urllib.request
import io
import logging

#https://data.nsw.gov.au/data/datastore/dump/945c6204-272a-4cad-8e33-dde791f5059a?bom=True

#https://data.nsw.gov.au/data/datastore/dump/945c6204-272a-4cad-8e33-dde791f5059a?format=json


class NswTestData(object):
    def __init__(self,
                 source_url=r'https://data.nsw.gov.au/data/dataset/'
                            r'60616720-3c60-4c52-b499-751f31e3b132/resource/945c6204-272a-4cad-8e33-dde791f5059a/download/'
                            r'covid-19-tests-by-date-and-postcode-local-health-district-and-local-government-area.csv',
                 date_field='test_date',
                 postcode_field='postcode',
                 lhd_code_field='lhd_2010_code',
                 lhd_name_field='lhd_2010_name',
                 lga_code_field='lga_code19',
                 lga_name_field='lga_name19'):
        self.source_url = source_url
        self.date_field = date_field
        self.postcode_field = postcode_field
        self.lhd_code_field = lhd_code_field
        self.lhd_name_field = lhd_name_field
        self.lga_code_field = lga_code_field
        self.lga_name_field = lga_name_field
        self.csv_date_format = '%Y-%m-%d'
        self.out_date_format = '%Y%m%d'
        self._source_data = None

    def load(self):
        """
        Loads or reloads the NswTestData.source_data element from the source url.

        :return: [{date_field: str, postcode_field: str, lhd_code_field: str, lhd_name_field: str, lga_code_field: str, lga_name_field: str}]
        :rtype: list[dict]
        """
        logging.info('Loading NSW Test data from source: ' + self.source_url)
        with urllib.request.urlopen(self.source_url) as response:
            content = response.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            data = []
            for row in reader:
                date_string = row[self.date_field]
                if date_string:
                    row[self.date_field] = self._reformat_date_string(date_string=date_string, out_format=self.out_date_format)
                    data.append(row)
                    # clean up blank (unknown) postcodes
                    if not row[self.postcode_field]:
                        row[self.postcode_field] = 'UNK'
            self._source_data = data

            return self._source_data

    def source_data(self):
        """
        Returns the NSW source data.  If not previously loaded, a load is performed first.
        :return: [{date_field: str, postcode_field: str, lhd_code_field: str, lhd_name_field: str, lga_code_field: str, lga_name_field: str}]
        :rtype: list[dict]
        """
        if not self._source_data:
            self.load()

        return self._source_data

    def counts_by_date_and_postcode(self):
        """
        Returns counts by date and postcode, with a key in the form datecode_postcode
        :return: {key: count}
        :rtype: dict
        """
        result = {}
        data = self.source_data()
        for row in data:
            key = '{}_{}'.format(row[self.date_field], row[self.postcode_field])
            result[key] = result.get(key, 0) + 1

        return result

    def counts_by_date(self):
        """
        Returns counts by date
        :return: {date_code: count}
        :rtype: dict
        """
        result = {}
        data = self.source_data()
        for row in data:
            date_code = row[self.date_field]
            result[date_code] = result.get(date_code, 0) + 1

        return result

    def _reformat_date_string(self, date_string, out_format):
        """
        Reformats the submitted date or datetime string to the correct format for the date_code field
        :type date_string: str
        :param out_format: the format string of the submitted date_string.  eg: '%Y-%m-%d'
        :type out_format: str
        :return: The reformatted date_string
        :rtype: str
        """

        dt = datetime.datetime.strptime(date_string, self.csv_date_format)
        return dt.strftime(out_format)


class NswNotificationData(object):
    def __init__(self,
                 source_url=r'https://data.nsw.gov.au/data/dataset/'
                            r'aefcde60-3b0c-4bc0-9af1-6fe652944ec2/resource/21304414-1ff1-4243-a5d2-f52778048b29/download/'
                            r'covid-19-cases-by-notification-date-and-postcode-local-health-district-and-local-government-area.csv',
                 date_field='notification_date',
                 postcode_field='postcode',
                 lhd_code_field='lhd_2010_code',
                 lhd_name_field='lhd_2010_name',
                 lga_code_field='lga_code19',
                 lga_name_field='lga_name19'):
        self.source_url = source_url
        self.date_field = date_field
        self.postcode_field = postcode_field
        self.lhd_code_field = lhd_code_field
        self.lhd_name_field = lhd_name_field
        self.lga_code_field = lga_code_field
        self.lga_name_field = lga_name_field
        self.csv_date_format = '%Y-%m-%d'
        self.out_date_format = '%Y%m%d'
        self._source_data = None

    def load(self):
        """
        Loads or reloads the NswTestData.source_data element from the source url.

        :return: [{date_field: str, postcode_field: str, lhd_code_field: str, lhd_name_field: str, lga_code_field: str, lga_name_field: str}]
        :rtype: list[dict]
        """
        logging.info('Loading NSW Notifications data from source: ' + self.source_url)
        with urllib.request.urlopen(self.source_url) as response:
            content = response.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            data = []
            for row in reader:
                date_string = row[self.date_field]
                if date_string:  # only append row if a date exists.  This avoids including blank entries at the end of the csv.
                    row[self.date_field] = self._reformat_date_string(date_string=date_string, out_format=self.out_date_format)
                    # clean up blank (unknown) postcodes
                    if row[self.postcode_field]:
                        v = str(row[self.postcode_field])
                        if '.' in v:
                            row[self.postcode_field] = v.split('.')[0]
                        else:
                            row[self.postcode_field] = v
                    else:
                        row[self.postcode_field] = 'UNK'
                    data.append(row)
            self._source_data = data

            return self._source_data

    def source_data(self):
        """
        Returns the NSW source data.  If not previously loaded, a load is performed first.
        :return: [{date_field: str, postcode_field: str, lhd_code_field: str, lhd_name_field: str, lga_code_field: str, lga_name_field: str}]
        :rtype: dict
        """
        if not self._source_data:
            self.load()

        return self._source_data

    def counts_by_date_and_postcode(self):
        """
        Returns counts by date and postcode, with a key in the form datecode_postcode
        :return: {key: count}
        :rtype: dict
        """
        result = {}
        data = self.source_data()
        for row in data:
            key = '{}_{}'.format(row[self.date_field], row[self.postcode_field])
            result[key] = result.get(key, 0) + 1

        return result

    def counts_by_date(self):
        """
        Returns counts by date
        :return: {date_code: count}
        :rtype: dict
        """
        result = {}
        data = self.source_data()
        for row in data:
            date_code = row[self.date_field]
            result[date_code] = result.get(date_code, 0) + 1

        return result

    def _reformat_date_string(self, date_string, out_format):
        """
        Reformats the submitted date or datetime string to the correct format for the date_code field
        :type date_string: str
        :param out_format: the format string of the submitted date_string.  eg: '%Y-%m-%d'
        :type out_format: str
        :return: The reformatted date_string
        :rtype: str
        """

        if out_format == self.csv_date_format:
            return date_string

        dt = datetime.datetime.strptime(date_string, self.csv_date_format)
        return dt.strftime(out_format)


class NswNotificationAndSourceData(object):
    def __init__(self,
                 source_url=r'https://data.nsw.gov.au/data/dataset/'
                            r'97ea2424-abaf-4f3e-a9f2-b5c883f42b6a/resource/2776dbb8-f807-4fb2-b1ed-184a6fc2c8aa/download/'
                            r'confirmed_cases_table4_location_likely_source.csv',
                 date_field='notification_date',
                 postcode_field='postcode',
                 lhd_code_field='lhd_2010_code',
                 lhd_name_field='lhd_2010_name',
                 lga_code_field='lga_code19',
                 lga_name_field='lga_name19',
                 likely_source_field='likely_source_of_infection'):
        self.source_url = source_url
        self.date_field = date_field
        self.postcode_field = postcode_field
        self.lhd_code_field = lhd_code_field
        self.lhd_name_field = lhd_name_field
        self.lga_code_field = lga_code_field
        self.lga_name_field = lga_name_field
        self.likely_source_field = likely_source_field
        self.csv_date_format = '%Y-%m-%d'
        self.out_date_format = '%Y%m%d'
        self._source_data = None

    def load(self):
        """
        Loads or reloads the NswTestData.source_data element from the source url.

        :return: [{date_field: str, postcode_field: str, lhd_code_field: str, lhd_name_field: str, lga_code_field: str, lga_name_field: str}]
        :rtype: list[dict]
        """
        logging.info('Loading NSW Notifications data from source: ' + self.source_url)
        with urllib.request.urlopen(self.source_url) as response:
            content = response.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            data = []
            for row in reader:
                date_string = row[self.date_field]
                if date_string:  # only append row if a date exists.  This avoids including blank entries at the end of the csv.
                    row[self.date_field] = self._reformat_date_string(date_string=date_string, out_format=self.out_date_format)
                    # clean up blank (unknown) postcodes
                    if row[self.postcode_field]:
                        v = str(row[self.postcode_field])
                        if '.' in v:
                            row[self.postcode_field] = v.split('.')[0]
                        else:
                            row[self.postcode_field] = v
                    else:
                        row[self.postcode_field] = 'UNK'
                    data.append(row)
            self._source_data = data

            return self._source_data

    def source_data(self):
        """
        Returns the NSW source data.  If not previously loaded, a load is performed first.
        :return: [{date_field: str, postcode_field: str, lhd_code_field: str, lhd_name_field: str, lga_code_field: str, lga_name_field: str}]
        :rtype: dict
        """
        if not self._source_data:
            self.load()

        return self._source_data

    def counts_by_date_and_postcode(self):
        """
        Returns counts by date and postcode, with a key in the form datecode_postcode
        :return: {key: count}
        :rtype: dict
        """
        result = {}
        data = self.source_data()
        for row in data:
            key = '{}_{}'.format(row[self.date_field], row[self.postcode_field])
            result[key] = result.get(key, 0) + 1

        return result

    def counts_by_date(self):
        """
        Returns counts by date
        :return: {date_code: count}
        :rtype: dict
        """
        result = {}
        data = self.source_data()
        for row in data:
            date_code = row[self.date_field]
            result[date_code] = result.get(date_code, 0) + 1

        return result

    def counts_by_date_postcode_source(self):
        result = {}
        data = self.source_data()
        for row in data:
            key = '{}_{}_{}'.format(row[self.date_field], row[self.postcode_field], row[self.likely_source_field])
            result[key] = result.get(key, 0) + 1

        return result

    def _reformat_date_string(self, date_string, out_format):
        """
        Reformats the submitted date or datetime string to the correct format for the date_code field
        :type date_string: str
        :param out_format: the format string of the submitted date_string.  eg: '%Y-%m-%d'
        :type out_format: str
        :return: The reformatted date_string
        :rtype: str
        """

        if out_format == self.csv_date_format:
            return date_string

        dt = datetime.datetime.strptime(date_string, self.csv_date_format)
        return dt.strftime(out_format)


class NswCasesAgeDistributionData(object):
    def __init__(self,
                 source_url=r'https://data.nsw.gov.au/data/dataset/'
                            r'3dc5dc39-40b4-4ee9-8ec6-2d862a916dcf/resource/24b34cb5-8b01-4008-9d93-d14cf5518aec/download/'
                            r'confirmed_cases_table2_age_group.csv',
                 date_field='notification_date',
                 age_group_field='age_group'):
        self.source_url = source_url
        self.date_field = date_field
        self.age_group_field = age_group_field
        self.csv_date_format = '%Y-%m-%d'
        self.out_date_format = '%Y%m%d'
        self._source_data = None

    def load(self):
        """
        Loads or reloads the NswTestData.source_data element from the source url.

        :return: [{date_field: datetime, age_group_field: str}]
        :rtype: list[dict]
        """
        logging.info('Loading: ' + self.source_url)
        with urllib.request.urlopen(self.source_url) as response:
            content = response.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            data = []
            for row in reader:
                date_string = row[self.date_field]
                if date_string:  # only append row if a date exists.  This avoids including blank entries at the end of the csv.
                    age_group = row[self.age_group_field].split('_')[1]
                    if age_group == '0-4':
                        age_group = '00-04'
                    elif age_group == '5-9':
                        age_group = '05-09'
                    data.append({self.date_field: datetime.datetime.strptime(date_string, self.csv_date_format),
                                 self.age_group_field: age_group})
            self._source_data = data

            return self._source_data

    def source_data(self):
        """
        Returns the NSW source data.  If not previously loaded, a load is performed first.
        :return: [{date_field: datetime, age_group_field: str}]
        :rtype: list[dict]
        """
        if not self._source_data:
            self.load()

        return self._source_data

    def counts_by_date_and_age_group(self):
        """
        Returns counts by date and age group, with a key in the form yyyymmdd_age_group
        :return: {key: count}
        :rtype: dict
        """
        result = {}
        data = self.source_data()
        for row in data:
            date_code = row[self.date_field].strftime(self.out_date_format)
            key = '{}_{}'.format(date_code, row[self.age_group_field])
            result[key] = result.get(key, 0) + 1

        return result

    def counts_by_age_group(self):
        """
        Returns counts by age group
        :return: {age_group: count}
        :rtype: dict
        """
        result = {}
        data = self.source_data()
        for row in data:
            age_group = row[self.age_group_field]
            result[age_group] = result.get(age_group, 0) + 1

        return result


class NswTestsAgeDistributionData(object):
    def __init__(self,
                 source_url=r'https://data.nsw.gov.au/data/dataset/'
                            r'793ac07d-a5f4-4851-835c-3f7158c19d15/resource/28730d42-675b-4573-ad71-8156313c73a1/download/'
                            r'pcr_testing_table2_age_group_agg.csv',
                 date_field='test_date',
                 age_group_field='age_group',
                 test_count_field='test_count'):
        self.source_url = source_url
        self.date_field = date_field
        self.age_group_field = age_group_field
        self.test_count_field = test_count_field
        self.csv_date_format = '%Y-%m-%d'
        self.out_date_format = '%Y%m%d'
        self._source_data = None

    def load(self):
        """
        Loads or reloads the NswTestData.source_data element from the source url.

        :return: [{date_field: datetime, age_group_field: str, tes}]
        :rtype: list[dict]
        """
        logging.info('Loading: ' + self.source_url)
        with urllib.request.urlopen(self.source_url) as response:
            content = response.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            data = []
            for row in reader:
                date_string = row[self.date_field]
                if date_string:  # only append row if a date exists.  This avoids including blank entries at the end of the csv.
                    age_group = row[self.age_group_field].split('_')[1]
                    if age_group == '0-4':
                        age_group = '00-04'
                    elif age_group == '5-9':
                        age_group = '05-09'
                    data.append({self.date_field: datetime.datetime.strptime(date_string, self.csv_date_format),
                                 self.age_group_field: age_group,
                                 self.test_count_field: row[self.test_count_field]})
            self._source_data = data

            return self._source_data

    def source_data(self):
        """
        Returns the NSW source data.  If not previously loaded, a load is performed first.
        :return: [{date_field: datetime, age_group_field: str}]
        :rtype: list[dict]
        """
        if not self._source_data:
            self.load()

        return self._source_data

    def counts_by_date_and_age_group(self):
        """
        Returns counts by date and age group, with a key in the form yyyymmdd_age_group
        :return: {key: count}
        :rtype: dict
        """
        result = {}
        data = self.source_data()
        for row in data:
            date_code = row[self.date_field].strftime(self.out_date_format)
            key = '{}_{}'.format(date_code, row[self.age_group_field])
            result[key] = row[self.test_count_field]

        return result