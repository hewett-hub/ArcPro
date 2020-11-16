import arcpy
import csv
import os
import datetime


def get_region_rows(csv_file):
    with open(csv_file, 'rb') as f:
        line = f.readline().strip()

    if line in [b'Province/State,Country/Region,Last Update,Confirmed,Deaths,Recovered',
                b'Province/State,Country/Region,Last Update,Confirmed,Deaths,Recovered,Latitude,Longitude']:
        return get_rows1(csv_file)
    elif line in [b'FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key',
                  b'FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key,Incidence_Rate,Case-Fatality_Ratio']:
        return get_rows2(csv_file)
    elif line.decode("utf-8-sig").encode("utf-8") in [b'Province/State,Country/Region,Last Update,Confirmed,Deaths,Recovered',
                                                      b'Province/State,Country/Region,Last Update,Confirmed,Deaths,Recovered,Latitude,Longitude']:
        return get_rows1(csv_file)
    elif line.decode("utf-8-sig").encode("utf-8") in \
            [b'FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key',
             b'FIPS,Admin2,Province_State,Country_Region,Last_Update,Lat,Long_,Confirmed,Deaths,Recovered,Active,Combined_Key,Incidence_Rate,Case-Fatality_Ratio']:

        return get_rows2(csv_file)
    else:
        arcpy.AddError('Unhandled csv structure: ' + str(line))


def get_rows1(csv_file):
    with open(csv_file, 'r') as csv_content:
        csv_rows = csv.reader(csv_content)
        result = {}
        for row in csv_rows:
            country = row[1]
            if country == 'Australia':
                state = row[0]
                if not state:
                    state = 'New South Wales'  # early tables don't have state.  All incidents in these tables are NSW

                confirmed = str2int(row[3])
                deaths = str2int(row[4])
                recovered = str2int(row[5])
                active = confirmed - (deaths + recovered)
                result[state] = {'State': state,
                                 'Last Update': row[2],
                                 'Confirmed': confirmed,
                                 'Deaths': deaths,
                                 'Recovered': recovered,
                                 'Active': active}

        return result


def get_rows2(csv_file):
    with open(csv_file, 'r') as csv_content:
        csv_rows = csv.reader(csv_content)
        result = {}
        for row in csv_rows:
            country = row[3]
            if country == 'Australia':
                state = row[2]
                if not state:
                    state = 'New South Wales'  # early tables don't have state.  All incidents in these tables are NSW

                confirmed = str2int(row[7])
                deaths = str2int(row[8])
                recovered = str2int(row[9])
                active = str2int(row[10])
                result[state] = {'State': state,
                                 'Last Update': row[4],
                                 'Confirmed': confirmed,
                                 'Deaths': deaths,
                                 'Recovered': recovered,
                                 'Active': active}

        return result


def str2int(value):
    if not value.strip():
        return 0
    return int(value)


def nullify_zeros(value):
    if value:
        return value
    else:
        return None


def update_table(csv_file, table, coords):
    arcpy.AddMessage('Processing: ' + csv_file)
    source_rows = get_region_rows(csv_file)

    if source_rows:
        file_name = os.path.basename(csv_file)

        date_parts = file_name.split('.')[0].split('-')
        date_value = datetime.date(int(date_parts[2]), int(date_parts[0]), int(date_parts[1]))

        where_clause = "FileName = '{}'".format(file_name)
        fields = ['State', 'ReportDate', 'ConfirmedCases', 'Deaths', 'Recovered', 'ActiveCases', 'LastUpdate', 'FileName', 'SHAPE@XY']

        with arcpy.da.UpdateCursor(table, fields, where_clause) as cursor:
            for row in cursor:
                item = source_rows.pop(row[0], None)
                if item:

                    confirmed = nullify_zeros(item['Confirmed'])
                    deaths = nullify_zeros(item['Deaths'])
                    recovered = nullify_zeros(item['Recovered'])
                    active = nullify_zeros(item['Active'])
                    point_coords = coords.get(item['State'], None)

                    new_row = [item['State'], date_value, confirmed, deaths, recovered, active, item['Last Update'], file_name, point_coords]
                    if row[2:6] != new_row[2:6]:
                        cursor.updateRow(new_row)

        if source_rows:
            with arcpy.da.InsertCursor(table, fields) as cursor:
                for item in source_rows.values():

                    confirmed = nullify_zeros(item['Confirmed'])
                    deaths = nullify_zeros(item['Deaths'])
                    recovered = nullify_zeros(item['Recovered'])
                    active = nullify_zeros(item['Active'])
                    point_coords = coords.get(item['State'], None)

                    new_row = [item['State'], date_value,  confirmed, deaths, recovered, active, item['Last Update'], file_name, point_coords]
                    cursor.insertRow(new_row)


def process_folder(folder, table):
    state_coords = {'Australian Capital Territory':  (149.130, -35.2833),
                    'From Diamond Princess': (139.638, 35.4437),
                    'New South Wales': (151.2093, -33.8688),
                    'Northern Territory': (130.8456, -12.4634),
                    'Queensland': (153.021, -27.4701),
                    'South Australia': (138.6007, -34.9285),
                    'Tasmania': (147.323, -42.8819),
                    'Victoria': (144.9631, -37.8136),
                    'Western Australia': (115.8605, -31.9505)}
    file_paths = [os.path.join(folder, x) for x in os.listdir(folder) if x.endswith('.csv')]
    file_paths.sort()
    for file_path in file_paths:
        update_table(file_path, table, state_coords)


source_folder = arcpy.GetParameterAsText(0)
target_table = arcpy.GetParameterAsText(1)

process_folder(source_folder, target_table)

arcpy.SetParameter(2, target_table)
