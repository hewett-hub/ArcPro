import datetime
import logging

from arcgis.features import FeatureLayer

from graphc.data.pois import StateCapitals
from graphc.covid.admin import AuthorityData
from graphc.covid.admin import AuthorityData2
from graphc.covid.admin import statistics
from graphc.covid.admin import utilities
from graphc.da import da_agol


class CrisperStatisticsByState(object):
    def __init__(self, service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                                   r'CRISPER_Statistics_by_State/FeatureServer/0'):
        self.service_url = service_url
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

    def layer(self):
        return FeatureLayer(self.service_url)

    def synchronize(self, new_data):
        logging.info('Synchronizing: ' + self.service_url)

        logging.info('Identifying Changes')

        deletes = []
        updates = []

        target_layer = self.layer()
        query_result = target_layer.query()
        for row in query_result:
            state = row.attributes[self.state_field]
            item = new_data.pop(state, None)
            if not item:
                deletes.append(row.attributes[query_result.object_id_field_name])
            else:
                update_required = False

                if da_agol.update_date_field(row=row,
                                             field_name=self.most_recent_case_date_field,
                                             new_value=item[self.most_recent_case_date_field]):
                    update_required = True

                if da_agol.update_int_field(row=row,
                                            field_name=self.most_recent_case_count_field,
                                            new_value=item[self.most_recent_case_count_field ]):
                    update_required = True

                if da_agol.update_int_field(row=row,
                                            field_name=self.total_cases_field,
                                            new_value=item[self.total_cases_field]):
                    update_required = True

                if da_agol.update_date_field(row=row,
                                             field_name=self.most_recent_death_date_field,
                                             new_value=item[self.most_recent_test_date_field]):
                    update_required = True

                if da_agol.update_int_field(row=row,
                                            field_name=self.most_recent_death_count_field,
                                            new_value=item[self.most_recent_death_count_field]):
                    update_required = True

                if da_agol.update_int_field(row=row,
                                            field_name=self.total_deaths_field,
                                            new_value=item[self.total_deaths_field]):
                    update_required = True

                if da_agol.update_date_field(row=row,
                                             field_name=self.most_recent_test_date_field,
                                             new_value=item[self.most_recent_test_date_field]):
                    update_required = True

                if da_agol.update_int_field(row=row,
                                            field_name=self.most_recent_test_count_field,
                                            new_value=item[self.most_recent_test_count_field]):
                    update_required = True

                if da_agol.update_int_field(row=row,
                                            field_name=self.total_tests_field,
                                            new_value=item[self.total_tests_field]):
                    update_required = True

                if update_required:
                    updates.append(row)

        # any remaining data_models items are new records
        adds = []
        for new_item in new_data.values():
            row = {"attributes":
                   {self.state_field: new_item[self.state_field],
                    self.most_recent_case_date_field: new_item[self.most_recent_case_date_field],
                    self.most_recent_case_count_field: new_item[self.most_recent_case_count_field],
                    self.total_cases_field: new_item[self.total_cases_field],
                    self.most_recent_test_date_field: new_item[self.most_recent_test_date_field],
                    self.most_recent_test_count_field: new_item[self.most_recent_test_count_field],
                    self.total_tests_field: new_item[self.total_tests_field],
                    self.most_recent_death_date_field: new_item[self.most_recent_death_date_field],
                    self.most_recent_death_count_field: new_item[self.most_recent_death_count_field],
                    self.total_deaths_field: new_item[self.total_deaths_field]},
                   "geometry": utilities.geometry_to_json(new_item['shape'])}
            adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=updates)

    @staticmethod
    def _new_state_item(state, shape):
        return {'state': state,
                'shape': shape,
                'total_cases': 0,
                'most_recent_case_date': None,
                'most_recent_case_count': None,
                'total_deaths': 0,
                'most_recent_death_date': None,
                'most_recent_death_count': None,
                'total_tests': 0,
                'most_recent_test_date': None,
                'most_recent_test_count': None}

    def _calculate_case_stats(self, new_data, source_data: AuthorityData.CasesByDateAndState):
        case_data = source_data.data()
        for case_report in case_data:
            state = case_report['state']
            cases = case_report['notifications']
            report_date = case_report['date_code']

            state_item = new_data.get(state, None)
            if not state_item:
                state_item = self._new_state_item(state, case_report['shape'])
                new_data[state] = state_item

            state_item['total_cases'] += cases
            most_recent_date = state_item['most_recent_case_date']
            if not most_recent_date or most_recent_date < report_date:
                state_item['most_recent_case_date'] = report_date
                state_item['most_recent_case_count'] = cases

        return new_data

    def _calculate_deaths_stats(self, new_data, source_data: AuthorityData.DeathsByDateAndState):
        death_data = source_data.data()
        for deaths_report in death_data:
            state = deaths_report['state']
            deaths = deaths_report['deaths']
            report_date = deaths_report['date_code']

            state_item = new_data.get(state, None)
            if not state_item:
                state_item = self._new_state_item(state, deaths_report['shape'])
                new_data[state] = state_item

            state_item['total_deaths'] += deaths
            most_recent_date = state_item['most_recent_death_date']
            if not most_recent_date or most_recent_date < report_date:
                state_item['most_recent_death_date'] = report_date
                state_item['most_recent_death_count'] = deaths

        return new_data

    def _calculate_tests_stats(self, new_data, source_data: AuthorityData.TestsByDateAndState):
        tests_data = source_data.data()
        for tests_report in tests_data:
            state = tests_report['state']
            tests = tests_report['tests']
            report_date = tests_report['date_code']

            state_item = new_data.get(state, None)
            if not state_item:
                state_item = self._new_state_item(state, tests_report['shape'])
                new_data[state] = state_item

            state_item['total_tests'] += tests
            most_recent_date = state_item['most_recent_test_date']
            if not most_recent_date or most_recent_date < report_date:
                state_item['most_recent_test_date'] = report_date
                state_item['most_recent_test_count'] = tests

        return new_data

    def synch_with_authority(self,
                             cases: AuthorityData.CasesByDateAndState,
                             tests: AuthorityData.TestsByDateAndState,
                             deaths: AuthorityData.DeathsByDateAndState):

        logging.info('Synchronizing: ' + self.service_url)

        logging.info('Calculating New Values')
        new_data = {}
        self._calculate_case_stats(new_data, cases)
        self._calculate_deaths_stats(new_data, deaths)
        self._calculate_tests_stats(new_data, tests)

        logging.info('Identifying Changes')

        deletes = []
        updates = []

        target_layer = self.layer()
        query_result = target_layer.query()
        for row in query_result:
            state = row.attributes[self.state_field]
            item = new_data.pop(state, None)
            if not item:
                deletes.append(row.attributes[query_result.object_id_field_name])
            else:
                update_required = False

                if da_agol.update_date_field(row, self.most_recent_case_date_field, item['most_recent_case_date']):
                    update_required = True

                if da_agol.update_int_field(row, self.most_recent_case_count_field, item['most_recent_case_count']):
                    update_required = True

                if da_agol.update_int_field(row, self.total_cases_field, item['total_cases']):
                    update_required = True

                if da_agol.update_date_field(row, self.most_recent_death_date_field, item['most_recent_death_date']):
                    update_required = True

                if da_agol.update_int_field(row, self.most_recent_death_count_field, item['most_recent_death_count']):
                    update_required = True

                if da_agol.update_int_field(row, self.total_deaths_field, item['total_deaths']):
                    update_required = True

                if da_agol.update_date_field(row, self.most_recent_test_date_field, item['most_recent_test_date']):
                    update_required = True

                if da_agol.update_int_field(row, self.most_recent_test_count_field, item['most_recent_test_count']):
                    update_required = True

                if da_agol.update_int_field(row, self.total_tests_field, item['total_tests']):
                    update_required = True

                if update_required:
                    updates.append(row)

        # any remaining data_models items are new records
        adds = []
        for new_item in new_data.values():
            row = {"attributes":
                   {self.state_field: new_item['state'],
                    self.most_recent_case_date_field: new_item['most_recent_case_date'],
                    self.most_recent_case_count_field: new_item['most_recent_case_count'],
                    self.total_cases_field: new_item['total_cases'],
                    self.most_recent_test_date_field: new_item['most_recent_test_date'],
                    self.most_recent_test_count_field: new_item['most_recent_test_count'],
                    self.total_tests_field: new_item['total_tests'],
                    self.most_recent_death_date_field: new_item['most_recent_death_date'],
                    self.most_recent_death_count_field: new_item['most_recent_death_count'],
                    self.total_deaths_field: new_item['total_deaths']},
                   "geometry": utilities.geometry_to_json(new_item['shape'])}
            adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=updates)


class CrisperCaseStatisticsByDateStateAndName(object):
    def __init__(self,
                 service_url,
                 place_id_field,
                 date_field='DateValue',
                 statistic_name_field='StatisticName',
                 statistic_value_field='StatisticValue'):
        self.service_url = service_url
        self.place_id_field = place_id_field
        self.date_field = date_field
        self.statistic_name_field = statistic_name_field
        self.statistic_value_field = statistic_value_field

    def layer(self):
        return FeatureLayer(self.service_url)

    def query(self, where_clause='1=1'):
        return self.layer().query(where=where_clause)

    def update_statistic(self, statistic_name, statistic_values, place_shapes, rounding=4):
        """

        :param statistic_name: statistic name (case sensitive)
        :type statistic_name: str
        :param statistic_values: {date_placeid: value}.  The placeid should always be uppercase.
        :type statistic_values:
        :param place_shapes: {placeid: shape}.  The placeid should always be uppercase.
        :type place_shapes:
        :param rounding:  The decimal place rounding to be applied to data values
        :type rounding: int
        :return:
        :rtype:
        """
        logging.info('Identifying Changes')

        deletes = []
        updates = []

        target_layer = self.layer()
        where_clause = "{} = '{}'".format(self.statistic_name_field, statistic_name)
        query_result = target_layer.query(where=where_clause)
        for row in query_result:
            row_date = da_agol.date_field_value_to_datetime(row.attributes[self.date_field])
            key = '{}_{}'.format(row_date.strftime('%Y%m%d'), row.attributes[self.place_id_field])
            item = statistic_values.get(key)

            if not item:
                deletes.append(row.attributes[query_result.object_id_field_name])
            elif da_agol.update_float_field(row, self.statistic_value_field, item['statistic_value'], rounding):
                updates.append(row)

        # any remaining data_models items are new records
        adds = []
        for key, value in statistic_values.items():
            date_value, place_id = key.split('_')
            date_value = datetime.datetime.strptime(date_value, '%Y%m%d').date()
            row = {"attributes":
                   {self.place_id_field: place_id,
                    self.date_field: date_value,
                    self.statistic_name_field: statistic_name,
                    self.statistic_value_field: round(value, rounding)},
                   "geometry": utilities.geometry_to_json(place_shapes.get(place_id, None))}
            adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=updates)


# ---------------------------------------------
# Notifications by Postcode
# ---------------------------------------------

# class Covid19CaseLocationsByPostcode(object):
#     """
#     A feature service wrapper class that supports common operations.
#     """
#
#     def __init__(self, service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
#                                    r'Case_Locations_By_Postcode/FeatureServer/0'):
#         self.service_url = service_url
#         self.postcode_field = 'PostCode'
#         self.date_code_field = 'DateString'
#         self.date_field = 'ReportDate'
#         self.date_code_format = '%Y%m%d'
#
#     def layer(self):
#         return FeatureLayer(self.service_url)
#
#     def query(self, where_clause='1=1'):
#         return self.layer().query(where=where_clause)
#
#     def synch_with_authority(self, authority: AuthorityData.NotificationsByDateAndPostcode):
#         logging.info('Synchronizing: ' + self.service_url)
#
#         source_data = authority.data_by_date_and_postcode()
#
#         logging.info('Identifying Changes')
#
#         deletes = []
#
#         target_layer = self.layer()
#         query_result = target_layer.query()
#         for row in query_result:
#             key = '{}_{}'.format(row.attributes[self.date_code_field], row.attributes[self.postcode_field])
#             update_item = source_data.get(key, None)
#             if update_item:
#                 # if an update item was found, subtract 1 from the notifications total.
#                 update_item['notifications'] -= 1
#                 if update_item['notifications'] < 1:
#                     # If the new notifications total is less than 1, then this was the last notification for the postcode/date.
#                     # Remove the postcode/date item from the collection of update items so any additional records associated with
#                     # this date/postcode combo will be deleted from the online data.
#                     source_data.pop(key, None)
#             else:
#                 # if no matching update item was found, delete the record from online.
#                 deletes.append(row.attributes[query_result.object_id_field_name])
#
#         # any remaining data_models items are new records
#         adds = []
#
#         for key, new_item in source_data.items():
#             date_code, postcode = key.split('_')
#             date = datetime.datetime.strptime(date_code, '%Y%m%d')
#             for i in range(new_item['notifications']):
#                 row = {"attributes":
#                        {self.date_code_field: date_code,
#                         self.date_field: date,
#                         self.postcode_field: postcode.upper()},
#                        "geometry": utilities.geometry_to_json(new_item['shape'])}
#                 adds.append(row)
#
#         return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=None)


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

    def synch_with_authority(self, authority: AuthorityData2.CasesByDatePostcodeSource):
        logging.info('Synchronizing: ' + self.service_url)

        fields = [authority.date_field, authority.postcode_field, authority.likely_source_field, authority.cases_field, 'SHAPE@']
        source_data = authority.indexed_records(fields=fields)

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
                update_item[authority.cases_field] -= 1
                if update_item[authority.cases_field] < 1:
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
            for i in range(new_item[authority.cases_field]):
                row = {"attributes":
                       {self.date_code_field: date_code,
                        self.date_field: date,
                        self.postcode_field: postcode.upper(),
                        self.likely_source_field: likely_source},
                       "geometry": utilities.geometry_to_json(new_item['SHAPE@'])}
                adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=None)


class Covid19NotificationsByDateAndPostcode(object):
    """
    A feature service wrapper class that supports common operations.
    """

    def __init__(self, service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                                   r'COVID19_Notifications_by_Date_and_Postcode/FeatureServer/0'):
        self.service_url = service_url
        self.id_field = 'ID'
        self.postcode_field = 'Postcode'
        self.date_field = 'Date'
        self.notifications_field = 'Notifications'
        self.date_code_format = '%Y%m%d'

    def layer(self):
        return FeatureLayer(self.service_url)

    def query(self, where_clause='1=1'):
        return self.layer().query(where=where_clause)

    def synch_with_authority(self, authority: AuthorityData.NotificationsByDateAndPostcode):
        logging.info('Synchronizing: ' + self.service_url)

        source = authority.data_by_date_and_postcode()

        logging.info('Identifying Changes')

        deletes = []
        updates = []

        target_layer = self.layer()
        query_result = target_layer.query()
        for row in query_result:
            key = row.attributes[self.id_field]
            item = source.pop(key, None)
            if not item:
                deletes.append(row.attributes[query_result.object_id_field_name])
            elif da_agol.update_int_field(row, self.notifications_field, item['notifications']):
                updates.append(row)

        # any remaining data_models items are new records
        adds = []
        for key, new_item in source.items():
            date_code, postcode = key.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            row = {"attributes":
                   {self.id_field: key,
                    self.date_field: date,
                    self.postcode_field: postcode.upper(),
                    self.notifications_field: new_item['notifications']},
                   "geometry": utilities.geometry_to_json(new_item['shape'])}
            adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=updates)


class Covid19TotalNotificationsByPostcode(object):
    """
    A feature service wrapper class that supports common operations.
    """
    def __init__(self, service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                                   r'COVID_19_Total_Notifications_by_Postcode/FeatureServer/0'):
        self.service_url = service_url
        self.postcode_field = 'Postcode'
        self.notifications_field = 'Notifications'
        self.most_recent_code_field = 'MostRecentCode'
        self.most_recent_date_field = 'MostRecentDate'
        self.most_recent_new_field = 'MostRecentNew'

    def layer(self):
        return FeatureLayer(self.service_url)

    def query(self, where_clause='1=1'):
        return self.layer().query(where=where_clause)

    def synch_with_authority(self, authority: AuthorityData.NotificationsByDateAndPostcode):
        logging.info('Synchronizing: ' + self.service_url)

        source = authority.total_notifications_by_postcode()

        logging.info('Identifying Changes')

        updates = []

        target_layer = self.layer()
        query_result = target_layer.query()
        for row in query_result:
            postcode = row.attributes[self.postcode_field]
            item = source.pop(postcode, None)
            if item:
                most_recent_code = item['most_recent']
                most_recent_new = item['most_recent_new']
                total = item['notifications']
            else:
                most_recent_code = None
                most_recent_new = None
                total = None

            update_required = False
            if da_agol.update_str_field(row, self.most_recent_code_field, most_recent_code):
                update_required = True

            if da_agol.update_date_field(row, self.most_recent_date_field, new_value=most_recent_code):
                update_required = True

            if da_agol.update_int_field(row, self.most_recent_new_field, most_recent_new):
                update_required = True

            if da_agol.update_int_field(row, self.notifications_field, total):
                update_required = True

            if update_required:
                updates.append(row)

        # any remaining data_models items are new records
        adds = []
        for postcode, new_item in source.items():
            most_recent_code = new_item['most_recent']
            row = {"attributes":
                   {self.postcode_field: postcode,
                    self.most_recent_code_field: most_recent_code,
                    self.most_recent_date_field: datetime.datetime.strptime(most_recent_code, '%Y%m%d'),
                    self.notifications_field: new_item['notifications'],
                    self.most_recent_new_field: new_item['most_recent_new']},
                   "geometry": utilities.geometry_to_json(new_item['shape'])}
            adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=None, updates=updates)


# ---------------------------------------------
# Notifications by State
# ---------------------------------------------


class Covid19StatisticsByDateAndState(object):
    """
    A feature service wrapper class that supports common operations.
    """

    def __init__(self, service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                                   r'COVID19_Daily_Statistics_by_Date_and_State/FeatureServer/0'):
        self.service_url = service_url
        self.id_field = 'DateState'
        self.state_field = 'State'
        self.date_field = 'DateValue'
        self.date_code_field = 'DateCode'
        self.new_deaths_field = 'NewDeaths'
        self.new_notifications_field = 'NewNotifications'
        self.new_tests_field = 'NewTests'
        self.total_deaths_field = 'TotalDeaths'
        self.total_notifications_field = 'TotalNotifications'
        self.total_tests_field = 'TotalTests'
        self.cases_7_day_ave_field = 'Cases7DayAve'
        self.tests_7_day_ave_field = 'Tests7DayAve'
        self.deaths_7_day_ave_field = 'Deaths7DayAve'
        self.date_code_format = '%Y%m%d'

    def layer(self):
        return FeatureLayer(self.service_url)

    def query(self, where_clause='1=1'):
        return self.layer().query(where=where_clause)

    @staticmethod
    def _new_item(state, date_code, shape):
        return{'state': state,
               'date_code': date_code,
               'shape': shape,
               'new_cases': 0,
               'new_deaths': 0,
               'new_tests': 0,
               'total_cases': 0,
               'total_deaths': 0,
               'total_tests': 0,
               'tests_7_day_ave': 0,
               'cases_7_day_ave': 0,
               'deaths_7_day_ave': 0
               }

    def _calculate_cases_stats(self, new_data, source_data: AuthorityData.CasesByDateAndState):

        case_data = source_data.cumulative_notifications_by_date_and_state(all_days=True)
        #case_data = statistics.cumulative_daily_totals_by_group(data=source_data.data(),
        #                                                        group_id_field=source_data.state_field,
        #                                                        value_field=source_data.cases_field,
        #                                                        date_field=source_data.date_field)
        averages = statistics.moving_daily_averages_by_date_and_group(data=source_data.data(),
                                                                      group_id_field='state',
                                                                      value_field='notifications',
                                                                      date_field='date_code',
                                                                      date_format='%Y%m%d',
                                                                      n=7)

        for key, values in case_data.items():
            data_item = new_data.get(key, None)
            if not data_item:
                data_item = self._new_item(values['state'], values['date_code'], values['shape'])
                new_data[key] = data_item
            data_item['new_cases'] = values['new_notifications']
            data_item['total_cases'] = values['notifications']
            data_item['cases_7_day_ave'] = averages.get(key, None)

        return new_data

    def _calculate_deaths_stats(self, new_data, source_data: AuthorityData.DeathsByDateAndState):

        deaths_data = source_data.cumulative_deaths_by_date_and_state(all_days=True)
        averages = statistics.moving_daily_averages_by_date_and_group(data=source_data.data(),
                                                                      group_id_field='state',
                                                                      value_field='deaths',
                                                                      date_field='date_code',
                                                                      date_format='%Y%m%d',
                                                                      n=7)

        for key, values in deaths_data.items():
            data_item = new_data.get(key, None)
            if not data_item:
                data_item = self._new_item(values['state'], values['date_code'], values['shape'])
                new_data[key] = data_item
            data_item['new_deaths'] = values['new_deaths']
            data_item['total_deaths'] = values['deaths']
            data_item['deaths_7_day_ave'] = averages.get(key, None)

    def _calculate_test_stats(self, new_data, source_data: AuthorityData.TestsByDateAndState):

        tests_data = source_data.cumulative_tests_by_date_and_state(all_days=True)
        averages = statistics.moving_daily_averages_by_date_and_group(data=source_data.data(),
                                                                      group_id_field='state',
                                                                      value_field='tests',
                                                                      date_field='date_code',
                                                                      date_format='%Y%m%d',
                                                                      n=7)

        for key, values in tests_data.items():
            data_item = new_data.get(key, None)
            if not data_item:
                data_item = self._new_item(values['state'], values['date_code'], values['shape'])
                new_data[key] = data_item
            data_item['new_tests'] = values['new_tests']
            data_item['total_tests'] = values['tests']
            data_item['tests_7_day_ave'] = averages.get(key, None)

    def synch_with_authority(self,
                             cases: AuthorityData.CasesByDateAndState,
                             tests: AuthorityData.TestsByDateAndState,
                             deaths: AuthorityData.DeathsByDateAndState):

        logging.info('Synchronizing: ' + self.service_url)

        logging.info('Calculating New Values')

        new_data = {}
        self._calculate_test_stats(new_data, tests)
        self._calculate_cases_stats(new_data, cases)
        self._calculate_deaths_stats(new_data, deaths)

        logging.info('Identifying Changes')

        deletes = []
        updates = []

        target_layer = self.layer()
        query_result = target_layer.query()
        for row in query_result:
            key = row.attributes[self.id_field]
            item = new_data.pop(key, None)
            if not item:
                deletes.append(row.attributes[query_result.object_id_field_name])
            else:
                update_required = False

                if da_agol.update_date_field(row, self.date_field, new_value=item['date_code']):
                    update_required = True

                if da_agol.update_int_field(row, self.new_notifications_field, item['new_cases']):
                    update_required = True

                if da_agol.update_int_field(row, self.total_notifications_field, item['total_cases']):
                    update_required = True

                if da_agol.update_int_field(row, self.new_deaths_field, item['new_deaths']):
                    update_required = True

                if da_agol.update_int_field(row, self.total_deaths_field, item['total_deaths']):
                    update_required = True

                if da_agol.update_int_field(row, self.new_tests_field, item['new_tests']):
                    update_required = True

                if da_agol.update_int_field(row, self.total_tests_field, item['total_tests']):
                    update_required = True

                if da_agol.update_float_field(row, self.cases_7_day_ave_field, item['cases_7_day_ave'], 4):
                    update_required = True

                if da_agol.update_float_field(row, self.tests_7_day_ave_field, item['tests_7_day_ave'], 4):
                    update_required = True

                if da_agol.update_float_field(row, self.deaths_7_day_ave_field, item['deaths_7_day_ave'], 4):
                    update_required = True

                if update_required:
                    updates.append(row)

        # any remaining data_models items are new records
        adds = []
        for id_val, new_item in new_data.items():
            row = {"attributes":
                   {self.id_field: id_val,
                    self.state_field: new_item['state'],
                    self.date_field: new_item['date_code'],
                    self.date_code_field: new_item['date_code'],
                    self.new_notifications_field: new_item['new_cases'],
                    self.total_notifications_field: new_item['total_cases'],
                    self.new_deaths_field: new_item['new_deaths'],
                    self.total_deaths_field: new_item['total_deaths'],
                    self.new_tests_field: new_item['new_tests'],
                    self.total_tests_field: new_item['total_tests'],
                    self.cases_7_day_ave_field: new_item['cases_7_day_ave'],
                    self.tests_7_day_ave_field: new_item['tests_7_day_ave'],
                    self.deaths_7_day_ave_field: new_item['deaths_7_day_ave']},
                   "geometry": utilities.geometry_to_json(new_item['shape'])}
            adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=updates)


class Covid19StatisticsByDateAndPostcode(object):
    def __init__(self, service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                                   r'COVID19_Statistics_by_Date_and_Postcode/FeatureServer/0'):
        self.service_url = service_url
        self.id_field = 'ID'
        self.postcode_field = 'Postcode'
        self.date_field = 'Date'
        self.date_code_field = 'DateCode'
        self.new_cases_field = 'NewCases'
        self.total_cases_field = 'TotalCases'
        self.new_tests_field = 'NewTests'
        self.total_tests_field = 'TotalTests'
        self.ave_7_tests_field = 'Tests7DayAve'
        self.date_code_format = '%Y%m%d'

    def layer(self):
        return FeatureLayer(self.service_url)

    def query(self, where_clause='1=1'):
        return self.layer().query(where=where_clause)

    @staticmethod
    def _new_item(postcode, date_code, shape):
        return {'postcode': postcode,
                'date_code': date_code,
                'shape': shape,
                'new_cases': 0,
                'new_tests': 0,
                'total_cases': 0,
                'total_tests': 0,
                'ave7_tests': 0
                }

    def _calculate_cases_stats(self, new_data, source_data: AuthorityData.NotificationsByDateAndPostcode):

        case_data = source_data.cumulative_notifications_by_date_and_postcode(all_days=True)

        for key, values in case_data.items():
            data_item = new_data.get(key, None)
            if not data_item:
                data_item = self._new_item(values['postcode'], values['date_code'], values['shape'])
                new_data[key] = data_item
            data_item['new_cases'] = values['new_notifications']
            data_item['total_cases'] = values['notifications']

        return new_data

    def _calculate_test_stats(self, new_data, source_data: AuthorityData.TestsByDateAndPostcode):

        tests_data = source_data.cumulative_tests_by_date_and_postcode(all_days=True)

        for key, values in tests_data.items():
            data_item = new_data.get(key, None)
            if not data_item:
                data_item = self._new_item(values['postcode'], values['date_code'], values['shape'])
                new_data[key] = data_item
            data_item['new_tests'] = values['new_tests']
            data_item['total_tests'] = values['tests']

        test_aves = source_data.avg_tests_7_day_by_date_and_postcode()
        for key, values in test_aves.items():
            data_item = new_data.get(key, None)
            if not data_item:
                data_item = self._new_item(values['postcode'], values['date_code'], values['shape'])
                new_data[key] = data_item
            data_item['ave7_tests'] = values['ave_tests']

    def synch_with_authority(self,
                             cases: AuthorityData.NotificationsByDateAndPostcode,
                             tests: AuthorityData.TestsByDateAndPostcode):

        logging.info('Synchronizing: ' + self.service_url)

        logging.info('Calculating New Values')

        new_data = {}
        self._calculate_test_stats(new_data, tests)
        self._calculate_cases_stats(new_data, cases)

        logging.info('Identifying Changes')

        deletes = []
        updates = []

        target_layer = self.layer()
        query_result = target_layer.query()
        for row in query_result:
            key = row.attributes[self.id_field]
            item = new_data.pop(key, None)
            if not item:
                deletes.append(row.attributes[query_result.object_id_field_name])
            else:
                update_required = False

                if da_agol.update_date_field(row, self.date_field, new_value=item['date_code']):
                    update_required = True

                if da_agol.update_int_field(row, self.new_cases_field, item['new_cases']):
                    update_required = True

                if da_agol.update_int_field(row, self.total_cases_field, item['total_cases']):
                    update_required = True

                if da_agol.update_int_field(row, self.new_tests_field, item['new_tests']):
                    update_required = True

                if da_agol.update_int_field(row, self.total_tests_field, item['total_tests']):
                    update_required = True

                if da_agol.update_float_field(row, self.ave_7_tests_field, item['ave7_tests']):
                    update_required = True

                if update_required:
                    updates.append(row)

        # any remaining data_models items are new records
        adds = []
        for id_val, new_item in new_data.items():
            row = {"attributes":
                   {self.id_field: id_val,
                    self.postcode_field: new_item['postcode'],
                    self.date_field: new_item['date_code'],
                    self.date_code_field: new_item['date_code'],
                    self.new_cases_field: new_item['new_cases'],
                    self.total_cases_field: new_item['total_cases'],
                    self.new_tests_field: new_item['new_tests'],
                    self.total_tests_field: new_item['total_tests'],
                    self.ave_7_tests_field: new_item['ave7_tests']},
                   "geometry": utilities.geometry_to_json(new_item['shape'])}
            adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=updates)

# ---------------------------------------------
# Test by Postcode
# ---------------------------------------------


class Covid19TestsByDateAndPostcode(object):
    """
    A feature service wrapper class that supports common operations.
    """
    def __init__(self, service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                                   r'COVID_19_Tests_by_Date_and_Postcode/FeatureServer/0'):
        self.service_url = service_url
        self.id_field = 'ID'
        self.postcode_field = 'Postcode'
        self.date_field = 'Date'
        self.tests_field = 'Tests'
        self.date_code_format = '%Y%m%d'

    def layer(self):
        return FeatureLayer(self.service_url)

    def query(self, where_clause='1=1'):
        return self.layer().query(where=where_clause)

    def synch_with_authority(self, authority: AuthorityData.TestsByDateAndPostcode):
        logging.info('Synchronizing: ' + self.service_url)

        source = authority.data_by_date_and_postcode()

        logging.info('Identifying Changes')

        deletes = []
        updates = []

        target_layer = self.layer()
        query_result = target_layer.query()
        for row in query_result:
            key = row.attributes[self.id_field]
            item = source.pop(key, None)
            if not item:
                deletes.append(row.attributes[query_result.object_id_field_name])
            elif row.attributes[self.tests_field] != item['tests']:
                row.attributes[self.tests_field] = item['tests']
                updates.append(row)

        # any remaining data_models items are new records
        adds = []
        for key, new_item in source.items():
            date_code, postcode = key.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            row = {"attributes":
                   {self.id_field: key,
                    self.date_field: date,
                    self.postcode_field: postcode.upper(),
                    self.tests_field: new_item['tests']},
                   "geometry": utilities.geometry_to_json(new_item['shape'])}
            adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=updates)


class Covid19TotalTestsByPostcode(object):
    """
    A feature service wrapper class that supports common operations.
    """
    def __init__(self, service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                                   r'COVID_19_Total_Tests_by_Postcode/FeatureServer/0'):
        self.service_url = service_url
        self.postcode_field = 'Postcode'
        self.tests_field = 'Tests'
        self.most_recent_code_field = 'MostRecentCode'
        self.most_recent_date_field = 'MostRecentDate'
        self.most_recent_tests_field = 'MostRecentNewTests'

    def layer(self):
        return FeatureLayer(self.service_url)

    def query(self, where_clause='1=1'):
        return self.layer().query(where=where_clause)

    def synch_with_authority(self, authority: AuthorityData.TestsByDateAndPostcode):
        logging.info('Synchronizing: ' + self.service_url)

        source = authority.total_tests_by_postcode()

        logging.info('Identifying Changes')

        updates = []

        target_layer = self.layer()
        query_result = target_layer.query()
        for row in query_result:
            postcode = row.attributes[self.postcode_field]
            item = source.pop(postcode, None)
            if item:
                most_recent_code = item['most_recent']
                total = item['tests']
                most_recent_tests = item['most_recent_new']
            else:
                most_recent_code = None
                total = None
                most_recent_tests = None

            update_required = False
            if row.attributes[self.most_recent_code_field] != most_recent_code:
                row.attributes[self.most_recent_code_field] = most_recent_code
                row.attributes[self.most_recent_date_field] = datetime.datetime.strptime(most_recent_code, '%Y%m%d') if most_recent_code else None
                update_required = True

            if row.attributes[self.tests_field] != total:
                row.attributes[self.tests_field] = total
                update_required = True

            if row.attributes[self.most_recent_tests_field] != most_recent_tests:
                row.attributes[self.most_recent_tests_field] = most_recent_tests
                update_required = True

            if update_required:
                updates.append(row)

        # any remaining data_models items are new records
        adds = []
        for postcode, new_item in source.items():
            most_recent_code = new_item['most_recent']
            row = {"attributes":
                   {self.postcode_field: postcode,
                    self.most_recent_code_field: most_recent_code,
                    self.most_recent_date_field: datetime.datetime.strptime(most_recent_code, '%Y%m%d'),
                    self.tests_field: new_item['tests'],
                    self.most_recent_tests_field: new_item['most_recent_new']},
                   "geometry": utilities.geometry_to_json(new_item['shape'])}
            adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=None, updates=updates)


class Covid19CumulativeTestsByDateAndPostcode(object):
    """
    A feature service wrapper class that supports common operations.
    """
    def __init__(self, service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
                                   r'COVID_19_Cumulative_Tests_by_Date_and_Postcode/FeatureServer/0'):
        self.service_url = service_url
        self.id_field = 'ID'
        self.postcode_field = 'Postcode'
        self.date_field = 'Date'
        self.tests_field = 'Tests'
        self.date_code_format = '%Y%m%d'

    def layer(self):
        return FeatureLayer(self.service_url)

    def query(self, where_clause='1=1'):
        return self.layer().query(where=where_clause)

    def synch_with_authority(self, authority: AuthorityData.TestsByDateAndPostcode):
        logging.info('Synchronizing: ' + self.service_url)

        source = authority.cumulative_tests_by_date_and_postcode(all_days=True)

        logging.info('Identifying Changes')
        deletes = []
        updates = []

        target_layer = self.layer()
        query_result = target_layer.query()
        for row in query_result:
            key = row.attributes[self.id_field]
            item = source.pop(key, None)
            if not item:
                deletes.append(row.attributes[query_result.object_id_field_name])
            elif row.attributes[self.tests_field] != item['tests']:
                row.attributes[self.tests_field] = item['tests']
                updates.append(row)

        # any remaining data_models items are new records
        adds = []
        for key, new_item in source.items():
            date_code, postcode = key.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            row = {"attributes":
                       {self.id_field: key,
                        self.date_field: date,
                        self.postcode_field: postcode.upper(),
                        self.tests_field: new_item['tests']},
                   "geometry": utilities.geometry_to_json(new_item['shape'])}
            adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=updates)