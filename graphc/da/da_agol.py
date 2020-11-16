import logging
import datetime

from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from arcgis.features import Feature

from graphc.utilities import datetime_utils


def date_field_value_to_datetime(value):
    if value:
        return datetime.datetime.fromtimestamp(value/1000.0)
    else:
        return None


def date_field_value_to_date_code(value, out_format):
    if value:
        return date_field_value_to_datetime(value).strftime(out_format)
    else:
        return None


def delete_rows(service_url, where_clause):
    deletes = []
    lyr = FeatureLayer(service_url)
    query_result = lyr.query(where=where_clause, return_ids_only=True)
    deletes = query_result['objectIds']

    if deletes:
        return lyr.edit_features(deletes=str(deletes))
    else:
        return None


def update_layer(layer, adds=None, deletes=None, updates=None, chunk_size=5000):
    """
    Performs updates on an arcgis feature service in manageable chunks.
    Updates are performed using multiple calls to the service where needed.  Large sets of updates are broken into
    smaller calls to avoid timeouts and other data size related issues.  Updates are executed in the following order:
    - Deletes
    - Adds
    - Updates
    If no elements are submitted for Adds, Deletes or Updates, then that stage of the process is skipped.

    :param layer: The Arcgis Feature Layer to be updated
    :type layer: arcgis.features.FeatureLayer
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
    logging.info('Updating: ' + layer.url)
    result = {'adds': 0, 'deletes': 0, 'updates': 0}
    # perform updates in order deletes, adds, updates to support models where:
    # - updates are performed by deleting old records and replacing with new (remove old items before adding new)
    # - items can be added and updated in same cycles (ensure adds are in place before updates are applied)
    if deletes:
        for chunk in _list_chunks(master_list=deletes, chunk_size=chunk_size):
            logging.info('Applying {} Deletes'.format(len(chunk)))
            layer.edit_features(deletes=str(chunk))
        result['deletes'] = len(deletes)
        logging.info('Total Deletes: {}'.format(result['deletes']))

    x = None
    if adds:
        for chunk in _list_chunks(master_list=adds, chunk_size=chunk_size):
            logging.info('Applying {} Adds'.format(len(chunk)))
            x = layer.edit_features(adds=chunk)
        result['adds'] = len(adds)
        logging.info('Total Adds: {}'.format(result['adds']))

    if updates:
        for chunk in _list_chunks(master_list=updates, chunk_size=chunk_size):
            logging.info('Applying {} Updates'.format(len(chunk)))
            layer.edit_features(updates=chunk)
        result['updates'] = len(updates)
        logging.info('Total Updates: {}'.format(result['updates']))

    return result


# Field Update Utils

def update_date_field(row: Feature, field_name: str, new_value: datetime.date):
    current_date_value = datetime_utils.to_date(row.attributes[field_name])

    if current_date_value == new_value:
        # if the values are the same, return False.
        return False

    # The values are different, Update the row.
    row.attributes[field_name] = new_value
    return True


def update_int_field(row: Feature, field_name: str, new_value: int = None):
    if row.attributes[field_name] != new_value:
        row.attributes[field_name] = new_value
        return True

    return False


def update_str_field(row: Feature, field_name: str, new_value: str = None, case_sensitive=True):
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
    if not case_sensitive and current_value.upper() == new_value.upper():
        return False

    # the strings are non-equivalent.  Update.
    row.attributes[field_name] = new_value
    return True


def update_float_field(row: Feature, field_name: str, new_value: float = None, rounding=4):
    current_value = row.attributes[field_name]
    if current_value:
        current_value = round(current_value, rounding)  # round non zero, non-null values.

    if new_value:
        test_value = round(new_value, rounding)  # round non zero, non-null values.
    else:
        test_value = new_value

    if current_value == test_value:
        return False

    row.attributes[field_name] = new_value
    return True


def _list_chunks(master_list, chunk_size):
    """
    Yield successive chunk-sized chunks from master_list.
    A utility function to support other methods in this module.
    """
    for i in range(0, len(master_list), chunk_size):
        yield master_list[i:i + chunk_size]


#