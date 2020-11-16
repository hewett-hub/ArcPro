"""
NOTE: Beautiful Soup must be installed to run: pip install beatuifulsoup4
NOTE: word2number must be installed to run: pip install word2number

run pip as admin.  If not recognized, use "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\Scripts\pip.exe" or equivalent path
in place of direct pip call.

refs:
https://medium.com/analytics-vidhya/web-scraping-for-beginners-with-python-and-beautifulsoup-3131435d0e97
https://pypi.org/project/word2number/
"""

import os
import requests
import re
import logging
import datetime
import json
from bs4 import BeautifulSoup as soup
from word2number import w2n
#from graphc.data.abs2020_LGA import LGA2020


from arcgis.gis import GIS

vic_source = r'https://www.dhhs.vic.gov.au'
target_workspace = r'E:\Documents2\tmp\COVID19'

lga_statistics_layer = r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/Daily_LGA_COVID_19_Statistics/FeatureServer/0'

# the local windows profile containing the credentials to be used to access the feature service.
profile = 'agol_graphc'


class Victoria(object):

    @classmethod
    def get_total_cases(cls, data_text):
        x = re.search("Victoria is [0-9]*[,]?[0-9]+ with [0-9]*[,]?[0-9]+ new cases reported yesterday", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("Victoria is [0-9]*[,]?[0-9]+ – an increase of [a-zA-Z]+ from yesterday", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("total number of cases now at [0-9]*[,]?[0-9]+", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        logging.warning('Total Cases not found')
        return None

    @classmethod
    def get_new_cases(cls, data_text):
        x = re.search("Victoria is [0-9]*[,]?[0-9]+ with [0-9]*[,]?[0-9]+ new cases reported yesterday", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[1])

        x = re.search("Victoria has recorded [0-9]*[,]?[0-9]+ new cases", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("Victoria is [0-9]*[,]?[0-9]+ – an increase of [a-zA-Z]+ from yesterday", data_text)
        if x:
            d = re.findall('of [a-zA-Z]+ from', x.group())[0][3:-5]
            return w2n.word_to_num(d)

        logging.warning('New Cases not found')
        return None

    @classmethod
    def get_reclassified_cases(cls, data_text):
        x = re.search("The overall total has increased by [0-9]+, with [a-zA-Z]+ cases reclassified", data_text)
        if x:
            d = re.findall('with [a-zA-Z]+ cases', x.group())[0][5:-6]
            return w2n.word_to_num(d)

        x = re.search("[0-9]*[,]?[0-9]+ cases were reclassified", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        logging.warning('Reclassified not found')
        return None

    @staticmethod
    def get_outbreak_linked(data_text):
        x = re.search("[0-9]+ new cases are linked to outbreaks", data_text)
        if x:
            d = re.findall('[0-9]+', x.group())
            return int(d[0])

        logging.warning('Linked to Outbreaks not found')
        return None

    @classmethod
    def get_routine_testing(cls, data_text):
        x = re.search("[0-9]*[,]?[0-9]+ new cases have been identified through routine testing", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        logging.warning('Routine Testing not found')
        return None

    @classmethod
    def get_under_investigation(cls, data_text):
        x = re.search("[0-9]*[,]?[0-9]+ cases are under investigation", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("[0-9]*[,]?[0-9]+ are under investigation", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        logging.warning('Under Investigation not found')
        return None

    @staticmethod
    def get_new_deaths(data_text):
        x = re.search("There have been no new deaths reported", data_text)
        if x:
            return 0

        x = re.search("There were no new deaths reported", data_text)
        if x:
            return 0

        x = re.search("There was one new death reported", data_text)
        if x:
            return 1

        x = re.search("There have been [0-9]+ new deaths reported", data_text)
        if x:
            d = re.findall('[0-9]+', x.group())
            return int(d[0])

        x = re.search("To date, [0-9]+ people have died", data_text)
        d = re.findall('[0-9]+', x.group())
        return int(d[0])

    @staticmethod
    def get_total_deaths(data_text):
        x = re.search("To date, [0-9]+ people have died", data_text)
        d = re.findall('[0-9]+', x.group())
        return int(d[0])

    @classmethod
    def get_community_transmission(cls, data_text):
        x = re.search(
            "There are [0-9]*[,]?[0-9]+ confirmed cases of coronavirus in Victoria that may have been acquired through community transmission",
            data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search(
            "[0-9]*[,]?[0-9]+ cases may indicate community transmission",
            data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        logging.warning('Community Transmission not found')
        return None

    @classmethod
    def get_unknown_transmission(cls, data_text):
        x = re.search("There have been [0-9]*[,]?[0-9]+ confirmed cases of coronavirus in Victoria that have been acquired through unknown transmission",
                      data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        logging.warning('Unknown Transmission not found')
        return None

    @classmethod
    def get_active_cases(cls, data_text):
        x = re.search("There are currently [0-9]*[,]?[0-9]+ active cases", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("[0-9]*[,]?[0-9]+ cases are currently active", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        logging.warning('Active Cases not found')
        return None

    @classmethod
    def get_hospitalisation(cls, data_text):
        x = re.search("Currently, [0-9]*[,]?[0-9]+ people with coronavirus infection are in hospital", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("Currently [0-9]*[,]?[0-9]+ people are in hospital", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("[0-9]*[,]?[0-9]+ cases of coronavirus are in hospital", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        logging.warning('Hospitalisations Not Found')
        return None

    @classmethod
    def get_hotel_quarantine_cases(cls, data_text):
        x = re.search("No cases have been detected in a returned travellers in hotel quarantine", data_text)
        if x:
            return 0

        x = re.search("No case has been detected in a returned traveller in hotel quarantine", data_text)
        if x:
            return 0

        x = re.search("No new cases have been detected in returned travellers in hotel quarantine", data_text)
        if x:
            return 0

        x = re.search("One new case has been detected in a returned traveller in hotel quarantine", data_text)
        if x:
            return 1

        logging.warning('Hotel Quarantine Cases Not Found')
        return None

    @classmethod
    def get_icu(cls, data_text):
        x = re.search("including [a-zA-Z]+ patients in intensive care", data_text)
        if x:
            d = re.findall('including [a-zA-Z]+ patients', x.group())[0][10:-9]
            return w2n.word_to_num(d)

        x = re.search("including [a-zA-Z]+ in intensive care", data_text)
        if x:
            d = re.findall('including [a-zA-Z]+ in', x.group())[0][10:-3]
            return w2n.word_to_num(d)

        x = re.search("including [0-9]+ patients in intensive care", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        logging.warning('ICU Not Found')
        return None

    @classmethod
    def get_recovered(cls, data_text):
        x = re.search("[0-9]*[,]?[0-9]+ people have recovered", data_text)
        d = re.findall('[0-9]*[,]?[0-9]+', x.group())
        return cls.str_to_int(d[0])

    @classmethod
    def get_metro(cls, data_text):
        x = re.search("there have been [0-9]*[,]?[0-9]+ in metropolitan Melbourne", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("[0-9]*[,]?[0-9]+ cases are from metropolitan Melbourne", data_text)
        d = re.findall('[0-9]*[,]?[0-9]+', x.group())
        return cls.str_to_int(d[0])

    @classmethod
    def get_regional(cls, data_text):
        x = re.search("and [0-9]*[,]?[0-9]+ in regional Victoria", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("[0-9]*[,]?[0-9]+ are from regional Victoria", data_text)
        d = re.findall('[0-9]*[,]?[0-9]+', x.group())
        return cls.str_to_int(d[0])

    @classmethod
    def get_males(cls, data_text):
        x = re.search("made up of [0-9]*[,]?[0-9]+ men", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("includes [0-9]*[,]?[0-9]+ men", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("include [0-9]*[,]?[0-9]+ men", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("[0-9]*[,]?[0-9]+ are men", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("made up of [0-9]*[,]?[0-9]+ males", data_text)
        d = re.findall('[0-9]*[,]?[0-9]+', x.group())
        return cls.str_to_int(d[0])

    @classmethod
    def get_females(cls, data_text):
        x = re.search("and [0-9]*[,]?[0-9]+ women", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("and [0-9]*[,]?[0-9]+ are women", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls.str_to_int(d[0])

        x = re.search("and [0-9]*[,]?[0-9]+ females", data_text)
        d = re.findall('[0-9]*[,]?[0-9]+', x.group())
        return cls.str_to_int(d[0])

    @staticmethod
    def get_tests(data_text):
        x = re.search("More than [0-9]*[,]?[0-9]+ tests", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return int(d[0].replace(',', ''))

        x = re.search("Almost [0-9]*[,]?[0-9]+ tests", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return int(d[0].replace(',', ''))

        x = re.search("More than [0-9]*[,]?[0-9]+ swabs", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return int(d[0].replace(',', ''))

        logging.warning('Tests not found.')
        return None

    @staticmethod
    def str_to_int(str_value, replace_empty=None):
        stripped = str_value.strip().replace('*', '').replace(',', '').replace('-', '')
        if stripped:
            return int(stripped)
        return replace_empty

    @classmethod
    def try_parse_structured_lga_table(cls, data):
        table = data.findAll('table')
        if table:
            lga_stats = []
            rows = table[0].tbody.findAll('tr')
            for row in rows:
                items = row.findAll('td')
                # some tables have headers within the table content and empty rows.
                # Only process if there are cells in the row and the first cell not 'LGA'
                # and the number of items is greater than 1.
                if items and items[0].text.strip().upper() != 'LGA':
                    if len(items) > 2:
                        stats = {
                            'lga_name': items[0].text.strip(),
                            'total_cases': cls.str_to_int(items[1].text, 0),
                            'active_cases': cls.str_to_int(items[2].text, 0)
                        }
                        lga_stats.append(stats)
                    elif len(items) == 2:
                        stats = {
                            'lga_name': items[0].text.strip(),
                            'total_cases': cls.str_to_int(items[1].text, 0),
                            'active_cases': None
                        }
                        lga_stats.append(stats)

            return lga_stats
        else:
            return None

    @staticmethod
    def split_string(string_value, split_strings):
        for split_string in split_strings:
            if split_string in string_value:
                return string_value.split(split_string)

        # handle special cases
        if re.search('Interstate [0-9]+', string_value):
            return string_value.split(' ')

        if re.search('Overseas [0-9]+', string_value):
            return string_value.split(' ')

        if re.search('Unknown [0-9]+', string_value):
            return string_value.split(' ')

        raise RuntimeError(string_value)

    @classmethod
    def try_parse_paragraph_table(cls, data):
        # get all paras in page
        paras = data.findAll('p')
        table = None
        # find last para that contains a ref to Stonnington followed by a number.  Stonnington was first entry in earliest reports
        # so should be in all subsequent reports with LGA totals.
        for p in paras:
            para_text = p.text.replace(u'\xa0', ' ')
            if re.search("Stonnington .+ [0-9]+", para_text, re.IGNORECASE):
                table = para_text

        lga_stats = []
        split_strings = [' (C) -', ' (S) -', ' (RC) -',
                         ' (C) ', ' (S) ', ' (RC) ', ' (A) ',
                         ' - ', '    ']
        rows = table.strip().split('\n')
        for row in rows:
            parts = cls.split_string(row, split_strings)
            stats = {
                'lga_name': parts[0].strip(),
                'total_cases': int(parts[1].strip()),
                'active_cases': None
            }
            lga_stats.append(stats)

        return lga_stats

    @classmethod
    def get_lga_stats(cls, data):
        result = cls.try_parse_structured_lga_table(data)
        if result:
            return result

        result = cls.try_parse_paragraph_table(data)
        if result:
            return result

        raise RuntimeError('Could not find LGA Stats')

    @staticmethod
    def get_data(working_date, base_url=vic_source):
        """
        Gets Victorian corona virus update page for specified date.
        The following url patterns have been identified and handled (note-samples are examples only and will not link to real world source_data):
        - https://www.dhhs.vic.gov.au/coronavirus-update-victoria-03-april-2020
        - https://www.dhhs.vic.gov.au/coronavirus-update-victoria-wednesday-3-april
        - https://www.dhhs.vic.gov.au/coronavirus-update-victoria-3-april-2020
        - https://www.dhhs.vic.gov.au/coronavirus-update-victoria-3-april
        - https://www.dhhs.vic.gov.au/coronavirus-update-victoria-wednesday-3-april-2020
        - https://www.dhhs.vic.gov.au/media-release-coronavirus-update-victoria-wednesday-3-april-2020

        If a url for the specified date is not found a RuntimeError is raised containing the working_date value
        :param working_date: date for which source_data is to be obtained
        :type working_date: datetime.datetime
        :param base_url: base vic url.
        :type base_url: string
        :return: request result
        :rtype: requests.api
        """
        day = working_date.strftime('%d').lstrip('0')
        month = working_date.strftime('%B')
        year = working_date.strftime('%Y')

        url_date_string = '{}-{}-{}'.format(day, month, year)
        source_url = base_url + r'/coronavirus-update-victoria-' + url_date_string
        r = requests.get(source_url)
        if r.status_code == 200:
            return r

        weekday = working_date.strftime('%A')
        url_date_string = '{}-{}-{}'.format(weekday, day, month)
        source_url = base_url + r'/coronavirus-update-victoria-' + url_date_string
        r = requests.get(source_url)
        if r.status_code == 200:
            return r

        url_date_string = '{}-{}-{}-{}'.format(weekday, day, month, year)
        source_url = base_url + r'/coronavirus-update-victoria-' + url_date_string
        r = requests.get(source_url)
        if r.status_code == 200:
            return r

        day = working_date.strftime('%d')
        url_date_string = '{}-{}-{}'.format(day, month, year)
        source_url = base_url + r'/coronavirus-update-victoria-' + url_date_string
        r = requests.get(source_url)
        if r.status_code == 200:
            return r

        url_date_string = '{}-{}'.format(day, month)
        source_url = base_url + r'/coronavirus-update-victoria-' + url_date_string
        r = requests.get(source_url)
        if r.status_code == 200:
            return r

        url_date_string = '{}-{}-{}'.format(weekday, day, month)
        source_url = base_url + r'/media-release-coronavirus-update-victoria-' + url_date_string
        r = requests.get(source_url)
        if r.status_code == 200:
            return r

        logging.warning('Report not found for: {}-{}-{}'.format(day, month, year))
        return None

    @classmethod
    def parse_daily_update(cls, daily_update_data):
        logging.info('Processing: ' + daily_update_data.url)
        result = {}

        page_soup = soup(daily_update_data._source_data, 'html5lib')
        data = page_soup.findAll('div',
                                 {'class': 'field field--name-field-dhhs-rich-text-text field--type-text-long field--label-hidden field--item'})[0]
        data_text = data.text.replace(u'\xa0', ' ')

        result['source'] = daily_update_data.url
        result['total_cases'] = cls.get_total_cases(data_text)
        result['new_cases'] = cls.get_new_cases(data_text)
        result['reclassified'] = cls.get_reclassified_cases(data_text)
        result['outbreak_linked'] = cls.get_outbreak_linked(data_text)
        result['routine_testing'] = cls.get_routine_testing(data_text)
        result['under_investigation'] = cls.get_under_investigation(data_text)
        result['new_deaths'] = cls.get_new_deaths(data_text)
        result['total_deaths'] = cls.get_total_deaths(data_text)
        result['unknown_transmission'] = cls.get_unknown_transmission(data_text)
        result['community_transmission'] = cls.get_community_transmission(data_text)
        result['hotel_quarantine_cases'] = cls.get_hotel_quarantine_cases(data_text)
        result['active_cases'] = cls.get_active_cases(data_text)
        result['hospitalisations'] = cls.get_hospitalisation(data_text)
        result['icu'] = cls.get_icu(data_text)
        result['recovered'] = cls.get_recovered(data_text)
        result['metro'] = cls.get_metro(data_text)
        result['regional'] = cls.get_regional(data_text)
        result['males'] = cls.get_males(data_text)
        result['females'] = cls.get_females(data_text)
        result['tests'] = cls.get_tests(data_text)
        result['lgas'] = cls.get_lga_stats(data)

        return result

    @classmethod
    def get_daily_extracts(cls, start_date, workspace):
        lga_helper = LgaSourceHelper()

        working_date = start_date
        while working_date < datetime.datetime.now():
            file_date_string = working_date.strftime('%Y%m%d')
            file_path = os.path.join(workspace, 'vic_' + file_date_string + '.json')
            if not os.path.exists(file_path):
                daily_update_data = cls.get_data(working_date)
                if daily_update_data:
                    data = cls.parse_daily_update(daily_update_data)
                    data['date_code'] = file_date_string
                    lga_helper.pre_process_vic_data(data['lgas'])
                    with open(file_path, 'w') as f:
                        f.write(json.dumps(data, indent=4, sort_keys=True))

                    appended = covid.DailyStatisticsByLGA().append_data(data)
                    logging.info("{} rows appended.".format(len(appended)))

            working_date += datetime.timedelta(days=1)


class LgaSourceHelper(object):
    def __init__(self, source=LGA2020.centriods()):
        self.source = source

    def pre_process_vic_data(self, lga_data):
        """
        Preprocesses the vic source abs2016 source_data by cleaning the LGA names and appending the geometries.
        :param lga_data: the list of LGA items to be processed.
        :type lga_data:
        :return:
        :rtype:
        """
        where_clause = "{} = '2'".format(self.source.ste_code_field)
        xys = self.source.load_xy_tuples(use_name=True, where_clause=where_clause)
        lga_codes = self.source.get_lga_codes(where_clause=where_clause)
        for lga in lga_data:
            lga['ste_name'] = "Victoria"
            lga['ste_code'] = "2"

            lga_name = lga['lga_name']
            for name, xy in xys.data():
                if name.upper().startswith(lga_name.upper()):
                    lga['lga_name'] = name
                    lga['xy'] = {'x': xy[0], 'y': xy[1]}

            lga['lga_code'] = lga_codes.get(lga['lga_name'])


if __name__ == "__main__":
    gis = GIS(profile=profile)


    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        handlers=[
            logging.FileHandler(os.path.join(target_workspace, 'UpdateLgaDailyStatistics.log')),
            logging.StreamHandler()
        ]
    )

    first_day = datetime.datetime(year=2020, month=4, day=21)
    Victoria.get_daily_extracts(start_date=first_day, workspace=target_workspace)
