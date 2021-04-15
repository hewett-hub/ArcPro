import arcpy
import datetime
import json
from dateutil.relativedelta import relativedelta


def parse_values(values_str):
    if values_str is None:
        return None

    return json.loads(values_str.strip(','))


def parse_t0(t0_str):
    return datetime.datetime.strptime(t0_str, '"YYYY/mm/dd hh:MM:SS",')


def parse_time_increment(intv_str, unit_str):
    interval = int(intv_str.strip(','))

    if unit_str == '"YEARS",':
        return relativedelta(years=interval)
    if unit_str == '"WEEKS",':
        return relativedelta(weeks=interval)
    elif unit_str == '"DAYS",':
        return relativedelta(days=interval)

    arcpy.AddError('Unhandled interval unit type: ' + unit_str)


def add_items(chart_table, loc_id, name, val_list, base_time, interval):
    if val_list is None:
        return None

    fields = ['LocationID', 'Date', 'ValueType', 'Value']
    row_time = base_time
    with arcpy.da.InsertCursor(chart_table, fields) as cursor:
        for item in val_list:
            row = [loc_id, row_time, name, item]
            cursor.insert_row(row)
            row_time += interval

    # return last row time for use as start time in predicted items.
    return row_time


def add_chart_values(chart_table, loc_id, html_str):
    arcpy.AddMessage(html_str)

    # split html str into lines
    lines = html_str.split()

    # get html var lines
    named_lines = {}
    for line in lines:
        if '=' in line:
            parts = line.split('=')
            name = parts[0].strip()
            named_lines[name] = parts[1].strip()

    # parse var lines that can be used in chart.
    ts_vals = parse_values(named_lines['var ts'])
    base_time = parse_t0(named_lines['t0'])
    time_increment = parse_time_increment(named_lines['intv'], named_lines['unit'])
    fit_vals = parse_values(named_lines.get('fit'))
    forecast_vals = parse_values(named_lines.get('forecast'))
    conf_int = parse_values(named_lines.get('conf_int'))

    # break out lo and hi conf values.
    if conf_int:
        conf_low = [x[0] for x in conf_int]
        conf_hi = [x[1] for x in conf_int]
    else:
        conf_low = None
        conf_hi = None

    # add items to table
    # known values
    future_time = add_items(chart_table, loc_id, 'ts', ts_vals, base_time, time_increment)
    add_items(chart_table, loc_id, 'fit', fit_vals, base_time, time_increment)

    # future values
    add_items(chart_table, loc_id, 'forecast', forecast_vals, future_time, time_increment)
    add_items(chart_table, loc_id, 'conf_low', conf_low, future_time, time_increment)
    add_items(chart_table, loc_id, 'conf_hi', conf_hi, future_time, time_increment)

    return chart_table


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

    return gdb


def fill_chart_table(stc_fc, chart_table):
    fields = ['LOCATION', 'HTML_CHART']
    with arcpy.da.SearchCursor(stc_fc, fields) as cursor:
        for row in cursor:
            loc = row[0]
            html_str = row[1]
            arcpy.AddMessage('Loc: {}'.format(loc))
            add_chart_values(chart_table=chart_table, loc_id=loc, html_str=html_str)

    return chart_table


if __name__ == "__main__":
    workspace_in = arcpy.GetParameterAsText(0)
    gdb_name_in = arcpy.GetParameterAsText(1)
    stc_fc_in = arcpy.GetParameterAsText(2)

    create_database(workspace=workspace_in, name=gdb_name_in, stc_fc=stc_fc_in)
