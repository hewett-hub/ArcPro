import arcpy
import xlrd
import datetime

data_source = r'E:\Documents2\ANU\Projects\RSD_Impact\RSPH ANU Engagement and Impact Tracker.xlsx'
feature_source = r'E:\Documents2\ArcGIS\Projects\RSD_Impacts\RSD_Impacts.gdb\WorldCountries'
target = r'E:\Documents2\ArcGIS\Projects\RSD_Impacts\RSD_Impacts.gdb\SurveyRecords_CountryCentroids'


def get_country_centroids():
    result = {}
    fields = ['Country', 'SHAPE@']
    with arcpy.da.SearchCursor(feature_source, fields) as cursor:
        for row in cursor:
            result[row[0]] = row[1].centroid

    return result


def get_data():
    workbook = xlrd.open_workbook(data_source, on_demand=True)
    worksheet = workbook.sheet_by_index(1)
    first_row = []  # The row where we stock the name of the column
    for col in range(worksheet.ncols):
        first_row.append(worksheet.cell_value(0, col))
    # transform the workbook to a list of dictionary
    data = []
    for row in range(1, worksheet.nrows):
        elm = {}
        for col in range(worksheet.ncols):
            elm[first_row[col]] = worksheet.cell_value(row, col)
        data.append(elm)
    return data, workbook.datemode


def parse_dates(row, date_mode):
    if row['Does this activity relate to single or multiple dates?'] == 'Single date':
        start_date = xlrd.xldate_as_datetime(row['Activity Date'], date_mode)
        end_date = start_date
    else:
        start_date = xlrd.xldate_as_datetime(row['Activity Start Date'], date_mode)
        end_date_value = row['Activity End Date']
        if end_date_value:
            end_date = xlrd.xldate_as_datetime(end_date_value, date_mode)
        else:
            end_date = datetime.datetime.now()
    return start_date.date(), end_date.date()


def get_record_values():
    raw_data, date_mode = get_data()
    centroids = get_country_centroids()

    result = {}
    for row in raw_data:
        id_val = int(row['ID'])
        start_date, end_date = parse_dates(row, date_mode)
        country = row['Country']
        if not country:
            country = 'Australia'
        centroid = centroids.get(country, None)
        if not centroid:
            arcpy.AddWarning('Country value not found - Record geometry not added: ' + country)
        result_row = [id_val, row['Activity type'], row['Academic lead email address'], start_date, end_date, row['Activity Details2'],
                      row['Does this activity contribute to any of the 5 NIG strategic goals?'], row['Field of Research Codes'],
                      row['Stakeholder name'], row['Stakeholder location'], row['Region'], country, centroid]
        result[id_val] = result_row

    return result


def rows_are_equal(row0, row1, value_indexes, date_indexes, shape_indexes):

    for index in value_indexes:
        if row0[index] != row1[index]:
            return False

    for index in date_indexes:
        d0 = row0[index].strftime("%Y-%m-%d")
        d1 = row1[index].strftime("%Y-%m-%d")
        if d0 != d1:
            return False

    for index in shape_indexes:
        s0 = row0[index]
        s1 = row1[index]
        if s0 and not s1:
            return False
        elif s1 and not s0:
            return False
        elif s0 and s1 and not s0.equals(s1):
            return False

    return True


def update_target():
    new_values = get_record_values()

    value_indexes = [1, 2, 5, 6, 7, 8, 9, 10, 11]
    date_indexes = [3, 4]
    shape_indexes = [12]
    fields = ['RecordID', 'ActivityType', 'AcademicLeadEmail', 'StartDate', 'EndDate', 'ActivityDetails', 'NIGGoals', 'FieldOfResearch',
              'Stakeholder', 'StakeholderLocation', 'Region', 'Country', 'SHAPE@']
    with arcpy.da.UpdateCursor(target, fields) as cursor:
        for row in cursor:
            id_val = row[0]
            new_row = new_values.pop(id_val, None)
            if new_row:
                if not rows_are_equal(row, new_row, value_indexes, date_indexes, shape_indexes):
                    cursor.updateRow(new_row)
                    arcpy.AddMessage('Row Updated {}'.format(id_val))
            else:
                cursor.deleteRow()
                arcpy.AddMessage('Row Deleted {}'.format(id_val))

    if new_values:
        fields = ['RecordID', 'ActivityType', 'AcademicLeadEmail', 'StartDate', 'EndDate', 'ActivityDetails', 'NIGGoals', 'FieldOfResearch',
                  'Stakeholder', 'StakeholderLocation', 'Region', 'Country', 'SHAPE@']
        with arcpy.da.InsertCursor(target, fields) as cursor:
            for row in new_values.values():
                row_id = row[0]
                cursor.insertRow(row)
                arcpy.AddMessage('Row Inserted {}'.format(row_id))


if __name__ == "__main__":
    update_target()
