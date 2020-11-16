import logging
import sys
import pprint

from arcgis.gis import GIS

from graphc.covid.admin import DataEngine


#from graphc.covid.source import JHU_SourceData
#from graphc.covid.source import covid19data_SourceData
#from graphc.data.pois import StateCapitals
#from graphc.data.abs2016 import POA2016

#from graphc.covid.admin import statistics

#from graphc.covid.admin.Covid19FeatureLayers import Covid19CaseLocationsByPostcode
from graphc.covid.admin.Covid19FeatureLayers2 import CrisperStatisticsByState
#from graphc.covid.admin.Covid19FeatureLayers3 import Covid19PostcodeStatisticPolygons
#from graphc.covid.admin import AuthorityData2

def do_test():
    #jhu_cases = JHU_SourceData.JhuCasesData()
    #jhu_deaths = JHU_SourceData.JhuDeathsData()
    #nsw_cases = NSW_SourceData.NswNotificationData()
    #nsw_tests = NSW_SourceData.NswTestData()
    #nsw_ages = NSW_SourceData.NswTestsAgeDistributionData()
    #poa_points = POA2016.centroids()
    #state_points = StateCapitals()

    #source = covid19data_SourceData.COVID_AU_state()'
    #authority = AuthorityData2.CasesByDateAndPostcode()
    #target = Covid19PostcodeStatisticPolygons()
    #result = target.update_from_source(authority)
    #source = DataEngine.CasesByDatePostcodeAndSource()
    #result = source.load()
    #tester = Covid19StatisticsByDateAndState()
    #result = tester.update_from_source()
    #DataExtractDates().set_update_time(tester.source)
    #authority = AuthorityData2.CasesByDatePostcodeSource()
    #tester = Covid19CaseLocationsByPostcode()
    #result = tester.synch_with_authority(authority)

    # tester = Covid19FeatureLayers2.CrisperTotalCasesByDatePostcodeSource()
    # result = tester.update_from_source()
    #result = tester.update_from_source(nsw_source=nsw_tests, geometry_source=state_points)
    tester = CrisperStatisticsByState()
    result = tester.update_from_source()
    pprint.pprint(result)

    #tester = AuthorityData2.CasesByDateAndState()
    #result = tester.update_from_source(jhu_source=jhu_cases, nsw_source=nsw_cases, geometry_source=state_points)
    #pprint.pprint(result)

    #tester = AuthorityData2.DeathsByDateAndState()
    #result = tester.update_from_source(jhu_source=jhu_deaths, geometry_source=state_points)
    #pprint.pprint(result)

    #tester = AuthorityData2.TestsByDateAndPostcode()
    #result = tester.update_from_source(nsw_source=nsw_tests, geometry_source=poa_points)
    #pprint.pprint(result)

    #tester = AuthorityData2.CasesByDateAndPostcode()
    #result = tester.update_from_source(nsw_source=nsw_cases, geometry_source=poa_points)
    #pprint.pprint(result)

    #tests_authority = AuthorityData.NotificationsByDateAndState()
    # nsw_source = NSW_SourceData.NswTestData()
    #result = auth_data.cumulative_notifications_by_date_and_postcode()
    #result = auth_data.update_from_source()
    # tester = Covid19FeatureLayers.Covid19NotificationsByDateAndPostcode()
    # tester.service_url = r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Notifications_TimeSeries_by_Postcode/FeatureServer/0'
    #auth_case_data = AuthorityData.CasesByDateAndState()
    #tester = Covid19FeatureLayers.Covid19StatisticsByDateAndState()
    #result = tester.synch_with_authority(AuthorityData.CasesByDateAndState(), AuthorityData.TestsByDateAndState(), AuthorityData.DeathsByDateAndState())
    #tester = Covid19FeatureLayers.Covid19StatisticsByDateAndPostcode()
    #result = tester.synch_with_authority(auth_case_data, auth_test_data)
    #pprint.pprint(result)
    #tester = Covid19FeatureLayers.Covid19NotificationsByDateAndState()
    #result = tester.synch_with_authority(auth_data)
    #auth_data.update_from_source()
    #tester = Covid19FeatureLayers.Covid19CaseLocationsByPostcode()
    #tester = Covid19FeatureLayers.Covid19TotalNotificationsByPostcode()
    #result = tester.synch_with_authority(authority=auth_data)

    #source = JHU_SourceData.JhuCasesData()
    #result = source.source_data()

    #pprint.pprint(result)


if __name__ == "__main__":
    log_file = r'E:\Documents2\tmp\dev_tester.log'
    profile = 'agol_graphc'

    # configure default logging to file
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.INFO,
        filename=log_file
    )

    # add console logging
    console_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(console_formatter)
    logging.getLogger().addHandler(console)

    # execute
    try:
        logging.info('------------------------------------------------------------------')
        log_entry = '{}'.format(sys.argv[0])

        logging.info(log_entry)
        # create GIS connection
        logging.info('Start signin using profile credentials')
        gis = GIS(profile=profile)
        logging.info('End signin using profile credentials')

        do_test()

    except Exception as e:
        print(e)
        logging.error(e, exc_info=True)
        raise