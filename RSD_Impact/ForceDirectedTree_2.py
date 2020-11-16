import xlrd
import json
import datetime


source = r'E:\Documents2\ANU\Projects\RSD_Impact\RSPH ANU Engagement and Impact Tracker.xlsx'
target = r'E:\Documents2\ANU\Projects\RSD_Impact\ForceDirectedTree_2.html'


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

chart.source_data = {data_values};

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

    new_item = {'name': item_value, 'value': 0}
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
    <p>Tree = TotalEngagements|Stakeholder name|Activity type|Academic lead email address|duration in days</p>
    <p>This is a Force Directed Tree demonstrator.<br>
    A Force Directed Tree is created using two or more fields organized in a hierarchical sequence, and a weighting value to be applied to the last
    node in the tree. In this example the weighting factor for each item is calculated by counting the number of days between the start and end date
    for the item.<br>
    Different charts can be created by selecting different combinations of fields and different weighting values.</p>
    <p>Additional weighting values can be applied to intermediate nodes. </p>
    <p>More focused charts can be created by selecting a subsets of source_data from the table.</p> 
    <p>Items do not have to have a single common root.  It is possible to have several root nodes on the chart.  For example, Stakeholder name could
    be used as a root, which would result in a separate tree for each stakeholder.
    <p>If an item was reported as a date range but did not have an end date reported, then the end date was set to the date at the time the chart was
    created.<br>
    If an item was reported as a single date then the item was assessed as having a weight of 1.</p>
</div>"""


def create_chart():
    chart_data = {'name': 'Total Engagements Score', 'children': []}
    source_data, date_mode = get_data()

    for row in source_data:
        stakeholder_name_item = stakeholder_names(row['Stakeholder name'], chart_data['children'])
        activity_type_item = activity_type(row['Activity type'], stakeholder_name_item['children'])
        academic_lead_item = academic_lead(row['Academic lead email address'], activity_type_item['children'])

        activity_start_date = parse_date(row['Activity Start Date'], date_mode)
        activity_end_date = parse_date(row['Activity End Date'], date_mode)

        duration = get_duration(activity_start_date, activity_end_date)
        academic_lead_item['value'] += duration

    data_string = json.dumps([chart_data])
    html_string = template().replace('{data_values}', data_string).replace('{footer}', footer())

    with open(target, 'w') as f:
        f.write(html_string)


if __name__ == "__main__":
    create_chart()
