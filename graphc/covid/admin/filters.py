"""
These filters accept data as a list of dictionaries, with each dictionary representing a record.
The filters then return a subset of records appropriate to their function.
"""


def most_recent_by_group(data, group_id_field, date_field):
    """
    Returns only the most recent entry for each group_id, indexed by group_id.
    :param data: [{group_field: group_id, value_field: value, date_field: date},....]
    :type data: list
    :param group_id_field: The data field to be used as the group ids.
    :type group_id_field: str
    :param date_field: The data field containing the date values.
    :type date_field: str
    :return: {group_id: {group_field: group_id, value_field: value, date_field: date}}
    :rtype: dict
    """

    result = {}
    for item in data:
        group_id = item[group_id_field]
        group_item = result.get(group_id, None)
        if group_item:
            if item[date_field] > group_item[date_field]:
                result[group_id] = item
        else:
            result[group_id] = item

    return result
