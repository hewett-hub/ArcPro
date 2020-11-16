import arcpy
import csv
import datetime
import urllib.request
import io

# CSV Source: https://data.gov.au/dataset/ds-nsw-aefcde60-3b0c-4bc0-9af1-6fe652944ec2/details?q=covid
source = r'https://data.nsw.gov.au/data/dataset/aefcde60-3b0c-4bc0-9af1-6fe652944ec2/resource/21304414-1ff1-4243-a5d2-f52778048b29/download/covid-19-cases-by-notification-date-and-postcode-local-health-district-and-local-government-area.csv'
target = r'\\mhsdata\mhs\workgroups\rsph\GRAPHC\SdeConnections\dot234_Publishing_COVID19.sde\PostcodeDailyCounts'
date_index = 0
postcode_index = 1

# postcode 2week trend [Postcode, ReportDate, TotalCases, D, Dminus1, Dminus2, Dminus3, ..... Dminus14, EditDate]
# postcode weekly trend [Postcode, ReportDate, TotalCases, W, Wminus1, ....... ,Wminus14, EditDate]
# postcode daily stats [Postcode, ReportDate, TotalCases, NewCases, EditDate]


def parse_date(date_string):
    if not date_string:
        return None, None
    print(date_string)
    date_parts = date_string.strip().split('-')
    if len(date_parts) < 3:
        return None, None

    new_date_string = '{}{}{}'.format(date_parts[0], date_parts[1], date_parts[2])
    new_date = datetime.date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))

    return new_date_string, new_date


def get_source():
    items = {}

    with urllib.request.urlopen(source) as response:
        content = response.read().decode('utf-8')
        reader = csv.reader(io.StringIO(content))
        for row in reader:
            print(row)
            date_value, date_obj = parse_date(row[date_index])
            postcode = row[postcode_index]
            if date_value and postcode:
                key = [date_value, postcode]
                item = items.get(key, None)

                if item:
                    item[2] += 1
                else:
                    items[key] = [date_value, postcode, 1, date_obj, None]

    calculate_deltas(items.values())

    return items


def calculate_deltas(item_list):
    last_total = 0
    last_postcode = None

    sorted_list = sorted(item_list, key=lambda x: (x[1], x[0]))  # sort by postcode then date
    for item in sorted_list:
        if item[1] == last_postcode:
            item[4] = item[2] - last_total
            last_total = item[2]
        else:
            last_postcode = item[1]
            item[4] = item[2]
            last_total = item[2]


def update_values():
    csv_items = get_source()

    fields = ['DateString', 'Postcode', 'COVID19Notifications']
    with arcpy.da.UpdateCursor(target, fields) as cursor:
        for row in cursor:
            key = [row[0], row[1]]
            csv_item = csv_items.pop(key, None)
            if csv_item and row[2] != csv_item[2]:
                row[2] = csv_item[2]
                cursor.updateRow(row)

    if csv_items:
        fields = ['DateString', 'Postcode', 'COVID19Notifications', 'Date']
        with arcpy.da.InsertCursor(target, fields) as cursor:
            for row in csv_items.values():
                cursor.insertRow(row)


if __name__ == "__main__":
    source_values = get_source()



