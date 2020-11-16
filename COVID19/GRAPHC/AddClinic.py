import arcpy


clinics = arcpy.GetParameterAsText(0)
new_location = arcpy.GetParameter(1)
clinic_type = arcpy.GetParameterAsText(2)
clinic = arcpy.GetParameterAsText(3)
hours = arcpy.GetParameterAsText(4)
commenced = arcpy.GetParameterAsText(5)
street_address = arcpy.GetParameterAsText(6)
suburb = arcpy.GetParameterAsText(7)
state = arcpy.GetParameterAsText(8)
postcode = arcpy.GetParameterAsText(9)
phone = arcpy.GetParameterAsText(10)
additional_info = arcpy.GetParameterAsText(11)

clinic_uc = clinic.upper()

fields = ['Clinic']
with arcpy.da.SearchCursor(clinics, fields) as cursor:
    for row in cursor:
        if row[0].upper() == clinic_uc:
            arcpy.AddError('Clinic already Exists: '.format(row[0]))


fields = ['SHAPE@', 'Clinic', 'OpeningHours', 'OperationCommenced', 'StreetAddress', 'Suburb', 'State', 'PostCode', 'ClinicType',
          'AdditionalInformation', 'Phone']
with arcpy.da.InsertCursor(clinics, fields) as cursor:
    id = cursor.insertRow([new_location, clinic, hours, commenced, street_address, suburb, state, postcode, clinic_type, additional_info, phone])
    
arcpy.SetParameter(12, id)
