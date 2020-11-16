import arcpy
import os
import time

# mb centroids in original abs2016 projection
unsimplified_meshblock_centroids = r'E:\Documents2\Data\ABS\2016\GDA94\ABS2016_MB.gdb\InsideCentroids'
umc_id_field = r'MB_CODE16'

# simplified mb polygons
simplified_meshblocks = r'E:\Documents2\Data\ABS\2016\WGS84wmas\ASGS1_MainStructure_Simp100.gdb\MB_2016_AUST'
sm_id_field = r'MB_CODE16'

# unsimplified output regions.
unsimplified_lgas = r'E:\Documents2\Data\ABS\2019\Source\LGA_2019_AUST.shp'
ul_id_field = r'LGA_CODE19'

# output spatial reference srid
out_srid = 3857  # WGS84 wmas

# output feature class
out_features = r'E:\Documents2\Data\ABS\2019\ABS2019_LGA.gdb\Simplified_Boundaries'

# scratch workspace to be used.
workspace = r'E:\Documents2\tmp\wkg.gdb'


tagged_centroids = None
tagged_polygons = None
dissolved_mbs = None

try:
    # calc timestamps for unique naming purposes.
    tag = str(int(time.time()))

    # apply region source_data (specifically, ids) to mb centroids
    print('Executing Identity')
    tagged_centroids = os.path.join(workspace, 'centroids' + tag)
    arcpy.Identity_analysis(in_features=unsimplified_meshblock_centroids, identity_features=unsimplified_lgas,
                            out_feature_class=tagged_centroids, join_attributes="ALL",
                            cluster_tolerance="", relationship="NO_RELATIONSHIPS")
    arcpy.AddIndex_management(tagged_centroids, umc_id_field, 'idx_0', 'UNIQUE')

    # copy simplified mb polygons so region ids can be joined in next step.
    print('Executing MB Copy')
    tagged_polygons = os.path.join(workspace, 'polygons' + tag)
    arcpy.Copy_management(simplified_meshblocks, tagged_polygons)
    arcpy.AddIndex_management(tagged_polygons, sm_id_field, 'idx_0', 'UNIQUE')

    # join tagged mb centroid to simplified mb polygons.
    print('Executing Join')
    arcpy.JoinField_management(tagged_polygons, sm_id_field, tagged_centroids, umc_id_field, [ul_id_field])
    arcpy.AddIndex_management(tagged_polygons, ul_id_field, 'idx_1')

    # dissolve simplified mb polygons to create simplified regions
    print('Executing Dissolve')
    dissolved_mbs = os.path.join(workspace, 'dissolved' + tag)
    arcpy.Dissolve_management(in_features=tagged_polygons, out_feature_class=dissolved_mbs, dissolve_field=ul_id_field,
                              statistics_fields="", multi_part="MULTI_PART", unsplit_lines="DISSOLVE_LINES")

    # 4 project source polys to output - copies all fields so no specific field copy needed.
    print('Creating Output Features')
    out_sr = arcpy.SpatialReference(out_srid)
    arcpy.Project_management(in_dataset=unsimplified_lgas, out_dataset=out_features, out_coor_system=out_sr)

    print('Replacing Geometries')
    # create polygon lookup dict
    lu = {}
    flds = [ul_id_field, 'SHAPE@']
    with arcpy.da.SearchCursor(dissolved_mbs, flds) as csr:
        for row in csr:
            lu[row[0]] = row[1]

    # 5 replace geometries with simplified geometries.
    with arcpy.da.UpdateCursor(out_features, flds) as csr:
        for row in csr:
            shp = lu.get(row[0])
            if shp:
                row[1] = shp
                csr.updateRow(row)
            else:
                arcpy.AddWarning("No geometry found for id=" + str(row[0]) + ". Geometry not updated.")

    print('Done')
finally:
    if tagged_centroids:
        arcpy.Delete_management(tagged_centroids)
    if tagged_polygons:
        arcpy.Delete_management(tagged_polygons)
    if dissolved_mbs:
        arcpy.Delete_management(dissolved_mbs)


