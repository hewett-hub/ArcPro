import arcpy
import copy
import datetime
import logging

from graphc.covid.source import NSW_SourceData
from graphc.covid.source import JHU_SourceData
from graphc.data.abs2016 import POA2016
from graphc.data.pois import StateCapitals
from graphc.da import da_arcpy
from graphc.utilities import datetime_utils

# --------------------------------------------
# Deaths
# --------------------------------------------


class CasesByDateAndState(object):
    def __init__(self, source=r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\CasesByDateAndState'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        self.source = source
        self.date_code_field = 'DateCode'
        self.state_field = 'State'
        self.cases_field = 'Cases'

        self.jhu_source = JHU_SourceData.JhuCasesData()
        self.nsw_source = NSW_SourceData.NswNotificationData()
        self.state_feature_source = StateCapitals()

        self._loaded = None

    def load(self):
        """
        Forces a load from source into a list of dictionaries and returns a copy of the list.
        Use the data method if you don't need to force a new load from source.
        :return: [{'date_code': str, 'state': str, 'notifications': int, 'shape': geometry}, ...]
        :rtype: list
        """
        logging.info('Loading: ' + self.source)
        result = []
        fields = [self.date_code_field, self.state_field, self.cases_field, 'SHAPE@']
        with arcpy.da.SearchCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                date_value = datetime_utils.to_date(row[0], date_format='%Y%m%d')
                result.append({'date_code': row[0], 'state': row[1], 'notifications': row[2], 'shape': row[3], 'date':date_value})

        self._loaded = copy.deepcopy(result)
        return result

    def data(self):
        """
        Obtains a copy of the loaded data items.  If the data has not been loaded, then load is called first.  Use this method instead
        of load if you don't need to force a full reload from source.
        :return: [{'date_code': str, 'state': str, 'notifications': int, 'shape': geometry}, ...]
        :rtype: list
        """
        if not self._loaded:
            self.load()
        return copy.deepcopy(self._loaded)

    def update_from_source(self):
        logging.info('Updating: ' + self.source)
        result = {'updates': 0, 'adds': 0, 'deletes': 0}

        jhu_source = self.jhu_source.counts_by_date_and_state(use_abbreviation=True)  # {key: count}
        nsw_source = self.nsw_source.counts_by_date()

        # perform updates and deletes
        fields = [self.date_code_field, self.state_field, self.cases_field]
        with arcpy.da.UpdateCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                date_code = row[0]
                state = row[1]
                if state.upper() == 'NSW':
                    nsw_notifications = nsw_source.pop(date_code, None)
                    if nsw_notifications is None:
                        cursor.deleteRow()
                        result['deletes'] += 1
                    elif nsw_notifications != row[2]:
                        row[2] = nsw_notifications
                        cursor.updateRow(row)
                        result['updates'] += 1
                else:
                    key = '{}_{}'.format(date_code, state)
                    notifications = jhu_source.pop(key, None)
                    if notifications is None:
                        cursor.deleteRow()
                        result['deletes'] += 1
                    elif notifications != row[2]:
                        row[2] = notifications
                        cursor.updateRow(row)
                        result['updates'] += 1

        # any remaining source items need to be inserted
        geometry_source = None
        if nsw_source or jhu_source:
            # only load geometry source if adds will occur.
            geometry_source = da_arcpy.load_indexed_values(source=self.state_feature_source.source,
                                                           id_field=self.state_feature_source.ste_abbv_field,
                                                           value_field="SHAPE@")
            fields = [self.date_code_field, self.state_field, self.cases_field, 'SHAPE@']

        if nsw_source:
            state = 'NSW'
            with arcpy.da.InsertCursor(in_table=self.source, field_names=fields) as cursor:
                for date_code, count in nsw_source.items():
                    geometry = geometry_source.get(state, None)
                    row = [date_code, state, count, geometry]
                    cursor.insertRow(row)
                    result['adds'] += 1

        if jhu_source:
            with arcpy.da.InsertCursor(in_table=self.source, field_names=fields) as cursor:
                for key, count in jhu_source.items():
                    date_code, state = key.split('_')
                    if state.upper() != 'NSW':
                        geometry = geometry_source.get(state, None)
                        row = [date_code, state, count, geometry]
                        cursor.insertRow(row)
                        result['adds'] += 1

        # force previously loaded data to none as it would reflect the data prior to update.
        # The next call that needs the source data will reload the updated data.
        self._loaded = None

        return result

    def cumulative_notifications_by_date_and_state(self, all_days=False):
        """
        Returns the cumulative notification totals for each state, indexed by a datecode_state key.
        A new cumulative total is calculated for each report date.  Only states with notifications are included, and each
        state stats will commence on the date of the first notification for that state.
        :param all_days: If true, a record will be generated for every day after the first notification in a state is found.  If False, items
        will only be generated for days where new notifications occur.  Default = False
        :type all_days: bool
        :return: {key: {'date_code': str, 'state': str, 'notifications': int, 'new_notifications': int, 'shape': geometry}}
        :rtype: dict
        """
        # get the source data sorted by Postcode then DateCode
        source_data = sorted(self.data(), key=lambda x: (x['state'], x['date_code']))

        # create initial result by registering only days for each postcode where new cases are registered
        result = {}
        state_start_dates = {}
        current_state = 'xxxx'
        total = 0
        for item in source_data:
            state = item['state']
            date_code = item['date_code']
            if state == current_state:  # still working with same state
                new_notifications = item['notifications']
                total += new_notifications  # add the current notifications to the current cumulative total
                item['new_notifications'] = new_notifications
                item['notifications'] = total  # update the item to show the cumulative total
            else:  # setup for new state.  For first state record cumulative total and notifications are equal.
                current_state = state
                total = item['notifications']
                item['new_notifications'] = item['notifications']
                state_start_dates[state] = date_code
            key = '{}_{}'.format(date_code, state)
            result[key] = item

        if all_days:
            # if all_days, fill in date gaps from loaded data.
            finish_date = datetime.datetime.now()
            notifications = None
            geometry = None
            for state, start_date in state_start_dates.items():
                date_value = datetime.datetime.strptime(start_date, '%Y%m%d')
                while date_value < finish_date:
                    date_code = date_value.strftime('%Y%m%d')
                    key = '{}_{}'.format(date_code, state)
                    item = result.get(key, None)
                    if item:
                        notifications = item['notifications']
                        geometry = item['shape']
                    else:
                        result[key] = {'date_code': date_code, 'state': state,
                                       'notifications': notifications, 'new_notifications': 0, 'shape': geometry}
                    date_value += datetime.timedelta(days=1)

        return result


class DeathsByDateAndState(object):
    def __init__(self, source=r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\DeathsByDateAndState'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        self.source = source
        self.date_code_field = 'DateCode'
        self.state_field = 'State'
        self.deaths_field = 'Deaths'

        self.jhu_source = JHU_SourceData.JhuDeathsData()
        self.state_feature_source = StateCapitals()

        self._loaded = None

    def load(self):
        """
        Forces a load from source into a list of dictionaries and returns a copy of the list.
        Use the data method if you don't need to force a new load from source.
        :return: [{'date_code': str, 'state': str, 'deaths': int, 'shape': geometry}, ...]
        :rtype: list
        """
        logging.info('Loading: ' + self.source)
        result = []
        fields = [self.date_code_field, self.state_field, self.deaths_field, 'SHAPE@']
        with arcpy.da.SearchCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                result.append({'date_code': row[0], 'state': row[1], 'deaths': row[2], 'shape': row[3]})

        self._loaded = copy.deepcopy(result)
        return result

    def data(self):
        """
        Obtains a copy of the loaded data items.  If the data has not been loaded, then load is called first.  Use this method instead
        of load if you don't need to force a full reload from source.
        :return: [{'date_code': str, 'state': str, 'deaths': int, 'shape': geometry}, ...]
        :rtype: list
        """
        if not self._loaded:
            self.load()
        return copy.deepcopy(self._loaded)

    def data_by_date_and_state(self):
        """
        Obtains a copy of the data items indexed by a key in the form datecode_postcode.
        :return: {key: {'date_code': str, 'state': str, 'deaths': int, 'shape': geometry}}
        :rtype: dict
        """
        result = {}
        source = self.data()
        for item in source:
            key = '{}_{}'.format(item['date_code'], item['state'])
            result[key] = item

        return result

    def update_from_source(self):
        logging.info('Updating: ' + self.source)
        result = {'updates': 0, 'adds': 0, 'deletes': 0}

        jhu_source = self.jhu_source.counts_by_date_and_state(use_abbreviation=True)  # {key: count}

        # perform updates and deletes
        fields = [self.date_code_field, self.state_field, self.deaths_field]
        with arcpy.da.UpdateCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                date_code = row[0]
                state = row[1]

                key = '{}_{}'.format(date_code, state)
                deaths = jhu_source.pop(key, None)
                if deaths is None:
                    cursor.deleteRow()
                    result['deletes'] += 1
                elif deaths != row[2]:
                    row[2] = deaths
                    cursor.updateRow(row)
                    result['updates'] += 1

        # any remaining source items need to be inserted
        geometry_source = None
        if jhu_source:
            # only load geometry source if adds will occur.
            geometry_source = da_arcpy.load_indexed_values(source=self.state_feature_source.source,
                                                           id_field=self.state_feature_source.ste_abbv_field,
                                                           value_field="SHAPE@")
            fields = [self.date_code_field, self.state_field, self.deaths_field, 'SHAPE@']

        if jhu_source:
            with arcpy.da.InsertCursor(in_table=self.source, field_names=fields) as cursor:
                for key, count in jhu_source.items():
                    date_code, state = key.split('_')
                    if state.upper() != 'NSW':
                        geometry = geometry_source.get(state, None)
                        row = [date_code, state, count, geometry]
                        cursor.insertRow(row)
                        result['adds'] += 1

        return result

    def deaths_by_date_and_state(self):
        return self.data_by_date_and_state()

    def total_deaths_by_state(self):
        """
        Calculates the total deaths and most recent death datecode for each state in the source data.
        - state: the state for which the values apply
        - deaths: the total deaths for the state
        - most_recent: the date code for the most recent reported deaths
        - most_recent_new: the number of deaths reported on the most recent day that deaths were reported for the state.
        :return: {state: {'deaths': int, 'most_recent': date_code, 'most_recent_new': int, 'shape': geometry}}
        :rtype: dict
        """

        result = {}
        source = self.data()
        for source_item in source:
            state = source_item['state']
            result_item = result.get(state, None)
            if result_item:
                result_item['deaths'] += source_item['deaths']
                if result_item['most_recent'] < source_item['date_code']:
                    result_item['most_recent'] = source_item['date_code']
                    result_item['most_recent_new'] = source_item['deaths']
            else:
                result[state] = {'deaths': source_item['deaths'], 'most_recent': source_item['date_code'],
                                 'most_recent_new': source_item['deaths'], 'shape': source_item['shape']}

        return result

    def cumulative_deaths_by_date_and_state(self, all_days=False):
        """
        Returns the cumulative deaths totals for each state, indexed by a datecode_state key.
        A new cumulative total is calculated for each report date.  Only states with deaths are included, and each
        state stats will commence on the date of the first death for that state.
        :param all_days: If true, a record will be generated for every day after the first death in a state is found.  If False, items
        will only be generated for days where new deaths occur.  Default = False
        :type all_days: bool
        :return: {key: {'date_code': str, 'state': str, 'deaths': int, 'new_deaths': int, 'shape': geometry}}
        :rtype: dict
        """
        # get the source data sorted by state then DateCode
        source_data = sorted(self.data(), key=lambda x: (x['state'], x['date_code']))

        # create initial result by registering only days for each postcode where new cases are registered
        result = {}
        state_start_dates = {}
        current_state = 'xxxx'
        total = 0
        for item in source_data:
            state = item['state']
            date_code = item['date_code']
            if state == current_state:  # still working with same state
                new_notifications = item['deaths']
                total += new_notifications  # add the current deaths to the current cumulative total
                item['new_deaths'] = new_notifications
                item['deaths'] = total  # update the item to show the cumulative total
            else:  # setup for new state.  For first state record cumulative total and deaths are equal.
                current_state = state
                total = item['deaths']
                item['new_deaths'] = item['deaths']
                state_start_dates[state] = date_code
            key = '{}_{}'.format(date_code, state)
            result[key] = item

        if all_days:
            # if all_days, fill in date gaps from loaded data.
            finish_date = datetime.datetime.now()
            deaths = None
            geometry = None
            for state, start_date in state_start_dates.items():
                date_value = datetime.datetime.strptime(start_date, '%Y%m%d')
                while date_value < finish_date:
                    date_code = date_value.strftime('%Y%m%d')
                    key = '{}_{}'.format(date_code, state)
                    item = result.get(key, None)
                    if item:
                        deaths = item['deaths']
                        geometry = item['shape']
                    else:
                        result[key] = {'date_code': date_code, 'state': state,
                                       'deaths': deaths, 'new_deaths': 0, 'shape': geometry}
                    date_value += datetime.timedelta(days=1)

        return result


class TestsByDateAndState(object):
    def __init__(self, source=r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\TestsByDateAndState'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        self.source = source
        self.date_code_field = 'DateCode'
        self.state_field = 'State'
        self.tests_field = 'Tests'

        self.nsw_source = NSW_SourceData.NswTestData()
        self.state_feature_source = StateCapitals()

        self._loaded = None

    def load(self):
        """
        Forces a load from source into a list of dictionaries and returns a copy of the list.
        Use the data method if you don't need to force a new load from source.
        :return: [{'date_code': str, 'state': str, 'tests': int, 'shape': geometry}, ...]
        :rtype: list
        """
        logging.info('Loading: ' + self.source)
        result = []
        fields = [self.date_code_field, self.state_field, self.tests_field, 'SHAPE@']
        with arcpy.da.SearchCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                result.append({'date_code': row[0], 'state': row[1], 'tests': row[2], 'shape': row[3]})

        self._loaded = copy.deepcopy(result)
        return result

    def data(self):
        """
        Obtains a copy of the loaded data items.  If the data has not been loaded, then load is called first.  Use this method instead
        of load if you don't need to force a full reload from source.
        :return: [{'date_code': str, 'state': str, 'tests': int, 'shape': geometry}, ...]
        :rtype: list
        """
        if not self._loaded:
            self.load()
        return copy.deepcopy(self._loaded)

    def data_by_date_and_state(self):
        """
        Obtains a copy of the data items indexed by a key in the form datecode_state.
        :return: {key: {'date_code': str, 'state': str, 'tests': int, 'shape': geometry}}
        :rtype: dict
        """
        result = {}
        source = self.data()
        for item in source:
            key = '{}_{}'.format(item['date_code'], item['state'])
            result[key] = item

        return result

    def update_from_source(self):
        logging.info('Updating: ' + self.source)
        result = {'updates': 0, 'adds': 0, 'deletes': 0}

        nsw_source = self.nsw_source.counts_by_date()

        # perform updates and deletes
        fields = [self.date_code_field, self.state_field, self.tests_field]
        with arcpy.da.UpdateCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                date_code = row[0]
                state = row[1]
                tests = None
                if state.upper() == 'NSW':
                    tests = nsw_source.pop(date_code, None)
                # only nsw test data available at the moment.  Add other states here as source becomes available.

                if not tests:
                    cursor.deleteRow()
                    result['deletes'] += 1
                elif tests != row[2]:
                    row[2] = tests
                    cursor.updateRow(row)
                    result['updates'] += 1

        # any remaining source items need to be inserted
        geometry_source = None
        if nsw_source:
            # only load geometry source if adds will occur.
            geometry_source = da_arcpy.load_indexed_values(source=self.state_feature_source.source,
                                                           id_field=self.state_feature_source.ste_abbv_field,
                                                           value_field="SHAPE@")
            fields = [self.date_code_field, self.state_field, self.tests_field, 'SHAPE@']

        if nsw_source:
            state = 'NSW'
            with arcpy.da.InsertCursor(in_table=self.source, field_names=fields) as cursor:
                for date_code, tests in nsw_source.items():
                    geometry = geometry_source.get(state, None)
                    row = [date_code, state, tests, geometry]
                    cursor.insertRow(row)
                    result['adds'] += 1

        # force previously loaded data to none as it would reflect the data prior to update.
        # The next call that needs the source data will reload the updated data.
        self._loaded = None

        return result

    def tests_by_date_and_state(self):
        return self.data_by_date_and_state()

    def total_tests_by_state(self):
        """
        Calculates the total tests and most recent tests datecode for each state in the source data.
        - state: the state for which the values apply
        - tests: the total tests for the postcode
        - most_recent: the date code for the most recent reported tests
        - most_recent_new: the number of tests reported on the most recent day that tests were reported for the postcode.
        :return: {state: {'tests': int, 'most_recent': date_code, 'most_recent_new': int, 'shape': geometry}}
        :rtype: dict
        """

        result = {}
        source = self.data()
        for source_item in source:
            state = source_item['state']
            result_item = result.get(state, None)
            if result_item:
                result_item['tests'] += source_item['tests']
                if result_item['most_recent'] < source_item['date_code']:
                    result_item['most_recent'] = source_item['date_code']
                    result_item['most_recent_new'] = source_item['tests']
            else:
                result[state] = {'tests': source_item['tests'], 'most_recent': source_item['date_code'],
                                 'most_recent_new': source_item['tests'], 'shape': source_item['shape']}

        return result

    def cumulative_tests_by_date_and_state(self, all_days=False):
        """
        Returns the cumulative tests totals for each state, indexed by a datecode_state key.
        A new cumulative total is calculated for each report date.  Only states with tests are included, and each
        state stats will commence on the date of the first tests for that state.
        :param all_days: If true, a record will be generated for every day after the first test in a state is found.  If False, items
        will only be generated for days where new tests occur.  Default = False
        :type all_days: bool
        :return: {key: {'date_code': str, 'state': str, 'tests': int, 'new_tests': int, 'shape': geometry}}
        :rtype: dict
        """
        # get the source data sorted by Postcode then DateCode
        source_data = sorted(self.data(), key=lambda x: (x['state'], x['date_code']))

        # create initial result by registering only days for each state where new cases are registered
        result = {}
        state_start_dates = {}
        current_state = 'xxxx'
        total = 0
        for item in source_data:
            state = item['state']
            date_code = item['date_code']
            if state == current_state:  # still working with same state
                new_notifications = item['tests']
                total += new_notifications  # add the current tests to the current cumulative total
                item['new_tests'] = new_notifications
                item['tests'] = total  # update the item to show the cumulative total
            else:  # setup for new state.  For first state record cumulative total and tests are equal.
                current_state = state
                total = item['tests']
                item['new_tests'] = item['tests']
                state_start_dates[state] = date_code
            key = '{}_{}'.format(date_code, state)
            result[key] = item

        if all_days:
            # if all_days, fill in date gaps from loaded data.
            finish_date = datetime.datetime.now()
            notifications = None
            geometry = None
            for state, start_date in state_start_dates.items():
                date_value = datetime.datetime.strptime(start_date, '%Y%m%d')
                while date_value < finish_date:
                    date_code = date_value.strftime('%Y%m%d')
                    key = '{}_{}'.format(date_code, state)
                    item = result.get(key, None)
                    if item:
                        notifications = item['tests']
                        geometry = item['shape']
                    else:
                        result[key] = {'date_code': date_code, 'state': state,
                                       'tests': notifications, 'new_tests': 0, 'shape': geometry}
                    date_value += datetime.timedelta(days=1)

        return result


# --------------------------------------------
# Notifications
# --------------------------------------------


class NotificationsByDateAndPostcode(object):
    def __init__(self, source=r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\NotificationsByDateAndPostcode'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        self.source = source
        self.date_code_field = 'DateCode'
        self.postcode_field = 'Postcode'
        self.notifications_field = 'Notifications'

        self.nsw_source = NSW_SourceData.NswNotificationData()
        self.postcode_feature_source = POA2016.centroids()

        self._loaded = None

    def load(self):
        """
        Forces a load from source into a list of dictionaries and returns a copy of the list.
        Use the data method if you don't need to force a new load from source.
        :return: [{'date_code': str, 'postcode': str, 'notifications': int, 'shape': geometry}, ...]
        :rtype: list
        """
        logging.info('Loading: ' + self.source)
        result = []
        fields = [self.date_code_field, self.postcode_field, self.notifications_field, 'SHAPE@']
        with arcpy.da.SearchCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                result.append({'date_code': row[0], 'postcode': row[1], 'notifications': row[2], 'shape': row[3]})

        self._loaded = copy.deepcopy(result)
        return result

    def data(self):
        """
        Obtains a copy of the loaded data items.  If the data has not been loaded, then load is called first.  Use this method instead
        of load if you don't need to force a full reload from source.
        :return: [{'date_code': str, 'postcode': str, 'notifications': int, 'shape': geometry}, ...]
        :rtype: list
        """
        if not self._loaded:
            self.load()
        return copy.deepcopy(self._loaded)

    def data_by_date_and_postcode(self):
        """
        Obtains a copy of the data items indexed by a key in the form datecode_postcode.
        :return: {key: {'date_code': str, 'postcode': str, 'notifications': int, 'shape': geometry}}
        :rtype: dict
        """
        result = {}
        source = self.data()
        for item in source:
            key = '{}_{}'.format(item['date_code'], item['postcode'])
            result[key] = item

        return result

    def update_from_source(self):
        logging.info('Updating: ' + self.source)
        result = {'updates': 0, 'adds': 0, 'deletes': 0}

        source = self.nsw_source.counts_by_date_and_postcode()  # {key: count}

        # perform updates and deletes
        fields = [self.date_code_field, self.postcode_field, self.notifications_field]
        with arcpy.da.UpdateCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                key = '{}_{}'.format(row[0], row[1])
                notifications = source.pop(key, None)
                if notifications is None:
                    cursor.deleteRow()
                    result['deletes'] += 1
                elif notifications != row[2]:
                    row[2] = notifications
                    cursor.updateRow(row)
                    result['updates'] += 1

        # any remaining source items need to be inserted
        if source:
            geometry_source = da_arcpy.load_indexed_values(source=self.postcode_feature_source.source,
                                                           id_field=self.postcode_feature_source.poa_code_field,
                                                           value_field="SHAPE@")
            fields = [self.date_code_field, self.postcode_field, self.notifications_field, 'SHAPE@']
            with arcpy.da.InsertCursor(in_table=self.source, field_names=fields) as cursor:
                for key, count in source.items():
                    date_code, postcode = key.split('_')
                    geometry = geometry_source.get(postcode, None)
                    row = [date_code, postcode, count, geometry]
                    cursor.insertRow(row)
                    result['adds'] += 1

        # force previously loaded data to none as it would reflect the data prior to update.
        # The next call that needs the source data will reload the updated data.
        self._loaded = None

        return result

    def notifications_by_date_and_postcode(self):
        return self.data_by_date_and_postcode()

    def total_notifications_by_postcode(self):
        """
        Calculates the total notifications and most recent notification datecode for each postcode in the source data.
        - postcode: the postcode for which the values apply
        - notifications: the total notifications for the postcode
        - most_recent: the date code for the most recent reported notifications
        - most_recent_new: the number of notifications reported on the most recent day that notifications were reported for the postcode.
        :return: {postcocde: {'notifications': int, 'most_recent': date_code, 'most_recent_new': int, 'shape': geometry}}
        :rtype: dict
        """

        result = {}
        source = self.data()
        for source_item in source:
            postcode = source_item['postcode']
            result_item = result.get(postcode, None)
            if result_item:
                result_item['notifications'] += source_item['notifications']
                if result_item['most_recent'] < source_item['date_code']:
                    result_item['most_recent'] = source_item['date_code']
                    result_item['most_recent_new'] = source_item['notifications']
            else:
                result[postcode] = {'notifications': source_item['notifications'], 'most_recent': source_item['date_code'],
                                    'most_recent_new': source_item['notifications'], 'shape': source_item['shape']}

        return result

    def cumulative_notifications_by_date_and_postcode(self, all_days=False):
        """
        Returns the cumulative notification totals for each postcode, indexed by a datecode_postcode key.
        A new cumulative total is calculated for each report date.  Only postcodes with notifications are included, and each
        postcodes stats will commence on the date of the first notification for that postcode.
        :param all_days: If true, a record will be generated for every day after the first notification in a postcode is found.  If False, items
        will only be generated for days where new notifications occur.  Default = False
        :type all_days: bool
        :return: {key: {'date_code': str, 'postcode': str, 'notifications': int, 'new_notifications': int, 'shape': geometry}}
        :rtype: dict
        """
        # get the source data sorted by Postcode then DateCode
        source_data = sorted(self.data(), key=lambda x: (x['postcode'], x['date_code']))

        # create initial result by registering only days for each postcode where new cases are registered
        result = {}
        postcode_start_dates = {}
        current_postcode = 'xxxx'
        total = 0
        for item in source_data:
            postcode = item['postcode']
            date_code = item['date_code']
            if postcode == current_postcode:  # still working with same postcode
                new_notifications = item['notifications']
                total += new_notifications  # add the current notifications to the current cumulative total
                item['new_notifications'] = new_notifications
                item['notifications'] = total  # update the item to show the cumulative total
            else:  # setup for new postcode.  For first postcode record cumulative total and notifications are equal.
                current_postcode = postcode
                total = item['notifications']
                item['new_notifications'] = item['notifications']
                postcode_start_dates[postcode] = date_code
            key = '{}_{}'.format(date_code, postcode)
            result[key] = item

        if all_days:
            # if all_days, fill in date gaps from loaded data.
            finish_date = datetime.datetime.now()
            notifications = None
            geometry = None
            for postcode, start_date in postcode_start_dates.items():
                date_value = datetime.datetime.strptime(start_date, '%Y%m%d')
                while date_value < finish_date:
                    date_code = date_value.strftime('%Y%m%d')
                    key = '{}_{}'.format(date_code, postcode)
                    item = result.get(key, None)
                    if item:
                        notifications = item['notifications']
                        geometry = item['shape']
                    else:
                        result[key] = {'date_code': date_code, 'postcode': postcode,
                                       'notifications': notifications, 'new_notifications': 0, 'shape': geometry}
                    date_value += datetime.timedelta(days=1)

        return result


class TotalNotificationsByPostcode(object):
    def __init__(self, source=r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\TotalNotificationsByPostcode'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        self.source = source
        self.postcode_field = 'Postcode'
        self.notifications_field = 'Notifications'
        self.most_recent_code_field = 'MostRecentCode'
        self.most_recent_date_field = 'MostRecentDate'

        self._loaded = None

    def load(self):
        """
        Forces a load from source into a list of dictionaries and returns a copy of the list.
        Use the data method if you don't need to force a new load from source.
        :return: [{'date_code': str, 'postcode': str, 'notifications': int, 'shape': geometry}, ...]
        :rtype: list
        """
        logging.info('Loading: ' + self.source)
        result = []
        fields = [self.most_recent_code_field, self.postcode_field, self.notifications_field, 'SHAPE@']
        with arcpy.da.SearchCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                result.append({'date_code': row[0], 'postcode': row[1], 'notifications': row[2], 'shape': row[3]})

        self._loaded = copy.deepcopy(result)
        return result

    def data(self):
        """
        Obtains a copy of the loaded data items.  If the data has not been loaded, then load is called first.  Use this method instead
        of load if you don't need to force a full reload from source.
        :return: [{'date_code': str, 'postcode': str, 'notifications': int, 'shape': geometry}, ...]
        :rtype: list
        """
        if not self._loaded:
            self.load()
        return copy.deepcopy(self._loaded)

    def data_by_postcode(self):
        """
        Obtains a copy of the data items indexed by  postcode.
        :return: {postcode: {'postcode': str, 'date_code': str, 'notifications': int, 'shape': geometry}}}
        :rtype: dict
        """
        result = {}
        source = self.data()
        for item in source:
            result[item['postcode']] = item

        return result

    def update_from_source(self, source: NotificationsByDateAndPostcode):

        source_data = source.total_notifications_by_postcode()

        logging.info('Updating: ' + self.source)
        result = {'updates': 0, 'adds': 0, 'deletes': 0}

        # perform updates and deletes
        fields = [self.postcode_field, self.most_recent_code_field, self.notifications_field, self.most_recent_date_field]
        with arcpy.da.UpdateCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                new_date_code = None
                new_notifications = None
                source_item = source_data.pop(row[0], None)
                if source_item:
                    new_date_code = source_item['most_recent']
                    new_notifications = source_item['notifications']

                update_required = False
                if row[1] != new_date_code:
                    row[1] = new_date_code
                    row[3] = datetime.datetime.strptime(new_date_code, '%Y%m%d')
                    update_required = True
                if row[2] != new_notifications:
                    row[2] = new_notifications
                    update_required = True

                if update_required:
                    cursor.updateRow(row)
                    result['updates'] += 1

        # any remaining source items need to be inserted
        if source_data:
            fields = [self.postcode_field, self.most_recent_code_field, self.notifications_field, self.most_recent_date_field, 'SHAPE@']
            with arcpy.da.InsertCursor(in_table=self.source, field_names=fields) as cursor:
                for postcode, item in source_data.items():
                    date_code = item['most_recent']
                    if date_code:
                        date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
                    else:
                        date_value = None
                    row = [postcode, date_code, item['notifications'], date_value, item['shape']]
                    cursor.insertRow(row)
                    result['adds'] += 1

        # force previously loaded data to none as it would reflect the data prior to update.
        # The next call that needs the source data will reload the updated data.
        self._loaded = None

        return result

    def total_notifications_by_postcode(self):
        """
        Obtains a copy of the data items indexed by  postcode.
        :return: {postcode: {'postcode': str, 'date_code': str, 'notifications': int, 'shape': geometry}}}
        :rtype: dict
        """
        return self.data_by_postcode()


class StatisticsByDateAndState(object):
    def __init__(self, source=r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\StatisticsByDateAndState'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        self.source = source
        self.date_code_field = 'DateCode'
        self.state_field = 'State'
        self.statistic_field = 'Statistic'
        self.value_field = 'Value'

        self.cases_source = JHU_SourceData.JhuCasesData()
        self.state_feature_source = StateCapitals()

        self._loaded = None

    def load(self):
        """
        Forces a load from source into a list of dictionaries and returns a copy of the list.
        Use the data method if you don't need to force a new load from source.
        :return: [{'date_code': str, 'state': str, 'notifications': int, 'shape': geometry}, ...]
        :rtype: list
        """
        logging.info('Loading: ' + self.source)
        result = []
        fields = [self.date_code_field, self.state_field, self.statistic_field, self.value_field, 'SHAPE@']
        with arcpy.da.SearchCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                result.append({'date_code': row[0], 'state': row[1], 'statistic': row[2], 'value': row[3], 'shape': row[3]})

        self._loaded = copy.deepcopy(result)
        return result

    def data(self):
        """
        Obtains a copy of the loaded data items.  If the data has not been loaded, then load is called first.  Use this method instead
        of load if you don't need to force a full reload from source.
        :return: [{'date_code': str, 'state': str, 'notifications': int, 'shape': geometry}, ...]
        :rtype: list
        """
        if not self._loaded:
            self.load()
        return copy.deepcopy(self._loaded)

    def data_by_date_and_state(self):
        """
        Obtains a copy of the data items indexed by a key in the form datecode_postcode.
        :return: {key: {'date_code': str, 'state': str, 'notifications': int, 'shape': geometry}}
        :rtype: dict
        """
        result = {}
        source = self.data()
        for item in source:
            key = '{}_{}'.format(item['date_code'], item['state'])
            result[key] = item

        return result

    def update_from_source(self):
        logging.info('Updating: ' + self.source)
        result = {'updates': 0, 'adds': 0, 'deletes': 0}

        source = self.cases_source.counts_by_date_and_state(use_abbreviation=True)  # {key: count}

        # perform updates and deletes
        fields = [self.date_code_field, self.state_field, self.notifications_field]
        with arcpy.da.UpdateCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                key = '{}_{}'.format(row[0], row[1])
                notifications = source.pop(key, None)
                if notifications is None:
                    cursor.deleteRow()
                    result['deletes'] += 1
                elif notifications != row[2]:
                    row[2] = notifications
                    cursor.updateRow(row)
                    result['updates'] += 1

        # any remaining source items need to be inserted
        if source:
            geometry_source = da_arcpy.load_indexed_values(source=self.state_feature_source.source,
                                                           id_field=self.state_feature_source.ste_abbv_field,
                                                           value_field="SHAPE@")
            fields = [self.date_code_field, self.state_field, self.notifications_field, 'SHAPE@']
            with arcpy.da.InsertCursor(in_table=self.source, field_names=fields) as cursor:
                for key, count in source.items():
                    date_code, postcode = key.split('_')
                    geometry = geometry_source.get(postcode, None)
                    row = [date_code, postcode, count, geometry]
                    cursor.insertRow(row)
                    result['adds'] += 1

        # force previously loaded data to none as it would reflect the data prior to update.
        # The next call that needs the source data will reload the updated data.
        self._loaded = None

        return result

    def notifications_by_date_and_state(self):
        return self.data_by_date_and_state()

    def total_notifications_by_state(self):
        """
        Calculates the total notifications and most recent notification datecode for each state in the source data.
        :return: {state: {'notifications': int, 'most_recent': date_code, 'shape': geometry}}
        :rtype: dict
        """

        result = {}
        source = self.data()
        for source_item in source:
            state = source_item['state']
            result_item = result.get(state, None)
            if result_item:
                result_item['notifications'] += source_item['notifications']
                if result_item['most_recent'] < source_item['date_code']:
                    result_item['most_recent'] = source_item['date_code']
            else:
                result[state] = {'notifications': source_item['notifications'], 'most_recent': source_item['date_code'],
                                 'shape': source_item['shape']}

        return result

    def cumulative_notifications_by_date_and_state(self):
        """
        Returns the cumulative notification totals for each state, indexed by a datecode_state key.
        A new cumulative total is calculated for each report date.  Only states with notifications are included, and each
        state stats will commence on the date of the first notification for that state.
        :return: {key: {'date_code': str, 'state': str, 'notifications': int, 'shape': geometry}}
        :rtype: dict
        """
        # get the source data sorted by Postcode then DateCode
        source_data = sorted(self.data(), key=lambda x: (x['postcode'], x['date_code']))

        result = {}
        current_state = 'xxxx'
        total = 0
        for item in source_data:
            state = item['state']
            date_code = item['date_code']
            if state == current_state:  # still working with same state
                total += item['notifications']  # add the current notifications to the current cumulative total
                item['notifications'] = total  # update the item to show the cumulative total
            else:  # setup for new postcode.  For first state record cumulative total and notifications are equal.
                current_state = state
                total = item['notifications']
            key = '{}_{}'.format(date_code, state)
            result[key] = item

        return result



class StateSummary(object):
    def __init__(self, source=r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\TestsByDateAndPostcode'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        self.source = source
        self.state_field = 'State'
        self.cases_field = 'Cases'
        self.deaths_field = 'Deaths'
        self.date_of_last_case_field = 'DateOfLastCase'

        self.cases_source = JHU_SourceData.JhuCasesData()
        self.deaths_source = JHU_SourceData.JhuDeathsData()
        self.state_feature_source = StateCapitals()

        self._loaded = None

    def load(self):
        """
        Forces a load from source into a list of dictionaries and returns a copy of the list.
        Use the data method if you don't need to force a new load from source.
        :return: [{'state': str, 'cases': int, 'deaths': int, 'date_of_last_case': date , 'shape': geometry}, ...]
        :rtype: list
        """
        logging.info('Loading: ' + self.source)
        result = []
        fields = [self.state_field, self.cases_field, self.deaths_field, self.date_of_last_case_field, 'SHAPE@']
        with arcpy.da.SearchCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                result.append({'state': row[0], 'cases': row[1], 'deaths': row[2], 'date_of_last_case': row[3], 'shape': row[4]})

        self._loaded = copy.deepcopy(result)
        return result

    def data(self):
        """
        Obtains a copy of the loaded data items.  If the data has not been loaded, then load is called first.  Use this method instead
        of load if you don't need to force a full reload from source.
        :return: [{'state': str, 'cases': int, 'deaths': int, 'date_of_last_case': date , 'shape': geometry}, ...]
        :rtype: list
        """
        if not self._loaded:
            self.load()
        return copy.deepcopy(self._loaded)

    def data_by_state(self):
        """
        Obtains a copy of the data items indexed by state.
        :return: {state: {'state': str, 'cases': int, 'deaths': int, 'date_of_last_case': date , 'shape': geometry}}
        :rtype: dict
        """
        source = self.data()
        result = {}
        for item in source:
            result[item['state']] = item

        return result

    def _extract_most_recent(self, data):
        result = {}
        keys = sorted(data.keys())
        for key in keys:
            date_code, state = key.split('_')



    def update_from_source(self):
        logging.info('Updating: ' + self.source)
        result = {'updates': 0, 'adds': 0, 'deletes': 0}

        cases_source = self.cases_source.counts_by_date_and_state(use_abbreviation=True)  # {date_state: new_cases}
        deaths_source = self.deaths_source.counts_by_date_and_state(use_abbreviation=True)  # {date_state: new_deaths}


        # perform updates and deletes
        fields = [self.date_code_field, self.postcode_field, self.tests_field]
        with arcpy.da.UpdateCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                key = '{}_{}'.format(row[0], row[1])
                notifications = source.pop(key, None)
                if notifications is None:
                    cursor.deleteRow()
                    result['deletes'] += 1
                elif notifications != row[2]:
                    row[2] = notifications
                    cursor.updateRow(row)
                    result['updates'] += 1

        # any remaining source items need to be inserted
        if source:
            geometry_source = da_arcpy.load_indexed_values(source=self.postcode_feature_source.source,
                                                           id_field=self.postcode_feature_source.poa_code_field,
                                                           value_field="SHAPE@")
            fields = [self.date_code_field, self.postcode_field, self.tests_field, 'SHAPE@']
            with arcpy.da.InsertCursor(in_table=self.source, field_names=fields) as cursor:
                for key, count in source.items():
                    date_code, postcode = key.split('_')
                    geometry = geometry_source.get(postcode, None)
                    row = [date_code, postcode, count, geometry]
                    cursor.insertRow(row)
                    result['adds'] += 1

        return result

# --------------------------------------------
# Tests
# --------------------------------------------


class TestsByDateAndPostcode(object):
    def __init__(self, source=r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\TestsByDateAndPostcode'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        self.source = source
        self.date_code_field = 'DateCode'
        self.postcode_field = 'Postcode'
        self.tests_field = 'Tests'

        self.nsw_source = NSW_SourceData.NswTestData()
        self.postcode_feature_source = POA2016.centroids()

        self._loaded = None

    def load(self):
        """
        Forces a load from source into a list of dictionaries and returns a copy of the list.
        Use the data method if you don't need to force a new load from source.
        :return: [{'date_code': str, 'postcode': str, 'tests': str, 'shape': geometry}, ...]
        :rtype: list
        """
        logging.info('Loading: ' + self.source)
        result = []
        fields = [self.date_code_field, self.postcode_field, self.tests_field, 'SHAPE@']
        with arcpy.da.SearchCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                result.append({'date_code': row[0], 'postcode': row[1], 'tests': row[2], 'shape': row[3]})

        self._loaded = copy.deepcopy(result)
        return result

    def data(self):
        """
        Obtains a copy of the loaded data items.  If the data has not been loaded, then load is called first.  Use this method instead
        of load if you don't need to force a full reload from source.
        :return: [{'date_code': str, 'postcode': str, 'tests': str, 'shape': geometry}, ...]
        :rtype: list
        """
        if not self._loaded:
            self.load()
        return copy.deepcopy(self._loaded)

    def data_by_date_and_postcode(self):
        """
        Obtains a copy of the data items indexed by a key in the form datecode_postcode.
        :return: {key: {'date_code': str, 'postcode': str, 'tests': str, 'shape': geometry}}
        :rtype: dict
        """
        result = {}
        source = self.data()
        for item in source:
            key = '{}_{}'.format(item['date_code'], item['postcode'])
            result[key] = item

        return result

    def update_from_source(self):
        logging.info('Updating: ' + self.source)
        result = {'updates': 0, 'adds': 0, 'deletes': 0}

        source = self.nsw_source.counts_by_date_and_postcode()  # {key: count}

        # perform updates and deletes
        fields = [self.date_code_field, self.postcode_field, self.tests_field]
        with arcpy.da.UpdateCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                key = '{}_{}'.format(row[0], row[1])
                notifications = source.pop(key, None)
                if notifications is None:
                    cursor.deleteRow()
                    result['deletes'] += 1
                elif notifications != row[2]:
                    row[2] = notifications
                    cursor.updateRow(row)
                    result['updates'] += 1

        # any remaining source items need to be inserted
        if source:
            geometry_source = da_arcpy.load_indexed_values(source=self.postcode_feature_source.source,
                                                           id_field=self.postcode_feature_source.poa_code_field,
                                                           value_field="SHAPE@")
            fields = [self.date_code_field, self.postcode_field, self.tests_field, 'SHAPE@']
            with arcpy.da.InsertCursor(in_table=self.source, field_names=fields) as cursor:
                for key, count in source.items():
                    date_code, postcode = key.split('_')
                    geometry = geometry_source.get(postcode, None)
                    row = [date_code, postcode, count, geometry]
                    cursor.insertRow(row)
                    result['adds'] += 1

        # force previously loaded data to none as it would reflect the data prior to update.
        # The next call that needs the source data will reload the updated data.
        self._loaded = None

        return result

    def tests_by_date_and_postcode(self):
        return self.data_by_date_and_postcode()

    def avg_tests_7_day_by_date_and_postcode(self):
        """
        Returns the 7 day average tests for each postcode, indexed by a datecode_postcode key.
        The 7 day average is the sum of the new tests for the 7 days up to the date (inclusive) divide by 7.
        A new 7 day average is calculated for each report date.  Only postcodes with notifications are included, and each
        postcodes stats will commence on the date of the first notification for that postcode.
        :return: {key: {'date_code': str, 'postcode': str, 'ave_tests': int, 'shape': geometry}}
        :rtype: dict
        """
        finish_date = datetime.datetime.now()

        wkg = {}
        for item in self.data():
            postcode = item['postcode']
            date = item['date_code']
            tests = item['tests']

            postcode_item = wkg.get(postcode, None)
            if not postcode_item:
                postcode_item = {'start_date': date, 'tests': {date: tests}, 'shape': item['shape']}
                wkg[postcode] = postcode_item
            else:
                postcode_item['tests'][date] = tests
                if postcode_item['start_date'] > date:
                    postcode_item['start_date'] = date

        result = {}
        for postcode, item in wkg.items():
            test_list = []
            start_date = datetime.datetime.strptime(item['start_date'], '%Y%m%d')
            test_items = item['tests']

            while start_date < finish_date:
                date_code = start_date.strftime('%Y%m%d')
                test_list.append(test_items.get(date_code, 0))
                if len(test_list) > 7:
                    test_list.pop(0)
                ave = sum(test_list)/7.0
                key = '{}_{}'.format(date_code, postcode)
                result[key] = {'date_code': date_code, 'postcode': postcode, 'ave_tests': ave, 'shape': item['shape']}
                start_date += datetime.timedelta(days=1)

        return result

    def total_tests_by_postcode(self):
        """
        Calculates the total tests and most recent test datecode for each postcode in the source data.
        - postcode: the postcode for which the values apply
        - tests: the total tests for the postcode
        - most_recent: the date code for the most recent reported tests
        - most_recent_new: the number of tests reported on the most recent day that tests were reported for the postcode.
        :return: {postcocde: {'tests': int, 'most_recent': date_code, 'most_recent_new': int, 'shape': geometry}}
        :rtype: dict
        """

        result = {}
        source = self.data()
        for source_item in source:
            postcode = source_item['postcode']
            result_item = result.get(postcode, None)
            if result_item:
                result_item['tests'] += source_item['tests']
                if result_item['most_recent'] < source_item['date_code']:
                    result_item['most_recent'] = source_item['date_code']
                    result_item['most_recent_new'] = source_item['tests']
            else:
                result[postcode] = {'tests': source_item['tests'], 'most_recent': source_item['date_code'],
                                    'most_recent_new': source_item['tests'], 'shape': source_item['shape']}

        return result

    def cumulative_tests_by_date_and_postcode(self, all_days=False):
        """
        Returns the cumulative test totals for each postcode, indexed by a datecode_postcode key.
        A new cumulative total is calculated for each report date.  Only postcodes with notifications are included, and each
        postcodes stats will commence on the date of the first notification for that postcode.
        :param all_days: If true, a record will be generated for every day after the first test in a postcode is found.  If False, items
        will only be generated for days where new tests occur.  Default = False
        :type all_days: bool
        :return: {key: {'date_code': str, 'postcode': str, 'tests': int, 'new_tests': int, 'shape': geometry}}
        :rtype: dict
        """
        # get the source data sorted by Postcode then DateCode
        source_data = sorted(self.data(), key=lambda x: (x['postcode'], x['date_code']))

        result = {}
        current_postcode = 'xxxx'
        postcode_start_dates = {}
        total = 0
        for item in source_data:
            postcode = item['postcode']
            date_code = item['date_code']
            if postcode == current_postcode:  # still working with same postcode
                new_tests = item['tests']
                total += new_tests  # add the current notifications to the current cumulative total
                item['new_tests'] = new_tests
                item['tests'] = total  # update the item to show the cumulative total
            else:  # setup for new postcode.  For first postcode record cumulative total and notifications are equal.
                current_postcode = postcode
                total = item['tests']
                item['new_tests'] = total
                postcode_start_dates[postcode] = date_code
            key = '{}_{}'.format(date_code, postcode)
            result[key] = item

        if all_days:
            # if all_days, fill in date gaps from loaded data.
            finish_date = datetime.datetime.now()
            tests = None
            geometry = None
            for postcode, start_date in postcode_start_dates.items():
                date_value = datetime.datetime.strptime(start_date, '%Y%m%d')
                while date_value < finish_date:
                    date_code = date_value.strftime('%Y%m%d')
                    key = '{}_{}'.format(date_code, postcode)
                    item = result.get(key, None)
                    if item:
                        tests = item['tests']
                        geometry = item['shape']
                    else:
                        result[key] = {'date_code': date_code, 'postcode': postcode,
                                       'tests': tests, 'new_tests': 0, 'shape': geometry}
                    date_value += datetime.timedelta(days=1)

        return result


class TotalTestsByPostcode(object):
    def __init__(self, source=r'E:\Documents2\ArcGIS\Projects\OnlineData\AuthorityData.gdb\TotalTestsByPostcode'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        self.source = source
        self.postcode_field = 'Postcode'
        self.tests_field = 'Tests'
        self.most_recent_code_field = 'MostRecentCode'
        self.most_recent_date_field = 'MostRecentDate'

        self._loaded = None

    def load(self):
        """
        Forces a load from source into a list of dictionaries and returns a copy of the list.
        Use the data method if you don't need to force a new load from source.
        :return: [{'date_code': str, 'postcode': str, 'tests': int, 'shape': geometry}, ...]
        :rtype: list
        """
        logging.info('Loading: ' + self.source)
        result = []
        fields = [self.most_recent_code_field, self.postcode_field, self.tests_field, 'SHAPE@']
        with arcpy.da.SearchCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                result.append({'date_code': row[0], 'postcode': row[1], 'tests': row[2], 'shape': row[3]})

        self._loaded = copy.deepcopy(result)
        return result

    def data(self):
        """
        Obtains a copy of the loaded data items.  If the data has not been loaded, then load is called first.  Use this method instead
        of load if you don't need to force a full reload from source.
        :return: [{'date_code': str, 'postcode': str, 'tests': int, 'shape': geometry}, ...]
        :rtype: list
        """
        if not self._loaded:
            self.load()
        return copy.deepcopy(self._loaded)

    def data_by_postcode(self):
        """
        Obtains a copy of the data items indexed by  postcode.
        :return: {postcode: {'postcode': str, 'date_code': str, 'tests': int, 'shape': geometry}}}
        :rtype: dict
        """
        result = {}
        source = self.data()
        for item in source:
            result[item['postcode']] = item

        return result

    def update_from_source(self, source: TestsByDateAndPostcode):

        source_data = source.total_tests_by_postcode()

        logging.info('Updating: ' + self.source)
        result = {'updates': 0, 'adds': 0, 'deletes': 0}

        # perform updates and deletes
        fields = [self.postcode_field, self.most_recent_code_field, self.tests_field, self.most_recent_date_field]
        with arcpy.da.UpdateCursor(in_table=self.source, field_names=fields) as cursor:
            for row in cursor:
                new_date_code = None
                new_tests = None
                source_item = source_data.pop(row[0], None)
                if source_item:
                    new_date_code = source_item['most_recent']
                    new_tests = source_item['tests']

                update_required = False
                if row[1] != new_date_code:
                    row[1] = new_date_code
                    row[3] = datetime.datetime.strptime(new_date_code, '%Y%m%d')
                    update_required = True
                if row[2] != new_tests:
                    row[2] = new_tests
                    update_required = True

                if update_required:
                    cursor.updateRow(row)
                    result['updates'] += 1

        # any remaining source items need to be inserted
        if source_data:
            fields = [self.postcode_field, self.most_recent_code_field, self.tests_field, self.most_recent_date_field, 'SHAPE@']
            with arcpy.da.InsertCursor(in_table=self.source, field_names=fields) as cursor:
                for postcode, item in source_data.items():
                    date_code = item['most_recent']
                    if date_code:
                        date_value = datetime.datetime.strptime(date_code, '%Y%m%d')
                    else:
                        date_value = None
                    row = [postcode, date_code, item['tests'], date_value, item['shape']]
                    cursor.insertRow(row)
                    result['adds'] += 1

        # force previously loaded data to none as it would reflect the data prior to update.
        # The next call that needs the source data will reload the updated data.
        self._loaded = None

        return result

    def total_tests_by_postcode(self):
        """
        Obtains a copy of the data items indexed by  postcode.
        :return: {postcode: {'postcode': str, 'date_code': str, 'tests': int, 'shape': geometry}}}
        :rtype: dict
        """
        return self.data_by_postcode()

