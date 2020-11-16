import arcpy
import pprint

source = r'E:\Documents2\Data\ABS\2016\GDA94\ASGS3_NonABSStructures.gdb\POA_2016_AUST'

out_csv = r'E:\Documents2\tmp\PostcodeAdjacencies2016.csv'

geometries = {}
where_clause = 'Shape_Length > 0'
fields = ['POA_CODE16', 'SHAPE@']
with arcpy.da.SearchCursor(source, fields, where_clause) as cursor:
    for row in cursor:
        geometries[row[0]] = row[1]

lines = []

lyr = arcpy.MakeFeatureLayer_management(in_features=source, out_layer='poa_layer', where_clause=where_clause)
for poa, poa_shape in geometries.items():
    print(poa)
    arcpy.SelectLayerByLocation_management(lyr, "INTERSECT", poa_shape, search_distance='100 Meters')
    with arcpy.da.SearchCursor(lyr, fields) as cursor:
        for row in cursor:
            poa2 = row[0]
            if poa2 != poa:
                lines.append('{},{}\n'.format(poa, poa2))

with open(out_csv, 'w') as out_file:
    out_file.writelines(lines)

