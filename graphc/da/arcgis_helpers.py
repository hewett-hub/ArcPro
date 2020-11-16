import copy
import datetime
import logging
import json

import arcpy
from arcgis.features import Feature
from arcgis.features import FeatureLayer
from arcgis.geometry import Geometry

from graphc.utilities import datetime_utils


class FeatureSourceHelper(object):
    def __init__(self, source, id_field):
        self.source = source
        self.id_field = id_field
        self._rounding = 4
        self._case_sensitive = True

        self.__loaded = None

    def load_records(self, fields=None, where_clause=None):
        raise NotImplementedError()

    def field_names(self):
        raise NotImplementedError()

    def indexed_records(self, fields, where_clause=None):
        """
        Loads records from the feature class and returns them as a dictionary of records indexed by the id_field values.
        :param fields: The list of fields to be returned.
        :type fields: list
        :param where_clause: An optional where clause
        :type where_clause:
        :return: {id_field_value: {id_fieldname: id_value, fieldname1: value1, fieldname2: value2, ...}, ...]
        :rtype: dict
        """
        if self.id_field not in fields:
            fields.append(self.id_field)

        records = self.records(fields, where_clause)
        result = {}
        for record in records:
            result[record[self.id_field]] = record

        return result

    def values_by_id(self, value_field, where_clause=None):
        """
        returns a lookup dictionary of {record_id: value}
        :param value_field: The value field to be returned.
        :type value_field: str
        :param where_clause: Optional where clause
        :type where_clause:
        :return: {record_id: value}
        :rtype: dict
        """
        result = {}
        for item in self.records(fields=[self.id_field, value_field], where_clause=where_clause):
            result[item[self.id_field]] = item[value_field]

        return result

    def records(self, fields, where_clause):
        if fields is not None:
            field_list = ','.join(fields)
        else:
            field_list = None

        if self.__loaded:
            if self.__loaded['fields'] == field_list and self.__loaded['where'] == where_clause:
                return self.__loaded['records']

        result = self.load_records(fields=fields, where_clause=where_clause)
        self.__loaded = {'fields': field_list, 'where': where_clause, 'records': result}

        return result

    def update_records(self, new_data, fields=None, where_clause=None, add_new=False, delete_unmatched=False,
                       rounding=4, case_sensitive=True):
        raise NotImplementedError()

    @staticmethod
    def new_helper(source, id_field):
        source_lower = source.lower()
        if source_lower.startswith('https:') or source_lower.startswith('http:'):
            return FeatureServiceHelper(source=source, id_field=id_field)
        else:
            return FeatureClassHelper(source=source, id_field=id_field)


class FeatureClassHelper(FeatureSourceHelper):
    def __init__(self, source, id_field):
        super().__init__(source=source, id_field=id_field)

        self.last_records = {}

    def load_records(self, fields=None, where_clause=None):
        """
        Loads records from the feature class and returns it as a list and returns them as a list of dictionary items.
        :param fields: The list of fields to be returned.
        :type fields:
        :param where_clause: An optional where clause
        :type where_clause:
        :return: [{fieldname1: value1, fieldname2: value2, ...}, ...]
        :rtype: list
        """
        shape_renamed = False
        logging.info('Loading: ' + self.source)
        field_types = self.field_types()
        if fields is None:
            fields = list(field_types.keys())
            for i in range(len(fields)):
                if fields[i] == 'Shape':
                    fields[i] = 'SHAPE@'
                    shape_renamed = True

        result = []
        with arcpy.da.SearchCursor(in_table=self.source, field_names=fields, where_clause=where_clause) as cursor:
            for row in cursor:
                if shape_renamed:
                    for i in range(len(fields)):
                        if fields[i] == 'SHAPE@':
                            fields[i] = 'Shape'
                item = self.row_to_record(row, fields, field_types)
                result.append(item)

        return result

    def field_types(self):
        """
        returns a dictionary of field types indexed by field name.
        :return: {field_name: field_type}
        :rtype:
        """
        field_types = {}
        for field in arcpy.ListFields(self.source):
            field_types[field.name] = field.type
        return field_types

    def field_names(self):
        return [f.name for f in arcpy.ListFields(self.source)]

    @staticmethod
    def row_to_record(row, fields, field_types):
        field_count = len(fields)
        result = {}
        for i in range(field_count):
            field_name = fields[i]
            field_type = field_types.get(field_name, None)
            field_value = row[i]
            if field_type == 'DATE' and field_value is not None:
                result[field_name] = datetime_utils.to_date(field_value)
            else:
                result[field_name] = row[i]

        return result

    @staticmethod
    def update_date_field(row, field_index: int, new_value):
        current_date_value = datetime_utils.to_datetime(row[field_index])
        new_date_value = datetime_utils.to_datetime(new_value)

        if current_date_value == new_date_value:
            # if the values are the same, return False.
            return False

        # The values are different, Update the row.
        row[field_index] = new_date_value
        return True

    @staticmethod
    def update_int_field(row, field_index: int, new_value: int = None):
        if row[field_index] != new_value:
            row[field_index] = new_value
            return True

        return False

    def update_str_field(self, row, field_index: int, new_value: str = None):
        current_value = row[field_index]

        # if both are equal (str=str or None=None) return False.
        if current_value == new_value:
            return False

        # if (str and None) or (None and str)
        if not (current_value and new_value):
            row[field_index] = new_value
            return True

        # both values are non-identical strings.
        # if the test is not case sensitive and both UC strings match, no update needed
        if not self._case_sensitive and current_value.upper() == new_value.upper():
            return False

        # the strings are non-equivalent.  Update.
        row[field_index] = new_value
        return True

    def update_float_field(self, row, field_index: int, new_value: float = None):
        current_value = row[field_index]
        if current_value:
            current_value = round(current_value, self._rounding)  # round non zero, non-null values.

        if new_value:
            test_value = round(new_value, self._rounding)  # round non zero, non-null values.
        else:
            test_value = new_value

        if current_value == test_value:
            return False

        row[field_index] = new_value
        return True

    @staticmethod
    def update_geometry_field(row, field_index: int, new_value: arcpy.Geometry = None):
        current_value = row[field_index]

        if current_value == new_value:
            return False

        row[field_index] = new_value
        return True

    def update_field(self, row, field_index: int, new_value, field_type: str):
        ignore_types = ['OID', "RASTER", 'BLOB']
        uc_field_type = field_type.upper()

        if uc_field_type in ['STRING']:
            return self.update_str_field(row, field_index, new_value)
        elif uc_field_type in ['SINGLE', 'DOUBLE']:
            return self.update_float_field(row, field_index, new_value)
        elif uc_field_type in ['INTEGER', 'SMALLINTEGER']:
            return self.update_int_field(row, field_index, new_value)
        elif uc_field_type in ['DATE']:
            return self.update_date_field(row, field_index, new_value)
        elif uc_field_type == 'GEOMETRY':
            return self.update_geometry_field(row, field_index, new_value)
        elif uc_field_type in ignore_types:
            return False
        else:
            raise ValueError('Unhandled field_type: ' + field_type)

    def update_records(self, new_data, fields=None, where_clause=None, add_new=False, delete_unmatched=False,
                       rounding=4, case_sensitive=True, shape_field='Shape'):
        """
        Updates the feature class using the new_data, with each record uniquely identified by the self.record_id_field.
        :param new_data: Dictionary records indexed by id.  {record_id: {field_name1: value1, field_name2: value2,...}}
        :type new_data: dict
        :param fields: The list of fields to be updated.  If an id_field is included, it will not be updated.
        :type fields:
        :param where_clause: An optional where clause to filter the updates.
        :type where_clause:
        :param add_new: If true, any records found in the new_data that do not have a corresponding record in the feature class will be deleted.
        :type add_new: bool
        :param delete_unmatched:  If true, any feature class records found that do not have a corresponding record in the new_data will be deleted.
        :type delete_unmatched: bool
        :param rounding: decimal rounding to be used when comparing double format numbers.
        :type rounding: int
        :param shape_field: The name of the new_data field containing the geometries field to be updated.
        Set to None if geometry is not to be updated.  Default='Shape'
        :type shape_field: str
        :param case_sensitive:
        :type case_sensitive:
        :return:
        :rtype:
        """

        logging.info('Updating: ' + self.source)
        result = {'adds': 0, 'deletes': 0, 'updates': 0}

        self._rounding = rounding
        self._case_sensitive = case_sensitive

        # use a local copy of new_data because we will be popping items.
        my_data = copy.deepcopy(new_data)

        field_types = self.field_types()

        all_fields = fields[:]
        if self.id_field not in all_fields:
            all_fields.append(self.id_field)
        id_index = all_fields.index(self.id_field)

        if shape_field:
            # the shape_field itself should not be in the fields used.  The SHAPE@ token is added to the fields instead.
            # the shape_field is not changed, because it is used to reference the new_data record geometries.
            if shape_field in all_fields:
                all_fields.remove(shape_field)
            if shape_field and 'SHAPE@' not in all_fields:
                all_fields.append('SHAPE@')

        field_count = len(all_fields)
        with arcpy.da.UpdateCursor(self.source, all_fields, where_clause) as cursor:
            for row in cursor:
                key = row[id_index]
                new_item = my_data.pop(key, None)
                if new_item:
                    update_required = False
                    for i in range(field_count):
                        field_name = all_fields[i]
                        if field_name != self.id_field:
                            if field_name == 'SHAPE@':
                                new_value = new_item[shape_field]
                                field_type = 'Geometry'
                            else:
                                new_value = new_item[field_name]
                                field_type = field_types[field_name]
                            if self.update_field(row, i, new_value, field_type):
                                update_required = True
                    if update_required:
                        cursor.updateRow(row)
                        result['updates'] += 1
                elif delete_unmatched:
                    cursor.deleteRow()
                    result['deletes'] += 1

        if my_data and add_new:
            with arcpy.da.InsertCursor(self.source, all_fields) as cursor:
                for item in my_data.values():
                    row = [None] * field_count
                    for i in range(field_count):
                        field_name = all_fields[i]
                        if field_name == 'SHAPE@':
                            new_value = item[shape_field]
                            field_type = 'Geometry'
                        else:
                            new_value = item[field_name]
                            field_type = field_types[field_name]
                        self.update_field(row, i, new_value, field_type)  # ensure all data rules are applied to the value being added.
                    cursor.insertRow(row)
                    result['adds'] += 1

        return result


class FeatureServiceHelper(FeatureSourceHelper):
    def __init__(self, source, id_field):
        super().__init__(source=source, id_field=id_field)
        self.layer = FeatureLayer(source)

    def query(self, fields=None, where_clause=None):
        if fields is None:
            fields = '*'
        elif isinstance(fields, list):
            fields = ','.join(fields)
        if where_clause is None:
            where_clause = '1=1'

        return self.layer.query(out_fields=fields, where=where_clause)

    def load_records(self, fields=None, where_clause=None):
        return self.query(fields=fields, where_clause=where_clause).to_dict('records')

    @staticmethod
    def _field_types(query_result):
        result = {}
        for field in query_result.fields:
            result[field['name']] = field['type']

        return result

    def field_names(self):
        return self.layer.properties.fields

    def update_records(self, new_data, fields=None, where_clause=None, add_new=False, delete_unmatched=False,
                       rounding=4, case_sensitive=True, shape_field='Shape'):
        """
        Updates the feature class using the new_data, with each record uniquely identified by the self.record_id_field.
        :param new_data: Dictionary records indexed by id.  {record_id: {field_name1: value1, field_name2: value2,...}}
        :type new_data: dict
        :param fields: The list of fields to be updated.  If an id_field is included, it will not be updated.
        :type fields:
        :param where_clause: An optional where clause to filter the updates.
        :type where_clause:
        :param add_new: If true, any records found in the new_data that do not have a corresponding record in the feature class will be deleted.
        :type add_new: bool
        :param delete_unmatched:  If true, any feature class records found that do not have a corresponding record in the new_data will be deleted.
        :type delete_unmatched: bool
        :param rounding: decimal rounding to be used when comparing double format numbers.
        :type rounding: int
        :param case_sensitive:
        :type case_sensitive:
        :param shape_field: The name of the geometry field in the new_data.  Set to None if geometry is not to be updated.  Default='Shape'
        :type shape_field: str
        :return:
        :rtype:
        """
        self._rounding = rounding
        self._case_sensitive = case_sensitive

        # use a local copy of new_data because we will be popping items.
        my_data = copy.deepcopy(new_data)

        if fields and self.id_field not in fields:
            fields.append(self.id_field)

        query_result = self.query(fields=fields, where_clause=where_clause)
        field_types = self._field_types(query_result)

        updates = []
        deletes = []

        for row in query_result:
            id_value = row.attributes[self.id_field]
            new_row = my_data.pop(id_value, None)
            if new_row:
                if self.update_row(row=row, field_types=field_types, new_values=new_row, shape_field=shape_field):
                    updates.append(row)
            elif delete_unmatched:
                deletes.append(row.attributes[query_result.object_id_field_name])

        adds = []
        if add_new:
            # any remaining data_models items are new records
            for id_value, new_item in my_data.items():
                new_geometry = new_item.pop(shape_field, None)
                row = self.generate_new_row(new_item, new_geometry)
                adds.append(row)

        return self.update_layer(adds=adds, deletes=None, updates=updates)

    def update_layer(self, adds=None, deletes=None, updates=None, chunk_size=1000):
        """
        Performs updates on an arcgis feature service in manageable chunks.
        Updates are performed using multiple calls to the service where needed.  Large sets of updates are broken into
        smaller calls to avoid timeouts and other data size related issues.  Updates are executed in the following order:
        - Deletes
        - Adds
        - Updates
        If no elements are submitted for Adds, Deletes or Updates, then that stage of the process is skipped.

        :param adds: The list of add items to be added.
        :type adds:
        :param deletes:
        :type deletes:
        :param updates:
        :type updates:
        :param chunk_size:
        :type chunk_size:
        :return:
        :rtype:
        """
        logging.info('Updating: ' + self.source)
        result = {'adds': 0, 'deletes': 0, 'updates': 0}
        # perform updates in order deletes, adds, updates to support models where:
        # - updates are performed by deleting old records and replacing with new (remove old items before adding new)
        # - items can be added and updated in same cycles (ensure adds are in place before updates are applied)
        if deletes:
            for chunk in self._list_chunks(master_list=deletes, chunk_size=chunk_size):
                logging.info('Applying {} Deletes'.format(len(chunk)))
                self.layer.edit_features(deletes=str(chunk))
            result['deletes'] = len(deletes)
            logging.info('Total Deletes: {}'.format(result['deletes']))

        if adds:
            for chunk in self._list_chunks(master_list=adds, chunk_size=chunk_size):
                logging.info('Applying {} Adds'.format(len(chunk)))
                self.layer.edit_features(adds=chunk)
            result['adds'] = len(adds)
            logging.info('Total Adds: {}'.format(result['adds']))

        if updates:
            for chunk in self._list_chunks(master_list=updates, chunk_size=chunk_size):
                logging.info('Applying {} Updates'.format(len(chunk)))
                self.layer.edit_features(updates=chunk)
            result['updates'] = len(updates)
            logging.info('Total Updates: {}'.format(result['updates']))

        return result

    @staticmethod
    def update_date_field(row: Feature, field_name: str, new_value: datetime.date):
        current_date_value = datetime_utils.to_datetime(row.attributes[field_name])
        new_date_value = datetime_utils.to_datetime(new_value)

        if current_date_value == new_date_value:
            # if the values are the same, return False.
            return False

        # The values are different, Update the row.
        row.attributes[field_name] = new_date_value
        return True

    @staticmethod
    def update_int_field(row: Feature, field_name: str, new_value: int = None):
        if row.attributes[field_name] != new_value:
            row.attributes[field_name] = new_value
            return True

        return False

    def update_str_field(self, row: Feature, field_name: str, new_value: str = None):
        current_value = row.attributes[field_name]

        # if both are equal (str=str or None=None) return False.
        if current_value == new_value:
            return False

        # if (str and None) or (None and str)
        if not (current_value and new_value):
            row.attributes[field_name] = new_value
            return True

        # both values are non-identical strings.
        # if the test is not case sensitive and both UC strings match, no update needed
        if not self._case_sensitive and current_value.upper() == new_value.upper():
            return False

        # the strings are non-equivalent.  Update.
        row.attributes[field_name] = new_value
        return True

    def update_float_field(self, row: Feature, field_name: str, new_value: float = None):
        current_value = row.attributes[field_name]
        if current_value:
            current_value = round(current_value, self._rounding)  # round non zero, non-null values.

        if new_value:
            test_value = round(new_value, self._rounding)  # round non zero, non-null values.
        else:
            test_value = new_value

        if current_value == test_value:
            return False

        row.attributes[field_name] = new_value
        return True

    def update_field(self, row: Feature, field_name: str, field_type: str, new_value):
        ignore_types = ['esriFieldTypeOID', 'esriFieldTypeGeometry', 'esriFieldTypeBlob', 'esriFieldTypeRaster']
        if field_type in ['esriFieldTypeSmallInteger', 'esriFieldTypeInteger']:
            return self.update_int_field(row, field_name=field_name, new_value=new_value)
        elif field_type in ['esriFieldTypeSingle', 'esriFieldTypeDouble']:
            return self.update_float_field(row=row, field_name=field_name, new_value=new_value)
        elif field_type == 'esriFieldTypeString':
            return self.update_str_field(row=row, field_name=field_name, new_value=new_value)
        elif field_type == 'esriFieldTypeDate':
            return self.update_date_field(row=row, field_name=field_name, new_value=new_value)
        elif field_type in ignore_types:
            return False

        raise ValueError('Unhandled field type: ' + field_type)

    def update_row(self, row: Feature, field_types, new_values, shape_field=None):
        update_required = False
        for field_name in row.fields:
            if field_name != self.id_field and field_name in new_values:
                field_type = field_types[field_name]
                new_value = new_values[field_name]
                if self.update_field(row=row, field_name=field_name, field_type=field_type, new_value=new_value):
                    update_required = True
        #if shape_field:  TODO implement feature updates in a way that handles minor locational variations (nm)
        #
        #    new_wkt = self.to_wkt(new_values[shape_field])
        #    current_wkt = self.to_wkt(row.geometry)

        #    if current_wkt != new_wkt:
        #        row.geometry = self.to_geometry(new_values[shape_field])
        #        update_required = True

        return update_required

    @ staticmethod
    def to_wkt(source):
        if source is None:
            return None
        if isinstance(source, Geometry):
            return source.WKT
        if isinstance(source, arcpy.Geometry):
            return source.WKT

        geom = Geometry(source)
        return geom.WKT

    @staticmethod
    def to_geometry(source):
        if source is None:
            return None

        if isinstance(source, Geometry):
            return source

        if isinstance(source, arcpy.Geometry):
            return Geometry(source.JSON)

        return Geometry(source)

    @staticmethod
    def generate_new_row(new_values, geometry=None):
        attributes = {}
        for field_name, value in new_values.items():
            attributes[field_name] = value

        geometry_value = geometry
        if geometry_value and isinstance(geometry_value, arcpy.Geometry):
            geometry_value = json.loads(geometry_value.JSON)

        return {"attributes": attributes,
                "geometry": geometry_value}

    @staticmethod
    def _list_chunks(master_list, chunk_size):
        """
        Yield successive chunk-sized chunks from master_list.
        A utility function to support other methods in this module.
        """
        for i in range(0, len(master_list), chunk_size):
            yield master_list[i:i + chunk_size]


class TableBase(object):
    def __init__(self, source, id_field, shape_field='Shape'):
        self.source = source
        self.id_field = id_field
        self.shape_field = shape_field
        self._helper = FeatureSourceHelper.new_helper(source, id_field)

    def records(self, fields=None, where_clause=None):
        return self._helper.records(fields=fields, where_clause=where_clause)

    def indexed_records(self, fields, id_field=None, where_clause=None):
        """
        Loads records from the feature class and returns them as a dictionary of records indexed by the id_field values.
        :param fields: The list of fields to be returned.
        :type fields: list
        :param id_field: Optional.  The field name to be used for indexing.  If None or not defined, the self.id_field value will be used.
        This field allows secondary id fields to be used if present.  For example, State Name vs State Code vs State Abbreviation
        :type id_field: string
        :param where_clause: An optional where clause
        :type where_clause:
        :return: {id_field_value: {id_fieldname: id_value, fieldname1: value1, fieldname2: value2, ...}, ...]
        :rtype: dict
        """
        if not id_field:
            id_field = self.id_field

        if id_field not in fields:
            fields.append(id_field)

        records = self.records(fields, where_clause)
        result = {}
        for record in records:
            result[record[id_field]] = record

        return result

    def values_by_id(self, value_field, id_field=None, where_clause=None):
        """
        returns a lookup dictionary of {record_id: value}
        :param value_field: The value field to be returned.
        :type value_field: str
        :param id_field: Optional.  The field name to be used for indexing.  If None or not defined, the self.id_field value will be used.
        This field allows secondary id fields to be used if present.  For example, State Name vs State Code vs State Abbreviation
        :type id_field: string
        :param where_clause: Optional where clause
        :type where_clause:
        :return: {record_id: value}
        :rtype: dict
        """
        result = {}
        if not id_field:
            id_field = self.id_field
        for item in self.records(fields=[id_field, value_field], where_clause=where_clause):
            result[item[id_field]] = item[value_field]

        return result

    def field_names(self):
        return self._helper.field_names()

    def update_records(self, new_data, fields=None, where_clause=None, add_new=False, delete_unmatched=False,
                       rounding=4, case_sensitive=True):
        self._helper.update_records(new_data=new_data,
                                    fields=fields,
                                    where_clause=where_clause,
                                    add_new=add_new,
                                    delete_unmatched=delete_unmatched,
                                    rounding=rounding,
                                    case_sensitive=case_sensitive)
