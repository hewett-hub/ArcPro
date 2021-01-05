import os
import arcpy
from arcpy.sa import *

# path to the Suicide Residences Points are found
point_fc = r'L:\CoreData\NCIS\LITS_20200729\NCIS.gdb\Residence_xy'

# path to the Suicide Incidents Points are found
# point_fc = r'L:\CoreData\NCIS\LITS_20200729\NCIS.gdb\Incidents_xy'

out_gdb = r'C:\tmp\Testing.gdb'
name_base = 'RescaleKD_SuicideRes_08_17_1k'
PointFilter = "ExclusionCode NOT IN (1) AND Incident_Year IN (2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008)"

# The theme names and filters for the various analyses to be performed on the input points.
theme_filters = {'ALLAges': PointFilter,
                 'Youth': PointFilter + " AND Age < 25",
                 'Adult': PointFilter + " AND Age > 24 AND Age < 45",
                 'Mature': PointFilter + " AND Age > 44 AND Age < 65",
                 'MidAge': PointFilter + " AND Age > 24 AND Age < 65",
                 'Elders': PointFilter + " AND Age > 64"}

cell_size = 500
search_radius = 1000

if not arcpy.Exists(out_gdb):
    folder_path, out_name = os.path.split(out_gdb)
    arcpy.CreateFileGDB_management(out_folder_path=folder_path, out_name=out_name)

arcpy.env.workspace = out_gdb
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference(3857)

arcpy.CheckOutExtension("Spatial")

try:
    for key, where_clause in theme_filters.items():
        out_name = '{}_{}'.format(name_base, key)
        out_path = os.path.join(out_gdb, out_name)
        if arcpy.Exists(out_path):
            raise RuntimeError('Result already exists: ' + out_path)

        filtered_points = arcpy.MakeFeatureLayer_management(in_features=point_fc, out_layer='lyr',
                                                            where_clause=where_clause)

        row_count = arcpy.GetCount_management(filtered_points)[0]

        kd_result = KernelDensity(in_features=filtered_points,
                                  population_field="NONE",
                                  cell_size=cell_size,
                                  search_radius=search_radius,
                                  area_unit_scale_factor="SQUARE_KILOMETERS",
                                  out_cell_values="DENSITIES",
                                  method="PLANAR",
                                  in_barriers=None)

        con_result = Con(kd_result, kd_result, None, "VALUE > 0")

        max_val = arcpy.GetRasterProperties_management(con_result, "MAXIMUM")

        transform_function = "Linear 0 {0} 0 # {0} #".format(max_val)
        out_raster = arcpy.sa.RescaleByFunction(in_raster=con_result,
                                                transformation_function=TfLinear(minimum=0, maximum=max_val,
                                                                                 lowerThreshold=0, valueBelowThreshold='#',
                                                                                 upperThreshold=max_val, valueAboveThreshold='#'),
                                                from_scale=0, to_scale=20)

        out_raster.save(out_path)

        arcpy.Delete_management(filtered_points)
        arcpy.Delete_management(kd_result)
        arcpy.Delete_management(con_result)
        print(out_name)

finally:
    arcpy.CheckInExtension("Spatial")