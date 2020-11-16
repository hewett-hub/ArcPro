import os
import requests
import re
import logging
import datetime
import json
from bs4 import BeautifulSoup as soup
from word2number import w2n

from graphc.data.abs2020 import LGA2020
from graphc.da import da_arcpy

import pprint


local_json_directory = r'E:\Documents2\tmp\COVID19'


class VicDailyUpdateParser(object):
    """A helper class that parses the Victorian Daily Update for the specified date and writes the results to a JSON file."""
    def __init__(self):
        self.lga_source = LGA2020.centroids()
        self.lga_special_cases = {'COLAC OTWAY': 'COLAC-OTWAY', 'WANGARRATTA': 'WANGARATTA'}
        self._lga_codes_by_name = None
        self._lga_starts = None

    @classmethod
    def _get_total_cases(cls, data_text):
        x = re.search("Victoria is [0-9]*[,]?[0-9]+ with [0-9]*[,]?[0-9]+ new cases reported yesterday", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("Victoria is [0-9]*[,]?[0-9]+ – an increase of [a-zA-Z]+ from yesterday", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("total number of cases now at [0-9]*[,]?[0-9]+", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        logging.warning('Total Cases not found')
        return None

    @classmethod
    def _get_new_cases(cls, data_text):
        x = re.search("Victoria is [0-9]*[,]?[0-9]+ with [0-9]*[,]?[0-9]+ new cases reported yesterday", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[1])

        x = re.search("Victoria has recorded [0-9]*[,]?[0-9]+ new cases", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("Victoria is [0-9]*[,]?[0-9]+ – an increase of [a-zA-Z]+ from yesterday", data_text)
        if x:
            d = re.findall('of [a-zA-Z]+ from', x.group())[0][3:-5]
            return w2n.word_to_num(d)

        logging.warning('New Cases not found')
        return None

    @classmethod
    def _get_reclassified_cases(cls, data_text):
        x = re.search("The overall total has increased by [0-9]+, with [a-zA-Z]+ cases reclassified", data_text)
        if x:
            d = re.findall('with [a-zA-Z]+ cases', x.group())[0][5:-6]
            return w2n.word_to_num(d)

        x = re.search("[0-9]*[,]?[0-9]+ cases were reclassified", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        logging.warning('Reclassified not found')
        return None

    @staticmethod
    def _get_outbreak_linked(data_text):
        x = re.search("[0-9]+ new cases are linked to outbreaks", data_text)
        if x:
            d = re.findall('[0-9]+', x.group())
            return int(d[0])

        logging.warning('Linked to Outbreaks not found')
        return None

    @classmethod
    def _get_routine_testing(cls, data_text):
        x = re.search("[0-9]*[,]?[0-9]+ new cases have been identified through routine testing", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        logging.warning('Routine Testing not found')
        return None

    @classmethod
    def _get_under_investigation(cls, data_text):
        x = re.search("[0-9]*[,]?[0-9]+ cases are under investigation", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("[0-9]*[,]?[0-9]+ are under investigation", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        logging.warning('Under Investigation not found')
        return None

    @staticmethod
    def _get_new_deaths(data_text):
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

        logging.warning('New Deaths not found')
        return None

    @staticmethod
    def _get_total_deaths(data_text):
        x = re.search("To date, [0-9]+ people have died", data_text)
        if x:
            d = re.findall('[0-9]+', x.group())
            return int(d[0])

        logging.warning('Total Deaths not found')
        return None

    @classmethod
    def _get_community_transmission(cls, data_text):
        x = re.search(
            "There are [0-9]*[,]?[0-9]+ confirmed cases of coronavirus in Victoria that may have been acquired through community transmission",
            data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search(
            "[0-9]*[,]?[0-9]+ cases may indicate community transmission",
            data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        logging.warning('Community Transmission not found')
        return None

    @classmethod
    def _get_unknown_transmission(cls, data_text):
        x = re.search("There have been [0-9]*[,]?[0-9]+ confirmed cases of coronavirus in Victoria that have been acquired through unknown transmission",
                      data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        logging.warning('Unknown Transmission not found')
        return None

    @classmethod
    def _get_active_cases(cls, data_text):
        x = re.search("There are currently [0-9]*[,]?[0-9]+ active cases", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("[0-9]*[,]?[0-9]+ cases are currently active", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        logging.warning('Active Cases not found')
        return None

    @classmethod
    def _get_hospitalisation(cls, data_text):
        x = re.search("Currently, [0-9]*[,]?[0-9]+ people with coronavirus infection are in hospital", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("Currently [0-9]*[,]?[0-9]+ people are in hospital", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("[0-9]*[,]?[0-9]+ cases of coronavirus are in hospital", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        logging.warning('Hospitalisations Not Found')
        return None

    @classmethod
    def _get_hotel_quarantine_cases(cls, data_text):
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
    def _get_icu(cls, data_text):
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
            return cls._str_to_int(d[0])

        logging.warning('ICU Not Found')
        return None

    @classmethod
    def _get_recovered(cls, data_text):
        x = re.search("[0-9]*[,]?[0-9]+ people have recovered", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        logging.warning('Recovered Not Found')
        return None

    @classmethod
    def _get_metro(cls, data_text):
        x = re.search("there have been [0-9]*[,]?[0-9]+ in metropolitan Melbourne", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("[0-9]*[,]?[0-9]+ cases are from metropolitan Melbourne", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        logging.warning('Metro Not Found')
        return None

    @classmethod
    def _get_regional(cls, data_text):
        x = re.search("and [0-9]*[,]?[0-9]+ in regional Victoria", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("[0-9]*[,]?[0-9]+ are from regional Victoria", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        logging.warning('Regional Not Found')
        return None

    @classmethod
    def _get_males(cls, data_text):
        x = re.search("made up of [0-9]*[,]?[0-9]+ men", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("includes [0-9]*[,]?[0-9]+ men", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("include [0-9]*[,]?[0-9]+ men", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("[0-9]*[,]?[0-9]+ are men", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("made up of [0-9]*[,]?[0-9]+ males", data_text)
        d = re.findall('[0-9]*[,]?[0-9]+', x.group())
        return cls._str_to_int(d[0])

    @classmethod
    def _get_females(cls, data_text):
        x = re.search("and [0-9]*[,]?[0-9]+ women", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("and [0-9]*[,]?[0-9]+ are women", data_text)
        if x:
            d = re.findall('[0-9]*[,]?[0-9]+', x.group())
            return cls._str_to_int(d[0])

        x = re.search("and [0-9]*[,]?[0-9]+ females", data_text)
        d = re.findall('[0-9]*[,]?[0-9]+', x.group())
        return cls._str_to_int(d[0])

    @staticmethod
    def _get_tests(data_text):
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
    def _str_to_int(str_value, replace_empty=None):
        stripped = str_value.strip().replace('*', '').replace(',', '').replace('-', '')
        if stripped:
            return int(stripped)
        return replace_empty

    @staticmethod
    def _handle_not_stated_cases(lga_data):
        """In some reports 'Not Stated' is broken out separately to 'Unknown'.  This method
        converts/aggregates 'Not Stated' counts into the 'Unknown' counts."""
        ns = None
        un = None
        for lga in lga_data:
            lga_name = lga['lga_name'].upper()
            if lga_name == 'NOT STATED':
                ns = lga
            elif lga_name == 'UNKNOWN':
                un = lga

        if ns:
            if un:
                total_cases = ns.get('total_cases', 0)
                active_cases = ns.get('active_cases', 0)
                un['total_cases'] = un.get('total_cases', 0) + total_cases
                un['active_cases'] = un.get('active_cases', 0) + active_cases
                lga_data.remove(ns)
            else:
                ns['lga_name'] = 'UNKNOWN'
                ns['lga_code'] = 'UNK'

    @staticmethod
    def _handle_interstate_overseas_cases(lga_data):
        """In some reports a combinded 'Interstate/Overseas' statistic is reported.  This method converts these
        cases to 'Interstate' for consistency of keys, although it should be noted that this will bias the sources.  These values
        may be updated later if better information becomes available."""

        interstate_cases = 0
        interstate_active = 0
        interstate_lga = None
        for lga in lga_data:
            name = lga['lga_name'].upper()
            if name in ['INTERSTATE/OVERSEAS', 'TUMBARUMBA', 'INTERSTATE']:
                interstate_cases += lga.get('total_cases', 0)
                active = lga.get('active_cases', None)
                if active:
                    interstate_active += active
                if name == 'INTERSTATE':
                    interstate_lga = lga
                else:
                    lga_data.remove(lga)

        # if we have any interstate values....
        if interstate_cases or interstate_active:
            if interstate_lga:
                # update the existing interstate item
                interstate_lga['total_cases'] = interstate_cases
                interstate_lga['active_cases'] = interstate_active if interstate_active else None
            else:
                # or create a new one if it doesn't exist...
                lga_data.append({'lga_name': 'INTERSTATE',
                                 'lga_code': 'IS',
                                 'total_cases': interstate_cases,
                                 'active_cases': interstate_active if interstate_active else None})
        return lga_data

    def _get_lga_codes_by_name(self):
        if not self._lga_codes_by_name:
            self._lga_codes_by_name = da_arcpy.load_indexed_values(source=self.lga_source._source,
                                                                   id_field=self.lga_source.lga_name_field,
                                                                   value_field=self.lga_source.lga_code_field,
                                                                   where_clause="{} = '2'".format(self.lga_source.ste_code_field))

        return self._lga_codes_by_name

    def _get_lga_starts(self):
        result = []
        source = self._get_lga_codes_by_name()
        for lga_name in source.keys():
            parts = re.split('[ -]', lga_name.upper())
            result.append(parts[0])

        return result

    def _clean_lga_ids(self, lga):
        lga_control = self._get_lga_codes_by_name()

        lga_name = lga['lga_name']

        lga_name = lga_name.replace('*', '').replace(':', '')  # replace dirty characters.
        lga_name = ' '.join(lga_name.split())  # remove multi-spaces in mid name.
        lga_name = lga_name.strip()  # remove white space and return characters at start and end of name
        lga_name = lga_name.upper()  # convert to upper to prevent capitalisation inconsistencies.

        if lga_name in self.lga_special_cases:
            lga_name = self.lga_special_cases[lga_name]

        if lga_name == 'UNDER INVESTIGATION':
            lga['lga_name'] = 'UNKNOWN'
            lga['lga_code'] = 'UNK'
            return lga

        if lga_name == 'UNKNOWN':
            lga['lga_name'] = 'UNKNOWN'
            lga['lga_code'] = 'UNK'
            return lga

        if lga_name == 'INTERSTATE':
            lga['lga_name'] = 'INTERSTATE'
            lga['lga_code'] = 'IS'
            return lga

        if lga_name == 'OVERSEAS':
            lga['lga_name'] = 'OVERSEAS'
            lga['lga_code'] = 'OS'
            return lga

        for name, code in lga_control.items():
            uc_name = name.upper()
            if uc_name.startswith(lga_name):
                lga['lga_name'] = name
                lga['lga_code'] = code
                return lga

    @classmethod
    def _try_parse_structured_lga_table(cls, data):
        table = data.findAll('table')
        lga_stats = []
        if table:
            rows = table[0].tbody.findAll('tr')
            for row in rows:
                items = row.findAll('td')
                # some tables have headers within the table content and empty rows.
                # Only process if there are cells in the row and the first cell not 'LGA'
                # and the number of items is greater than 1.
                if items and items[0].text.strip().upper() not in ['LGA', 'LOCAL GOVERNMENT AREA']:
                    if len(items) > 2:
                        stats = {
                            'lga_name': items[0].text.strip(),
                            'total_cases': cls._str_to_int(items[1].text, 0),
                            'active_cases': cls._str_to_int(items[2].text, 0)
                        }
                        lga_stats.append(stats)
                    elif len(items) == 2:
                        stats = {
                            'lga_name': items[0].text.strip(),
                            'total_cases': cls._str_to_int(items[1].text, 0),
                            'active_cases': None
                        }
                        lga_stats.append(stats)

        return lga_stats

    def _try_parse_paragraph_table(self, data):
        split_strings = ['(C) -', '(S) -', '(RC) -',
                         '(C)', '(S)', '(RC)', '(A)',
                         ' - ', '    ', ' -']
        idents = self._get_lga_starts()
        # get all paras in page
        paras = data.findAll('p')
        table = None
        # find last para that contains a ref to Stonnington followed by a number.  Stonnington was first entry in earliest reports
        # so should be in all subsequent reports with LGA totals.
        lga_stats = []
        for p in paras:
            para_text = p.text.replace(u'\xa0', ' ')
            para_parts = re.split('[ -]', para_text.upper())
            test_value = para_parts[0]
            if test_value in idents:
                # if re.search("Stonnington .+ [0-9]+", para_text, re.IGNORECASE):
                table = para_text

                rows = table.strip().split('\n')
                for row in rows:
                    parts = self._split_string(row, split_strings)
                    stats = {
                        'lga_name': parts[0],
                        'total_cases': int(parts[1].strip()),
                        'active_cases': None
                    }
                    lga_stats.append(stats)

        return lga_stats

    @staticmethod
    def _split_string(string_value, split_strings):
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

    def _get_lga_stats(self, data):
        result = self._try_parse_structured_lga_table(data)
        if not result:
            result = self._try_parse_paragraph_table(data)

        if not result:
            logging.warning('Could not find LGA statistics')
            return []

        # remove the Totals items.  They are available in the full report or can
        # be recalculated at need.
        for lga in result:
            if lga['lga_name'].upper().startswith('TOTAL'):
                result.remove(lga)

        for lga in result:
            self._clean_lga_ids(lga=lga)

        self._handle_not_stated_cases(result)
        self._handle_interstate_overseas_cases(result)

        # final lga recognition check - prevents unexpected/unhandled changes to LGA table structures causing bad
        # data uploads.
        for lga in result:
            if 'lga_code' not in lga:
                raise RuntimeError('Bad LGA Name: ' + lga['lga_name'])

        return result

    def _parse_daily_update(self, daily_update_data):
        logging.info('Processing: ' + daily_update_data.url)
        result = {}

        page_soup = soup(daily_update_data.content, 'html5lib')
        data = page_soup.findAll('div',
                                 {'class': 'field field--name-field-dhhs-rich-text-text field--type-text-long field--label-hidden field--item'})[0]
        data_text = data.text.replace(u'\xa0', ' ')

        result['source'] = daily_update_data.url
        result['total_cases'] = self._get_total_cases(data_text)
        result['new_cases'] = self._get_new_cases(data_text)
        result['reclassified'] = self._get_reclassified_cases(data_text)
        result['outbreak_linked'] = self._get_outbreak_linked(data_text)
        result['routine_testing'] = self._get_routine_testing(data_text)
        result['under_investigation'] = self._get_under_investigation(data_text)
        result['new_deaths'] = self._get_new_deaths(data_text)
        result['total_deaths'] = self._get_total_deaths(data_text)
        result['unknown_transmission'] = self._get_unknown_transmission(data_text)
        result['community_transmission'] = self._get_community_transmission(data_text)
        result['hotel_quarantine_cases'] = self._get_hotel_quarantine_cases(data_text)
        result['active_cases'] = self._get_active_cases(data_text)
        result['hospitalisations'] = self._get_hospitalisation(data_text)
        result['icu'] = self._get_icu(data_text)
        result['recovered'] = self._get_recovered(data_text)
        result['metro'] = self._get_metro(data_text)
        result['regional'] = self._get_regional(data_text)
        result['males'] = self._get_males(data_text)
        result['females'] = self._get_females(data_text)
        result['tests'] = self._get_tests(data_text)
        result['lgas'] = self._get_lga_stats(data)

        return result

    def get_daily_extract(self, working_date, base_url=r'https://www.dhhs.vic.gov.au/'):
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
        logging.info('Attempting to find daily update for {}'.format(working_date))
        day = working_date.strftime('%d').lstrip('0')
        month = working_date.strftime('%B')
        year = working_date.strftime('%Y')
        date_tag = working_date.strftime('%Y%m%d')

        url_date_string = '{}-{}-{}'.format(day, month, year)
        source_url = base_url + r'/coronavirus-update-victoria-' + url_date_string
        r = requests.get(source_url)
        if r.status_code == 200:
            result = self._parse_daily_update(r)
            result['date_code'] = date_tag
            return result

        weekday = working_date.strftime('%A')
        url_date_string = '{}-{}-{}'.format(weekday, day, month)
        source_url = base_url + r'/coronavirus-update-victoria-' + url_date_string
        r = requests.get(source_url)
        if r.status_code == 200:
            result = self._parse_daily_update(r)
            result['date_code'] = date_tag
            return result

        url_date_string = '{}-{}-{}-{}'.format(weekday, day, month, year)
        source_url = base_url + r'/coronavirus-update-victoria-' + url_date_string
        r = requests.get(source_url)
        if r.status_code == 200:
            result = self._parse_daily_update(r)
            result['date_code'] = date_tag
            return result

        day = working_date.strftime('%d')
        url_date_string = '{}-{}-{}'.format(day, month, year)
        source_url = base_url + r'/coronavirus-update-victoria-' + url_date_string
        r = requests.get(source_url)
        if r.status_code == 200:
            result = self._parse_daily_update(r)
            result['date_code'] = date_tag
            return result

        url_date_string = '{}-{}'.format(day, month)
        source_url = base_url + r'/coronavirus-update-victoria-' + url_date_string
        r = requests.get(source_url)
        if r.status_code == 200:
            result = self._parse_daily_update(r)
            result['date_code'] = date_tag
            return result

        url_date_string = '{}-{}-{}'.format(weekday, day, month)
        source_url = base_url + r'/media-release-coronavirus-update-victoria-' + url_date_string
        r = requests.get(source_url)
        if r.status_code == 200:
            result = self._parse_daily_update(r)
            result['date_code'] = date_tag
            return result

        logging.warning('Report not found for: {}-{}-{}'.format(day, month, year))
        return None

    def get_daily_extracts(self, start_date, json_files_directory):
        working_date = start_date
        data_files = []
        while working_date < datetime.datetime.now():
            file_date_string = working_date.strftime('%Y%m%d')
            file_path = os.path.join(json_files_directory, 'vic_' + file_date_string + '.json')
            if not os.path.exists(file_path):
                daily_extract = self.get_daily_extract(working_date)
                if daily_extract:
                    daily_extract['date_code'] = file_date_string
                    with open(file_path, 'w') as f:
                        f.write(json.dumps(daily_extract, indent=4, sort_keys=True))

                    logging.info("Extract Created: {}".format(file_path))
                    data_files.append(file_path)
            else:
                data_files.append(file_path)

            working_date += datetime.timedelta(days=1)

        return data_files


class VicData(object):
    def __init__(self):
        self.update_parser = VicDailyUpdateParser()
        self.lga_features = LGA2020.centroids()
        self.start_date = datetime.datetime(2020, 3, 23)
        self.working_directory = local_json_directory

    def daily_cases_by_lga(self):
        """
        Returns the daily new and total cases by LGA.  LGAs will only be added to the result once they have at least one case.
        :return:[{'lga_name': str, 'lga_code': str, 'date_code': str, 'cases': int, 'total_cases': int}]
        :rtype:
        """

        result = []
        source_files = self.update_parser.get_daily_extracts(self.start_date, self.working_directory)
        for data_file in source_files:
            with open(data_file, 'r') as content:
                json_data = json.load(content)
                date_code = json_data['date_code']
                lga_data = json_data.get('lgas', [])
                for lga in lga_data:
                    lga['date_code'] = date_code
                    result.append(lga)

        self._calc_daily_deltas(result, key_name='lga_name', value_name='total_cases', delta_name='cases')

        return result

    @staticmethod
    def _calc_daily_deltas(lga_data, key_name, value_name, delta_name):
        """
        Calculates the 'cases' value for each lga by subtracting the previous total from the current.
        :param lga_data: list of lga items which contain, at a minimum, lga_name and date_code.
        :type lga_data:
        :return:
        :rtype:
        """

        working = {}
        for item in lga_data:
            lga_name = item[key_name]
            working_items = working.get(lga_name, None)
            if not working_items:
                working_items = []
                working[lga_name] = working_items
            working_items.append(item)

        for lga_items in working.values():
            sorted_items = sorted(lga_items, key=lambda k: k['date_code'])

            prev_value = 0
            for lga_item in sorted_items:
                current_value = lga_item[value_name]
                lga_item[delta_name] = current_value - prev_value
                prev_value = current_value

        return lga_data


if __name__ == "__main__":
    workspace = r'E:\Documents2\tmp\COVID19'
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        filename=os.path.join(workspace, 'VicSourceData.log')
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # add the handler to the root logger
    logging.getLogger().addHandler(console)

    data_source = VicData()
    out = data_source.daily_cases_by_lga()
    pprint.pprint(out)

    #test_data = daily_lga_totals(lga_centroids=lga_centroid_source)
    # pprint.pprint(test_data)


