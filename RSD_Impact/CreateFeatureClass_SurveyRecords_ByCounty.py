import arcpy

feature_type = 'POINT'
out_path = r'E:\Documents2\ArcGIS\Projects\RSD_Impacts\RSD_Impacts.gdb'
out_name = r'SurveyRecords_CountryCentroids'
sr = r'E:\Documents2\ArcGIS\Projects\RSD_Impacts\RSD_Impacts.gdb\WorldCountries'

fields = [['RecordID', 'LONG', 'ID'],
          ['ActivityType', 'TEXT', 'Activity Type', 50],
          ['AcademicLeadEmail', 'TEXT', 'Academic Lead Email', 100],
          ['StartDate', 'DATE', 'Start Date'],
          ['EndDate', 'DATE', 'End Date'],
          ['ActivityDetails', 'TEXT', 'Activity Details', 1000],
          ['NIGGoals', 'TEXT', 'NIG Strategic Goals', 200],
          ['FieldOfResearch', 'TEXT', 'Field of Research', 100],
          ['Stakeholder', 'TEXT', 'Stakeholder Name', 250],
          ['StakeholderLocation', 'TEXT', 'Stakeholder Location', 100],
          ['Region', 'TEXT', 'Region', 50],
          ['Country', 'TEXT', 'Country', 100]]

fc0 = arcpy.CreateFeatureclass_management(out_path=out_path, out_name=out_name, geometry_type=feature_type, spatial_reference=sr)
fl0 = arcpy.MakeFeatureLayer_management(fc0, 'tmp_lyr')
arcpy.management.AddFields(fl0, fields)

