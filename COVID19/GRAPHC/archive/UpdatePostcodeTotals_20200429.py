import arcpy
import csv
import urllib.request
import io
import logging
import datetime

# CSV Source: https://data.gov.au/dataset/ds-nsw-aefcde60-3b0c-4bc0-9af1-6fe652944ec2/details?q=covid
nsw_source = r'https://data.nsw.gov.au/data/dataset/aefcde60-3b0c-4bc0-9af1-6fe652944ec2/resource/21304414-1ff1-4243-a5d2-f52778048b29/download/covid-19-cases-by-notification-date-and-postcode-local-health-district-and-local-government-area.csv'
count_by_postcode_target = r'\\mhsdata\mhs\workgroups\rsph\GRAPHC\SdeConnections\dot234_Publishing_COVID19.sde\TotalCasesByPostcode'
individual_cases_target = r'\\mhsdata\mhs\workgroups\rsph\GRAPHC\SdeConnections\dot234_Publishing_COVID19.sde\IndividualCasesByPostcode'
postcode_index = 1
date_index = 0


def parse_nsw_source(item_list):
    logging.info('Getting NSW source_data: ' + nsw_source)
    with urllib.request.urlopen(nsw_source) as response:
        content = response.read().decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            postcode = row[postcode_index]
            if postcode:
                postcode = postcode.strip()
            if len(postcode) <= 4:
                date_string, date_value = parse_date(row[date_index])
                item_list.append([date_string, date_value, postcode])


def parse_date(date_value):
    day_part, month_part, year_part = date_value.split('-')
    year_length = len(year_part)
    if year_length == 2:
        year_part = '20' + year_part
    elif year_length != 4:
        raise RuntimeError('Invalid year value: ' + date_value)

    date_string = year_part + month_part + day_part
    date_result = datetime.datetime(year_part, month_part, day_part)

    return date_string, date_result


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


def get_nsw_totals2(item_list, postcode_counts):
    for item in item_list:
        postcode = item[2]
        if postcode in postcode_counts:
            postcode_counts[postcode] += 1
        else:
            postcode_counts[postcode] = 1


def get_postcode_points():
    result = {}
    fields = ['Postcode', 'SHAPE@XY']
    with arcpy.da.SearchCursor(count_by_postcode_target, fields) as cursor:
        for row in cursor:
            result[row[0]] = row[1]

    return result


def update_values(postcode_counts):
    fields = ['Postcode', 'TotalCases']
    with arcpy.da.UpdateCursor(count_by_postcode_target, fields) as cursor:
        for row in cursor:
            count_value = postcode_counts.pop(row[0], None)
            if row[1] != count_value:
                row[1] = count_value
                cursor.updateRow(row)

    return postcode_counts


def handle_unknown_postcodes(postcode_counts):
    if postcode_counts:
        fields = ['SHAPE@XY', 'Postcode', 'TotalCases']
        with arcpy.da.InsertCursor(count_by_postcode_target, fields) as cursor:
            for postcode, count in postcode_counts.data():
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
        source_data = []
        parse_nsw_source(source_data)

        postcode_totals = {}
        # incidents = []
        #get_nsw_totals(postcode_totals)
        get_nsw_totals2(source_data, postcode_totals)
        postcodes_found = len(postcode_totals)

        logging.info('Updating Database: ' + count_by_postcode_target)
        update_values(postcode_totals)

        handle_unknown_postcodes(postcode_totals)
        logging.info('SUCCESS - {} Postcodes Processed'.format(postcodes_found))
    except Exception as e:
        logging.error(e, exc_info=True)
