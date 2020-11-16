import arcpy
import datetime


def region_template():
    return {'Confirmed': 0,
            'Deaths': 0,
            'Recovered': 0,
            'Active': 0}


def date_template():
    return {'Australia': region_template(),
            'Australian Capital Territory': region_template(),
            'New South Wales': region_template(),
            'Northern Territory': region_template(),
            'Queensland': region_template(),
            'South Australia': region_template(),
            'Tasmania': region_template(),
            'Victoria': region_template(),
            'Western Australia': region_template(),
            'External territories': region_template(),
            'Jervis Bay Territory': region_template()}


def nullify_zeros(value):
    if value:
        return value
    else:
        return None


def get_file_names(source_table):
    result = []
    fields = ['FileName']
    with arcpy.da.SearchCursor(source_table, fields) as cursor:
        for row in cursor:
            result.append(row[0])

    result.sort()
    return result


def filename2datestring(file_name):
    base_parts = file_name.split('.')
    date_parts = base_parts[0].split('-')
    return '{}{}{}'.format(date_parts[2], date_parts[0], date_parts[1])


def get_stats(source_table):

    file_names = get_file_names(source_table)

    data_items = {}
    fields = ['State', 'ConfirmedCases', 'Deaths', 'Recovered', 'ActiveCases']
    for file_name in file_names:
        where_clause = "FileName = '{}' AND State != 'From Diamond Princess'".format(file_name)
        date_string = filename2datestring(file_name)
        data_item = date_template()
        data_items[date_string] = data_item
        aus_data = data_item['Australia']
        with arcpy.da.SearchCursor(source_table, fields, where_clause) as cursor:
            for row in cursor:
                aus_data['Confirmed'] += row[1] if row[1] else 0
                aus_data['Deaths'] += row[2] if row[2] else 0
                aus_data['Recovered'] += row[3] if row[3] else 0
                aus_data['Active'] += row[4] if row[4] else 0

                state_data = data_item[row[0]]
                state_data['Confirmed'] = row[1]
                state_data['Deaths'] = row[2]
                state_data['Recovered'] = row[3]
                state_data['Active'] = row[4]

    return data_items


def update_summary(source_table, target_table):
    data_values = get_stats(source_table)

    fields = ['ReportDate', 'DateString',
              'AUS_Confirmed', 'AUS_Deaths', 'AUS_Recovered', 'AUS_Active',
              'ACT_Confirmed', 'ACT_Deaths', 'ACT_Recovered', 'ACT_Active',
              'NSW_Confirmed', 'NSW_Deaths', 'NSW_Recovered', 'NSW_Active',
              'NT_Confirmed', 'NT_Deaths', 'NT_Recovered', 'NT_Active',
              'QLD_Confirmed', 'QLD_Deaths', 'QLD_Recovered', 'QLD_Active',
              'SA_Confirmed', 'SA_Deaths', 'SA_Recovered', 'SA_Active',
              'TAS_Confirmed', 'TAS_Deaths', 'TAS_Recovered', 'TAS_Active',
              'VIC_Confirmed', 'VIC_Deaths', 'VIC_Recovered', 'VIC_Active',
              'WA_Confirmed', 'WA_Deaths', 'WA_Recovered', 'WA_Active']

    with arcpy.da.UpdateCursor(target_table, fields) as cursor:
        for row in cursor:
            date_string = row[1]
            item = data_values.pop(date_string)
            if item:
                date_val = row[0]
                new_row = [date_val, date_string,
                           nullify_zeros(item['Australia']['Confirmed']),
                           nullify_zeros(item['Australia']['Deaths']),
                           nullify_zeros(item['Australia']['Recovered']),
                           nullify_zeros(item['Australia']['Active']),
                           nullify_zeros(item['Australian Capital Territory']['Confirmed']),
                           nullify_zeros(item['Australian Capital Territory']['Deaths']),
                           nullify_zeros(item['Australian Capital Territory']['Recovered']),
                           nullify_zeros(item['Australian Capital Territory']['Active']),
                           nullify_zeros(item['New South Wales']['Confirmed']),
                           nullify_zeros(item['New South Wales']['Deaths']),
                           nullify_zeros(item['New South Wales']['Recovered']),
                           nullify_zeros(item['New South Wales']['Active']),
                           nullify_zeros(item['Northern Territory']['Confirmed']),
                           nullify_zeros(item['Northern Territory']['Deaths']),
                           nullify_zeros(item['Northern Territory']['Recovered']),
                           nullify_zeros(item['Northern Territory']['Active']),
                           nullify_zeros(item['Queensland']['Confirmed']),
                           nullify_zeros(item['Queensland']['Deaths']),
                           nullify_zeros(item['Queensland']['Recovered']),
                           nullify_zeros(item['Queensland']['Active']),
                           nullify_zeros(item['South Australia']['Confirmed']),
                           nullify_zeros(item['South Australia']['Deaths']),
                           nullify_zeros(item['South Australia']['Recovered']),
                           nullify_zeros(item['South Australia']['Active']),
                           nullify_zeros(item['Tasmania']['Confirmed']),
                           nullify_zeros(item['Tasmania']['Deaths']),
                           nullify_zeros(item['Tasmania']['Recovered']),
                           nullify_zeros(item['Tasmania']['Active']),
                           nullify_zeros(item['Victoria']['Confirmed']),
                           nullify_zeros(item['Victoria']['Deaths']),
                           nullify_zeros(item['Victoria']['Recovered']),
                           nullify_zeros(item['Victoria']['Active']),
                           nullify_zeros(item['Western Australia']['Confirmed']),
                           nullify_zeros(item['Western Australia']['Deaths']),
                           nullify_zeros(item['Western Australia']['Recovered']),
                           nullify_zeros(item['Western Australia']['Active'])]

                if row != new_row:
                    cursor.updateRow(new_row)

    if data_values:
        with arcpy.da.InsertCursor(target_table, fields) as cursor:
            for key in sorted(data_values.keys()):
                item = data_values[key]
                date_val = datetime.datetime.strptime(key, "%Y%m%d")
                new_row = [date_val, key,
                           nullify_zeros(item['Australia']['Confirmed']),
                           nullify_zeros(item['Australia']['Deaths']),
                           nullify_zeros(item['Australia']['Recovered']),
                           nullify_zeros(item['Australia']['Active']),
                           nullify_zeros(item['Australian Capital Territory']['Confirmed']),
                           nullify_zeros(item['Australian Capital Territory']['Deaths']),
                           nullify_zeros(item['Australian Capital Territory']['Recovered']),
                           nullify_zeros(item['Australian Capital Territory']['Active']),
                           nullify_zeros(item['New South Wales']['Confirmed']),
                           nullify_zeros(item['New South Wales']['Deaths']),
                           nullify_zeros(item['New South Wales']['Recovered']),
                           nullify_zeros(item['New South Wales']['Active']),
                           nullify_zeros(item['Northern Territory']['Confirmed']),
                           nullify_zeros(item['Northern Territory']['Deaths']),
                           nullify_zeros(item['Northern Territory']['Recovered']),
                           nullify_zeros(item['Northern Territory']['Active']),
                           nullify_zeros(item['Queensland']['Confirmed']),
                           nullify_zeros(item['Queensland']['Deaths']),
                           nullify_zeros(item['Queensland']['Recovered']),
                           nullify_zeros(item['Queensland']['Active']),
                           nullify_zeros(item['South Australia']['Confirmed']),
                           nullify_zeros(item['South Australia']['Deaths']),
                           nullify_zeros(item['South Australia']['Recovered']),
                           nullify_zeros(item['South Australia']['Active']),
                           nullify_zeros(item['Tasmania']['Confirmed']),
                           nullify_zeros(item['Tasmania']['Deaths']),
                           nullify_zeros(item['Tasmania']['Recovered']),
                           nullify_zeros(item['Tasmania']['Active']),
                           nullify_zeros(item['Victoria']['Confirmed']),
                           nullify_zeros(item['Victoria']['Deaths']),
                           nullify_zeros(item['Victoria']['Recovered']),
                           nullify_zeros(item['Victoria']['Active']),
                           nullify_zeros(item['Western Australia']['Confirmed']),
                           nullify_zeros(item['Western Australia']['Deaths']),
                           nullify_zeros(item['Western Australia']['Recovered']),
                           nullify_zeros(item['Western Australia']['Active'])]

                cursor.insertRow(new_row)

    return target_table


daily_stats = arcpy.GetParameterAsText(0)
target_summary = arcpy.GetParameterAsText(1)

updated_summary = update_summary(daily_stats, target_summary)

arcpy.SetParameter(2, updated_summary)