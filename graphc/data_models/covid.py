import json
import datetime


class DailyRegionStatistics(object):
    def __init__(self, date_format='%Y-%m-%d'):
        """

        :param date_format: The date format to be used internally
        :type date_format: str
        """
        self.data = {}  # {region_id: {date_string: {}}}
        self._date_format = date_format

    def date_format(self):
        return self._date_format

    def _reformat_date(self, date_string, date_format):
        """
        Reformats the submitted date string into the internal date format.
        :param date_string: the date string to be reformatted
        :type date_string: str
        :param date_format: the format of the submitted string
        :type date_format: str
        :return: the reformatted date string.
        :rtype: str
        """
        dt = datetime.datetime.strptime(date_string, date_format)
        return dt.strftime(self._date_format)

    def add_to_daily_count(self, region_id, date_string, date_format, count_key, count_value):
        """

        :param region_id:
        :type region_id:
        :param date_string:
        :type date_string:
        :param date_format: the date format of the submitted date string
        :type date_format:
        :param count_key: The key to which the count value will be added
        :type count_key: str
        :param count_value: The value to be added to the count
        :type count_value: int or float
        :return:
        :rtype:
        """
        # reformat the date
        date = self._reformat_date(date_string, date_format)

        region = self.data.get(region_id, None)
        if not region:
            region = {}
            self.data[region_id] = region

        daily_stats = region.get(date, None)
        if not daily_stats:
            daily_stats = {}
            region[date] = daily_stats

        if count_key in daily_stats:
            daily_stats[count_key] += count_value
        else:
            daily_stats[count_key] = count_value

    def _update_totals(self, data_key):
        for item in self.data.values():
            dates = sorted(item.keys())
            current_total = 0
            for date in dates:
                date_item = item[date]
                current_total += date_item.get(data_key, 0)
                date_item['total_' + data_key] = current_total

    def calculate_cumulative_daily_totals(self, keys):
        """
        Creates or updates the cumulative daily totals for each submitted key.
        For example, if keys is ['cases', 'tests'] then 'total_cases' and 'total_tests' will be calculated for each
        daily entry found, with the cumulative value being the sum of all daily values up to (and including) the date
        being calculated.
        :param keys:
        :type keys:
        :return:
        :rtype:
        """
        for key in keys:
            self._update_totals(key)

    def get_rows(self, keys):
        result = []
        for region_id, region_values in self.data.items():
            for date, date_values in region_values.data():
                result_item = {'region_id': region_id, 'date': date}
                for key in keys:
                    result_item[key] = date_values.get(key, None)
                result.append(result_item)

        return result

    def save_json(self, file_path):
        dump_data = {'data': self.data,
                     'date_format': self._date_format}

        with open(file_path, 'w') as f:
            f.write(json.dumps(dump_data, indent=4, sort_keys=True))

    def load_json(self, file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)

        self.data = data['data']
        self._date_format = data['date_format']
