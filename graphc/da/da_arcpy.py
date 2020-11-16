"""
A utility module that assists in querying data using arcpy.
This module is suitable for accessing data in local and enterprise databases, but not online data.
"""

import arcpy
import numpy
import logging


def load_xy_geometries(source, id_field, where_clause=None):
    """
    Gets xy coords as a geometry format, indexed by id_field values.  In cases where geometries are empty, the geometry value returned will be None.
    :param source: The path to the data source.
    :type source: str
    :param id_field: the field that will be used to index the result.  If ids are not unique, only last item found will be returned.
    :type id_field: str
    :param where_clause: Optional: A where clause to filter the results returned.
    :type where_clause: str
    :return: {id, {'x': float, 'y': float}}
    :rtype: dict
    """
    logging.info('Loading xy geometries from: ' + source)
    result = {}
    fields = [id_field, 'SHAPE@XY']
    with arcpy.da.SearchCursor(source, fields, where_clause) as cursor:
        for row in cursor:
            xy = row[1]
            if xy:
                result[row[0]] = {'x': xy[0], 'y': xy[1]}
            else:
                row[1] = None

    return result


def load_xy_tuples(source, id_field, where_clause=None):
    """
    Gets xy coords as a tuple, indexed by id_field values.
    :param source: The path to the data source.
    :type source: str
    :param id_field: the field that will be used to index the result.  If ids are not unique, only last item found will be returned.
    :type id_field: str
    :param where_clause: Optional: A where clause to filter the results returned.
    :type where_clause: str
    :return: {id, (x,y)}
    :rtype: dict
    """
    logging.info('Loading xy tuples from: ' + source)
    result = {}
    fields = [id_field, 'SHAPE@XY']
    with arcpy.da.SearchCursor(source, fields, where_clause) as cursor:
        for row in cursor:
            result[row[0]] = row[1]

    return result


def load_indexed_values(source, id_field, value_field, where_clause=None):
    """
    Builds a value lookup indexed by an id. {id, value}
    :param source: The path to the data source.
    :type source: str
    :param id_field: the field that will be used to index the result.  If ids are not unique, only last item found will be returned.
    :type id_field: str
    :param value_field: the field holding the value components.
    :param value_field: str
    :param where_clause: Optional: A where clause to filter the results returned.
    :type where_clause: str

    :return: {id, value}
    :rtype: dict
    """
    logging.info('Loading indexed values from: ' + source)
    result = {}
    fields = [id_field, value_field]
    with arcpy.da.SearchCursor(source, fields, where_clause) as cursor:
        for row in cursor:
            result[row[0]] = row[1]

    return result


def load_indexed_items(source, id_field, value_fields, where_clause=None):
    """
    Builds a lookup of named values indexed by an id. {id, {field_name: value, ...}}
    :param source: The path to the data source.
    :type source: str
    :param id_field: the field that will be used to index the result.  If ids are not unique, only last item found will be returned.
    :type id_field: str
    :param value_fields: the list of fields to be returned.
    :param value_fields: list
    :param where_clause: Optional: A where clause to filter the results returned.
    :type where_clause: str

    :return: {id, value}
    :rtype: dict
    """

    logging.info('Loading indexed value dictionaries from: ' + source)
    # ensure id field is first item in fields list
    fields = value_fields[:]  # copy the value fields so we don't alter the input parameter.
    if id_field in fields:  # if the id field is anywhere in the fields list,
        fields.remove(id_field)  # remove it so we don't duplicate the call to the field
    fields.insert(0, id_field)  # insert the id field at the start of the field list.

    field_count = len(fields)
    result = {}
    with arcpy.da.SearchCursor(source, fields, where_clause) as cursor:
        for row in cursor:
            id_value = row[0]
            item = {}
            for i in range(field_count):
                item[fields[i]] = row[i]
            result[id_value] = item

    return result


def unique_field_values(table, field):
    data = arcpy.da.TableToNumPyArray(table, [field])
    return numpy.unique(data[field])

