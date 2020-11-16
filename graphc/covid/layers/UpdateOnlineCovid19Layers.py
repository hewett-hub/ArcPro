"""
This module contains the consolidated update task calls required to maintain the GRAPHC COVID-19 online resources.
This module will be updated as new resources are added.
A single call to the update method should trigger updates of all of the online resources where an automated update is possible.
"""
import argparse
import logging
import sys

from arcgis.gis import GIS

from graphc.covid.layers import Covid19CaseLocationsByPostcode, Covid19NotificationsByDateAndPostcode, Covid19TestsByDateAndPostcode, \
    Covid19TotalNotificationsByPostcode, Covid19TotalTestsByPostcode


def update():
    """
    the update function contains the configuration settings and calls for the individual update tasks to be performed.
    :return:
    :rtype:
    """
    task1 = Covid19NotificationsByDateAndPostcode.UpdateFromSourceTask()
    task1.nsw_notifications_source.source_url = \
        r'https://data.nsw.gov.au/data/dataset/aefcde60-3b0c-4bc0-9af1-6fe652944ec2/resource/21304414-1ff1-4243-a5d2-f52778048b29/download/' \
        r'covid-19-cases-by-notification-date-and-postcode-local-health-district-and-local-government-area.csv'
    task1.feature_service.service_url = \
        r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID19_Notifications_by_Date_and_Postcode/FeatureServer/0'
    logging.info('Updating: ' + task1.feature_service.service_url)
    task1.full_update()

    task2 = Covid19TestsByDateAndPostcode.UpdateFromSourceTask()
    task2.nsw_tests_source.source_url = \
        r'https://data.nsw.gov.au/data/dataset/60616720-3c60-4c52-b499-751f31e3b132/resource/945c6204-272a-4cad-8e33-dde791f5059a/download/' \
        r'covid-19-tests-by-date-and-postcode-local-health-district-and-local-government-area.csv'
    task2.feature_service.service_url = \
        r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Tests_by_Date_and_Postcode/FeatureServer/0'
    task2.postcode_feature_source = task1.postcode_feature_source
    logging.info('Updating: ' + task2.feature_service.service_url)
    task2.full_update()

    task3 = Covid19CaseLocationsByPostcode.UpdateTask()
    task3.source_data = task1.feature_service
    task3.feature_service.service_url = \
        r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/Case_Locations_By_Postcode/FeatureServer/0'
    logging.info('Updating: ' + task3.feature_service.service_url)
    task3.update()

    task4 = Covid19TotalNotificationsByPostcode.UpdateTask()
    task4.source_data = task1.feature_service
    task4.feature_service.service_url =  \
        r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Total_Notifications_by_Postcode/FeatureServer/0'
    logging.info('Updating: ' + task4.feature_service.service_url)
    task4.update()

    task5 = Covid19TotalTestsByPostcode.UpdateTask()
    task5.source_data = task2.feature_service
    task5.feature_service.service_url = \
        r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Total_Tests_by_Postcode/FeatureServer/0'
    logging.info('Updating: ' + task5.feature_service.service_url)
    task5.update()

"""    task6 = Covid19CumulativeNotificationsByDateAndPostcode.UpdateTask()
    task6.source_data = task1.feature_service
    task6.feature_service.service_url = \
        r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Cumulative_Notifications_by_Date_and_Postcode/FeatureServer/0'
    logging.info('Updating: ' + task6.feature_service.service_url)
    task6.update()"""

"""task7 = Covid19CumulativeTestsByDateAndPostcode.UpdateTask()
    task7.source_data = task2.feature_service
    task7.feature_service.service_url = \
        r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Cumulative_Tests_by_Date_and_Postcode/FeatureServer/0'
    logging.info('Updating: ' + task7.feature_service.service_url)
    task7.update()"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile",
                        required=False,
                        default='agol_graphc',
                        help="Local Profile used to access the ArcGIS Online instance.")
    parser.add_argument("-l", "--log",
                        required=False,
                        default=r'E:\Documents2\tmp\UpdateOnlineCovid19Layers.log',
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