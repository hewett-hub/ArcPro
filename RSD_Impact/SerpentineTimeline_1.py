import xlrd
import datetime


source = r'E:\Documents2\ANU\Projects\RSD_Impact\RSPH ANU Engagement and Impact Tracker.xlsx'
category_field = 'Stakeholder name'
task_field = 'Academic lead email address'

target = r'E:\Documents2\ANU\Projects\RSD_Impact\SerpentineTimeline_1.html'


def template():
    return """<!-- Styles -->
<style>
#chartdiv {
  width: 100%;
  height: 600px;
}

.demo-theme-dark .demo-background {
  background: #000;
}

</style>

<!-- Resources -->
<script src="https://www.amcharts.com/lib/4/core.js"></script>
<script src="https://www.amcharts.com/lib/4/charts.js"></script>
<script src="https://www.amcharts.com/lib/4/plugins/timeline.js"></script>
<script src="https://www.amcharts.com/lib/4/plugins/bullets.js"></script>
<script src="https://www.amcharts.com/lib/4/themes/animated.js"></script>

<!-- Chart code -->
<script>
am4core.ready(function() {

// Themes begin
am4core.useTheme(am4themes_animated);
// Themes end

var chart = am4core.create("chartdiv", am4plugins_timeline.SerpentineChart);
chart.curveContainer.padding(50, 20, 50, 150);
chart.levelCount = 4;
chart.yAxisRadius = am4core.percent(25);
chart.yAxisInnerRadius = am4core.percent(-25);
chart.maskBullets = false;

var colorSet = new am4core.ColorSet();
colorSet.saturation = 0.5;

chart.source_data = {data_values};

chart.dateFormatter.dateFormat = "yyyy-MM-dd";
chart.dateFormatter.inputDateFormat = "yyyy-MM-dd";
chart.fontSize = 11;

var categoryAxis = chart.yAxes.push(new am4charts.CategoryAxis());
categoryAxis.dataFields.category = "category";
categoryAxis.renderer.grid.template.disabled = true;
categoryAxis.renderer.labels.template.paddingRight = 25;
categoryAxis.renderer.minGridDistance = 10;
categoryAxis.renderer.innerRadius = -60;
categoryAxis.renderer.radius = 60;

var dateAxis = chart.xAxes.push(new am4charts.DateAxis());
dateAxis.renderer.minGridDistance = 70;
dateAxis.baseInterval = { count: 1, timeUnit: "day" };
dateAxis.renderer.tooltipLocation = 0;
dateAxis.startLocation = -0.5;
dateAxis.renderer.line.strokeDasharray = "1,4";
dateAxis.renderer.line.strokeOpacity = 0.6;
dateAxis.tooltip.background.fillOpacity = 0.2;
dateAxis.tooltip.background.cornerRadius = 5;
dateAxis.tooltip.label.fill = new am4core.InterfaceColorSet().getFor("alternativeBackground");
dateAxis.tooltip.label.paddingTop = 7;

var labelTemplate = dateAxis.renderer.labels.template;
labelTemplate.verticalCenter = "middle";
labelTemplate.fillOpacity = 0.7;
labelTemplate.background.fill = new am4core.InterfaceColorSet().getFor("background");
labelTemplate.background.fillOpacity = 1;
labelTemplate.padding(7, 7, 7, 7);

var series = chart.series.push(new am4plugins_timeline.CurveColumnSeries());
series.columns.template.height = am4core.percent(20);
series.columns.template.tooltipText = "{task}: [bold]{openDateX}[/] - [bold]{dateX}[/]";

series.dataFields.openDateX = "start";
series.dataFields.dateX = "end";
series.dataFields.categoryY = "category";
series.columns.template.propertyFields.fill = "color"; // get color from source_data
series.columns.template.propertyFields.stroke = "color";
series.columns.template.strokeOpacity = 0;

var bullet = series.bullets.push(new am4charts.CircleBullet());
bullet.circle.radius = 3;
bullet.circle.strokeOpacity = 0;
bullet.propertyFields.fill = "color";
bullet.locationX = 0;


var bullet2 = series.bullets.push(new am4charts.CircleBullet());
bullet2.circle.radius = 3;
bullet2.circle.strokeOpacity = 0;
bullet2.propertyFields.fill = "color";
bullet2.locationX = 1;


var imageBullet1 = series.bullets.push(new am4plugins_bullets.PinBullet());
imageBullet1.disabled = true;
imageBullet1.propertyFields.disabled = "disabled1";
imageBullet1.locationX = 1;
imageBullet1.circle.radius = 20;
imageBullet1.propertyFields.stroke = "color";
imageBullet1.background.propertyFields.fill = "color";
imageBullet1.image = new am4core.Image();
imageBullet1.image.propertyFields.href = "image1";

var imageBullet2 = series.bullets.push(new am4plugins_bullets.PinBullet());
imageBullet2.disabled = true;
imageBullet2.propertyFields.disabled = "disabled2";
imageBullet2.locationX = 0;
imageBullet2.circle.radius = 20;
imageBullet2.propertyFields.stroke = "color";
imageBullet2.background.propertyFields.fill = "color";
imageBullet2.image = new am4core.Image();
imageBullet2.image.propertyFields.href = "image2";


var eventSeries = chart.series.push(new am4plugins_timeline.CurveLineSeries());
eventSeries.dataFields.dateX = "eventDate";
eventSeries.dataFields.categoryY = "category";
eventSeries.source_data = {event_series};
eventSeries.strokeOpacity = 0;

var flagBullet = eventSeries.bullets.push(new am4plugins_bullets.FlagBullet())
flagBullet.label.propertyFields.text = "letter";
flagBullet.locationX = 0;
flagBullet.tooltipText = "{description}";

chart.scrollbarX = new am4core.Scrollbar();
chart.scrollbarX.align = "center"
chart.scrollbarX.width = am4core.percent(85);

var cursor = new am4plugins_timeline.CurveCursor();
chart.cursor = cursor;
cursor.xAxis = dateAxis;
cursor.yAxis = categoryAxis;
cursor.lineY.disabled = true;
cursor.lineX.strokeDasharray = "1,4";
cursor.lineX.strokeOpacity = 1;

dateAxis.renderer.tooltipLocation2 = 0;
categoryAxis.cursorTooltipEnabled = false;



}); // end am4core.ready()
</script>

<!-- HTML -->
<div id="chartdiv"></div>
amCharts

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


def parse_dates(row, date_mode):
    if row['Does this activity relate to single or multiple dates?'] == 'Single date':
        start_date = xlrd.xldate_as_datetime(row['Activity Date'], date_mode)
        end_date = start_date + datetime.timedelta(days=1)
    else:
        start_date = xlrd.xldate_as_datetime(row['Activity Start Date'], date_mode)
        end_date_value = row['Activity End Date']
        if end_date_value:
            end_date = xlrd.xldate_as_datetime(end_date_value, date_mode)
        else:
            end_date = datetime.datetime.now()
    return start_date.date().strftime("%Y-%m-%d"), end_date.date().strftime("%Y-%m-%d")


def get_color_index(category, category_list):
    if category not in category_list:
        category_list.append(category)

    return str(category_list.index(category))


def event_series_values():
    return '['\
            '{ category: "", eventDate: "2020-03-15", letter: "A", description: "Mandatory Self Isolation for all international arrivals" }, ' \
            '{ category: "", eventDate: "2020-03-19", letter: "B", description: "Ruby Princes disembarked passengers in Sydney" }, '\
            '{ category: "", eventDate: "2020-03-20", letter: "C", description: "Borders closed to non residents." }, '\
            ']'


def footer():
    return """
<div>
    <p>Category = {}<br>Task = {}</p>
    <p>This is a Serpentine Timeline demonstrator.<br>
    A Serpentine Timeline is created using a Category field and a Task Field. <br>
    Different charts can be created by selecting different combinations of fields.</p>
    <p>More focused charts can be created by selecting a subset of source_data from the table.  This allows a 'third' element to be included in the chart.
    For example, if only Stakeholder Name = 'ABC News' was selected, we could then set Category = 'Type of Activity' and Task = 'Academic lead email
    address' to see who was making presentations to the ABC and what they were talking about. 
    <p>Event Flags can be defined manually or by using single date items from the csv.</p>
    <p>If an item was reported as a date range but did not have an end date reported, then the end date was set to the date at the time the chart was
    created.<br>
    If an item was reported as a single date then the end date was set to reported date +1 day.  This prevents the item from collapsing to a dot
    which can be hard to interact with.</p>
</div>""".format(category_field, task_field)


def create_chart():
    source_data, date_mode = get_data()

    category_list = []
    chart_data = ''
    for row in source_data:
        category = row[category_field]
        task = row[task_field]
        colour = get_color_index(category, category_list)
        start_date, end_date = parse_dates(row, date_mode)

        item_string = '{' \
                      '"category": "' + category + '", ' \
                      '"start": "' + start_date + '", ' \
                      '"end": "' + end_date + '", ' \
                      '"color": colorSet.getIndex(' + colour + '), ' \
                      '"task": "' + task + '"}'

        if chart_data:
            chart_data += ', ' + item_string
        else:
            chart_data = '[' + item_string

    chart_data += ']'

    html_string = template().replace('{data_values}', chart_data).replace('{event_series}', event_series_values()).replace('{footer}', footer())

    with open(target, 'w') as f:
        f.write(html_string)


if __name__ == "__main__":
    create_chart()
