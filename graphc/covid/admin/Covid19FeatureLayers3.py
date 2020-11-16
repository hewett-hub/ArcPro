import datetime
import copy

from graphc.covid.admin import DataEngine
from graphc.covid.admin import FeatureSources
from graphc.covid.admin import filters
from graphc.covid.admin import statistics
from graphc.da.arcgis_helpers import TableBase

# these imports support Covid19CaseLocationsByPostcode
import logging
from arcgis.features import FeatureLayer
from graphc.da import da_agol
from graphc.covid.admin import utilities


class Covid19CaseLocationsByPostcode(object):
    """
    A feature service wrapper class that supports common operations.
    """

    def __init__(self, service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                                   r'Case_Locations_By_Postcode/FeatureServer/0'):
        self.service_url = service_url
        self.postcode_field = 'PostCode'
        self.date_code_field = 'DateString'
        self.date_field = 'ReportDate'
        self.likely_source_field = 'LikelySource'
        self.date_code_format = '%Y%m%d'

    def layer(self):
        return FeatureLayer(self.service_url)

    def query(self, where_clause='1=1'):
        return self.layer().query(where=where_clause)

    def synch_with_authority(self, data_engine: DataEngine.DataEngine, feature_source: FeatureSources.FeatureSources):
        logging.info('Synchronizing: ' + self.service_url)

        source_records = copy.deepcopy(data_engine.cases_by_date_postcode_and_source().records())  # make a copy so we don't alter source.
        source_data = {}
        for record in source_records:
            date_code = record['Date'].strftime('%Y%m%d')
            key = '{}_{}_{}'.format(date_code, record['Postcode'], record['LikelySource'])
            source_data[key] = record
        shapes = feature_source.postcode_points().items()

        logging.info('Identifying Changes')

        deletes = []

        target_layer = self.layer()
        query_result = target_layer.query()
        for row in query_result:
            key = '{}_{}_{}'.format(row.attributes[self.date_code_field], row.attributes[self.postcode_field],
                                    row.attributes[self.likely_source_field])
            update_item = source_data.get(key, None)
            if update_item:
                # if an update item was found, subtract 1 from the notifications total.
                update_item['Cases'] -= 1
                if update_item['Cases'] < 1:
                    # If the new notifications total is less than 1, then this was the last notification for the postcode/date.
                    # Remove the postcode/date item from the collection of update items so any additional records associated with
                    # this date/postcode combo will be deleted from the online data.
                    source_data.pop(key, None)
            else:
                # if no matching update item was found, delete the record from online.
                deletes.append(row.attributes[query_result.object_id_field_name])

        # any remaining data_models items are new records
        adds = []

        for key, new_item in source_data.items():
            date_code, postcode, likely_source = key.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            for i in range(new_item['Cases']):
                row = {"attributes":
                       {self.date_code_field: date_code,
                        self.date_field: date,
                        self.postcode_field: postcode.upper(),
                        self.likely_source_field: likely_source},
                       "geometry": utilities.geometry_to_json(shapes.get(postcode, None))}
                adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=None)


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

    def update_from_source(self, data_engine: DataEngine.DataEngine, feature_source: FeatureSources.FeatureSources):

        shapes = feature_source.postcode_points()
        source_records = data_engine.cases_by_date_and_postcode().items()

        target_fields = [self.id_field, self.cases_field, self.most_recent_code_field, self.most_recent_date_field, self.most_recent_new_field,
                         self.shape_field]

        new_records = {}

        most_recent = filters.most_recent_by_group(data=source_records, group_id_field='Postcode', date_field='Date')
        totals = statistics.totals_by_group(data=source_records, group_id_field='Postcode', value_field='Cases')
        for postcode, record in most_recent.items():
            total = totals.get(postcode, None)
            shape_value = shapes.get(postcode, None)
            new_record = self.create_record(postcode=postcode,
                                            total_cases=total,
                                            most_recent_case_date=record['Date'],
                                            most_recent_case_count=record['Cases'],
                                            shape=shape_value)

            new_records[new_record[self.id_field]] = new_record

        self.update_records(new_data=new_records, fields=target_fields, add_new=True, delete_unmatched=True, rounding=4, case_sensitive=True)


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
                self.date_field: date,
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

    def update_from_source(self, data_engine: DataEngine.DataEngine, feature_source: FeatureSources.FeatureSources):

        new_records = {}

        # Cases data
        shapes = feature_source.postcode_points().items()
        records = data_engine.cases_by_date_and_postcode().records()
        for record in records:
            postcode = record['Postcode']
            date_value = record['Date']
            shape_value = shapes.get(postcode, None)
            new_record = self.create_record(date=date_value,
                                            postcode=postcode,
                                            new_cases=record['Cases'],
                                            shape=shape_value)
            new_records[new_record[self.id_field]] = new_record

        # Cumulative cases.
        data = statistics.cumulative_daily_totals_by_group(data=records,
                                                           group_id_field='Postcode',
                                                           value_field='Cases',
                                                           date_field='Date')
        for id_value, value in data.items():
            record = new_records.get(id_value, None)
            if not record:
                date_code, postcode = id_value.split('_')
                record = self.create_record(date=date_code, date_format='%Y%m%d', postcode=postcode, shape=shapes.get(postcode, None))
                new_records[id_value] = record
            record[self.total_cases_field] = value

        # -----------------------------------------------------------------------------------------------------
        # Tests

        records = data_engine.tests_by_date_and_postcode().records()
        for record in records:
            postcode = record['Postcode']
            date_value = record['Date']
            tests_value = record['Tests']
            id_value = self.create_id(date=date_value, postcode=postcode)

            new_record = new_records.get(id_value, None)
            if not new_record:
                new_record = self.create_record(date=date_value, postcode=postcode, shape=shapes.get(postcode, None))
                new_records[id_value] = new_record
            new_record[self.new_tests_field] = tests_value

        # Cumulative deaths.
        data = statistics.cumulative_daily_totals_by_group(data=records,
                                                           group_id_field='Postcode',
                                                           value_field='Tests',
                                                           date_field='Date')
        for id_value, value in data.items():
            record = new_records.get(id_value, None)
            if not record:
                date_code, postcode = id_value.split('_')
                record = self.create_record(date=date_code, date_format='%Y%m%d', postcode=postcode, shape=shapes.get(postcode, None))
                new_records[id_value] = record
            record[self.total_tests_field] = value

        # Tests 7 day Average
        data = statistics.moving_daily_averages_by_date_and_group(data=records,
                                                                  group_id_field='Postcode',
                                                                  value_field='Tests',
                                                                  date_field='Date',
                                                                  n=7)
        for id_value, value in data.items():
            record = new_records.get(id_value, None)
            if not record:
                date_code, postcode = id_value.split('_')
                record = self.create_record(date=date_code, date_format='%Y%m%d', postcode=postcode, shape=shapes.get(postcode, None))
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
                self.date_field: date,
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

    def update_from_source(self, data_engine: DataEngine.DataEngine, feature_source: FeatureSources.FeatureSources):
        # Cases data
        # capture state geometries so we have them if derivative statistics cause new records to be generated for new dates.
        shapes = feature_source.postcode_points().items()
        records = data_engine.cases_by_date_postcode_and_source().records()
        for record in records:
            postcode = record['Cases']
            # add a postcode_likelySource group id for use cumulative stats aggregation.
            postcode_source = '{}_{}'.format(postcode, record['LikelySource'])
            record['group_id'] = postcode_source

        data = statistics.cumulative_daily_totals_by_group(data=records, group_id_field='group_id', value_field='Cases',
                                                           date_field='Date', none_value=0)

        new_records = {}
        for key, value in data.items():
            date_code, postcode, likely_source = key.split('_')
            date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
            shape = shapes.get(postcode, None)
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
        self.tests_pct_positive = 'TestsPctPos'

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
                self.date_field: date,
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
                self.tests_pct_positive: test_pct_pos,
                self.shape_field: shape}

    @staticmethod
    def create_id(date, state):
        if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
            return '{}_{}'.format(date.strftime('%Y%m%d'), state)
        else:
            return '{}_{}'.format(date, state)

    def update_from_source(self, data_engine: DataEngine.DataEngine, feature_source: FeatureSources.FeatureSources):

        # get geometries indexed by state abbreviation.
        shapes = feature_source.state_capital_points().items()

        new_records = {}

        # Cases data
        last_date = datetime.datetime.min
        records = data_engine.cases_by_date_and_state().records()
        for record in records:
            state = record['State']
            date_value = record['Date']
            shape_value = shapes.get(state, None)
            if date_value > last_date:
                last_date = date_value
            new_record = self.create_record(date=date_value,
                                            state=state,
                                            new_cases=record['Cases'],
                                            shape=shape_value)
            new_records[new_record[self.id_field]] = new_record

        # Cumulative cases.
        data = statistics.cumulative_daily_totals_by_group(data=records,
                                                           group_id_field='State',
                                                           value_field='Cases',
                                                           date_field='Date',
                                                           end_date=last_date)

        for id_value, value in data.items():
            record = new_records.get(id_value, None)
            if not record:
                date_code, state = id_value.split('_')
                record = self.create_record(date=date_code, date_format='%Y%m%d', state=state, shape=shapes.get(state, None))
                new_records[id_value] = record

            record[self.total_cases_field] = value

        # Cases 7 day Average
        data = statistics.moving_daily_averages_by_date_and_group(data=records,
                                                                  group_id_field='State',
                                                                  value_field='Cases',
                                                                  date_field='Date',
                                                                  n=7,
                                                                  end_date=last_date)

        for id_value, value in data.items():
            date_code, state = id_value.split('_')
            record = new_records.get(id_value, None)
            if not record:
                record = self.create_record(date=date_code, date_format='%Y%m%d', state=state, shape=shapes.get(state, None))
                new_records[id_value] = record

            record_date = record[self.date_field]
            if record_date > last_date:
                record[self.cases_7_day_ave_field] = None
            else:
                record[self.cases_7_day_ave_field] = value

        # ---------------------------------------------------------------------------------
        # Deaths
        last_date = datetime.datetime.min

        records = data_engine.deaths_by_date_and_state().records()
        for record in records:
            state = record['State']
            date_value = record['Date']
            if date_value > last_date:
                last_date = date_value
            deaths_value = record['Deaths']
            id_value = self.create_id(date=date_value, state=state)

            new_record = new_records.get(id_value, None)
            if not new_record:
                new_record = self.create_record(date=date_value, state=state, shape=shapes.get(state, None))
                new_records[id_value] = new_record
            new_record[self.new_deaths_field] = deaths_value

        # Cumulative deaths.
        data = statistics.cumulative_daily_totals_by_group(data=records,
                                                           group_id_field='State',
                                                           value_field='Deaths',
                                                           date_field='Date',
                                                           end_date=last_date)

        for id_value, value in data.items():
            record = new_records.get(id_value, None)
            if not record:
                date_code, state = id_value.split('_')
                record = self.create_record(date=date_code, date_format='%Y%m%d', state=state, shape=shapes.get(state, None))
                new_records[id_value] = record

            record[self.total_deaths_field] = value

        # Deaths 7 day Average
        data = statistics.moving_daily_averages_by_date_and_group(data=records,
                                                                  group_id_field='State',
                                                                  value_field='Deaths',
                                                                  date_field='Date',
                                                                  n=7,
                                                                  end_date=last_date)

        for id_value, value in data.items():
            date_code, state = id_value.split('_')
            record = new_records.get(id_value, None)
            if not record:
                record = self.create_record(date=date_code, date_format='%Y%m%d', state=state, shape=shapes.get(state, None))
                new_records[id_value] = record

            record_date = record[self.date_field]
            if record_date > last_date:
                record[self.deaths_7_day_ave_field] = None
            else:
                record[self.deaths_7_day_ave_field] = value

        # -----------------------------------------------------------------------------------------------------
        # Tests
        last_date = datetime.datetime.min

        records = data_engine.tests_by_date_and_state().records()
        for record in records:
            state = record['State']
            date_value = record['Date']
            if date_value > last_date:
                last_date = date_value
            tests_value = record['Tests']
            id_value = self.create_id(date=date_value, state=state)

            new_record = new_records.get(id_value, None)
            if not new_record:
                new_record = self.create_record(date=date_value, state=state, shape=shapes.get(state, None))
                new_records[id_value] = new_record
            new_record[self.new_tests_field] = tests_value

        # Cumulative tests.
        data = statistics.cumulative_daily_totals_by_group(data=records,
                                                           group_id_field='State',
                                                           value_field='Tests',
                                                           date_field='Date',
                                                           end_date=last_date)

        for id_value, value in data.items():
            record = new_records.get(id_value, None)
            if not record:
                date_code, state = id_value.split('_')
                record = self.create_record(date=date_code, date_format='%Y%m%d', state=state, shape=shapes.get(state, None))
                new_records[id_value] = record

            record[self.total_tests_field] = value

        # Tests 7 day Average
        data = statistics.moving_daily_averages_by_date_and_group(data=records,
                                                                  group_id_field='State',
                                                                  value_field='Tests',
                                                                  date_field='Date',
                                                                  n=7,
                                                                  end_date=last_date)

        for id_value, value in data.items():
            date_code, state = id_value.split('_')
            record = new_records.get(id_value, None)
            if not record:
                record = self.create_record(date=date_code, date_format='%Y%m%d', state=state, shape=shapes.get(state, None))
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
                record[self.tests_pct_positive] = (float(cases)/float(tests)) * 100.0
            elif tests:  # no cases, so rate will be 0.
                record[self.tests_pct_positive] = 0
            else:  # cannot divide a number by zero or None.
                record[self.tests_pct_positive] = None

        target_fields = [self.id_field, self.date_field, self.date_code_field, self.date_field,
                         self.new_cases_field, self.total_cases_field, self.cases_7_day_ave_field,
                         self.new_deaths_field, self.total_deaths_field, self.deaths_7_day_ave_field,
                         self.new_tests_field, self.total_tests_field, self.tests_7_day_ave_field,
                         self.tests_pct_positive]

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

    def update_from_source(self, data_engine: DataEngine.DataEngine, feature_source: FeatureSources.FeatureSources):

        new_records = {}
        test_date = (datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=1))

        # get geometries indexed by state abbreviation.
        shapes = feature_source.state_capital_points().items()

        # Cases data

        records = [x for x in data_engine.cases_by_date_and_state().records() if x['Cases'] > 0]
        most_recent = filters.most_recent_by_group(data=records, group_id_field='State', date_field='Date')
        totals = statistics.totals_by_group(data=records, group_id_field='State', value_field='Cases')
        for state, record in most_recent.items():
            new_record = new_records.get(state, None)
            if not new_record:
                shape_value = shapes.get(state, None)
                new_record = self.new_record(state, shape_value)
                new_records[state] = new_record

            most_recent_date = record['Date']
            most_recent_value = record['Cases']
            new_record[self.most_recent_case_date_field] = most_recent_date
            new_record[self.most_recent_case_count_field] = most_recent_value
            new_record[self.total_cases_field] = totals.get(state, 0)

            if most_recent_date >= test_date:
                new_record[self.new_cases_field] = most_recent_value
            else:
                new_record[self.new_cases_field] = 0

        # Tests data
        tests = data_engine.tests_by_date_and_state()
        records = [x for x in tests.records() if x['Tests'] > 0]
        most_recent = filters.most_recent_by_group(data=records, group_id_field='State', date_field='Date')
        totals = statistics.totals_by_group(data=records, group_id_field='State', value_field='Tests')
        for state, record in most_recent.items():
            new_record = new_records.get(state, None)
            if not new_record:
                shape_value = shapes.get(state, None)
                new_record = self.new_record(state, shape_value)
                new_records[state] = new_record

            most_recent_date = record['Date']
            most_recent_value = record['Tests']
            new_record[self.most_recent_test_date_field] = most_recent_date
            new_record[self.most_recent_test_count_field] = most_recent_value
            new_record[self.total_tests_field] = totals.get(state, 0)

            if most_recent_date >= test_date:
                new_record[self.new_tests_field] = most_recent_value
            else:
                new_record[self.new_tests_field] = 0

        # Deaths data
        deaths = data_engine.deaths_by_date_and_state()
        records = [x for x in deaths.records() if x['Deaths'] > 0]
        most_recent = filters.most_recent_by_group(data=records, group_id_field='State', date_field='Date')
        totals = statistics.totals_by_group(data=records, group_id_field='State', value_field='Deaths')
        for state, record in most_recent.items():
            new_record = new_records.get(state, None)
            if not new_record:
                shape_value = shapes.get(state, None)
                new_record = self.new_record(state, shape_value)
                new_records[state] = new_record

            most_recent_date = record['Date']
            most_recent_value = record['Deaths']

            new_record[self.most_recent_death_date_field] = most_recent_date
            new_record[self.most_recent_death_count_field] = most_recent_value
            new_record[self.total_deaths_field] = totals.get(state, 0)

            if most_recent_date >= test_date:
                new_record[self.new_deaths_field] = most_recent_value
            else:
                new_record[self.new_deaths_field] = 0

        now_time = datetime.datetime.now()
        for record in new_records.values():
            test_date = record[self.most_recent_case_date_field]  # datetime.datetime
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
                self.date_field: date,
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

    def update_from_source(self, data_engine: DataEngine.DataEngine, feature_source: FeatureSources.FeatureSources):

        case_data = data_engine.cases_by_date_and_state().records()
        shapes = feature_source.state_capital_points().items()

        new_records = {}
        for interval in self.intervals:
            interval_values = statistics.moving_daily_averages_by_date_and_group(data=case_data,
                                                                                 group_id_field='State',
                                                                                 value_field='Cases',
                                                                                 date_field='Date',
                                                                                 n=interval)

            for date_state, mda in interval_values.items():
                date, state = date_state.split('_')
                state_geom = shapes.get(state, None)
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
                self.date_field: date,
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

    def update_from_source(self, data_engine: DataEngine.DataEngine, feature_source: FeatureSources.FeatureSources):

        death_data = data_engine.deaths_by_date_and_state().records()
        shapes = feature_source.state_capital_points().items()

        new_records = {}
        for interval in self.intervals:
            interval_values = statistics.moving_daily_averages_by_date_and_group(data=death_data,
                                                                                 group_id_field='State',
                                                                                 value_field='Deaths',
                                                                                 date_field='Date',
                                                                                 n=interval)

            for date_state, mda in interval_values.items():
                date, state = date_state.split('_')
                state_geom = shapes.get(state, None)
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
                self.date_field: date,
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

    def update_from_source(self, data_engine: DataEngine.DataEngine, feature_source: FeatureSources.FeatureSources):

        test_data = data_engine.tests_by_date_and_state().records()
        shapes = feature_source.state_capital_points().items()

        new_records = {}
        for interval in self.intervals:
            interval_values = statistics.moving_daily_averages_by_date_and_group(data=test_data,
                                                                                 group_id_field='State',
                                                                                 value_field='Tests',
                                                                                 date_field='Date',
                                                                                 n=interval)

            for date_state, mda in interval_values.items():
                date, state = date_state.split('_')
                state_geom = shapes.get(state, None)
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

    def update_from_source(self, data_engine: DataEngine.DataEngine):

        source_records = data_engine.cases_by_date_postcode_and_source().records()

        target_fields = [self.id_field, self.cases_field, self.most_recent_code_field, self.most_recent_date_field, self.most_recent_new_field]

        new_records = {}

        most_recent = filters.most_recent_by_group(data=source_records, group_id_field='Postcode', date_field='Date')
        totals = statistics.totals_by_group(data=source_records, group_id_field='Postcode', value_field='Cases')
        for postcode, record in most_recent.items():
            total = totals.get(postcode, None)
            new_record = self.create_record(postcode=postcode,
                                            total_cases=total,
                                            most_recent_case_date=record['Date'],
                                            most_recent_case_count=record['Cases'])

            new_records[new_record[self.id_field]] = new_record

        self.update_records(new_data=new_records, fields=target_fields, add_new=True, delete_unmatched=False, rounding=4, case_sensitive=True)