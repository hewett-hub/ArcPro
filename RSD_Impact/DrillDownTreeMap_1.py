import xlrd
import json
import datetime


source = r'E:\Documents2\ANU\Projects\RSD_Impact\RSPH ANU Engagement and Impact Tracker.xlsx'
target = r'E:\Documents2\ANU\Projects\RSD_Impact\DrillDownTreeMap_1.html'
tier_0 = 'Activity type'
tier_1 = 'Stakeholder name'
tier_2 = 'Academic lead email address'


def template():
    return """
<!-- Styles -->
<style>
#chartdiv {
  width: 100%;
  height: 500px;
}
</style>

<!-- Resources -->
<script src="https://www.amcharts.com/lib/4/core.js"></script>
<script src="https://www.amcharts.com/lib/4/charts.js"></script>
<script src="https://www.amcharts.com/lib/4/themes/animated.js"></script>

<!-- Chart code -->
<script>
am4core.ready(function() {

// Themes begin
am4core.useTheme(am4themes_animated);
// Themes end

var source_data = {data_values}

function processData(source_data) {
  return source_data;
}

// create chart
var chart = am4core.create("chartdiv", am4charts.TreeMap);
chart.hiddenState.properties.opacity = 0; // this makes initial fade in effect

// only one level visible initially
chart.maxLevels = 1;
// define source_data fields
chart.dataFields.value = "count";
chart.dataFields.name = "name";
chart.dataFields.children = "children";
chart.homeText = "{title}";

// enable navigation
chart.navigationBar = new am4charts.NavigationBar();

// level 0 series template
var level0SeriesTemplate = chart.seriesTemplates.create("0");
level0SeriesTemplate.strokeWidth = 2;

// by default only current level series bullets are visible, but as we need brand bullets to be visible all the time, we modify it's hidden state
level0SeriesTemplate.bulletsContainer.hiddenState.properties.opacity = 1;
//level0SeriesTemplate.bulletsContainer.hiddenState.properties.visible = true;

var bullet0 = level0SeriesTemplate.bullets.push(new am4charts.LabelBullet());
bullet0.locationX = 0.5;
bullet0.locationY = 0.5;
bullet0.label.text = "{name}";
bullet0.label.fill = am4core.color("#ffffff");
bullet0.label.fontSize = 12;
bullet0.label.fillOpacity = 0.7;

// create hover state
var columnTemplate = level0SeriesTemplate.columns.template;
var hoverState = columnTemplate.states.create("hover");

// darken
hoverState.adapter.add("fill", function (fill, target) {
  if (fill instanceof am4core.Color) {
    return am4core.color(am4core.colors.brighten(fill.rgb, -0.2));
  }
  return fill;
})

// level1 series template
var level1SeriesTemplate = chart.seriesTemplates.create("1");
level1SeriesTemplate.columns.template.fillOpacity = 0;

var bullet1 = level1SeriesTemplate.bullets.push(new am4charts.LabelBullet());
bullet1.locationX = 0.5;
bullet1.locationY = 0.5;
bullet1.label.text = "{name}";
bullet1.label.fill = am4core.color("#ffffff");
bullet1.label.fontSize = 12;
bullet1.label.fillOpacity = 0.7;

// level2 series template
var level2SeriesTemplate = chart.seriesTemplates.create("2");
level2SeriesTemplate.columns.template.fillOpacity = 0;

var bullet2 = level2SeriesTemplate.bullets.push(new am4charts.LabelBullet());
bullet2.locationX = 0.5;
bullet2.locationY = 0.5;
bullet2.label.text = "{name}";
bullet2.label.fill = am4core.color("#ffffff");
bullet2.label.fontSize = 12;
bullet2.label.fillOpacity = 0.7;

chart.source_data = processData(source_data);

}); // end am4core.ready()
</script>

<!-- HTML -->
<div id="chartdiv"></div>

{footer}
"""


def get_data():

    workbook = xlrd.open_workbook(source, on_demand=True)
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


def parse_date(date_value, date_mode):
    if date_value:
        dt = xlrd.xldate_as_datetime(date_value, date_mode)
        return dt.date()
    else:
        return None


def get_duration(start_date, end_date):
    if start_date and end_date:
        return (end_date - start_date).days
    elif start_date:
        return (datetime.datetime.now().date() - start_date).days
    else:
        return 1


def academic_lead(academic_lead_name, academic_leads):
    item_value = 'Academic Lead: ' + academic_lead_name
    for item in academic_leads:
        if item_value == item['name']:
            return item

    new_item = {'name': item_value, 'count': 0}
    academic_leads.append(new_item)
    return new_item


def activity_type(activity_type_name, activity_types):
    item_value = 'Activity Type: ' + activity_type_name
    for item in activity_types:
        if item_value == item['name']:
            return item

    new_item = {'name': item_value, 'children': []}
    activity_types.append(new_item)
    return new_item


def stakeholder_names(stakeholder_name, stakeholders):
    item_value = 'Stakeholder Name: ' + stakeholder_name
    for item in stakeholders:
        if item_value == item['name']:
            return item

    new_item = {'name': item_value, 'children': []}
    stakeholders.append(new_item)
    return new_item


def footer():
    return """
<div>
    <p>Tree = Stakeholder name|Activity type|Academic lead email address|duration in days</p>
    <p>This is a Drill Down Tree Map demonstrator.<br>
    A Drill Down Tree Map is created using two or more fields organized in a hierarchical sequence, and a weighting value to be applied to the last
    node in the tree. In this example the weighting factor for each item is calculated by counting the number of days between the start and end date
    for the item.<br>
    Different charts can be created by selecting different combinations of fields and different weighting values.</p>
    <p>Additional weighting values can be applied to intermediate nodes. </p>
    <p>More focused charts can be created by selecting a subsets of source_data from the table.</p> 
    <p>If an item was reported as a date range but did not have an end date reported, then the end date was set to the date at the time the chart was
    created.<br>
    If an item was reported as a single date then the item was assessed as having a weight of 1.</p>
</div>"""


def create_chart():
    chart_data = []
    source_data, date_mode = get_data()

    for row in source_data:
        stakeholder_name_item = stakeholder_names(row['Stakeholder name'], chart_data)
        activity_type_item = activity_type(row['Activity type'], stakeholder_name_item['children'])
        academic_lead_item = academic_lead(row['Academic lead email address'], activity_type_item['children'])

        activity_start_date = parse_date(row['Activity Start Date'], date_mode)
        activity_end_date = parse_date(row['Activity End Date'], date_mode)

        duration = get_duration(activity_start_date, activity_end_date)
        academic_lead_item['count'] += duration

    data_string = json.dumps(chart_data)
    html_string = template().\
        replace('{data_values}', data_string).\
        replace('{footer}', footer()).\
        replace('{title}', 'RSPH Demo')

    with open(target, 'w') as f:
        f.write(html_string)


if __name__ == "__main__":
    create_chart()
