import csv
import json


source = r'E:\Downloads\COVID-19-master\csse_covid_19_data\csse_covid_19_time_series\time_series_covid19_confirmed_global.csv'
target = r'E:\Documents2\ANU\Projects\COVID19\ConfirmedCases_RadarChart.html'


def template():
    return """
<!-- Styles -->
<style>
#chartdiv {
  width: 100%;
  height: 700px;
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

var case_counts = {data_values}

var start_date = 0;
var end_date = {end_date};
var current_day = {end_date};
var colorSet = new am4core.ColorSet();

var chart = am4core.create("chartdiv", am4charts.RadarChart);
chart.hiddenState.properties.opacity = 0;

chart.startAngle = 270 - 180;
chart.endAngle = 270 + 180;

chart.padding(5,15,5,10)
chart.radius = am4core.percent(65);
chart.innerRadius = am4core.percent(40);

// year label goes in the middle
var yearLabel = chart.radarContainer.createChild(am4core.Label);
yearLabel.horizontalCenter = "middle";
yearLabel.verticalCenter = "middle";
yearLabel.fill = am4core.color("#673AB7");
yearLabel.fontSize = 30;
yearLabel.text = String(current_day);

// zoomout button
var zoomOutButton = chart.zoomOutButton;
zoomOutButton.dx = 0;
zoomOutButton.dy = 0;
zoomOutButton.marginBottom = 15;
zoomOutButton.parent = chart.rightAxesContainer;

// scrollbar
chart.scrollbarX = new am4core.Scrollbar();
chart.scrollbarX.parent = chart.rightAxesContainer;
chart.scrollbarX.orientation = "vertical";
chart.scrollbarX.align = "center";
chart.scrollbarX.exportable = false;

// vertical orientation for zoom out button and scrollbar to be positioned properly
chart.rightAxesContainer.layout = "vertical";
chart.rightAxesContainer.padding(120, 20, 120, 20);

// category axis
var categoryAxis = chart.xAxes.push(new am4charts.CategoryAxis());
categoryAxis.renderer.grid.template.location = 0;
categoryAxis.dataFields.category = "region";

var categoryAxisRenderer = categoryAxis.renderer;
var categoryAxisLabel = categoryAxisRenderer.labels.template;
categoryAxisLabel.location = 0.5;
categoryAxisLabel.radius = 28;
categoryAxisLabel.relativeRotation = 90;

categoryAxisRenderer.fontSize = 11;
categoryAxisRenderer.minGridDistance = 10;
categoryAxisRenderer.grid.template.radius = -25;
categoryAxisRenderer.grid.template.strokeOpacity = 0.05;
categoryAxisRenderer.grid.template.interactionsEnabled = false;

categoryAxisRenderer.ticks.template.disabled = true;
categoryAxisRenderer.axisFills.template.disabled = true;
categoryAxisRenderer.line.disabled = true;

categoryAxisRenderer.tooltipLocation = 0.5;
categoryAxis.tooltip.defaultState.properties.opacity = 0;

// value axis
var valueAxis = chart.yAxes.push(new am4charts.ValueAxis());
valueAxis.min = 0;
valueAxis.max = {max_value};
valueAxis.strictMinMax = true;
valueAxis.tooltip.defaultState.properties.opacity = 0;
valueAxis.tooltip.animationDuration = 0;
valueAxis.cursorTooltipEnabled = true;
valueAxis.zIndex = 10;

var valueAxisRenderer = valueAxis.renderer;
valueAxisRenderer.axisFills.template.disabled = true;
valueAxisRenderer.ticks.template.disabled = true;
valueAxisRenderer.minGridDistance = 20;
valueAxisRenderer.grid.template.strokeOpacity = 0.05;


// series
var series = chart.series.push(new am4charts.RadarColumnSeries());
series.columns.template.width = am4core.percent(90);
series.columns.template.strokeOpacity = 0;
series.dataFields.valueY = "value" + current_day;
series.dataFields.categoryX = "region";
series.tooltipText = "{categoryX}:{valueY.value}";

// this makes columns to be of a different color, depending on value
series.heatRules.push({ target: series.columns.template, property: "fill", minValue: 0, maxValue: {max_value}, min: am4core.color("#673AB7"), max: am4core.color("#F44336"), dataField: "valueY" });

// cursor
var cursor = new am4charts.RadarCursor();
chart.cursor = cursor;
cursor.behavior = "zoomX";

cursor.xAxis = categoryAxis;
cursor.innerRadius = am4core.percent(40);
cursor.lineY.disabled = true;

cursor.lineX.fillOpacity = 0.2;
cursor.lineX.fill = am4core.color("#000000");
cursor.lineX.strokeOpacity = 0;
cursor.fullWidthLineX = true;

// year slider
var dateSliderContainer = chart.createChild(am4core.Container);
dateSliderContainer.layout = "vertical";
dateSliderContainer.padding(0, 38, 0, 38);
dateSliderContainer.width = am4core.percent(100);

var dateSlider = dateSliderContainer.createChild(am4core.Slider);
dateSlider.events.on("rangechanged", function () {
    updateRadarData(start_date + Math.round(dateSlider.start * (end_date - start_date)));
})
dateSlider.orientation = "horizontal";
dateSlider.start = 0.5;
dateSlider.exportable = false;

chart.source_data = generateRadarData();

function generateRadarData() {
    var source_data = [];
    var i = 0;
    for (var country in case_counts) {
        var countryData = case_counts[country];

        countryData.forEach(function (region) {
            var rawDataItem = { "region": region[0] }

            for (var y = 2; y < region.length; y++) {
                rawDataItem["value" + (start_date + y - 2)] = region[y];
            }

            source_data.push(rawDataItem);
        });

        createRange(country, countryData, i);
        i++;

    }
    return source_data;
}


function updateRadarData(date) {
    if (current_day != date) {
        current_day = date;
        yearLabel.text = "Day: " + String(current_day);
        yearLabel.text = getDateString(date);
        series.dataFields.valueY = "value" + current_day;
        chart.invalidateRawData();
    }
}

function getDateString(date_increment){
    var dateString  = "{start_date}";
    var year        = dateString.substring(0,4);
    var month       = dateString.substring(4,6);
    var day         = dateString.substring(6,8);

    var date        = new Date(year, month, day);
    date.setDate(date.getDate() + date_increment)
    return date.getDate() + '/' + date.getMonth() + '/' + date.getFullYear()
}

function createRange(name, countryData, index) {

    var axisRange = categoryAxis.axisRanges.create();
    axisRange.axisFill.interactionsEnabled = true;
    axisRange.text = name;
    // first region
    axisRange.category = countryData[0][0];
    // last region
    axisRange.endCategory = countryData[countryData.length - 1][0];

    // every 3rd color for a bigger contrast
    axisRange.axisFill.fill = colorSet.getIndex(index * 3);
    axisRange.grid.disabled = true;
    axisRange.label.interactionsEnabled = false;
    axisRange.label.bent = true;

    var axisFill = axisRange.axisFill;
    axisFill.innerRadius = -0.001; // almost the same as 100%, we set it in pixels as later we animate this property to some pixel value
    axisFill.radius = -20; // negative radius means it is calculated from max radius
    axisFill.disabled = false; // as regular fills are disabled, we need to enable this one
    axisFill.fillOpacity = 1;
    axisFill.togglable = true;

    axisFill.showSystemTooltip = true;
    axisFill.readerTitle = "click to zoom";
    axisFill.cursorOverStyle = am4core.MouseCursorStyle.pointer;

    axisFill.events.on("hit", function (event) {
        var dataItem = event.target.dataItem;
        if (!event.target.isActive) {
            categoryAxis.zoom({ start: 0, end: 1 });
        }
        else {
            categoryAxis.zoomToCategories(dataItem.category, dataItem.endCategory);
        }
    })

    // hover state
    var hoverState = axisFill.states.create("hover");
    hoverState.properties.innerRadius = -10;
    hoverState.properties.radius = -25;

    var axisLabel = axisRange.label;
    axisLabel.location = 0.5;
    axisLabel.fill = am4core.color("#ffffff");
    axisLabel.radius = 3;
    axisLabel.relativeRotation = 0;
}

var slider = dateSliderContainer.createChild(am4core.Slider);
slider.start = 1;
slider.exportable = false;
slider.events.on("rangechanged", function () {
    var start = slider.start;

    chart.startAngle = 270 - start * 179 - 1;
    chart.endAngle = 270 + start * 179 + 1;

    valueAxis.renderer.axisAngle = chart.startAngle;
})

}); // end am4core.ready()
</script>

<!-- HTML -->
<div id="chartdiv"></div>

{footer}
"""


def get_data():
    data = {}
    headers = None
    max_value = 0
    with open(source) as csv_file:
        rows = csv.reader(csv_file)
        for row in rows:
            if headers:
                region = row[0]
                country = row[1]
                if not region:
                    region = country
                country_data = data.get(country, None)
                if not country_data:
                    country_data = []
                    data[country] = country_data
                region_data = [region]
                case_values = [int(x) for x in row[4:]]
                max_item = max(case_values)
                if max_item > max_value:
                    max_value = max_item
                region_data.extend(case_values)
                country_data.append(region_data)
            else:
                headers = row

    start_date = parse_date(headers[4])
    return data, start_date, len(headers) - 4, max_value


def parse_date(date_value):
    if date_value:
        parts = date_value.split('/')
        year_part = parts[2]
        month_part = parts[0].zfill(2)
        day_part = parts[1].zfill(2)
        return '20{}{}{}'.format(year_part, month_part, day_part)
    else:
        return None


def footer():
    return """
<div>
    <p>This chart shows the global COVID19 cases over time.  Use the slider to adjust the dates.</p>
    <p>source_data values are sourced from the John Hopkins COVID19 dataset.</p>
    <p>This is a Radar Timeline demonstrator created by GRAPHC using amCharts.<br>
</div>"""


def create_chart():
    chart_data = []
    chart_data, start_date, date_count, max_value = get_data()

    print(max_value)
    data_string = json.dumps(chart_data)
    html_string = template().\
        replace('{data_values}', data_string).\
        replace('{footer}', footer()).\
        replace('{start_date}', start_date).\
        replace('{end_date}', str(date_count)).\
        replace('{max_value}', str(max_value))

    with open(target, 'w') as f:
        f.write(html_string)


if __name__ == "__main__":
    create_chart()
