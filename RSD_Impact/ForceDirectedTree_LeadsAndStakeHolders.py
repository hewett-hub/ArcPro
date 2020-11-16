import xlrd
import json


source = r'E:\Documents2\ANU\Projects\RSD_Impact\RSPH ANU Engagement and Impact Tracker.xlsx'
target = r'E:\Documents2\ANU\Projects\RSD_Impact\test.html'


def template():
    return """

<!-- Styles -->
<style>
#chartdiv {
  width: 100%;
  height:100%;
  max-width:100%;
}
</style>

<!-- Resources -->
<script src="https://www.amcharts.com/lib/4/core.js"></script>
<script src="https://www.amcharts.com/lib/4/charts.js"></script>
<script src="https://www.amcharts.com/lib/4/plugins/forceDirected.js"></script>
<script src="https://www.amcharts.com/lib/4/themes/animated.js"></script>

<!-- Chart code -->
<script>
am4core.ready(function() {

// Themes begin
am4core.useTheme(am4themes_animated);
// Themes end

var chart = am4core.create("chartdiv", am4plugins_forceDirected.ForceDirectedTree);
var networkSeries = chart.series.push(new am4plugins_forceDirected.ForceDirectedSeries())

chart.source_data = [
  {data_values}
];

networkSeries.dataFields.value = "value";
networkSeries.dataFields.name = "name";
networkSeries.dataFields.children = "children";
networkSeries.nodes.template.tooltipText = "{name}:{value}";
networkSeries.nodes.template.fillOpacity = 1;

networkSeries.nodes.template.label.text = "{name}"
networkSeries.fontSize = 10;

networkSeries.links.template.strokeWidth = 1;

var hoverState = networkSeries.links.template.states.create("hover");
hoverState.properties.strokeWidth = 3;
hoverState.properties.strokeOpacity = 1;

networkSeries.nodes.template.events.on("over", function(event) {
  event.target.dataItem.childLinks.each(function(link) {
    link.isHover = true;
  })
  if (event.target.dataItem.parentLink) {
    event.target.dataItem.parentLink.isHover = true;
  }

})

networkSeries.nodes.template.events.on("out", function(event) {
  event.target.dataItem.childLinks.each(function(link) {
    link.isHover = false;
  })
  if (event.target.dataItem.parentLink) {
    event.target.dataItem.parentLink.isHover = false;
  }
})

}); // end am4core.ready()
</script>

<!-- HTML -->
<div id="chartdiv"></div>'"""


def get_data():
    workbook = xlrd.open_workbook(source, on_demand=True)
    worksheet = workbook.sheet_by_index(1)
    first_row = []  # The row where we stock the name of the column
    for col in range(worksheet.ncols):
        first_row.append(worksheet.cell_value(0, col))
    # tronsform the workbook to a list of dictionnary
    data = []
    for row in range(1, worksheet.nrows):
        elm = {}
        for col in range(worksheet.ncols):
            elm[first_row[col]] = worksheet.cell_value(row, col)
        data.append(elm)
    return data


def academic_lead(academic_lead_name, academic_leads):
    item_value = 'Academic Lead: ' + academic_lead_name
    for item in academic_leads:
        if item_value == item['name']:
            return item

    new_item = {'name': item_value, 'children': []}
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


def stakeholder_type(stakeholder_type_name, stakeholder_type_names):
    item_value = 'Stakeholder Type: ' + stakeholder_type_name
    for item in stakeholder_type_names:
        if item_value == item['name']:
            return item

    new_item = {'name': item_value, 'children': []}
    stakeholder_type_names.append(new_item)
    return new_item


def stakeholder(stakeholder_name, stakeholders):
    item_value = 'Stakeholder: ' + stakeholder_name
    for item in stakeholders:
        if item['name'] == item_value:
            item['value'] += 1
            return item

    stakeholders.append({'name': item_value, 'value': 1})


def create_chart():
    chart_data = {'name': "Total Engagements", 'children': []}
    source_data = get_data()

    for row in source_data:
        academic_lead_item = academic_lead(row['Academic lead email address'], chart_data['children'])
        activity_type_item = activity_type(row['Type of Activity'], academic_lead_item['children'])
        stakeholder_type_item = stakeholder_type(row['Type of stakeholder'], activity_type_item['children'])
        stakeholder(row['Stakeholder name'], stakeholder_type_item['children'])

    data_string = json.dumps(chart_data)
    html_string = template().replace('{data_values}', data_string)

    with open(target, 'w') as f:
        f.write(html_string)


if __name__ == "__main__":
    create_chart()
