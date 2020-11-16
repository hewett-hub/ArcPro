import datetime
import logging
import argparse
import sys
import copy

from arcgis.gis import GIS
from arcgis.features import FeatureLayer

from graphc.da import da_agol
from graphc.da import da_arcpy
from graphc.covid.source.NSW_SourceData import NswNotificationData, NswTestData
from graphc.data.abs2016 import POA2016


class StatisticsByNameRegionAndDateCode(object):
    """
    A layer wrapper class for feature service layers where values are stored in tables in the format:
    - StatisticName
    - RegionID
    - DateCode
    - VALUE
    Each value is identified by the unique combination of StatisticName, RegionID and DateCode
    Each set of statistics have the same StatisticName.

    This style of table is useful to support multi-series timeline dashboard tables, where each Statistic Name can be used as a series
    in the chart.  The same table can also allow for dynamic filtering by selection or map view.
    """
    def __init__(self,
                 service_url,
                 region_id_field,
                 date_code_field='DateCode',
                 statistic_name_field='Statistic',
                 value_field='Value',
                 date_field='Date'):
        self.service_url = service_url
        self.region_id_field = region_id_field
        self.date_code_field = date_code_field
        self.date_field = date_field
        self.statistic_field = statistic_name_field
        self.value_field = value_field
        self.date_code_format = '%Y%m%d'

    def layer(self):
        return FeatureLayer(self.service_url)

    def get_statistic_items(self, statistic_name, include_geometry=True):
        """
        returns all items for the named statistic as a list of dictionaries.
        :param statistic_name: The name of the statistic to be found.
        :type statistic_name: str
        :param include_geometry: If True, then the geometry will be included.
        :type include_geometry: bool
        :return: list
        :rtype:
        """

        result = []
        target_layer = self.layer()
        where_clause = "{} = '{}'".format(self.statistic_field, statistic_name.upper())
        query_result = target_layer.query(where=where_clause)
        for row in query_result:
            item = {self.region_id_field: row.attributes[self.region_id_field],
                    self.date_code_field: row.attributes[self.date_code_field],
                    self.value_field: row.attributes[self.value_field]}
            if include_geometry:
                item['geometry'] = row.geometry
            result.append(item)

        return result

    def statistic_full_update(self, statistic_name, update_values):
        """
        Updates the feature service for the named statistic by matching the table values to the submitted update_values.
        The update_values must represent the full set of values for the named statistic.
        If the named statistic does not exist in the layer, it will be added.

        Date field values are derived from the date_code values.
        Existing XYs are not updated, submitted xys are used if rows are added.
        :param statistic_name: The name of the statistic to be updated.  Not case sensitive - will be forced to upper case.
        :type statistic_name: str
        :param update_values: {id: {'value': float, 'geometry': {...}}} with id in format yyyymmdd_rrrr where:
        - yyyy is the 4 digit year
        - mm is the 2 digit month, with leading zeros if required (ie 02 for February)
        - dd is the 2 digit day of the month, with leading zeros as needed.
        - rrrr is the region id.
        id must always be upper case.
        :type update_values: dict
        :return:
        :rtype:
        """

        uc_statistic_name = statistic_name.upper()
        logging.info('Updating Statistics: {}'.format(uc_statistic_name))
        copied_values = copy.deepcopy(update_values)
        deletes = []
        updates = []
        target_layer = self.layer()
        where_clause = "{} = '{}'".format(self.statistic_field, uc_statistic_name)
        query_result = target_layer.query(where=where_clause)
        for row in query_result:
            key = '{}_{}'.format(row.attributes[self.date_code_field], row.attributes[self.region_id_field])
            if key not in copied_values:
                deletes.append(row.attributes[query_result.object_id_field_name])

            item = copied_values.pop(key, None)
            if item:
                if row.attributes[self.value_field] != item['value']:
                    row.attributes[self.value_field] = item['value']
                    updates.append(row)

        # any remaining data_models items are new records
        adds = []

        for key, new_item in copied_values.items():
            date_code, region = key.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            row = {"attributes":
                       {self.region_id_field: region.upper(),
                        self.date_code_field: date_code.upper(),
                        self.statistic_field: uc_statistic_name,
                        self.value_field: new_item['value'],
                        self.date_field: date},
                   "geometry": new_item['geometry']}
            adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=updates, chunk_size=10000)



class NamedStatisticsByRegionAndDate(object):
    """
    A base class for a feature layer that contains named statistics grouped by region_id and date.
    Multiple statistics types can be held in the one layer.
    Each statistic type has a distinct name.
    Within each statistic type, each record is identified by a distinct datecode_regionid pair.
    """
    def __init__(self, service_url, region_id_field, statistic_name,
                 date_code_field='DateCode', date_field='Date', statistic_field='Statistic', value_field='Value'):
        self.service_url = service_url
        self.region_id_field = region_id_field
        self.statistic_name = statistic_name.upper()
        self.date_code_field = date_code_field
        self.date_field = date_field
        self.statistic_field = statistic_field
        self.value_field = value_field
        self.date_code_format = '%Y%m%d'

    def layer(self):
        return FeatureLayer(self.service_url)

    def query_statistic(self, where_clause=None):
        """
        Queries the source feature layer and returns a feature set.
        Only records where the self.statistic_field == self.statistic_name are returned.
        Additional where clause arguments are appended to the underlying statistic filter with an AND statement.
        :param where_clause: An optional where clause to filter the statistic values further.
        :type where_clause:
        :return:
        :rtype:
        """
        full_where_clause = "{} = '{}'".format(self.statistic_field, self.statistic_name)
        if where_clause:
            full_where_clause += " AND " + where_clause

        return self.layer().query(where=full_where_clause)

    def update_statistic(self, update_values, allow_deletes=False):
        """
        Updates the feature service for the named statistic by updating or adding the submitted rows.  Statistic Items are
        identified by date_code and postcode.
        Date values are derived from the date_code values.
        Existing XYs are not updated, submitted xys are used if rows are added.
        :param update_values: {id: {'value': float, 'geometry': {...}}} with id in format yyyymmdd_rrrr where:
        - yyyy is the 4 digit year
        - mm is the 2 digit month, with leading zeros if required (ie 02 for February)
        - dd is the 2 digit day of the month, with leading zeros as needed.
        - rrrr is the region id.
        id must always be upper case.
        :type update_values: dict
        :param allow_deletes: If set to True any records not found in the source rows will be deleted.  Default=False
        :type allow_deletes: bool
        :return:
        :rtype:
        """

        logging.info('Updating Statistics: {}'.format(self.statistic_name))
        copied_values = copy.deepcopy(update_values)
        deletes = []
        updates = []
        target_layer = self.layer()
        where_clause = "Statistic = '{}'".format(self.statistic_name)
        query_result = target_layer.query(where=where_clause)
        for row in query_result:
            key = '{}_{}'.format(row.attributes[self.date_code_field], row.attributes[self.region_id_field])
            if allow_deletes and key not in copied_values:
                deletes.append(row.attributes[query_result.object_id_field_name])

            item = copied_values.pop(key, None)
            if item:
                if row.attributes[self.value_field] != item['value']:
                    row.attributes[self.value_field] = item['value']
                    updates.append(row)

        # any remaining data_models items are new records
        adds = []

        for key, new_item in copied_values.items():
            date_code, region = key.split('_')
            date = datetime.datetime.strptime(date_code, '%Y%m%d')
            row = {"attributes":
                       {self.region_id_field: region.upper(),
                        self.date_code_field: date_code.upper(),
                        self.statistic_field: self.statistic_name,
                        self.value_field: new_item['value'],
                        self.date_field: date},
                   "geometry": new_item['geometry']}
            adds.append(row)

        return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=updates, chunk_size=10000)

    def get_indexed_values(self, where_clause=None, include_geometry=True):
        result = {}
        source = self.query_statistic(where_clause=where_clause)
        for row in source:
            date_code = row.attributes[self.date_code_field]
            region_id = row.attributes[self.region_id_field]
            key = '{}_{}'.format(date_code, region_id)
            if include_geometry:
                result[key] = {'value': row.attributes[self.value_field], 'geometry': row.geometry}
            else:
                result[key] = {'value': row.attributes[self.value_field]}

        return result

    def format_date_string(self, date_string, in_format):
        """
        Reformats the submitted date or datetime string to the correct format for the date_code field
        :type date_string: str
        :param in_format: the format string of the submitted date_string.  eg: '%Y-%m-%d'
        :type in_format: str
        :return: The reformatted date_string
        :rtype: str
        """

        dt = datetime.datetime.strptime(date_string, in_format)
        return dt.strftime(self.date_code_format)


class Covid19NotificationsByPostcodeAndDate(object):
    def __init__(self):
        self.target = NamedStatisticsByRegionAndDate(
            service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Statistics_by_Postcode_and_Date/FeatureServer/0',
            region_id_field='Postcode',
            statistic_name='NOTIFICATIONS'
        )
        self.nsw_source = NswNotificationData()
        self.geometry_source = POA2016.centroids()

    def get_update_values(self):

    def update(self):

        # get the source data
        source_data = self.nsw_source.source_data()

        # get postcode xys
        xys = da_arcpy.load_xy_geometries(source=self.geometry_source._source,
                                          id_field=self.geometry_source.poa_code_field)

        # convert to input rows
        data = {}
        for row in source_data:
            date_str = self.target.format_date_string(date_string=row[self.nsw_source.date_field], in_format=self.nsw_source.csv_date_format)
            postcode = row[self.nsw_source.postcode_field]
            if not postcode:
                postcode = 'UNK'

            key = '{}_{}'.format(date_str, postcode)
            data_item = data.get(key, None)
            if data_item:
                data_item['value'] += 1
            else:
                xy = xys.get(postcode, None)
                data[key] = {'value': 1, 'geometry': xy}

        return self.target.update_statistic(update_values=data, allow_deletes=True)


class Covid19TestsByPostcodeAndDate(object):
    def __init__(self):
        self.target = NamedStatisticsByRegionAndDate(
            service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Statistics_by_Postcode_and_Date/FeatureServer/0',
            region_id_field='Postcode',
            statistic_name='TESTS'
        )
        self.nsw_source = NswNotificationData()
        self.geometry_source = POA2016.centroids()

    def update(self):

        # get the source data
        source_data = self.nsw_source.source_data()

        # get postcode xys
        xys = da_arcpy.load_xy_geometries(source=self.geometry_source._source,
                                          id_field=self.geometry_source.poa_code_field)

        # convert to input rows
        data = {}
        for row in source_data:
            date_str = self.target.format_date_string(date_string=row[self.nsw_source.date_field], in_format=self.nsw_source.csv_date_format)
            postcode = row[self.nsw_source.postcode_field]
            if not postcode:
                postcode = 'UNK'

            key = '{}_{}'.format(date_str, postcode)
            data_item = data.get(key, None)
            if data_item:
                data_item['value'] += 1
            else:
                xy = xys.get(postcode, None)
                data[key] = {'value': 1, 'xy': xy}

        return self.target.update_statistic(update_values=data, allow_deletes=True)


class Covid19TotalNotificationsByPostcodeAndDate(object):
    def __init__(self):
        self.target = NamedStatisticsByRegionAndDate(
            service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Statistics_by_Postcode_and_Date/FeatureServer/0',
            region_id_field='Postcode',
            statistic_name='TOTAL NOTIFICATIONS'
        )
        self.source = Covid19NotificationsByPostcodeAndDate()

    def update(self):

        # get the source data
        source_data = self.source.

        # get postcode xys
        xys = da_arcpy.load_xy_geometries(source=self.geometry_source._source,
                                          id_field=self.geometry_source.poa_code_field)

        # convert to input rows
        data = {}
        for row in source_data:
            date_str = self.target.format_date_string(date_string=row[self.nsw_source.most_recent_date_field], in_format=self.nsw_source.csv_date_format)
            postcode = row[self.nsw_source.postcode_field]
            if not postcode:
                postcode = 'UNK'

            key = '{}_{}'.format(date_str, postcode)
            data_item = data.get(key, None)
            if data_item:
                data_item['value'] += 1
            else:
                xy = xys.get(postcode, None)
                data[key] = {'value': 1, 'geometry': xy}

        return self.target.update_statistic(update_values=data, allow_deletes=True)
#
# class Covid19StatisticsByPostcodeAndDate(object):
#     """
#     A feature service wrapper class that supports common operations.
#     """
#     def __init__(self, service_url=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/'
#                                    r'COVID_19_Statistics_by_Postcode_and_Date/FeatureServer/0'):
#         self.service_url = service_url
#         self.postcode_field = 'Postcode'
#         self.date_code_field = 'DateCode'
#         self.date_field = 'Date'
#         self.statistic_field = 'Statistic'
#         self.value_field = 'Value'
#         self.date_code_format = '%Y%m%d'
#
#     def layer(self):
#         return FeatureLayer(self.service_url)
#
#     def query(self, where_clause='1=1'):
#         return self.layer().query(where=where_clause)
#
#     def update_statistic(self, statistic, update_values, allow_deletes=False):
#         """
#         Updates the feature service for the named statistic by updating or adding the submitted rows.  Statistic Items are
#         identified by date_code and postcode.
#         Date values are derived from the date_code values.
#         Existing XYs are not updated, submitted xys are used if rows are added.
#         :param statistic: The name of the statistic to be updated.
#         :type statistic: str
#         :param update_values: {id: {'value': float, 'xy': {'x': float, 'y': float}}} with id in format yyyymmdd_pppp where:
#         - yyyy is the 4 digit year
#         - mm is the 2 digit month, with leading zeros if required (ie 02 for February)
#         - dd is the 2 digit day of the month, with leading zeros as needed.
#         - pppp is the 4 digit postcode, or 'UNK' if the postcode is unknown.
#         id must always be upper case.
#         :type update_values: dict
#         :param allow_deletes: If set to True any records not found in the source rows will be deleted.  Default=False
#         :type allow_deletes: bool
#         :return:
#         :rtype:
#         """
#         uc_statistic = statistic.upper()
#
#         logging.info('Updating Statistics: {}'.format(uc_statistic))
#         copied_values = copy.deepcopy(update_values)
#         deletes = []
#         updates = []
#         target_layer = self.layer()
#         where_clause = "Statistic = '{}'".format(uc_statistic)
#         query_result = target_layer.query(where=where_clause)
#         for row in query_result:
#             key = '{}_{}'.format(row.attributes[self.date_code_field], row.attributes[self.postcode_field])
#             if allow_deletes and key not in copied_values:
#                 deletes.append(row.attributes[query_result.object_id_field_name])
#
#             item = copied_values.pop(key, None)
#             if item:
#                 if row.attributes[self.value_field] != item['value']:
#                     row.attributes[self.value_field] = item['value']
#                     updates.append(row)
#
#         # any remaining data_models items are new records
#         adds = []
#
#         for key, new_item in copied_values.items():
#             date_code, postcode = key.split('_')
#             date = datetime.datetime.strptime(date_code, '%Y%m%d')
#             row = {"attributes":
#                        {self.postcode_field: postcode.upper(),
#                         self.date_code_field: date_code.upper(),
#                         self.statistic_field: uc_statistic,
#                         self.value_field: new_item['value'],
#                         self.date_field: date},
#                    "geometry": new_item['xy']}
#             adds.append(row)
#
#         return da_agol.update_layer(layer=target_layer, adds=adds, deletes=deletes, updates=updates, chunk_size=10000)
#
#     def format_date_string(self, date_string, in_format):
#         """
#         Reformats the submitted date or datetime string to the correct format for the date_code field
#         :type date_string: str
#         :param in_format: the format string of the submitted date_string.  eg: '%Y-%m-%d'
#         :type in_format: str
#         :return: The reformatted date_string
#         :rtype: str
#         """
#
#         dt = datetime.datetime.strptime(date_string, in_format)
#         return dt.strftime(self.date_code_format)
#
#
# class NotificationsStatistic(object):
#     def __init__(self):
#         self.target = Covid19StatisticsByPostcodeAndDate()
#         self.nsw_source = NswNotificationData()
#         self.geometry_source = POA2016.centroids()
#         self.statistic_name = 'NOTIFICATIONS'
#
#     def update(self):
#
#         # get the source data
#         source_data = self.nsw_source.source_data()
#
#         # get postcode xys
#         xys = da_arcpy.load_xy_geometries(source=self.geometry_source.source,
#                                           id_field=self.geometry_source.poa_code_field)
#
#         # convert to input rows
#         data = {}
#         for row in source_data:
#             date_str = self.target.format_date_string(date_string=row[self.nsw_source.date_field], in_format=self.nsw_source.date_format)
#             postcode = row[self.nsw_source.postcode_field]
#             if not postcode:
#                 postcode = 'UNK'
#
#             key = '{}_{}'.format(date_str, postcode)
#             data_item = data.get(key, None)
#             if data_item:
#                 data_item['value'] += 1
#             else:
#                 xy = xys.get(postcode, None)
#                 data[key] = {'value': 1, 'xy': xy}
#
#         return self.target.update_statistic(statistic=self.statistic_name, update_values=data, allow_deletes=True)
#
#
# class TestsStatisticUpdater(object):
#     def __init__(self):
#         self.target = Covid19StatisticsByPostcodeAndDate()
#         self.nsw_source = NswTestData()
#         self.postcode_feature_source = POA2016.centroids()
#         self.statistic_name = 'TESTS'
#
#     def update(self):
#
#         # get the source data
#         source_data = self.nsw_source.source_data()
#
#         # get postcode xys
#         xys = da_arcpy.load_xy_geometries(source=self.postcode_feature_source.source,
#                                           id_field=self.postcode_feature_source.poa_code_field)
#
#         # convert to input rows
#         data = {}
#         for row in source_data:
#             date_str = self.target.format_date_string(date_string=row[self.nsw_source.date_field], in_format=self.nsw_source.date_format)
#             postcode = row[self.nsw_source.postcode_field]
#             if not postcode:
#                 postcode = 'UNK'
#
#             key = '{}_{}'.format(date_str, postcode)
#             data_item = data.get(key, None)
#             if data_item:
#                 data_item['value'] += 1
#             else:
#                 xy = xys.get(postcode, None)
#                 data[key] = {'value': 1, 'xy': xy}
#
#         return self.target.update_statistic(statistic=self.statistic_name, update_values=data, allow_deletes=True)
#
#
# class TotalNotificationsStatisticUpdater(object):
#     def __init__(self):
#         self.target = Covid19StatisticsByPostcodeAndDate()
#         self.source_data = Covid19StatisticsByPostcodeAndDate()
#         self.statistic_name = 'TOTAL_NOTIFICATIONS'
#
#     def update(self):
#         """
#         Performs a full update from the source data, including adds, deletes and updates.
#         :return:
#         :rtype:
#         """
#         # get all postcode notification records.
#         source_where_clause = "{} = '{}'".format(self.source_data.statistic_field, self.)
#         source_values = self.source_data.query()
#         id_field = self.source_data.id_field
#         notifications_field = self.source_data.notifications_field
#         data = {}
#         for row in source_values:
#             id_value = row.attributes[id_field]
#             date_code, postcode = id_value.split('_')
#             data_item = data.get(postcode, None)
#             if data_item:
#                 data_item['notifications'][date_code] = row.attributes[notifications_field]
#             else:
#                 data_item = {'notifications': {date_code: row.attributes[notifications_field]}, 'xy': row.geometry}
#                 data[postcode] = data_item
#
#         update_data = {}
#         date_format = self.source_data.date_code_format
#         end_date = datetime.datetime.now()
#         for postcode, postcode_values in data.items():
#             notifications = postcode_values['notifications']
#             xy = postcode_values['xy']
#             total = 0
#             start_date = datetime.datetime(year=2020, month=1, day=1)
#             while start_date < end_date:
#                 date_code = start_date.strftime(date_format)
#                 total += notifications.get(date_code, 0)
#                 if total > 0:
#                     id_value = '{}_{}'.format(date_code, postcode)
#                     update_data[id_value] = {'notifications': total, 'xy': xy}
#                 start_date += datetime.timedelta(days=1)
#
#         return self.feature_service.update(update_values=update_data, allow_deletes=True)
