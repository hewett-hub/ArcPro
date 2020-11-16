import datetime
from graphc.utilities import datetime_utils


def cumulative_daily_totals(data,
                            value_field,
                            date_field,
                            date_format='%Y%m%d',
                            start_date: datetime.datetime = None,
                            end_date: datetime.datetime = None,
                            none_value=0):

    if none_value is None:
        none_value = 0

    # aggregate values by date
    result = {}
    for item in data:
        item_value = item[value_field]
        if item_value is None:
            item_value = none_value

        this_value = datetime_utils.to_datetime(item[date_field], date_format)
        date_code = this_value.strftime('%Y%m%d')
        result[date_code] = result.get(date_code, 0) + item_value

    """
    For each group found, for each date, calculates the sum of all previous dates for that group.
    :param data: A list of records in the form [{group_field: group_id, value_field: value, date_field: date}, ...]
    :type data: list
    :param group_id_field: The name of the field containing the group ids used to link group records.  For example, 'postcode'
    :type group_id_field: str
    :param value_field: The name of the field containing the values to be averaged.
    :type value_field: str
    :param date_field: The name of the field containing the date values
    :type date_field: str
    :param date_format: If the date values in the data are date strings, set this parameter to the date format string (eg: '%Y%m%d').
    Default is '%Y%m%d'
    :type date_format: str
    :param start_date: The optional earliest date for which values will be calculated.  If not defined, the first date found in each group will
    be used as the start date.
    :type start_date: datetime
    :param end_date: The optional last date for which values will be calculated.  If not defined, the current date will be used.
    :type end_date: datetime
    :param none_value: The value to be used if no record is found for a specific date/region, or if the value in a data record is None.
    The default value is 0
    :type none_value: float
    :return: {yyyymmdd_group: avg}
    :rtype:
    """
    # calculate start and end dates
    if start_date:
        # ensure date is in datetime format
        start_date = datetime_utils.to_datetime(start_date, date_format)
    else:
        start_date = datetime_utils.to_datetime(min(result.keys()), '%Y%m%d')

    if end_date:
        end_date = datetime_utils.to_datetime(end_date, date_format)
    else:
        end_date = datetime.datetime.now()

    # calculate cumulative daily totals
    step = datetime.timedelta(days=1)

    total_value = 0
    while start_date <= end_date:
        date_code = start_date.strftime('%Y%m%d')
        total_value += result.get(date_code, 0)
        result[date_code] = total_value

        start_date += step

    return result


def cumulative_daily_totals_by_group(data,
                                     group_id_field,
                                     value_field,
                                     date_field,
                                     date_format='%Y%m%d',
                                     start_date: datetime.date = None,
                                     end_date: datetime.date = None,
                                     none_value=0):
    """
    For each group found, for each date, calculates the sum of all previous dates for that group.
    :param data: A list of records in the form [{group_field: group_id, value_field: value, date_field: date}, ...]
    :type data: list
    :param group_id_field: The name of the field containing the group ids used to link group records.  For example, 'postcode'
    :type group_id_field: str
    :param value_field: The name of the field containing the values to be averaged.
    :type value_field: str
    :param date_field: The name of the field containing the date values
    :type date_field: str
    :param date_format: If the date values in the data are date strings, set this parameter to the date format string (eg: '%Y%m%d').
    Default is '%Y%m%d'
    :type date_format: str
    :param start_date: The optional earliest date for which values will be calculated.  If not defined, the first date found in each group will
    be used as the start date.
    :type start_date: datetime
    :param end_date: The optional last date for which values will be calculated.  If not defined, the current date will be used.
    :type end_date: datetime
    :param none_value: The value to be used if no record is found for a specific date/region, or if the value in a data record is None.
    The default value is 0
    :type none_value: float
    :return: {yyyymmdd_group: avg}
    :rtype:
    """
    # calculate start and end dates
    if not start_date:
        start_date = datetime.date.min

    if end_date:
        if isinstance(end_date, datetime.datetime):
            end_date = end_date.date()
    else:
        end_date = datetime.datetime.now().date()

    # force None to 0.  Cannot add Nones to int or float
    if none_value is None:
        none_value = 0

    # extract relevant data and separate into groups
    group_data = {}
    for item in data:
        date_value = datetime_utils.to_date(item[date_field], date_format)

        if start_date <= date_value <= end_date:
            group = item[group_id_field]

            stat_value = item[value_field]
            if stat_value is None:
                stat_value = none_value

            # separate items into groups
            group_values = group_data.get(group, None)
            if not group_values:
                group_values = {}
                group_data[group] = group_values
            group_values[date_value] = group_values.get(date_value, 0) + stat_value

    # calculate cumulative daily totals
    result = {}
    for group, group_values in group_data.items():
        # if the start date was defined, use that date, otherwise use the first date in the group.
        if start_date > datetime.date.min:
            group_date = start_date
        else:
            group_date = min(group_values.keys())

        step = datetime.timedelta(days=1)

        total = 0
        while group_date <= end_date:
            total += group_values.get(group_date, none_value)
            key = '{}_{}'.format(group_date.strftime('%Y%m%d'), group)
            result[key] = total

            group_date += step

    return result


def moving_daily_averages(data,
                          value_field,
                          date_field,
                          n=7,
                          date_format='%Y%m%d',
                          end_date=None,
                          none_value=0):
    """
    For each group found, calculates the average value for the past n days for each date from first item found until the end date, or last item found.
    :param data: A list of records in the form [{value_field: value, date_field: date}, ...]
    :type data: list
    :param value_field: The name of the field containing the values to be averaged.
    :type value_field: str
    :param date_field: The name of the field containing the date values
    :type date_field: str
    :param n: the number of days to be averaged.
    :type n: int
    :param date_format: If the date values in the data are date strings, set this parameter to the date format string (eg: '%Y%m%d').
    Default is '%Y%m%d'
    :type date_format: str
    :param end_date: The optional last date for which values will be calculated.  If not defined, the maximum date value in the data will be used.
    :type end_date: datetime
    :param none_value: The value to be used if no record is found for a specific date/region, or if the value in a data record is None.
    The default value is 0
    :type none_value: float
    :return: {yyyymmdd: avg}
    :rtype:
    """

    wkg = {}
    for item in data:
        date_value = datetime_utils.to_datetime(item[date_field], date_format)
        date_code = date_value.strftime('%Y%m%d')
        value = item[value_field]
        if value is None:
            value = none_value

        wkg[date_code] = wkg.get(date_code, 0) + value

    # calculate start and end dates
    start_date = datetime_utils.to_datetime(min(wkg.keys()), '%Y%m%d')

    if end_date:
        end_date = datetime_utils.to_datetime(end_date, date_format)
    else:
        end_date = datetime.datetime.now()

    result = {}
    value_list = []
    while start_date <= end_date:
        date_code = start_date.strftime('%Y%m%d')
        value_list.append(wkg.get(date_code, none_value))
        if len(value_list) > n:
            value_list.pop(0)
        ave = sum(value_list) / float(n)
        result[date_code] = ave
        start_date += datetime.timedelta(days=1)

    return result


def moving_daily_averages_by_date_and_group(data,
                                            group_id_field,
                                            value_field,
                                            date_field,
                                            n=7,
                                            date_format='%Y%m%d',
                                            end_date=None,
                                            none_value=0):
    """
    For each group found, calculates the average value for the past n days for each date from first item found until the end date, or last item found.
    :param data: A list of records in the form [{group_field: group_id, value_field: value, date_field: date}, ...]
    :type data: list
    :param group_id_field: The name of the field containing the group ids used to link group records.  For example, 'postcode'
    :type group_id_field: str
    :param value_field: The name of the field containing the values to be averaged.
    :type value_field: str
    :param date_field: The name of the field containing the date values
    :type date_field: str
    :param n: the number of days to be averaged.
    :type n: int
    :param date_format: If the date values in the data are date strings, set this parameter to the date format string (eg: '%Y%m%d').
    Default is '%Y%m%d'
    :type date_format: str
    :param end_date: The optional last date for which values will be calculated.  If not defined, the maximum date value in the data will be used.
    :type end_date: datetime
    :param none_value: The value to be used if no record is found for a specific date/region, or if the value in a data record is None.
    The default value is 0
    :type none_value: float
    :return: {yyyymmdd_group: avg}
    :rtype:
    """

    # If an end date is provided, use that, otherwise use the most recent date in the dataset.
    finish_date = end_date
    if finish_date:
        if isinstance(finish_date, datetime.datetime):
            finish_date = finish_date.date()
    else:
        finish_date = datetime_utils.to_date(max([item[date_field] for item in data]), date_format)

    wkg = {}
    for item in data:
        group = item[group_id_field]
        date_value = datetime_utils.to_date(item[date_field], date_format)
        value = item[value_field]

        group_item = wkg.get(group, None)
        if not group_item:
            group_item = {'start_date': date_value, 'values': {date_value: value}}
            wkg[group] = group_item
        else:
            group_item['values'][date_value] = value
            if group_item['start_date'] > date_value:
                group_item['start_date'] = date_value

    result = {}
    for group, item in wkg.items():
        group_list = []
        start_date = item['start_date']
        group_values = item['values']

        while start_date <= finish_date:
            group_list.append(group_values.get(start_date, none_value))
            if len(group_list) > n:
                group_list.pop(0)
            ave = sum(group_list) / float(n)
            key = '{}_{}'.format(start_date.strftime('%Y%m%d'), group)
            result[key] = ave
            start_date += datetime.timedelta(days=1)

    return result


def totals_by_group(data, group_id_field, value_field):
    """
    Calculates the total value for each group in the data.
    :param data: A list of records in the form [{group_field: group_id, value_field: value}, ...]
    :type data: list
    :param group_id_field: the name of the field containing the group_ids.
    :type group_id_field: str
    :param value_field: the name of the field containing the values to be summed
    :type value_field: str
    :return: {group_id: total}
    :rtype: dict
    """

    result = {}
    for item in data:
        value = item[value_field]
        if value is not None:
            group_id = item[group_id_field]
            result[group_id] = result.get(group_id, 0) + value

    return result


def totals_by_date(data, date_field, value_field, date_format='%Y%m%d'):
    """
    Calculates the total value for each group in the data.
    :param data: A list of records in the form [{date_field: date, value_field: value}, ...]
    :type data: list
    :param date_field: the name of the field containing the dates.
    :type date_field: str
    :param value_field: the name of the field containing the values to be summed
    :type value_field: str
    :param date_format:
    :type date_format:
    :return: {yyyymmdd: total}
    :rtype: dict
    """

    result = {}
    for item in data:
        value = item[value_field]
        if value is not None:
            date_value = datetime_utils.to_datetime(item[date_field], date_format)
            date_code = date_value.strftime('%Y%m%d')
            result[date_code] = result.get(date_code, 0) + value

    return result

