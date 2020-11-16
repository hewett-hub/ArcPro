import datetime
import logging
import argparse
import copy
import sys

from arcgis.gis import GIS
from arcgis.features import FeatureLayer

from graphc.covid.source.VIC_SourceData import VicData
from graphc.covid.source.NSW_SourceData import NswNotificationData
from graphc.data.abs2019 import LGA2019
from graphc.data.abs2020 import LGA2020
from graphc.da import da_arcpy


default_service_url = r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/DailyCovid19CasesByLga/FeatureServer/0'


class DailyCovid19CasesByLGA(object):
    def __init__(self, service_url=default_service_url):
        self.layer = FeatureLayer(service_url)
        self.lga_code_field = 'LGA_CODE'
        self.lga_name_field = 'LGA_NAME'
        self.lga_version_field = 'LGA_Version'
        self.date_field = 'Date'
        self.date_code_field = 'DateCode'
        self.cases_field = 'Cases'
        self.total_cases_field = 'TotalCases'
        self.date_code_format = '%Y%m%d'

    def query(self, where_clause):
        return self.layer.query(where=where_clause)

    def update(self, rows, allow_deletes=False):
        """
        updates the feature service by updating or adding the submitted rows.  Rows are identified by date_code and postcode.
        Date values are derived from the date_code values.
        Existing XYs are not updated, submitted xys are used if rows are added.
        :param rows: [{'lga_name': str, 'lga_code': str, 'date_code': str, 'cases': int, 'total_cases': int, 'xy': {'x': float, 'y': float}}]
        :type rows: [dict]
        :param allow_deletes: If set to True any records not found in the source rows will be deleted.  Default=False
        :type allow_deletes: bool
        :return:
        :rtype:
        """

        # build lookup from submitted rows:
        items = {}
        for row in rows:
            key = '{}_{}'.format(row['lga_code'], row['date_code'])
            items[key] = row

        deletes = []
        updates = []
        query_result = self.layer.query()
        for row in query_result:
            lga_code = row.attributes[self.lga_code_field]
            date_code = row.attributes[self.date_code_field]
            key = '{}_{}'.format(lga_code, date_code)
            if allow_deletes and key not in items:
                deletes.append(row.attributes[query_result.object_id_field_name])

            item = items.pop(key, None)
            if item:
                update_required = False
                if row.attributes[self.cases_field] != item['cases']:
                    row.attributes[self.cases_field] = item['cases']
                    update_required = True
                if row.attributes[self.total_cases_field] != item['total_cases']:
                    row.attributes[self.total_cases_field] = item['total_cases']
                    update_required = True
                if update_required:
                    updates.append(row)

        # any remaining data_models items are new records
        adds = []
        new_items = items.values()
        if new_items:
            for new_item in new_items:
                date = datetime.datetime.strptime(new_item['date_code'], '%Y%m%d')
                row = {"attributes":
                           {self.date_field: date,
                            self.lga_name_field: new_item['lga_name'],
                            self.lga_code_field: new_item['lga_code'],
                            self.lga_version_field: new_item['lga_version'],
                            self.date_code_field: new_item['date_code'],
                            self.total_cases_field: new_item['total_cases'],
                            self.cases_field: new_item['cases']},
                       "geometry": new_item['xy']}
                adds.append(row)

        logging.info('Updating: {}'.format(self.layer.url))
        logging.info('ADDS: {}'.format(len(adds)))
        logging.info('DELETES: {}'.format(len(deletes)))
        logging.info('UPDATES: {}'.format(len(updates)))
        if updates or adds or deletes:
            return self.layer.edit_features(updates=updates, adds=adds, deletes=str(deletes))
        else:
            return None

    def format_date_string(self, date_string, in_format):
        """
        Reformats the submitted date or datetime string to the correct format for the date_code field
        :type date_string: str
        :param in_format: the format string of the submitted date_string.  eg: '%Y-%m-%d'
        :type in_format: str
        :return: The reformatted date_string
        :rtype: str
        """

        dt = datetime.datetime.strptime(date_string, in_format)
        return dt.strftime(self.date_code_format)


class UpdateFromSourceTask(object):
    """
    An update task encapsulating all of the required input parameters and structures.
    Upon initial creation the defaults are set.
    Defaults can be modified after creation using through the class properties.
    """
    def __init__(self, service_url=default_service_url):
        self.target = DailyCovid19CasesByLGA(service_url)
        self.nsw_source = NswNotificationData()
        self.vic_source = VicData()
        self.lga2019 = LGA2019.centroids()
        self.lga2020 = LGA2020.centroids()

    def _get_nsw_source(self):
        # get the source data
        source_data = self.nsw_source.source_data()

        # sort rows by date and lga_code.
        sorted_data = sorted(source_data, key=lambda x: (x[self.nsw_source.lga_code_field], x[self.nsw_source.date_field]))

        # convert to input rows
        xys = da_arcpy.load_xy_geometries(source=self.lga2019._source,
                                          id_field=self.lga2019.lga_code_field,
                                          where_clause="{} = '1'".format(self.lga2019.ste_code_field))

        totals = {}
        wkg = {}
        for row in sorted_data:
            date_str = self.target.format_date_string(date_string=row[self.nsw_source.date_field], in_format=self.nsw_source.csv_date_format)
            lga_code = row[self.nsw_source.lga_code_field]
            if not lga_code:
                lga_code = '00000'

            total = totals.get(lga_code, 0) + 1
            totals[lga_code] = total

            key = '{}_{}'.format(lga_code, date_str)
            wkg_item = wkg.get(key, None)
            if wkg_item:
                wkg_item['cases'] += 1
                wkg_item['total_cases'] = total
            else:
                lga_name = row[self.nsw_source.lga_name_field]
                wkg_item = {'lga_code': lga_code,
                            'lga_name': lga_name,
                            'date_code': date_str,
                            'cases': 1,
                            'total_cases': total,
                            'lga_version': '2019',
                            'xy': xys.get(lga_code, None)}
                wkg[key] = wkg_item
        return wkg.values()

    def update_nsw(self):
        source = self._get_nsw_source()
        return self.target.update(rows=source, allow_deletes=False)

    def _get_vic_source(self):
        source_data = self.vic_source.daily_cases_by_lga()

        xys = da_arcpy.load_xy_geometries(source=self.lga2020._source,
                                          id_field=self.lga2020.lga_code_field,
                                          where_clause="{} = '2'".format(self.lga2020.ste_code_field))

        for source_item in source_data:
            source_id = source_item['lga_code']
            source_item['xy'] = xys.get(source_id, None)
            source_item['lga_version'] = '2020'

        return source_data

    def update_vic(self):
        source = self._get_vic_source()
        return self.target.update(rows=source, allow_deletes=False)

    def full_update(self):
        """
        Performs a full update from the source data, inculding adds, deletes and updates.
        A combination of the date_code and postcode are used as the full identifier.
        :return:
        :rtype:
        """
        unconsolidated = []
        unconsolidated.extend(self._get_nsw_source())
        unconsolidated.extend(self._get_vic_source())

        consolidated = {}
        for item in unconsolidated:
            date_code = item['date_code']
            lga_code = item['lga_code']
            key = '{}_{}'.format(lga_code, date_code)
            existing = consolidated.get(key)
            if existing:
                existing['cases'] += item['cases']
                existing['total_cases'] += item['total_cases']
            else:
                consolidated[key] = copy.deepcopy(item)  # use a copy so original source not altered.

        return self.target.update(rows=consolidated.values(), allow_deletes=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile",
                        required=False,
                        default='agol_graphc',
                        help="Local Profile used to access the ArcGIS Online instance.")
    parser.add_argument("-l", "--log",
                        required=False,
                        default=r'E:\Documents2\tmp\DailyCovid19CasesByPostcode.log',
                        help='Log file to be created or used.')
    parser.add_argument("-u", "--update",
                        action='store_true',
                        help='If specified, update from source will be performed using system defaults.')
    parser.add_argument("-t", "--target",
                        required=False,
                        default=default_service_url,
                        help='The full url to the target feature service layer(including layer id).')

    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        filename=args.log
    )

    try:
        log_entry = '"{}" -p "{}" -l "{}" -t "{}"'.format(sys.argv[0], args.profile, args.log, args.target)
        if args.update:
            log_entry += ' -u'

        logging.info(log_entry)
        # create GIS connection
        logging.info('Start signin using profile credentials')
        gis = GIS(profile=args.profile)
        logging.info('End signin using profile credentials')

        if args.update:
            task = UpdateFromSourceTask(args.target)
            task.full_update()

    except Exception as e:
        print(e)
        logging.error(e, exc_info=True)
        raise
