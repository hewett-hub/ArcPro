import arcpy
import datetime


def parse_raw_vals(raw_vals_str):
    raw_vals = raw_vals_str[1:-2]
    raw_vals = raw_vals.split(',')

    return [float(n) for n in raw_vals]


def parse_t0(t0_str):
    return datetime.datetime.strptime(t0_str, '"YYYY/mm/dd hh:MM:SS",')


def parse_time_increment(intv_str, unit_str):
    interval = float(intv_str.strip(','))

    if unit_str == '"WEEKS",':
        return datetime.timedelta(weeks=interval)
    elif unit_str == '"DAYS",':
        return datetime.timedelta(days=interval)

    arcpy.AddError('Unhandled interval unit type: ' + unit_str)


def add_chart_values(chart_table, loc_id, html_str):
    arcpy.AddMessage(html_str)
    lines = html_str.split()

    named_lines = {}
    for line in lines:
        if '=' in line:
            parts = line.split('=')
            name = parts[0].strip()
            named_lines[name] = parts[1].strip()

    raw_vals = parse_raw_vals(named_lines['var ts'])
    base_time = parse_t0(named_lines['t0'])
    time_increment = parse_time_increment(named_lines['intv'], named_lines['unit'])


def create_chart_table(gdb):
    tbl = arcpy.CreateTable_management(out_path=gdb, out_name='Chart_Values')
    arcpy.AddField_management(in_table=tbl, field_name='LocationID', field_type='Long')
    arcpy.AddField_management(in_table=tbl, field_name='Date', field_type='Date')
    arcpy.AddField_management(in_table=tbl, field_name='ValueType', field_type='Text', field_length=50)
    arcpy.AddField_management(in_table=tbl, field_name='Value', field_type='Float')

    return tbl


def create_database(workspace, name, stc_fc):
    gdb = arcpy.CreateFileGDB_management(out_folder_path=workspace, out_name=name)
    fc = arcpy.FeatureClassToFeatureClass_conversion(in_features=stc_fc, out_path=gdb, out_name='STC_Features')

    tbl = create_chart_table(gdb)

    fill_chart_table(stc_fc=fc, chart_table=tbl)


def fill_chart_table(stc_fc, chart_table):
    fields = ['LOCATION', 'HTML_CHART']
    with arcpy.da.SearchCursor(stc_fc, fields) as cursor:
        for row in cursor:
            loc = row[0]
            html_str = row[1]
            add_chart_values(chart_table=chart_table, loc_id=loc, html_str=html_str)
