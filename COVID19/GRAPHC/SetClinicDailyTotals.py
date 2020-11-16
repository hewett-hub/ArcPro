import arcpy


def get_clinic_point():
    fields = ['SHAPE@', 'Clinic']
    clinic_name = clinic.upper()
    with arcpy.da.SearchCursor(clinics_features, fields) as cursor:
        for row in cursor:
            if row[1] and row[1].upper() == clinic_name:
                return row[0]

    arcpy.AddError('Clinic Not Found: ' + clinic)


def update_row():
    test_values = []
    confirmed_values = []

    pt = get_clinic_point()  # ensure clinic name is valid and get point in case of need for insert.

    result_value = None
    clinic_name = clinic.upper()

    fields = ['Clinic', 'ReportDate', 'TestsConducted', 'ConfirmedCases']
    entry_date_only = entry_date.date()
    with arcpy.da.UpdateCursor(stats_features, fields) as cursor:
        for row in cursor:
            if row[0] and row[0].upper() == clinic_name:
                record_date = row[1]
                test_val = row[2]
                confirmed_val = row[3]

                if record_date.date() == entry_date_only:
                    test_values.append(tests)
                    confirmed_values.append(confirmed)
                    if test_val != tests or confirmed_val != confirmed:
                        row[2] = tests
                        row[3] = confirmed
                        cursor.updateRow(row)
                        result_value = 'Updated'
                    else:
                        result_value = 'No Change'
                else:
                    test_values.append(test_val)
                    confirmed_values.append(confirmed_val)

    if not result_value:
        fields = ['SHAPE@', 'Clinic', 'ReportDate', 'TestsConducted', 'ConfirmedCases']
        new_row = [pt, clinic, entry_date_only, tests, confirmed]
        with arcpy.da.InsertCursor(stats_features, fields) as cursor:
            cursor.insertRow(new_row)
        test_values.append(tests)
        confirmed_values.append(confirmed)
        result_value = 'Inserted'

    return result_value, sum(filter(None, test_values)), sum(filter(None, confirmed_values))


def update_totals(tests_val, confirmed_val):
    fields = ['TotalTests', 'TotalConfirmed']
    where_clause = "UPPER(Clinic) = '{}'".format(clinic.upper())
    with arcpy.da.UpdateCursor(clinics_features, fields, where_clause) as cursor:
        for row in cursor:
            row[0] = tests_val
            row[1] = confirmed_val
            cursor.updateRow(row)


clinics_features = arcpy.GetParameter(0)
stats_features = arcpy.GetParameter(2)
stats_id_field = arcpy.GetParameterAsText(3)
clinic = arcpy.GetParameterAsText(4)
entry_date = arcpy.GetParameter(5)
tests = arcpy.GetParameter(6)
confirmed = arcpy.GetParameter(7)

result, test_total, confirmed_total = update_row()
if result != 'No Change':
    update_totals(test_total, confirmed_total)

arcpy.SetParameter(7, result)
