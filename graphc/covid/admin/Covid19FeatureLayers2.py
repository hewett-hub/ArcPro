import datetime

from graphc.covid.admin import AuthorityData2
from graphc.covid.admin import filters
from graphc.covid.admin import statistics
from graphc.da.arcgis_helpers import TableBase


class Covid19NotificationsByDateAndPostcode(TableBase):
    """
    A feature service wrapper class that supports common operations.
    """

    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                              r'COVID19_Notifications_by_Date_and_Postcode/FeatureServer/0'):

        self.postcode_field = 'Postcode'
        self.date_field = 'Date'
        self.cases_field = 'Notifications'
        self.date_code_format = '%Y%m%d'

        super().__init__(source=source, id_field='ID')

    def create_record(self, postcode, date, cases, shape):
        date_code = date.strftime('%Y%m%d')
        id_value = '{}_{}'.format(date_code, postcode)
        return {self.id_field: id_value,
                self.postcode_field: postcode,
                self.date_field: date,
                self.cases_field: cases,
                self.shape_field: shape}

    def update_from_source(self, cases: AuthorityData2.CasesByDateAndPostcode = AuthorityData2.CasesByDateAndPostcode()):

        source_fields = [cases.postcode_field, cases.date_field, cases.cases_field, 'SHAPE@']
        source_records = cases.records(source_fields)

        target_fields = [self.id_field, self.date_field, self.postcode_field, self.cases_field, self.shape_field]

        data = {}
        for record in source_records:
            date_value = record[cases.date_field].replace(hour=12)  # force date time to midday to prevent time zone issues with midnight times.
            new_record = self.create_record(postcode=record[cases.postcode_field],
                                            date=date_value,
                                            cases=record[cases.cases_field],
                                            shape=record['SHAPE@'])
            data[new_record[self.id_field]] = new_record

        self.update_records(new_data=data, fields=target_fields, add_new=True, delete_unmatched=True, rounding=4, case_sensitive=True)


class Covid19TotalNotificationsByPostcode(TableBase):
    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                              r'COVID_19_Total_Notifications_by_Postcode/FeatureServer/0'):

        self.cases_field = 'Notifications'
        self.most_recent_code_field = 'MostRecentCode'
        self.most_recent_date_field = 'MostRecentDate'
        self.most_recent_new_field = 'MostRecentNew'

        super().__init__(source=source, id_field='Postcode')

    def create_record(self, postcode, total_cases, most_recent_case_date, most_recent_case_count, shape):
        date_code = most_recent_case_date.strftime('%Y%m%d')
        return {self.id_field: postcode,
                self.cases_field: total_cases,
                self.most_recent_date_field: most_recent_case_date,
                self.most_recent_code_field: date_code,
                self.most_recent_new_field: most_recent_case_count,
                self.shape_field: shape}

    def update_from_source(self, cases: AuthorityData2.CasesByDateAndPostcode = AuthorityData2.CasesByDateAndPostcode()):

        source_fields = [cases.postcode_field, cases.date_field, cases.cases_field, 'SHAPE@']
        source_records = cases.records(source_fields)

        target_fields = [self.id_field, self.cases_field, self.most_recent_code_field, self.most_recent_date_field, self.most_recent_new_field,
                         self.shape_field]

        new_records = {}

        most_recent = filters.most_recent_by_group(data=source_records, group_id_field=cases.postcode_field, date_field=cases.date_field)
        totals = statistics.totals_by_group(data=source_records, group_id_field=cases.postcode_field, value_field=cases.cases_field)
        for postcode, record in most_recent.items():
            total = totals.get(postcode, None)
            date_value = record[cases.date_field].replace(hour=12)  # force date time to midday to prevent time zone issues with midnight times.
            new_record = self.create_record(postcode=record[cases.postcode_field],
                                            total_cases=total,
                                            most_recent_case_date=date_value,
                                            most_recent_case_count=record[cases.cases_field],
                                            shape=record['SHAPE@'])

            new_records[new_record[self.id_field]] = new_record

        self.update_records(new_data=new_records, fields=target_fields, add_new=True, delete_unmatched=True, rounding=4, case_sensitive=True)


class Covid19PostcodeStatisticPolygons(TableBase):
    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                              r'COVID_19_Postcode_Statistic_Polygons/FeatureServer/0'):

        self.cases_field = 'TotalCases'
        self.most_recent_code_field = 'MostRecentDateCode'
        self.most_recent_date_field = 'MostRecentCaseDate'
        self.most_recent_new_field = 'MostRecentNewCases'

        super().__init__(source=source, id_field='Postcode')

    def create_record(self, postcode, total_cases, most_recent_case_date, most_recent_case_count, shape=None):
        date_code = most_recent_case_date.strftime('%Y%m%d')
        return {self.id_field: postcode,
                self.cases_field: total_cases,
                self.most_recent_date_field: most_recent_case_date,
                self.most_recent_code_field: date_code,
                self.most_recent_new_field: most_recent_case_count,
                self.shape_field: shape}

    def update_from_source(self, cases: AuthorityData2.CasesByDateAndPostcode = AuthorityData2.CasesByDateAndPostcode()):

        source_fields = [cases.postcode_field, cases.date_field, cases.cases_field]
        source_records = cases.records(source_fields)

        target_fields = [self.id_field, self.cases_field, self.most_recent_code_field, self.most_recent_date_field, self.most_recent_new_field]

        new_records = {}

        most_recent = filters.most_recent_by_group(data=source_records, group_id_field=cases.postcode_field, date_field=cases.date_field)
        totals = statistics.totals_by_group(data=source_records, group_id_field=cases.postcode_field, value_field=cases.cases_field)
        for postcode, record in most_recent.items():
            total = totals.get(postcode, None)
            date_value = record[cases.date_field].replace(hour=12)  # force date time to midday to prevent time zone issues with midnight times.
            new_record = self.create_record(postcode=record[cases.postcode_field],
                                            total_cases=total,
                                            most_recent_case_date=date_value,
                                            most_recent_case_count=record[cases.cases_field])

            new_records[new_record[self.id_field]] = new_record

        self.update_records(new_data=new_records, fields=target_fields, add_new=True, delete_unmatched=False, rounding=4, case_sensitive=True)


class Covid19StatisticsByDateAndPostcode(TableBase):
    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                              r'COVID19_Statistics_by_Date_and_Postcode/FeatureServer/0'):

        self.postcode_field = 'Postcode'
        self.date_field = 'Date'
        self.date_code_field = 'DateCode'
        self.new_cases_field = 'NewCases'
        self.total_cases_field = 'TotalCases'
        self.new_tests_field = 'NewTests'
        self.total_tests_field = 'TotalTests'
        self.ave_7_tests_field = 'Tests7DayAve'
        self.date_code_format = '%Y%m%d'

        super().__init__(source=source, id_field='ID')

    def create_record(self, date, postcode,
                      new_cases=None, total_cases=None,
                      new_tests=None, total_tests=None, ave_tests=None,
                      shape=None, date_format='%Y%m%d'):

        record_id = self.create_id(date, postcode)

        if isinstance(date, str):
            date = datetime.datetime.strptime(date, date_format)

        return {self.id_field: record_id,
                self.date_field: date.replace(hour=12),
                self.date_code_field: date.strftime('%Y%m%d'),
                self.postcode_field: postcode,
                self.new_cases_field: new_cases,
                self.total_cases_field: total_cases,
                self.new_tests_field: new_tests,
                self.total_tests_field: total_tests,
                self.ave_7_tests_field: ave_tests,
                self.shape_field: shape}

    @staticmethod
    def create_id(date, postcode):
        if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
            return '{}_{}'.format(date.strftime('%Y%m%d'), postcode)
        else:
            return '{}_{}'.format(date, postcode)

    def update_from_source(self,
                           cases: AuthorityData2.CasesByDateAndPostcode = AuthorityData2.CasesByDateAndPostcode(),
                           tests: AuthorityData2.TestsByDateAndPostcode = AuthorityData2.TestsByDateAndPostcode()):

        new_records = {}

        # Cases data
        # capture state geometries so we have them if derivative statistics cause new records to be generated for new dates.
        geometries = {}
        fields = [cases.postcode_field, cases.date_field, cases.cases_field, 'SHAPE@']
        records = cases.records(fields)
        for record in records:
            postcode = record[cases.postcode_field]
            date_value = record[cases.date_field]
            new_record = self.create_record(date=date_value,
                                            postcode=postcode,
                                            new_cases=record[cases.cases_field],
                                            shape=record['SHAPE@'])
            new_records[new_record[self.id_field]] = new_record
            if postcode not in geometries:
                geometries[postcode] = record['SHAPE@']

        # Cumulative cases.
        data = statistics.cumulative_daily_totals_by_group(data=records,
                                                           group_id_field=cases.postcode_field,
                                                           value_field=cases.cases_field,
                                                           date_field=cases.date_field)
        for id_value, value in data.items():
            record = new_records.get(id_value, None)
            if not record:
                date_code, postcode = id_value.split('_')
                record = self.create_record(date=date_code, date_format='%Y%m%d', postcode=postcode, shape=geometries.get(postcode, None))
                new_records[id_value] = record
            record[self.total_cases_field] = value

        # -----------------------------------------------------------------------------------------------------
        # Tests

        fields = [tests.postcode_field, tests.date_field, tests.tests_field, 'SHAPE@']
        records = tests.records(fields=fields)
        for record in records:
            postcode = record[tests.postcode_field]
            date_value = record[tests.date_field]
            tests_value = record[tests.tests_field]
            id_value = self.create_id(date=date_value, postcode=postcode)

            new_record = new_records.get(id_value, None)
            if not new_record:
                new_record = self.create_record(date=date_value, postcode=postcode, shape=geometries.get(postcode, None))
                new_records[id_value] = new_record
            new_record[self.new_tests_field] = tests_value

        # Cumulative deaths.
        data = statistics.cumulative_daily_totals_by_group(data=records,
                                                           group_id_field=tests.postcode_field,
                                                           value_field=tests.tests_field,
                                                           date_field=tests.date_field)
        for id_value, value in data.items():
            record = new_records.get(id_value, None)
            if not record:
                date_code, postcode = id_value.split('_')
                record = self.create_record(date=date_code, date_format='%Y%m%d', postcode=postcode, shape=geometries.get(postcode, None))
                new_records[id_value] = record
            record[self.total_tests_field] = value

        # Tests 7 day Average
        data = statistics.moving_daily_averages_by_date_and_group(data=records,
                                                                  group_id_field=tests.postcode_field,
                                                                  value_field=tests.tests_field,
                                                                  date_field=tests.date_field,
                                                                  n=7)
        for id_value, value in data.items():
            record = new_records.get(id_value, None)
            if not record:
                date_code, postcode = id_value.split('_')
                record = self.create_record(date=date_code, date_format='%Y%m%d', postcode=postcode, shape=geometries.get(postcode, None))
                new_records[id_value] = record
            record[self.ave_7_tests_field] = value

        target_fields = [self.id_field, self.date_field, self.date_code_field, self.date_field,
                         self.new_cases_field, self.total_cases_field,
                         self.new_tests_field, self.total_tests_field, self.ave_7_tests_field]

        self.update_records(new_data=new_records,
                            fields=target_fields,
                            where_clause=None,
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)


class CrisperTotalCasesByDatePostcodeSource(TableBase):
    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                              r'CRISPERTotalCasesByDatePostcodeSource/FeatureServer/0'):

        self.postcode_field = 'Postcode'
        self.date_field = 'Date'
        self.likely_source_field = 'LikelySource'
        self.cases_field = 'Cases'
        self.date_code_format = '%Y%m%d'

        super().__init__(source=source, id_field='RecordId')

    def create_record(self, date, postcode, likely_source=None, total_cases=None, shape=None, date_format='%Y%m%d'):

        record_id = self.create_id(date, postcode, likely_source)

        if isinstance(date, str):
            date = datetime.datetime.strptime(date, date_format)

        return {self.id_field: record_id,
                self.date_field: date.replace(hour=12),
                self.postcode_field: postcode,
                self.likely_source_field: likely_source,
                self.cases_field: total_cases,
                self.shape_field: shape}

    @staticmethod
    def create_id(date, postcode, likely_source):
        if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
            return '{}_{}_{}'.format(date.strftime('%Y%m%d'), postcode, likely_source)
        else:
            return '{}_{}_{}'.format(date, postcode, likely_source)

    def update_from_source(self, cases: AuthorityData2.CasesByDatePostcodeSource = AuthorityData2.CasesByDatePostcodeSource()):
        new_records = {}

        # Cases data
        # capture state geometries so we have them if derivative statistics cause new records to be generated for new dates.
        geometries = {}
        fields = [cases.postcode_field, cases.date_field, cases.likely_source_field, cases.cases_field, 'SHAPE@']
        records = cases.records(fields)
        for record in records:
            postcode = record[cases.postcode_field]
            # add a postcode_likelySource group id for use cumulative stats aggregation.
            postcode_source = '{}_{}'.format(postcode, record[cases.likely_source_field])
            record['group_id'] = postcode_source

            if postcode not in geometries:
                geometries[postcode] = record['SHAPE@']

        data = statistics.cumulative_daily_totals_by_group(data=records, group_id_field='group_id', value_field=cases.cases_field,
                                                           date_field=cases.date_field, none_value=0)

        new_records = {}
        for key, value in data.items():
            date_code, postcode, likely_source = key.split('_')
            date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
            shape = geometries.get(postcode, None)
            new_record = self.create_record(date=date_value, postcode=postcode, likely_source=likely_source, total_cases=value, shape=shape)
            new_records[new_record[self.id_field]] = new_record

        target_fields = [self.id_field, self.date_field, self.postcode_field, self.likely_source_field, self.cases_field]
        self.update_records(new_data=new_records,
                            fields=target_fields,
                            where_clause=None,
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)


class Covid19StatisticsByDateAndState(TableBase):
    """
    A feature service wrapper class that supports common operations.
    """

    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                              r'COVID19_Daily_Statistics_by_Date_and_State/FeatureServer/0'):

        self.state_field = 'State'
        self.date_field = 'DateValue'
        self.date_code_field = 'DateCode'
        self.new_deaths_field = 'NewDeaths'
        self.new_cases_field = 'NewNotifications'
        self.new_tests_field = 'NewTests'
        self.total_deaths_field = 'TotalDeaths'
        self.total_cases_field = 'TotalNotifications'
        self.total_tests_field = 'TotalTests'
        self.cases_7_day_ave_field = 'Cases7DayAve'
        self.tests_7_day_ave_field = 'Tests7DayAve'
        self.deaths_7_day_ave_field = 'Deaths7DayAve'
        self.tests_pct_positive_field = 'TestsPctPos'

        super().__init__(source=source, id_field='DateState')

    def create_record(self, date, state,
                      new_cases=0, total_cases=0, ave_cases=0,
                      new_deaths=0, total_deaths=0, ave_deaths=0,
                      new_tests=0, total_tests=0, ave_tests=0,
                      test_pct_pos=None,
                      shape=None, date_format='%Y%m%d'):

        record_id = self.create_id(date, state)

        if isinstance(date, str):
            date = datetime.datetime.strptime(date, date_format)

        return {self.id_field: record_id,
                self.date_field: date.replace(hour=12),
                self.date_code_field: date.strftime('%Y%m%d'),
                self.state_field: state,
                self.new_cases_field: new_cases,
                self.total_cases_field: total_cases,
                self.cases_7_day_ave_field: ave_cases,
                self.new_deaths_field: new_deaths,
                self.total_deaths_field: total_deaths,
                self.deaths_7_day_ave_field: ave_deaths,
                self.new_tests_field: new_tests,
                self.total_tests_field: total_tests,
                self.tests_7_day_ave_field: ave_tests,
                self.tests_pct_positive_field: test_pct_pos,
                self.shape_field: shape}

    @staticmethod
    def create_id(date, state):
        if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
            return '{}_{}'.format(date.strftime('%Y%m%d'), state)
        else:
            return '{}_{}'.format(date, state)

    def update_from_source(self,
                           cases=AuthorityData2.CasesByDateAndState2(),
                           deaths=AuthorityData2.DeathsByDateAndState2(),
                           tests=AuthorityData2.TestsByDateAndState2()):

        new_records = {}

        # Cases data

        # capture state geometries so we have them if derivative statistics cause new records to be generated for new dates.
        geometries = {}
        last_date = datetime.datetime.min
        fields = [cases.state_field, cases.date_field, cases.cases_field, 'SHAPE@']

        records = cases.records(fields)
        for record in records:
            state = record[cases.state_field]
            date_value = record[cases.date_field]
            if date_value > last_date:
                last_date = date_value
            new_record = self.create_record(date=date_value,
                                            state=state,
                                            new_cases=record[cases.cases_field],
                                            shape=record['SHAPE@'])
            new_records[new_record[self.id_field]] = new_record
            if state not in geometries:
                geometries[state] = record['SHAPE@']

        # Cumulative cases.
        data = statistics.cumulative_daily_totals_by_group(data=records,
                                                           group_id_field=cases.state_field,
                                                           value_field=cases.cases_field,
                                                           date_field=cases.date_field,
                                                           end_date=last_date)

        for id_value, value in data.items():
            record = new_records.get(id_value, None)
            if not record:
                date_code, state = id_value.split('_')
                record = self.create_record(date=date_code, date_format='%Y%m%d', state=state, shape=geometries.get(state, None))
                new_records[id_value] = record

            record[self.total_cases_field] = value

        # Cases 7 day Average
        data = statistics.moving_daily_averages_by_date_and_group(data=records,
                                                                  group_id_field=cases.state_field,
                                                                  value_field=cases.cases_field,
                                                                  date_field=cases.date_field,
                                                                  n=7,
                                                                  end_date=last_date)

        for id_value, value in data.items():
            date_code, state = id_value.split('_')
            record = new_records.get(id_value, None)
            if not record:
                record = self.create_record(date=date_code, date_format='%Y%m%d', state=state, shape=geometries.get(state, None))
                new_records[id_value] = record

            record_date = record[self.date_field]
            if record_date > last_date:
                record[self.cases_7_day_ave_field] = None
            else:
                record[self.cases_7_day_ave_field] = value


        # ---------------------------------------------------------------------------------
        # Deaths
        last_date = datetime.datetime.min

        fields = [deaths.state_field, deaths.date_field, deaths.deaths_field, 'SHAPE@']
        records = deaths.records(fields=fields)
        for record in records:
            state = record[deaths.state_field]
            date_value = record[deaths.date_field]
            if date_value > last_date:
                last_date = date_value
            deaths_value = record[deaths.deaths_field]
            id_value = self.create_id(date=date_value, state=state)

            new_record = new_records.get(id_value, None)
            if not new_record:
                new_record = self.create_record(date=date_value, state=state, shape=geometries.get(state, None))
                new_records[id_value] = new_record
            new_record[self.new_deaths_field] = deaths_value

        # Cumulative deaths.
        data = statistics.cumulative_daily_totals_by_group(data=records,
                                                           group_id_field=deaths.state_field,
                                                           value_field=deaths.deaths_field,
                                                           date_field=deaths.date_field,
                                                           end_date=last_date)

        for id_value, value in data.items():
            record = new_records.get(id_value, None)
            if not record:
                date_code, state = id_value.split('_')
                record = self.create_record(date=date_code, date_format='%Y%m%d', state=state, shape=geometries.get(state, None))
                new_records[id_value] = record

            record[self.total_deaths_field] = value

        # Deaths 7 day Average
        data = statistics.moving_daily_averages_by_date_and_group(data=records,
                                                                  group_id_field=deaths.state_field,
                                                                  value_field=deaths.deaths_field,
                                                                  date_field=deaths.date_field,
                                                                  n=7,
                                                                  end_date=last_date)

        for id_value, value in data.items():
            date_code, state = id_value.split('_')
            record = new_records.get(id_value, None)
            if not record:
                record = self.create_record(date=date_code, date_format='%Y%m%d', state=state, shape=geometries.get(state, None))
                new_records[id_value] = record

            record_date = record[self.date_field]
            if record_date > last_date:
                record[self.deaths_7_day_ave_field] = None
            else:
                record[self.deaths_7_day_ave_field] = value

        # -----------------------------------------------------------------------------------------------------
        # Tests
        last_date = datetime.datetime.min

        fields = [tests.state_field, tests.date_field, tests.tests_field, 'SHAPE@']
        records = tests.records(fields=fields)
        for record in records:
            state = record[tests.state_field]
            date_value = record[tests.date_field]
            if date_value > last_date:
                last_date = date_value
            tests_value = record[tests.tests_field]
            id_value = self.create_id(date=date_value, state=state)

            new_record = new_records.get(id_value, None)
            if not new_record:
                new_record = self.create_record(date=date_value, state=state, shape=geometries.get(state, None))
                new_records[id_value] = new_record
            new_record[self.new_tests_field] = tests_value

        # Cumulative tests.
        data = statistics.cumulative_daily_totals_by_group(data=records,
                                                           group_id_field=tests.state_field,
                                                           value_field=tests.tests_field,
                                                           date_field=tests.date_field,
                                                           end_date=last_date)

        for id_value, value in data.items():
            record = new_records.get(id_value, None)
            if not record:
                date_code, state = id_value.split('_')
                record = self.create_record(date=date_code, date_format='%Y%m%d', state=state, shape=geometries.get(state, None))
                new_records[id_value] = record

            record[self.total_tests_field] = value

        # Tests 7 day Average
        data = statistics.moving_daily_averages_by_date_and_group(data=records,
                                                                  group_id_field=tests.state_field,
                                                                  value_field=tests.tests_field,
                                                                  date_field=tests.date_field,
                                                                  n=7,
                                                                  end_date=last_date)

        for id_value, value in data.items():
            date_code, state = id_value.split('_')
            record = new_records.get(id_value, None)
            if not record:
                record = self.create_record(date=date_code, date_format='%Y%m%d', state=state, shape=geometries.get(state, None))
                new_records[id_value] = record

            record_date = record[self.date_field]
            if record_date > last_date:
                record[self.tests_7_day_ave_field] = None
            else:
                record[self.tests_7_day_ave_field] = value

        for record in new_records.values():
            tests = record[self.new_tests_field]
            cases = record[self.new_cases_field]
            if tests and cases:
                record[self.tests_pct_positive_field] = (float(cases) / float(tests)) * 100.0
            elif tests:  # no cases, so rate will be 0.
                record[self.tests_pct_positive_field] = 0
            else:  # cannot divide a number by zero or None.
                record[self.tests_pct_positive_field] = None

        target_fields = [self.id_field, self.date_field, self.date_code_field, self.date_field,
                         self.new_cases_field, self.total_cases_field, self.cases_7_day_ave_field,
                         self.new_deaths_field, self.total_deaths_field, self.deaths_7_day_ave_field,
                         self.new_tests_field, self.total_tests_field, self.tests_7_day_ave_field,
                         self.tests_pct_positive_field]

        self.update_records(new_data=new_records,
                            fields=target_fields,
                            where_clause=None,
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)


class CrisperStatisticsByState(TableBase):
    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/CRISPER_Statistics_by_State/FeatureServer/0'):

        self.state_field = 'State'
        self.most_recent_case_date_field = 'MostRecentCaseDate'
        self.most_recent_case_count_field = 'MostRecentCaseCount'
        self.total_cases_field = 'TotalCases'
        self.most_recent_test_date_field = 'MostRecentTestDate'
        self.most_recent_test_count_field = 'MostRecentTestCount'
        self.total_tests_field = 'TotalTests'
        self.most_recent_death_date_field = 'MostRecentDeathDate'
        self.most_recent_death_count_field = 'MostRecentDeathCount'
        self.total_deaths_field = 'TotalDeaths'
        self.new_cases_field = 'NewCases'
        self.new_deaths_field = 'NewDeaths'
        self.new_tests_field = 'NewTests'
        self.days_since_last_case_field = 'DaysSinceLastCase'

        super().__init__(source=source, id_field=self.state_field)

    def new_record(self, state, shape):
        return {self.state_field: state,
                self.shape_field: shape,
                self.total_cases_field: 0,
                self.most_recent_case_date_field: None,
                self.most_recent_case_count_field: None,
                self.total_deaths_field: 0,
                self.most_recent_death_date_field: None,
                self.most_recent_death_count_field: None,
                self.total_tests_field: 0,
                self.most_recent_test_date_field: None,
                self.most_recent_test_count_field: None,
                self.new_tests_field: None,
                self.new_cases_field: None,
                self.new_deaths_field: None,
                self.days_since_last_case_field: None}

    def update_from_source(self,
                           cases=AuthorityData2.CasesByDateAndState2(),
                           deaths=AuthorityData2.DeathsByDateAndState2(),
                           tests=AuthorityData2.TestsByDateAndState2()):

        new_records = {}
        test_date = datetime.datetime.now().replace(hour=12, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1)

        # Cases data
        records = [x for x in cases.records() if x[cases.cases_field] > 0]
        most_recent = filters.most_recent_by_group(data=records, group_id_field=cases.state_field, date_field=cases.date_field)
        totals = statistics.totals_by_group(data=records, group_id_field=cases.state_field, value_field=cases.cases_field)
        for state, record in most_recent.items():
            new_record = new_records.get(state, None)
            if not new_record:
                new_record = self.new_record(state, record[cases.shape_field])
                new_records[state] = new_record

            most_recent_date = record[cases.date_field].replace(hour=12)
            most_recent_value = record[cases.cases_field]
            new_record[self.most_recent_case_date_field] = most_recent_date
            new_record[self.most_recent_case_count_field] = most_recent_value
            new_record[self.total_cases_field] = totals.get(state, 0)

            if most_recent_date >= test_date:
                new_record[self.new_cases_field] = most_recent_value
            else:
                new_record[self.new_cases_field] = 0


        # Tests data
        records = [x for x in tests.records() if x[tests.tests_field] > 0]
        most_recent = filters.most_recent_by_group(data=records, group_id_field=tests.state_field, date_field=tests.date_field)
        totals = statistics.totals_by_group(data=records, group_id_field=tests.state_field, value_field=tests.tests_field)
        for state, record in most_recent.items():
            new_record = new_records.get(state, None)
            if not new_record:
                new_record = self.new_record(state, record[tests.shape_field])
                new_records[state] = new_record

            most_recent_date = record[tests.date_field].replace(hour=12)
            most_recent_value = record[tests.tests_field]
            new_record[self.most_recent_test_date_field] = most_recent_date
            new_record[self.most_recent_test_count_field] = most_recent_value
            new_record[self.total_tests_field] = totals.get(state, 0)

            if most_recent_date >= test_date:
                new_record[self.new_tests_field] = most_recent_value
            else:
                new_record[self.new_tests_field] = 0

        # Deaths data
        records = [x for x in deaths.records() if x[deaths.deaths_field] > 0]
        most_recent = filters.most_recent_by_group(data=records, group_id_field=deaths.state_field, date_field=deaths.date_field)
        totals = statistics.totals_by_group(data=records, group_id_field=deaths.state_field, value_field=deaths.deaths_field)
        for state, record in most_recent.items():
            new_record = new_records.get(state, None)
            if not new_record:
                new_record = self.new_record(state, record[deaths.shape_field])
                new_records[state] = new_record

            most_recent_date = record[deaths.date_field].replace(hour=12)
            most_recent_value = record[deaths.deaths_field]

            new_record[self.most_recent_death_date_field] = most_recent_date
            new_record[self.most_recent_death_count_field] = most_recent_value
            new_record[self.total_deaths_field] = totals.get(state, 0)

            if most_recent_date >= test_date:
                new_record[self.new_deaths_field] = most_recent_value
            else:
                new_record[self.new_deaths_field] = 0

        now_time = datetime.datetime.now().date()
        for record in new_records.values():
            test_date = record[self.most_recent_case_date_field].date()  # datetime.datetime
            if test_date:
                days_since_case = (now_time - test_date).days - 1  # if yesterday was last case, days since = 0.
                if days_since_case < 0:  # handle where last case reported was today (i.e. days_since_case = -1)
                    days_since_case = 0
                record[self.days_since_last_case_field] = days_since_case

        fields = [self.state_field,
                  self.total_cases_field, self.most_recent_case_date_field, self.most_recent_case_count_field,
                  self.total_tests_field, self.most_recent_test_date_field, self.most_recent_test_count_field,
                  self.total_deaths_field, self.most_recent_death_date_field, self.most_recent_death_count_field,
                  self.new_cases_field, self.new_deaths_field, self.new_tests_field, self.days_since_last_case_field]

        return self.update_records(new_data=new_records, fields=fields, add_new=True, delete_unmatched=False)

    @staticmethod
    def update_recent_counts(aus_record, ref_record, date_field, count_field):
        aus_date = aus_record[date_field]
        ref_date = ref_record[date_field]

        if not aus_date:
            aus_record[date_field] = ref_date
            aus_record[count_field] = ref_record[count_field]
        elif ref_date:
            ref_count = ref_record[count_field]
            if aus_date == ref_date:
                aus_record[count_field] += ref_count if ref_count else 0
            elif aus_date < ref_date:
                aus_record[date_field] = ref_date
                aus_record[count_field] = ref_count

    @staticmethod
    def add_value(aus_record, ref_record, value_field):
        aus_value = aus_record[value_field]
        ref_value = ref_record[value_field]

        if aus_value is None:
            if ref_value is not None:
                aus_record[value_field] = ref_value
        elif ref_value:
            aus_record[value_field] += ref_value


class CrisperCaseStatisticsByDateStateAndName(TableBase):
    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                              r'CRISPER_Case_Statistics_by_Date_State_and_Name/FeatureServer/0'):
        self.source = source
        self.place_id_field = 'State'
        self.date_field = 'DateValue'
        self.statistic_name_field = 'StatisticName'
        self.statistic_value_field = 'StatisticValue'

        super().__init__(source=source, id_field='RecordId')

    def create_record(self, stat_name, state, date, value, shape):
        date_code = date.strftime('%Y%m%d')
        id_value = '{}_{}_{}'.format(date_code, state, stat_name)
        return {self.id_field: id_value,
                self.place_id_field: state,
                self.date_field: date.replace(hour=12),
                self.statistic_name_field: stat_name,
                self.statistic_value_field: value,
                self.shape_field: shape}

    def update_from_source(self, cases: AuthorityData2.CasesByDateAndState = AuthorityData2.CasesByDateAndState()):
        source_fields = [cases.state_field, cases.date_field, cases.cases_field, 'SHAPE@']
        source_records = cases.records(fields=source_fields)

        target_fields = [self.id_field, self.date_field, self.place_id_field, self.statistic_value_field, self.shape_field]

        geometries = {}
        data = {}
        stat_name = 'New'
        for record in source_records:
            new_record = self.create_record(stat_name=stat_name,
                                            state=record[cases.state_field],
                                            date=record[cases.date_field],
                                            value=record[cases.cases_field],
                                            shape=record['SHAPE@'])
            data[new_record[self.id_field]] = new_record
            geometries[record[cases.state_field]] = record['SHAPE@']

        self.update_records(new_data=data,
                            fields=target_fields,
                            where_clause="{} = '{}'".format(self.statistic_name_field, stat_name),
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)

        data = {}
        stat_name = 'Total'
        values = statistics.cumulative_daily_totals_by_group(data=source_records,
                                                             group_id_field=cases.state_field,
                                                             value_field=cases.cases_field,
                                                             date_field=cases.date_field)
        for date_state, value in values.items():
            date_code, state = date_state.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            shape = geometries[state]
            new_record = self.create_record(stat_name=stat_name,
                                            state=state,
                                            date=date,
                                            value=value,
                                            shape=shape)

            data[new_record[self.id_field]] = new_record

        self.update_records(new_data=data,
                            fields=target_fields,
                            where_clause="{} = '{}'".format(self.statistic_name_field, stat_name),
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)

        data = {}
        stat_name = '7 Day Average'
        values = statistics.moving_daily_averages_by_date_and_group(data=source_records,
                                                                    group_id_field=cases.state_field,
                                                                    value_field=cases.cases_field,
                                                                    date_field=cases.date_field,
                                                                    n=7)

        for date_state, value in values.items():
            date_code, state = date_state.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            shape = geometries[state]
            new_record = self.create_record(stat_name=stat_name,
                                            state=state,
                                            date=date,
                                            value=value,
                                            shape=shape)

            data[new_record[self.id_field]] = new_record

        self.update_records(new_data=data,
                            fields=target_fields,
                            where_clause="{} = '{}'".format(self.statistic_name_field, stat_name),
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)


class CrisperDeathStatisticsByDateStateAndName(TableBase):
    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                              r'CRISPER_Death_Statistics_by_Date_State_and_Name/FeatureServer/0'):
        self.source = source
        self.place_id_field = 'State'
        self.date_field = 'DateValue'
        self.statistic_name_field = 'StatisticName'
        self.statistic_value_field = 'StatisticValue'

        super().__init__(source=source, id_field='RecordId')

    def create_record(self, stat_name, state, date, value, shape):
        date_code = date.strftime('%Y%m%d')
        id_value = '{}_{}_{}'.format(date_code, state, stat_name)
        return {self.id_field: id_value,
                self.place_id_field: state,
                self.date_field: date.replace(hour=12),
                self.statistic_name_field: stat_name,
                self.statistic_value_field: value,
                self.shape_field: shape}

    def update_from_source(self, deaths: AuthorityData2.DeathsByDateAndState = AuthorityData2.DeathsByDateAndState()):
        source_fields = [deaths.state_field, deaths.date_field, deaths.deaths_field, 'SHAPE@']
        source_records = deaths.records(fields=source_fields)

        target_fields = [self.id_field, self.date_field, self.place_id_field, self.statistic_value_field, self.shape_field]

        geometries = {}
        data = {}
        stat_name = 'New'
        for record in source_records:
            new_record = self.create_record(stat_name=stat_name,
                                            state=record[deaths.state_field],
                                            date=record[deaths.date_field],
                                            value=record[deaths.deaths_field],
                                            shape=record['SHAPE@'])
            data[new_record[self.id_field]] = new_record
            geometries[record[deaths.state_field]] = record['SHAPE@']

        self.update_records(new_data=data,
                            fields=target_fields,
                            where_clause="{} = '{}'".format(self.statistic_name_field, stat_name),
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)

        data = {}
        stat_name = 'Total'
        values = statistics.cumulative_daily_totals_by_group(data=source_records,
                                                             group_id_field=deaths.state_field,
                                                             value_field=deaths.deaths_field,
                                                             date_field=deaths.date_field)
        for date_state, value in values.items():
            date_code, state = date_state.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            shape = geometries[state]
            new_record = self.create_record(stat_name=stat_name,
                                            state=state,
                                            date=date,
                                            value=value,
                                            shape=shape)

            data[new_record[self.id_field]] = new_record

        self.update_records(new_data=data,
                            fields=target_fields,
                            where_clause="{} = '{}'".format(self.statistic_name_field, stat_name),
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)

        data = {}
        stat_name = '7 Day Average'
        values = statistics.moving_daily_averages_by_date_and_group(data=source_records,
                                                                    group_id_field=deaths.state_field,
                                                                    value_field=deaths.deaths_field,
                                                                    date_field=deaths.date_field,
                                                                    n=7)

        for date_state, value in values.items():
            date_code, state = date_state.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            shape = geometries[state]
            new_record = self.create_record(stat_name=stat_name,
                                            state=state,
                                            date=date,
                                            value=value,
                                            shape=shape)

            data[new_record[self.id_field]] = new_record

        self.update_records(new_data=data,
                            fields=target_fields,
                            where_clause="{} = '{}'".format(self.statistic_name_field, stat_name),
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)


class CrisperTestStatisticsByDateStateAndName(TableBase):
    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                              r'CRISPER_Tests_Statistics_by_Date_State_and_Name/FeatureServer/0'):
        self.source = source
        self.place_id_field = 'State'
        self.date_field = 'DateValue'
        self.statistic_name_field = 'StatisticName'
        self.statistic_value_field = 'StatisticValue'

        super().__init__(source=source, id_field='RecordId')

    def create_record(self, stat_name, state, date, value, shape):
        date_code = date.strftime('%Y%m%d')
        id_value = '{}_{}_{}'.format(date_code, state, stat_name)
        return {self.id_field: id_value,
                self.place_id_field: state,
                self.date_field: date.replace(hour=12),
                self.statistic_name_field: stat_name,
                self.statistic_value_field: value,
                self.shape_field: shape}

    def update_from_source(self, deaths: AuthorityData2.TestsByDateAndState = AuthorityData2.TestsByDateAndState()):
        source_fields = [deaths.state_field, deaths.date_field, deaths.tests_field, 'SHAPE@']
        source_records = deaths.records(fields=source_fields)

        target_fields = [self.id_field, self.date_field, self.place_id_field, self.statistic_value_field, self.shape_field]

        geometries = {}
        data = {}
        stat_name = 'New'
        for record in source_records:
            new_record = self.create_record(stat_name=stat_name,
                                            state=record[deaths.state_field],
                                            date=record[deaths.date_field],
                                            value=record[deaths.tests_field],
                                            shape=record['SHAPE@'])
            data[new_record[self.id_field]] = new_record
            geometries[record[deaths.state_field]] = record['SHAPE@']

        self.update_records(new_data=data,
                            fields=target_fields,
                            where_clause="{} = '{}'".format(self.statistic_name_field, stat_name),
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)

        data = {}
        stat_name = 'Total'
        values = statistics.cumulative_daily_totals_by_group(data=source_records,
                                                             group_id_field=deaths.state_field,
                                                             value_field=deaths.tests_field,
                                                             date_field=deaths.date_field)
        for date_state, value in values.items():
            date_code, state = date_state.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            shape = geometries[state]
            new_record = self.create_record(stat_name=stat_name,
                                            state=state,
                                            date=date,
                                            value=value,
                                            shape=shape)

            data[new_record[self.id_field]] = new_record

        self.update_records(new_data=data,
                            fields=target_fields,
                            where_clause="{} = '{}'".format(self.statistic_name_field, stat_name),
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)

        data = {}
        stat_name = '7 Day Average'
        values = statistics.moving_daily_averages_by_date_and_group(data=source_records,
                                                                    group_id_field=deaths.state_field,
                                                                    value_field=deaths.tests_field,
                                                                    date_field=deaths.date_field,
                                                                    n=7)

        for date_state, value in values.items():
            date_code, state = date_state.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            shape = geometries[state]
            new_record = self.create_record(stat_name=stat_name,
                                            state=state,
                                            date=date,
                                            value=value,
                                            shape=shape)

            data[new_record[self.id_field]] = new_record

        self.update_records(new_data=data,
                            fields=target_fields,
                            where_clause="{} = '{}'".format(self.statistic_name_field, stat_name),
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)


class CrisperMovingDailyAverageCasesByDateAndState(TableBase):
    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                              r'CRISPER_MovingDailyAverages_StateCases/FeatureServer/0'):
        self.source = source
        self.state_field = 'State'
        self.date_field = 'Date'
        self.interval_field = 'IntervalDays'
        self.mda_field = 'MDA'
        self.intervals = [7, 14]

        super().__init__(source=source, id_field='RecordID')

    def create_record(self, date, state, interval, mda,
                      shape=None, date_format='%Y%m%d'):

        record_id = self.create_id(date=date, state=state, interval=interval)

        if isinstance(date, str):
            date = datetime.datetime.strptime(date, date_format)

        return {self.id_field: record_id,
                self.date_field: date.replace(hour=12),
                self.state_field: state,
                self.interval_field: interval,
                self.mda_field: mda,
                self.shape_field: shape}

    @staticmethod
    def create_id(date, state, interval):
        if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
            return '{}_{}_{}'.format(date.strftime('%Y%m%d'), state, interval)
        else:
            return '{}_{}_{}'.format(date, state, interval)

    def update_from_source(self, cases=AuthorityData2.CasesByDateAndState2()):

        case_data = cases.records()
        geometries = {}
        for item in case_data:
            existing_geom = geometries.get(item[cases.state_field], None)
            if not existing_geom:
                geometries[item[cases.state_field]] = item[cases.shape_field]

        new_records = {}
        for interval in self.intervals:
            interval_values = statistics.moving_daily_averages_by_date_and_group(data=case_data,
                                                                                 group_id_field=cases.state_field,
                                                                                 value_field=cases.cases_field,
                                                                                 date_field=cases.date_field,
                                                                                 n=interval)

            for date_state, mda in interval_values.items():
                date, state = date_state.split('_')
                state_geom = geometries.get(state, None)
                new_record = self.create_record(date=date, state=state, interval=interval, mda=mda, shape=state_geom)
                new_records[new_record[self.id_field]] = new_record

        target_fields = [self.id_field, self.date_field, self.state_field, self.interval_field, self.mda_field, self.shape_field]

        self.update_records(new_data=new_records,
                            fields=target_fields,
                            where_clause=None,
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)


class CrisperMovingDailyAverageDeathsByDateAndState(TableBase):
    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                              r'CRISPER_MovingDailyAverages_StateDeaths/FeatureServer/0'):
        self.source = source
        self.state_field = 'State'
        self.date_field = 'Date'
        self.interval_field = 'IntervalDays'
        self.mda_field = 'MDA'
        self.intervals = [7, 14]

        super().__init__(source=source, id_field='RecordID')

    def create_record(self, date, state, interval, mda,
                      shape=None, date_format='%Y%m%d'):

        record_id = self.create_id(date=date, state=state, interval=interval)

        if isinstance(date, str):
            date = datetime.datetime.strptime(date, date_format)

        return {self.id_field: record_id,
                self.date_field: date.replace(hour=12),
                self.state_field: state,
                self.interval_field: interval,
                self.mda_field: mda,
                self.shape_field: shape}

    @staticmethod
    def create_id(date, state, interval):
        if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
            return '{}_{}_{}'.format(date.strftime('%Y%m%d'), state, interval)
        else:
            return '{}_{}_{}'.format(date, state, interval)

    def update_from_source(self, deaths=AuthorityData2.DeathsByDateAndState2()):

        death_data = deaths.records()
        geometries = {}
        for item in death_data:
            existing_geom = geometries.get(item[deaths.state_field], None)
            if not existing_geom:
                geometries[item[deaths.state_field]] = item[deaths.shape_field]

        new_records = {}
        for interval in self.intervals:
            interval_values = statistics.moving_daily_averages_by_date_and_group(data=death_data,
                                                                                 group_id_field=deaths.state_field,
                                                                                 value_field=deaths.deaths_field,
                                                                                 date_field=deaths.date_field,
                                                                                 n=interval)

            for date_state, mda in interval_values.items():
                date, state = date_state.split('_')
                state_geom = geometries.get(state, None)
                new_record = self.create_record(date=date, state=state, interval=interval, mda=mda, shape=state_geom)
                new_records[new_record[self.id_field]] = new_record

        target_fields = [self.id_field, self.date_field, self.state_field, self.interval_field, self.mda_field, self.shape_field]

        self.update_records(new_data=new_records,
                            fields=target_fields,
                            where_clause=None,
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)


class CrisperMovingDailyAverageTestsByDateAndState(TableBase):
    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                              r'CRISPER_MovingDailyAverages_StateTests/FeatureServer/0'):
        self.source = source
        self.state_field = 'State'
        self.date_field = 'Date'
        self.interval_field = 'IntervalDays'
        self.mda_field = 'MDA'
        self.intervals = [7, 14]

        super().__init__(source=source, id_field='RecordID')

    def create_record(self, date, state, interval, mda,
                      shape=None, date_format='%Y%m%d'):

        record_id = self.create_id(date=date, state=state, interval=interval)

        if isinstance(date, str):
            date = datetime.datetime.strptime(date, date_format)

        return {self.id_field: record_id,
                self.date_field: date.replace(hour=12),
                self.state_field: state,
                self.interval_field: interval,
                self.mda_field: mda,
                self.shape_field: shape}

    @staticmethod
    def create_id(date, state, interval):
        if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
            return '{}_{}_{}'.format(date.strftime('%Y%m%d'), state, interval)
        else:
            return '{}_{}_{}'.format(date, state, interval)

    def update_from_source(self, tests=AuthorityData2.TestsByDateAndState2()):

        test_data = tests.records()
        geometries = {}
        for item in test_data:
            existing_geom = geometries.get(item[tests.state_field], None)
            if not existing_geom:
                geometries[item[tests.state_field]] = item[tests.shape_field]

        new_records = {}
        for interval in self.intervals:
            interval_values = statistics.moving_daily_averages_by_date_and_group(data=test_data,
                                                                                 group_id_field=tests.state_field,
                                                                                 value_field=tests.tests_field,
                                                                                 date_field=tests.date_field,
                                                                                 n=interval)

            for date_state, mda in interval_values.items():
                date, state = date_state.split('_')
                state_geom = geometries.get(state, None)
                new_record = self.create_record(date=date, state=state, interval=interval, mda=mda, shape=state_geom)
                new_records[new_record[self.id_field]] = new_record

        target_fields = [self.id_field, self.date_field, self.state_field, self.interval_field, self.mda_field, self.shape_field]

        self.update_records(new_data=new_records,
                            fields=target_fields,
                            where_clause=None,
                            add_new=True,
                            delete_unmatched=True,
                            rounding=4,
                            case_sensitive=True)


class DataExtractDates(TableBase):
    def __init__(self, source=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/DataExtractDates/FeatureServer/0'):

        self.date_field = 'Date'
        self.item_id_field = 'ItemID'
        self.name_field = 'Name'
        self.url_field = 'URL'

        super().__init__(source=source, id_field=self.url_field)

    def set_update_time(self, url, update_time=None):
        if not update_time:
            update_time = datetime.datetime.now()
        fields = [self.item_id_field, self.date_field]
        where_clause = "{} = '{}'".format(self.url_field, url)

        new_data = {url: {self.url_field: url, self.date_field: update_time}}
        self.update_records(new_data=new_data, fields=fields, where_clause=where_clause, add_new=False, delete_unmatched=False)
