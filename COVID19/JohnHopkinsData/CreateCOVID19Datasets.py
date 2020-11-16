import arcpy


def create_daily_stats_australia(target_workspace):
    sr = arcpy.SpatialReference(4326)
    out_fc = arcpy.CreateFeatureclass_management(out_path=target_workspace, out_name='DAILY_STATISTICS_AUSTRALIA', geometry_type='POINT',
                                                 spatial_reference=sr)
    arcpy.AddField_management(in_table=out_fc, field_name='State', field_type='TEXT', field_length=30)
    arcpy.AddField_management(in_table=out_fc, field_name='ReportDate', field_type='DATE')
    arcpy.AddField_management(in_table=out_fc, field_name='ConfirmedCases', field_type='LONG')
    arcpy.AddField_management(in_table=out_fc, field_name='Deaths', field_type='LONG')
    arcpy.AddField_management(in_table=out_fc, field_name='Recovered', field_type='LONG')
    arcpy.AddField_management(in_table=out_fc, field_name='ActiveCases', field_type='LONG')
    arcpy.AddField_management(in_table=out_fc, field_name='LastUpdate', field_type='TEXT', field_length=25)
    arcpy.AddField_management(in_table=out_fc, field_name='FileName', field_type='TEXT', field_length=15)

    return out_fc


def create_daily_state_stats(target_workspace):
    tmp_table = arcpy.CreateTable_management(out_path='in_memory', out_name='DAILY_SUMMARY')
    arcpy.AddField_management(in_table=tmp_table, field_name='ReportDate', field_type='DATE')
    arcpy.AddField_management(in_table=tmp_table, field_name='DateString', field_type='TEXT', field_length=8)

    arcpy.AddField_management(in_table=tmp_table, field_name='AUS_Confirmed', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='AUS_Deaths', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='AUS_Recovered', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='AUS_Active', field_type='LONG')

    arcpy.AddField_management(in_table=tmp_table, field_name='ACT_Confirmed', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='ACT_Deaths', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='ACT_Recovered', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='ACT_Active', field_type='LONG')

    arcpy.AddField_management(in_table=tmp_table, field_name='NSW_Confirmed', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='NSW_Deaths', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='NSW_Recovered', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='NSW_Active', field_type='LONG')

    arcpy.AddField_management(in_table=tmp_table, field_name='NT_Confirmed', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='NT_Deaths', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='NT_Recovered', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='NT_Active', field_type='LONG')

    arcpy.AddField_management(in_table=tmp_table, field_name='QLD_Confirmed', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='QLD_Deaths', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='QLD_Recovered', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='QLD_Active', field_type='LONG')

    arcpy.AddField_management(in_table=tmp_table, field_name='SA_Confirmed', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='SA_Deaths', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='SA_Recovered', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='SA_Active', field_type='LONG')

    arcpy.AddField_management(in_table=tmp_table, field_name='TAS_Confirmed', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='TAS_Deaths', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='TAS_Recovered', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='TAS_Active', field_type='LONG')

    arcpy.AddField_management(in_table=tmp_table, field_name='VIC_Confirmed', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='VIC_Deaths', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='VIC_Recovered', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='VIC_Active', field_type='LONG')

    arcpy.AddField_management(in_table=tmp_table, field_name='WA_Confirmed', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='WA_Deaths', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='WA_Recovered', field_type='LONG')
    arcpy.AddField_management(in_table=tmp_table, field_name='WA_Active', field_type='LONG')

    out_table = arcpy.TableToTable_conversion(in_rows=tmp_table, out_path=target_workspace, out_name='DAILY_SUMMARY')
    arcpy.Delete_management(tmp_table)

    return out_table


output_workspace = arcpy.GetParameterAsText(0)
output_table = arcpy.GetParameterAsText(1)

if output_table == 'DAILY_STATISTICS_AUSTRALIA':
    result = create_daily_stats_australia(output_workspace)
    arcpy.SetParameter(2, result)
elif output_table == 'DAILY_SUMMARY':
    result = create_daily_state_stats(output_workspace)
    arcpy.SetParameter(2, result)
else:
    arcpy.AddError('Invalid Output Table parameter')


