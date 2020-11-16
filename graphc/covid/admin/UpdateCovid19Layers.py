"""
This module contains the consolidated update task calls required to maintain the GRAPHC COVID-19 online resources.
This module will be updated as new resources are added.
A single call to the update method should trigger updates of all of the online resources where an automated update is possible.
"""
import argparse
import logging
import sys

from arcgis.gis import GIS

from graphc.covid.admin import AuthorityData2
from graphc.covid.admin import Covid19FeatureLayers
from graphc.covid.admin import Covid19FeatureLayers2


def update():
    cases = AuthorityData2.CasesByDateAndState2()
    cases.update_from_source()
    deaths = AuthorityData2.DeathsByDateAndState2()
    deaths.update_from_source()
    tests = AuthorityData2.TestsByDateAndState2()
    tests.update_from_source()

    time_stamper = Covid19FeatureLayers2.DataExtractDates()

    updater = Covid19FeatureLayers2.CrisperStatisticsByState()
    updater.update_from_source(cases=cases, deaths=deaths, tests=tests)
    time_stamper.set_update_time(updater.source)

    updater = Covid19FeatureLayers2.Covid19StatisticsByDateAndState()
    updater.update_from_source(cases=cases, deaths=deaths, tests=tests)
    time_stamper.set_update_time(updater.source)

    updater = Covid19FeatureLayers2.CrisperMovingDailyAverageCasesByDateAndState()
    updater.update_from_source(cases=cases)
    time_stamper.set_update_time(updater.source)

    updater = Covid19FeatureLayers2.CrisperMovingDailyAverageDeathsByDateAndState()
    updater.update_from_source(deaths=deaths)
    time_stamper.set_update_time(updater.source)

    updater = Covid19FeatureLayers2.CrisperMovingDailyAverageTestsByDateAndState()
    updater.update_from_source(tests=tests)
    time_stamper.set_update_time(updater.source)

    cases = AuthorityData2.CasesByDateAndPostcode()
    cases.update_from_source()
    tests = AuthorityData2.TestsByDateAndPostcode()
    tests.update_from_source()

    updater = Covid19FeatureLayers2.Covid19StatisticsByDateAndPostcode()
    updater.update_from_source(cases=cases, tests=tests)
    time_stamper.set_update_time(updater.source)

    updater = Covid19FeatureLayers2.Covid19TotalNotificationsByPostcode()
    updater.update_from_source(cases=cases)
    time_stamper.set_update_time(updater.source)

    updater = Covid19FeatureLayers2.Covid19PostcodeStatisticPolygons()
    updater.update_from_source(cases=cases)
    time_stamper.set_update_time(updater.source)

    # update authority data-sets
    notifications_by_date_and_postcode = AuthorityData2.CasesByDatePostcodeSource()
    notifications_by_date_and_postcode.update_from_source()

    updater = Covid19FeatureLayers.Covid19CaseLocationsByPostcode()
    updater.synch_with_authority(notifications_by_date_and_postcode)
    time_stamper.set_update_time(updater.service_url)

    updater = Covid19FeatureLayers2.CrisperTotalCasesByDatePostcodeSource()
    updater.update_from_source(notifications_by_date_and_postcode)
    time_stamper.set_update_time(updater.source)





    #tests_by_date_and_postcode = AuthorityData.TestsByDateAndPostcode()
    #tests_by_date_and_postcode.update_from_source()

    #notifications_by_date_and_state = AuthorityData.CasesByDateAndState()
    #notifications_by_date_and_state.update_from_source()

    #tests_by_date_and_state = AuthorityData.TestsByDateAndState()
    #tests_by_date_and_state.update_from_source()

    #death_by_date_and_state = AuthorityData.DeathsByDateAndState()
    #death_by_date_and_state.update_from_source()

    # update derived layers
    #Covid19FeatureLayers.CrisperStatisticsByState().synch_with_authority(cases=notifications_by_date_and_state,
    #                                                                     tests=tests_by_date_and_state,
    #                                                                     deaths=death_by_date_and_state)

    #Covid19FeatureLayers.Covid19NotificationsByDateAndPostcode().synch_with_authority(notifications_by_date_and_postcode)
    #Covid19FeatureLayers.Covid19TotalNotificationsByPostcode().synch_with_authority(notifications_by_date_and_postcode)

    #Covid19FeatureLayers.Covid19TestsByDateAndPostcode().synch_with_authority(tests_by_date_and_postcode)
    #Covid19FeatureLayers.Covid19TotalTestsByPostcode().synch_with_authority(tests_by_date_and_postcode)

    #statistics_by_date_and_postcode = Covid19FeatureLayers.Covid19StatisticsByDateAndPostcode()
    #statistics_by_date_and_postcode.synch_with_authority(notifications_by_date_and_postcode, tests_by_date_and_postcode)

    #statistics_by_date_and_state = Covid19FeatureLayers.Covid19StatisticsByDateAndState()
    #statistics_by_date_and_state.synch_with_authority(notifications_by_date_and_state, tests_by_date_and_state, death_by_date_and_state)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile",
                        required=False,
                        default='agol_graphc',
                        help="Local Profile used to access the ArcGIS Online instance.")
    parser.add_argument("-l", "--log",
                        required=False,
                        default=r'E:\Documents2\tmp\UpdateOnlineCovid19Layers2.log',
                        help='Log file to be created or used.')

    args = parser.parse_args()

    # configure default logging to file
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        filename=args.log
    )

    # add console logging
    console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(console_formatter)
    logging.getLogger().addHandler(console)

    # execute
    try:
        log_entry = '"{}" -p "{}" -l "{}"'.format(sys.argv[0], args.profile, args.log)

        logging.info(log_entry)
        # create GIS connection
        logging.info('Start signin using profile credentials')
        gis = GIS(profile=args.profile)
        logging.info('End signin using profile credentials')

        update()

    except Exception as e:
        print(e)
        logging.error(e, exc_info=True)
        raise
