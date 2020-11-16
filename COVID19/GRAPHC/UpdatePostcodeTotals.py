import arcpy
import csv
import urllib.request
import io
import logging
import datetime
import copy


# CSV Source: https://data.gov.au/dataset/ds-nsw-aefcde60-3b0c-4bc0-9af1-6fe652944ec2/details?q=covid
nsw_source = r'https://data.nsw.gov.au/data/dataset/aefcde60-3b0c-4bc0-9af1-6fe652944ec2/resource/21304414-1ff1-4243-a5d2-f52778048b29/download/covid-19-cases-by-notification-date-and-postcode-local-health-district-and-local-government-area.csv'
count_by_postcode_target = r'\\mhsdata\mhs\workgroups\rsph\GRAPHC\SdeConnections\dot234_Publishing_COVID19.sde\TotalCasesByPostcode'
individual_cases_target = r'\\mhsdata\mhs\workgroups\rsph\GRAPHC\SdeConnections\dot234_Publishing_COVID19.sde\IndividualCasesByPostcode'
poa2sa3_source = r'\\mhsdata\mhs\workgroups\rsph\GRAPHC\RESOURCES\Data\abs\Correspondences\POA2016toSA32016\POA2016toSA32016.csv'
sa3_2016_centroid_counts_target = r'\\mhsdata\mhs\workgroups\rsph\GRAPHC\SdeConnections\dot234_Publishing_COVID19.sde\SA3_2016_CentroidCounts_covid19'
sa3_2016_boundary_counts_target = r'\\mhsdata\mhs\workgroups\rsph\GRAPHC\SdeConnections\dot234_Publishing_COVID19.sde\SA3_2016_BoundariesCount_covid19'
sa3_lana_attributes_target = r'\\mhsdata\mhs\workgroups\rsph\GRAPHC\SdeConnections\dot234_Publishing_COVID19.sde\LANA_Attribs_Covid'
postcode_index = 1
date_index = 0
date_now = datetime.datetime.now()


def parse_nsw_source():
    """
    Parses the NSW source source_data into a list of dictionary items.
    :return: returns a list of dictionary objects with one item for each row.
    :rtype: [{'date_string': str, 'date': datetime, 'postcode': int, 'report_age': int}]
    """
    result = []
    logging.info('Getting NSW source_data: ' + nsw_source)
    with urllib.request.urlopen(nsw_source) as response:
        content = response.read().decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            postcode = row[postcode_index]
            if postcode:
                postcode = postcode.strip()
            if len(postcode) <= 4:
                date_string, date_value, days_since_date = parse_date(row[date_index])
                result_item = {'date_string': date_string, 'date': date_value, 'postcode': postcode, 'report_age': days_since_date}
                result.append(result_item)

    return result


def parse_date(date_value):
    """
    Parses a date in format "dd-mm-yy" or "dd-mm-yyyy" into a date string and a datetime object.
    :param date_value: The date string to be parsed.
    :type date_value: str
    :return: a date string (yyyymmdd) and a datetime object
    :rtype: str, datetime
    """
    if '-' in date_value:
        year_part, month_part, day_part = date_value.split('-')
    else:
        day_part, month_part, year_part = date_value.split('/')

    year_length = len(year_part)
    if year_length == 2:
        year_part = '20' + year_part
    elif year_length != 4:
        raise RuntimeError('Invalid year value: ' + date_value)

    date_string = year_part + month_part.zfill(2) + day_part.zfill(2)
    date_result = datetime.datetime(int(year_part), int(month_part), int(day_part))
    days_since_report = (date_now - date_result).days

    return date_string, date_result, days_since_report


# deprecated during upgrates to support individual incident entries
# replaced with parse_nsw_source and get_nsw_totals2
def get_nsw_totals(postcode_counts):
    logging.info('Getting NSW source_data: ' + nsw_source)
    with urllib.request.urlopen(nsw_source) as response:
        content = response.read().decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            postcode = row[postcode_index]
            if postcode:
                postcode = postcode.strip()
            if postcode in postcode_counts:
                postcode_counts[postcode] += 1
            elif len(postcode) <= 4:
                postcode_counts[postcode] = 1


def get_counts_by_postcode(postcode_list, postcode_counts):
    """
    Appends the counts of postcodes in the postcode_list to the postcode_counts.
    :param postcode_list: A list of postcode string values
    :type postcode_list: [str]
    :param postcode_counts: A dictionary of postcode counts {postcode: count}
    :type postcode_counts: {str: int}
    :return: the updated postcode counts dictionary.
    :rtype: {str: int}
    """
    for postcode in postcode_list:
        if postcode in postcode_counts:
            postcode_counts[postcode] += 1
        else:
            postcode_counts[postcode] = 1


def get_postcode_points():
    """
    Creates a lookup dictionary of {postcode: (x,y)} pairs from the count by postcode target.  The
    count by postcode target is assumed to have a point for every known postcode.
    :return: The postcode XY coords indexed by postcode.
    :rtype: {str: (float, float)}
    """
    result = {}
    fields = ['Postcode', 'SHAPE@XY']
    with arcpy.da.SearchCursor(count_by_postcode_target, fields) as cursor:
        for row in cursor:
            result[row[0]] = row[1]

    return result


def _update_current_individual_cases(source_values):
    """
    :param source_values: The source source_data to be used.
    :type source_values: [{'date_string': str, 'date': datetime, 'postcode': int}]
    :return:
    :rtype:
    """

    postcode_locations = get_postcode_points()

    # build the result values
    result_values = {}
    for item in source_values:
        key_val = item['date_string'] + item['postcode']
        result_value = result_values.get(key_val, None)
        if result_value:
            result_value['count'] += 1
        else:
            result_value = copy.deepcopy(item)
            result_value['count'] = 1

            result_location = postcode_locations.get(item['postcode'], None)
            if result_location:
                result_value['xy'] = result_location
            else:
                result_value['xy'] = (17100000, -4600000)

            result_values[key_val] = result_value

    this_changes_made = 0

    fields = ['DateString', 'Postcode', 'SHAPE@XY', 'ReportAge']
    with arcpy.da.UpdateCursor(individual_cases_target, fields) as cursor:
        for row in cursor:
            date_string = row[0]
            postcode = row[1]
            key_val = date_string + postcode
            linked_result = result_values.get(key_val, None)
            if linked_result:
                xy = linked_result['xy']
                report_age = linked_result['report_age']
                if xy != row[2] or report_age != row[3]:
                    new_row = [date_string, postcode, xy, report_age]
                    cursor.updateRow(new_row)
                    this_changes_made += 1

                current_count = linked_result['count']
                if current_count > 1:
                    linked_result['count'] -= 1
                else:
                    del(result_values[key_val])
            else:
                cursor.deleteRow()
                this_changes_made += 1

    if len(result_values) > 0:
        fields = ['DateString', 'Postcode', 'SHAPE@XY', 'ReportDate', 'ReportAge']
        with arcpy.da.InsertCursor(individual_cases_target, fields) as cursor:
            for result_value in result_values.values():
                while result_value['count'] > 0:
                    new_row = [result_value['date_string'],
                               result_value['postcode'],
                               result_value['xy'],
                               result_value['date'],
                               result_value['report_age']]
                    cursor.insertRow(new_row)
                    this_changes_made += 1
                    result_value['count'] -= 1

    return this_changes_made


def _update_total_cases_by_postcodes(postcode_counts):
    """
    Updates the count_by_postcode_target table to match the values in the postcode_counts parameter.

    If a postcode in the table is not found in the counts then the value for that postcode is set to None.
    Postcodes are never deleted from the table.

    If a postcode is found in the postcode counts that is not in the table, then those postcodes are passed
    to _handle_new_postcodes for inclusion in the table.

    This function does not alter the postcode_counts object.

    :param postcode_counts: A dictionary of {postcode: case_count} values.
    :type postcode_counts: {str: int}
    """

    # make a local copy of postcode_counts so we don't inadvertently change the source dictionary for other uses.
    local_copy = copy.deepcopy(postcode_counts)
    fields = ['Postcode', 'TotalCases']
    with arcpy.da.UpdateCursor(count_by_postcode_target, fields) as cursor:
        for row in cursor:
            count_value = local_copy.pop(row[0], None)
            if row[1] != count_value:
                row[1] = count_value
                cursor.updateRow(row)

    # if any postcodes remain unhandled, add them to the table.
    if len(local_copy) > 0:
        _handle_new_postcodes(local_copy)


def _update_total_cases_by_sa3(postcode_counts):
    """
    Updates the sa3_target table using postcode counts and poa to sa3 correspondences.

    :param postcode_counts:
    :type postcode_counts:
    :return:
    :rtype:
    """

    # parse correspondences
    weights = {}
    with open(poa2sa3_source, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            poa = str(row[0]).strip()
            if len(poa) == 4:
                sa3 = str(row[1]).strip()
                ratio = float(row[3])

                poa_weights = weights.get(poa, None)
                if poa_weights:
                    poa_weights[sa3] = ratio
                else:
                    weights[poa] = {sa3: ratio}

    # calculate SA3 values
    sa3_values = {}
    for poa, poa_value in postcode_counts.data():
        if poa_value and poa in weights:
            poa_weights = weights[poa]
            for sa3, poa_ratio in poa_weights.items():
                if sa3 in sa3_values:
                    sa3_values[sa3] += round((poa_ratio * poa_value), 2)
                else:
                    sa3_values[sa3] = round((poa_ratio * poa_value), 2)

    # update sa3 table
    changes = 0
    changes += update_sa3_totals(sa3_values, sa3_2016_centroid_counts_target, 'SA3', 'COVID19_Count')
    changes += update_sa3_totals(sa3_values, sa3_2016_boundary_counts_target, 'SA3', 'COVID19_Count')
    changes += update_sa3_totals(sa3_values, sa3_lana_attributes_target, 'SA3_CODE16', 'COVID19_Count')
    return changes


def update_sa3_totals(sa3_values, sa3_target, sa3_id_field, sa3_total_field):
    # update sa3 table
    logging.info('Updating Database: ' + sa3_target)

    changes = 0
    fields = [sa3_id_field, sa3_total_field]
    with arcpy.da.UpdateCursor(sa3_target, fields) as cursor:
        for row in cursor:
            sa3 = row[0]
            new_value = sa3_values.get(sa3, None)
            if row[1] != new_value:
                row[1] = new_value
                cursor.updateRow(row)
                changes += 1

    logging.info('SUCCESS - {} Changes Made'.format(changes))

    return changes


def _handle_new_postcodes(new_postcode_counts):
    """
    Adds the values for submitted postcodes to the count_by_postcode_target table with a default xy coordinate value.

    It is assumed that all postcodes submitted in the new_postcode_counts do not already exist in the table.
    :param new_postcode_counts: A dictionary of {postcode: case_count} values to be inserted.
    :type new_postcode_counts: {str: int}
    """
    if new_postcode_counts:
        fields = ['SHAPE@XY', 'Postcode', 'TotalCases']
        with arcpy.da.InsertCursor(count_by_postcode_target, fields) as cursor:
            for postcode, count in new_postcode_counts.data():
                row = [(17100000, -4600000), postcode, count]
                cursor.insertRow(row)


if __name__ == "__main__":
    log = arcpy.GetParameterAsText(0)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log),
            logging.StreamHandler()
        ]
    )

    try:
        source_data = parse_nsw_source()

        postcode_totals = {}
        get_counts_by_postcode([x['postcode'] for x in source_data], postcode_totals)
        postcodes_found = len(postcode_totals)

        logging.info('Updating Database: ' + count_by_postcode_target)
        _update_total_cases_by_postcodes(postcode_totals)
        logging.info('SUCCESS - {} Postcodes Processed'.format(postcodes_found))

        logging.info('Updating Database: ' + individual_cases_target)
        changes_made = _update_current_individual_cases(source_data)
        logging.info('SUCCESS - {} Changes Made'.format(changes_made))

        _update_total_cases_by_sa3(postcode_totals)

    except Exception as e:
        logging.error(e, exc_info=True)
