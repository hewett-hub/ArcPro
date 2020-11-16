import datetime


from graphc.covid.source import NSW_SourceData
from graphc.covid.source import covid19data_SourceData
from graphc.data.abs2016 import POA2016
from graphc.data.pois import StateCapitals
from graphc.da.arcgis_helpers import TableBase


# --------------------------------------------
# by Date and State
# --------------------------------------------


class CasesByDateAndState(TableBase):
    def __init__(self):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        super().__init__(source=source, id_field='RecordId')

        self.state_field = 'State'
        self.date_field = 'Date'
        self.cases_field = 'Cases'

    def update_from_source(self,
                           covid_source: covid19data_SourceData.COVID_AU_state = covid19data_SourceData.COVID_AU_state(),
                           nsw_source: NSW_SourceData.NswNotificationData = NSW_SourceData.NswNotificationData(),
                           geometry_source: TableBase = None):
        new_records = {}

        # get state capital geometries indexed by state abbreviation
        if not geometry_source:
            geometry_source = StateCapitals()
        features = geometry_source.values_by_id(value_field='SHAPE@')

        for item in covid_source.source_data():
            date_value = item[covid_source.fields.date]
            state = item[covid_source.fields.state_abbrev]
            case_count = item[covid_source.fields.confirmed]
            date_code = date_value.strftime('%Y%m%d')
            shape_value = features.get(state, None)
            key = '{}_{}'.format(date_code, state)
            new_records[key] = {self.id_field: key,
                                self.state_field: state,
                                self.date_field: date_value,
                                self.cases_field: case_count,
                                self.shape_field: shape_value}

        # load nsw source.  NSW source values override any existing jhu values for nsw.
        state = 'NSW'
        for date_code, case_count in nsw_source.counts_by_date().items():
            key = '{}_{}'.format(date_code, state)
            new_record = new_records.get(key, None)
            if new_record:
                new_record[self.cases_field] = case_count
            else:
                date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
                shape_value = features.get(state, None)
                new_records[key] = {self.id_field: key,
                                    self.state_field: state,
                                    self.date_field: date_value,
                                    self.cases_field: case_count,
                                    self.shape_field: shape_value}

        aus_records = {}
        for date_state, record in new_records.items():
            date_code, state = date_state.split('_')
            key = '{}_AUS'.format(date_code)
            aus_record = aus_records.get(key, None)
            if aus_record:
                aus_record[self.cases_field] += record[self.cases_field]
            else:
                date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
                aus_records[key] = {self.id_field: key,
                                    self.state_field: 'AUS',
                                    self.date_field: date_value,
                                    self.cases_field: record[self.cases_field],
                                    self.shape_field: None}

        for key, record in aus_records.items():
            new_records[key] = record

        fields = [self.id_field, self.date_field, self.state_field, self.cases_field]
        return self._helper.update_records(new_data=new_records, fields=fields, add_new=True, delete_unmatched=True, shape_field=self.shape_field)


class CasesByDateAndState(TableBase):
    def __init__(self, source: str = r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\CasesByDateAndState2'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        super().__init__(source=source, id_field='RecordId')

        self.state_field = 'State'
        self.date_field = 'Date'
        self.cases_field = 'Cases'

    def update_from_source(self,
                           jhu_source: JHU_SourceData.JhuCasesData = JHU_SourceData.JhuCasesData(),
                           nsw_source: NSW_SourceData.NswNotificationData = NSW_SourceData.NswNotificationData(),
                           geometry_source: TableBase = None):
        new_records = {}

        # get state capital geometries indexed by state abbreviation
        if not geometry_source:
            geometry_source = StateCapitals()
        features = geometry_source.values_by_id(value_field='SHAPE@')

        # load jhu source first.  Most states do not have their own source.
        jhu_data = jhu_source.counts_by_date_and_state(use_abbreviation=True)
        for key, case_count in jhu_data.items():
            date_code, state = key.split('_')
            date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
            shape_value = features.get(state, None)
            new_records[key] = {self.id_field: key,
                                self.state_field: state,
                                self.date_field: date_value,
                                self.cases_field: case_count,
                                self.shape_field: shape_value}

        # load nsw source.  NSW source values override any existing jhu values for nsw.
        state = 'NSW'
        for date_code, case_count in nsw_source.counts_by_date().items():
            key = '{}_{}'.format(date_code, state)
            new_record = new_records.get(key, None)
            if new_record:
                new_record[self.cases_field] = case_count
            else:
                date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
                shape_value = features.get(state, None)
                new_records[key] = {self.id_field: key,
                                    self.state_field: state,
                                    self.date_field: date_value,
                                    self.cases_field: case_count,
                                    self.shape_field: shape_value}

        aus_records = {}
        for date_state, record in new_records.items():
            date_code, state = date_state.split('_')
            key = '{}_AUS'.format(date_code)
            aus_record = aus_records.get(key, None)
            if aus_record:
                aus_record[self.cases_field] += record[self.cases_field]
            else:
                date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
                aus_records[key] = {self.id_field: key,
                                    self.state_field: 'AUS',
                                    self.date_field: date_value,
                                    self.cases_field: record[self.cases_field],
                                    self.shape_field: None}

        for key, record in aus_records.items():
            new_records[key] = record

        fields = [self.id_field, self.date_field, self.state_field, self.cases_field]
        return self._helper.update_records(new_data=new_records, fields=fields, add_new=True, delete_unmatched=True, shape_field=self.shape_field)


class DeathsByDateAndState2(TableBase):
    def __init__(self, source: str = r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\DeathsByDateAndState2'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        super().__init__(source=source, id_field='RecordId')

        self.state_field = 'State'
        self.date_field = 'Date'
        self.deaths_field = 'Deaths'

    def update_from_source(self,
                           covid_source: covid19data_SourceData.COVID_AU_state = covid19data_SourceData.COVID_AU_state(),
                           geometry_source: TableBase = None):
        new_records = {}

        # get state capital geometries indexed by state abbreviation
        if not geometry_source:
            geometry_source = StateCapitals()
        features = geometry_source.values_by_id(value_field='SHAPE@')

        for item in covid_source.source_data():
            date_value = item[covid_source.fields.date]
            state = item[covid_source.fields.state_abbrev]
            deaths_count = item[covid_source.fields.deaths]
            date_code = date_value.strftime('%Y%m%d')
            shape_value = features.get(state, None)
            key = '{}_{}'.format(date_code, state)
            new_records[key] = {self.id_field: key,
                                self.state_field: state,
                                self.date_field: date_value,
                                self.deaths_field: deaths_count,
                                self.shape_field: shape_value}

        aus_records = {}
        for date_state, record in new_records.items():
            date_code, state = date_state.split('_')
            key = '{}_AUS'.format(date_code)
            aus_record = aus_records.get(key, None)
            if aus_record:
                aus_record[self.deaths_field] += record[self.deaths_field]
            else:
                date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
                aus_records[key] = {self.id_field: key,
                                    self.state_field: 'AUS',
                                    self.date_field: date_value,
                                    self.deaths_field: record[self.deaths_field],
                                    self.shape_field: None}

        for key, record in aus_records.items():
            new_records[key] = record

        fields = [self.id_field, self.date_field, self.state_field, self.deaths_field]
        return self._helper.update_records(new_data=new_records, fields=fields, add_new=True, delete_unmatched=True, shape_field=self.shape_field)


class DeathsByDateAndState(TableBase):
    def __init__(self, source: str = r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\DeathsByDateAndState2'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        super().__init__(source=source, id_field='RecordId')

        self.state_field = 'State'
        self.date_field = 'Date'
        self.deaths_field = 'Deaths'

    def update_from_source(self,
                           jhu_source: JHU_SourceData.JhuDeathsData = JHU_SourceData.JhuDeathsData(),
                           geometry_source: TableBase = None):
        new_records = {}

        # get state capital geometries indexed by state abbreviation
        if not geometry_source:
            geometry_source = StateCapitals()
        features = geometry_source.values_by_id(value_field='SHAPE@')

        # load jhu source.  No other deaths by state yet.
        jhu_data = jhu_source.counts_by_date_and_state(use_abbreviation=True)
        for key, deaths_count in jhu_data.items():
            date_code, state = key.split('_')
            date_value = datetime.datetime.strptime(date_code, '%Y%m%d').date()
            shape_value = features.get(state, None)
            new_records[key] = {self.id_field: key,
                                self.state_field: state,
                                self.date_field: date_value,
                                self.deaths_field: deaths_count,
                                self.shape_field: shape_value}

        aus_records = {}
        for date_state, record in new_records.items():
            date_code, state = date_state.split('_')
            key = '{}_AUS'.format(date_code)
            aus_record = aus_records.get(key, None)
            if aus_record:
                aus_record[self.deaths_field] += record[self.deaths_field]
            else:
                date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
                aus_records[key] = {self.id_field: key,
                                    self.state_field: 'AUS',
                                    self.date_field: date_value,
                                    self.deaths_field: record[self.deaths_field],
                                    self.shape_field: None}

        for key, record in aus_records.items():
            new_records[key] = record

        fields = [self.id_field, self.date_field, self.state_field, self.deaths_field]
        return self._helper.update_records(new_data=new_records, fields=fields, add_new=True, delete_unmatched=True, shape_field=self.shape_field)


class HospitalDataByDateAndState(TableBase):
    def __init__(self, source: str = r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\HospitalDataByDateAndState'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        super().__init__(source=source, id_field='RecordId')

        self.state_field = 'State'
        self.date_field = 'Date'
        self.deaths_field = 'Deaths'


class TestsByDateAndState2(TableBase):
    def __init__(self, source: str = r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\TestsByDateAndState2'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        super().__init__(source=source, id_field='RecordId')

        self.state_field = 'State'
        self.date_field = 'Date'
        self.tests_field = 'Tests'

    def update_from_source(self,
                           covid_source: covid19data_SourceData.COVID_AU_state = covid19data_SourceData.COVID_AU_state(),
                           nsw_source: NSW_SourceData.NswTestData = NSW_SourceData.NswTestData(),
                           geometry_source: TableBase = None):
        new_records = {}

        # get state capital geometries indexed by state abbreviation
        if not geometry_source:
            geometry_source = StateCapitals()
        features = geometry_source.values_by_id(value_field='SHAPE@')

        for item in covid_source.source_data():
            date_value = item[covid_source.fields.date]
            state = item[covid_source.fields.state_abbrev]
            tests_count = item[covid_source.fields.tests]
            date_code = date_value.strftime('%Y%m%d')
            shape_value = features.get(state, None)
            key = '{}_{}'.format(date_code, state)
            new_records[key] = {self.id_field: key,
                                self.state_field: state,
                                self.date_field: date_value,
                                self.tests_field: tests_count,
                                self.shape_field: shape_value}

        # load nsw source.  NSW source values override any existing jhu values for nsw.
        state = 'NSW'
        for date_code, test_count in nsw_source.counts_by_date().items():
            key = '{}_{}'.format(date_code, state)
            new_record = new_records.get(key, None)
            if new_record:
                new_record[self.tests_field] = test_count
            else:
                date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
                shape_value = features.get(state, None)
                new_records[key] = {self.id_field: key,
                                    self.state_field: state,
                                    self.date_field: date_value,
                                    self.tests_field: test_count,
                                    self.shape_field: shape_value}

        aus_records = {}
        for date_state, record in new_records.items():
            date_code, state = date_state.split('_')
            key = '{}_AUS'.format(date_code)
            aus_record = aus_records.get(key, None)
            if aus_record:
                aus_record[self.tests_field] += record[self.tests_field]
            else:
                date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
                aus_records[key] = {self.id_field: key,
                                    self.state_field: 'AUS',
                                    self.date_field: date_value,
                                    self.tests_field: record[self.tests_field],
                                    self.shape_field: None}

        for key, record in aus_records.items():
            new_records[key] = record

        fields = [self.id_field, self.date_field, self.state_field, self.tests_field]
        return self._helper.update_records(new_data=new_records, fields=fields, add_new=True, delete_unmatched=True, shape_field=self.shape_field)


class TestsByDateAndState(TableBase):
    def __init__(self, source: str = r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\TestsByDateAndState2'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        super().__init__(source=source, id_field='RecordId')

        self.state_field = 'State'
        self.date_field = 'Date'
        self.tests_field = 'Tests'

    def update_from_source(self,
                           nsw_source: NSW_SourceData.NswTestData = NSW_SourceData.NswTestData(),
                           geometry_source: TableBase = None):
        new_records = {}

        # get state capital geometries indexed by state abbreviation
        if not geometry_source:
            geometry_source = StateCapitals()
        features = geometry_source.values_by_id(value_field='SHAPE@')

        # load nsw source.  No other tests data yet
        state = 'NSW'
        for date_code, test_count in nsw_source.counts_by_date().items():
            key = '{}_{}'.format(date_code, state)
            new_record = new_records.get(key, None)
            if new_record:
                new_record[self.tests_field] = test_count
            else:
                date_value = datetime.datetime.strptime(date_code, '%Y%m%d').date()
                shape_value = features.get(state, None)
                new_records[key] = {self.id_field: key,
                                    self.state_field: state,
                                    self.date_field: date_value,
                                    self.tests_field: test_count,
                                    self.shape_field: shape_value}

        aus_records = {}
        for date_state, record in new_records.items():
            date_code, state = date_state.split('_')
            key = '{}_AUS'.format(date_code)
            aus_record = aus_records.get(key, None)
            if aus_record:
                aus_record[self.tests_field] += record[self.tests_field]
            else:
                date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
                aus_records[key] = {self.id_field: key,
                                    self.state_field: 'AUS',
                                    self.date_field: date_value,
                                    self.tests_field: record[self.tests_field],
                                    self.shape_field: None}

        for key, record in aus_records.items():
            new_records[key] = record

        fields = [self.id_field, self.date_field, self.state_field, self.tests_field]
        return self._helper.update_records(new_data=new_records, fields=fields, add_new=True, delete_unmatched=True, shape_field=self.shape_field)


# --------------------------------------------
# by Date and Postcode
# --------------------------------------------


class CasesByDateAndPostcode(TableBase):
    def __init__(self, source: str = r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\CasesByDateAndPostcode2'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        super().__init__(source=source, id_field='RecordId')

        self.date_field = 'Date'
        self.postcode_field = 'Postcode'
        self.cases_field = 'Cases'

    def update_from_source(self,
                           nsw_source: NSW_SourceData.NswNotificationData = NSW_SourceData.NswNotificationData(),
                           geometry_source: TableBase = None):
        new_records = {}

        # get state capital geometries indexed by state abbreviation
        if not geometry_source:
            geometry_source = POA2016.centroids()
        features = geometry_source.values_by_id(value_field='SHAPE@')

        # load nsw source.  NSW source values override any existing jhu values for nsw.
        for key, case_count in nsw_source.counts_by_date_and_postcode().items():
            date_code, postcode = key.split('_')
            new_record = new_records.get(key, None)
            if new_record:
                new_record[self.cases_field] = case_count
            else:
                shape_value = features.get(postcode, None)
                date_value = datetime.datetime.strptime(date_code, '%Y%m%d').date()
                new_records[key] = {self.id_field: key,
                                    self.postcode_field: postcode,
                                    self.date_field: date_value,
                                    self.cases_field: case_count,
                                    self.shape_field: shape_value}

        fields = [self.id_field, self.date_field, self.postcode_field, self.cases_field]
        return self._helper.update_records(new_data=new_records, fields=fields, add_new=True, delete_unmatched=True, shape_field=self.shape_field)


class CasesByDatePostcodeSource(TableBase):
    def __init__(self, source: str = r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\CasesByDatePostcodeSource'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        super().__init__(source=source, id_field='RecordId')

        self.date_field = 'Date'
        self.postcode_field = 'Postcode'
        self.cases_field = 'Cases'
        self.likely_source_field = 'LikelySource'

        self.source_conversions = {'Overseas': 'Overseas',
                                   'Locally acquired - source not identified': 'Locally Acquired - Unknown Source',
                                   'Locally acquired - contact of a confirmed case and/or in a known cluster': 'Locally Acquired - Known Source',
                                   'Interstate': 'Interstate'}

    def __convert_key(self, in_key):
        date_code, postcode, source = in_key.split('_')
        converted_source = self.source_conversions[source]
        return '{}_{}_{}'.format(date_code, postcode, converted_source)

    def update_from_source(self,
                           nsw_source: NSW_SourceData.NswNotificationAndSourceData = NSW_SourceData.NswNotificationAndSourceData(),
                           geometry_source: TableBase = None):
        new_records = {}

        # get state capital geometries indexed by state abbreviation
        if not geometry_source:
            geometry_source = POA2016.centroids()
        features = geometry_source.values_by_id(value_field='SHAPE@')

        # load nsw source.  NSW source values override any existing jhu values for nsw.
        for key, case_count in nsw_source.counts_by_date_postcode_source().items():
            my_key = self.__convert_key(key)
            date_code, postcode, source = my_key.split('_')
            new_record = new_records.get(my_key, None)
            if new_record:
                new_record[self.cases_field] = case_count
            else:
                shape_value = features.get(postcode, None)
                date_value = datetime.datetime.strptime(date_code, '%Y%m%d').date()
                new_records[my_key] = {self.id_field: my_key,
                                       self.postcode_field: postcode,
                                       self.date_field: date_value,
                                       self.likely_source_field: source,
                                       self.cases_field: case_count,
                                       self.shape_field: shape_value}

        fields = [self.id_field, self.date_field, self.postcode_field, self.likely_source_field, self.cases_field]
        return self._helper.update_records(new_data=new_records, fields=fields, add_new=True, delete_unmatched=True, shape_field=self.shape_field)


class TestsByDateAndPostcode(TableBase):
    def __init__(self, source: str = r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\TestsByDateAndPostcode2'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        super().__init__(source=source, id_field='RecordId')

        self.date_field = 'Date'
        self.postcode_field = 'Postcode'
        self.tests_field = 'Tests'

    def update_from_source(self,
                           nsw_source: NSW_SourceData.NswTestData = NSW_SourceData.NswTestData(),
                           geometry_source: TableBase = None):
        new_records = {}

        # get state capital geometries indexed by state abbreviation
        if not geometry_source:
            geometry_source = POA2016.centroids()
        features = geometry_source.values_by_id(value_field='SHAPE@')

        # load nsw source.
        for key, test_count in nsw_source.counts_by_date_and_postcode().items():
            date_code, postcode = key.split('_')
            new_record = new_records.get(key, None)
            if new_record:
                new_record[self.tests_field] = test_count
            else:
                shape_value = features.get(postcode, None)
                date_value = datetime.datetime.strptime(date_code, '%Y%m%d').date()
                new_records[key] = {self.id_field: key,
                                    self.postcode_field: postcode,
                                    self.date_field: date_value,
                                    self.tests_field: test_count,
                                    self.shape_field: shape_value}

        fields = [self.id_field, self.date_field, self.postcode_field, self.tests_field]
        return self._helper.update_records(new_data=new_records, fields=fields, add_new=True, delete_unmatched=True, shape_field=self.shape_field)
