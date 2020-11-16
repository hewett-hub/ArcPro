import os
import json
import logging
import pprint
import argparse
from arcgis.gis import GIS

from graphc.data.abs2016 import POA2016
from graphc.da.source_data import covid_nsw
from graphc.da.agol import covid
from graphc.data_models.covid import DailyRegionStatistics


def update_daily_testing_by_postcode():
    daily_postcode_stats = DailyRegionStatistics()

    source = covid_nsw.NswTestData()
    source.add_postcode_tests(data_model=daily_postcode_stats, name='tests')

    daily_postcode_stats.calculate_cumulative_daily_totals(['tests'])
    postcode_centroid_xys = POA2016.centriods().load_xy_tuples()

    target = covid.DailyCovid19TestingByPostcode()
    update_rows = daily_postcode_stats.get_rows(['tests', 'total_tests'])
    pprint.pprint(update_rows)
    cleaned_data = target.pre_process_data(raw_data=update_rows,
                                           geometry_source=postcode_centroid_xys,
                                           postcode_key='region_id',
                                           date_str_key='date',
                                           date_format=source.csv_date_format,
                                           tests_key='tests',
                                           total_tests_key='total_tests')
    pprint.pprint(cleaned_data)



class DailyCovid19TestingByPostcodeUpdater(object):
    def __init__(self, target=covid.DailyCovid19TestingByPostcode(), nsw_source=covid_nsw.NswTestData(), geometry_source=POA2016.centriods()):
        self.target = target
        self.nsw_source = nsw_source
        self.geometry_source = geometry_source

    def update(self):
        logging.info('Updating: ' + self.target.layer.url)
        nsw_source = self.nsw_source.daily_postcode_statistics()
        with open(os.path.join(workspace, 'nsw_tests_source.json'), 'w') as f:
            f.write(json.dumps(nsw_source, indent=4))
        cleaned_data = self.target.pre_process_data(raw_data=nsw_source, geometry_source=self.geometry_source)
        self.target.update_data(data=cleaned_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile",
                        required=False,
                        help="Local Profile used to access the ArcGIS Online instance.",
                        default='agol_graphc')
    parser.add_argument("-w", "--workspace",
                        required=False,
                        help='Workspace folder for log and json dumps.',
                        default=r'E:\Documents2\tmp')

    args = parser.parse_args()

    workspace = args.workspace
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        filename=os.path.join(workspace, 'UpdateCovidData.log')
    )

    logging.info('Profile: ' + args.profile)

    gis = GIS(profile=args.profile)

    update_daily_testing_by_postcode()
