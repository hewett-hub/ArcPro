import arcpy
import json
import arcgis
import datetime


def geometry_to_json(geometry: arcpy.Geometry):
    """
    Converts an arcpy Geometry class from a local or enterprise feature class to a json object that can be submitted to an ArcGIS Online API
    :param geometry: The geometry to be converted.
    :type geometry: arcpy.Geometry
    :return: a dictionary representation of the geometry suitable for submission to a rest endpoint update, add or edit function.
    :rtype: dict
    """
    if geometry:
        return json.loads(geometry.JSON)
    else:
        return None


def date_code(date, out_format='%Y%m%d', in_format=None):
    """Reformats the date to a sting in the out_format.  Handles string to string and datetime or date to string."""
    if isinstance(date, str):
        if in_format == out_format:
            return date
        else:
            return datetime.datetime.strptime(date, format=in_format).strftime(out_format)
    else:
        return date.strftime(out_format)
