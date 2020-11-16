import datetime


def to_date(date_value, date_format='%Y%m%d'):
    """
    Accepts a variety of possible date representations and converts them to a datetime.date object where possible.
    Intended for use in methods where the input format of date values may vary.
    :param date_value: The date value to be converted
    :type date_value: Any
    :param date_format: The date string format to be used if the input date_value is a string.  '%Y%d%m' is default.
    :type date_format: str
    :return: datetime.date
    :rtype: datetime.date
    """
    if date_value is None:
        return None

    if isinstance(date_value, datetime.datetime):
        return date_value.date()
    elif isinstance(date_value, datetime.date):
        return date_value
    elif isinstance(date_value, str):
        return datetime.datetime.strptime(date_value, date_format).date()
    elif isinstance(date_value, int):
        return datetime.datetime.fromtimestamp(date_value/1000.0).date()

    raise ValueError('Invalid Date value.')


def to_datetime(datetime_value, date_format='%Y%m%d'):
    """
    Accepts a variety of possible datetime representations and converts them to a datetime.datetime object where possible.
    Intended for use in methods where the input format of date values may vary.
    :param datetime_value: The date value to be converted
    :type datetime_value: Any
    :param date_format: The date string format to be used if the input date_value is a string.  '%Y%d%m' is default.
    :type date_format: str
    :return: datetime.datetime
    :rtype: datetime.datetime
    """

    if datetime_value is None:
        return None

    if isinstance(datetime_value, datetime.datetime):
        return datetime_value
    elif isinstance(datetime_value, datetime.date):
        return datetime.datetime.combine(datetime_value, datetime.datetime.min.time())
    elif isinstance(datetime_value, str):
        return datetime.datetime.strptime(datetime_value, date_format)
    elif isinstance(datetime_value, int):
        return datetime.datetime.fromtimestamp(datetime_value / 1000.0)

    raise ValueError('Invalid DateTime value.')


def round_to_day(datetime_value, date_format='%Y%m%d'):
    return to_datetime(datetime_value, date_format).replace(hour=0, minute=0, second=0, microsecond=0)
