"""
A quick script to clean up duplicate postcodes introduced during development of UpdateTotalCasesByPostcode.py.
"""
from arcgis.gis import GIS
from arcgis.features import FeatureLayer

target = None# r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/Total_Cases_By_Postcode/FeatureServer/0'

gis = GIS(profile='agol_graphc')

target_layer = FeatureLayer(target)
query_result = target_layer.query()
postcode_features = query_result.features

known_postcodes = []
duplicates = []
for postcode_feature in postcode_features:
    postcode = postcode_feature.attributes['PostCode']
    if postcode in known_postcodes:
        duplicates.append(postcode_feature.attributes['OBJECTID'])
    else:
        known_postcodes.append(postcode)

result = target_layer.edit_features(deletes=str(duplicates))
print(result)