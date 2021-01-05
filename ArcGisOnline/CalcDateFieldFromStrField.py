import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
from pprint import pprint

from arcgis.gis import GIS
from arcgis.features import FeatureLayer

lyr_url = r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Alerts_Editable/FeatureServer/0'
str_field = 'Dates'
date_field = 'DateValue'
profile = 'agol_graphc'
where_clause = '1=1'

gis = GIS(profile='agol_graphc')
layer = FeatureLayer(url=lyr_url)
fields = [str_field, date_field]
test_dt = datetime.datetime.now()
query_result = layer.query(out_fields=",".join(fields), where=where_clause)
updates = []

for row in query_result:
    date_str = row.attributes[str_field]
    date_val = parser.parse(date_str).replace(hour=12)
    if date_val > test_dt:
        date_val = date_val + relativedelta(years=-1)
    date_ms = date_val.timestamp() * 1000
    if row.attributes[date_field] != date_ms:
        row.attributes[date_field] = date_ms
        updates.append(row)

if updates:
    pprint(layer.edit_features(updates=updates))
else:
    print('No Updates Required')
