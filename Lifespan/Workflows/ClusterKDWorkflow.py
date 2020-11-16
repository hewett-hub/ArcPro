import os
import arcpy
from arcpy.sa import *

# -----------------------------PARAMETERS-------------------------------------

# If Use Existing == True, then existing components will be used for the calculation if they
# already exist.  This can save time by preventing un-necessary re-calculation in case of
# a code crash.  However, the user is responsible for manually deleting components that may
# be partial or incorrect results.  To do a full recalculation, delete any existing target
# databases before execution, or if they contain results from other processes, delete any
# existing output data-sets before execution.

recalculate_all = False  # if true, the working and result databases will be deleted and all values recalculated from scratch.
use_existing = True  # If true, existing result files will be used instead of recalculated.  recalculate_all=True will override this.
keep_working = False  # if False the working gdb will be deleted at the end of the script execution.

# path to the gdb in which the LITS extracts are to be stored
# lits_gdb = r'L:\Work\KernelDensity\LITS_20200729\ClusterAnalyses\LITS_20200729_08_17.gdb'
lits_gdb = r'L:\Work\KernelDensity\LITS_20200729\Testing\LITS_20200729_08_17.gdb'

# path to the gdb in which the cluster analysis results are to be stored.
# cluster_analysis_gdb = r'L:\Work\KernelDensity\LITS_20200729\ClusterAnalyses\ClusterAnalyses_08_17.gdb'
cluster_analysis_gdb = r'L:\Work\KernelDensity\LITS_20200729\Testing\ClusterAnalyses_08_17.gdb'

# path to the gdb in which the kd working layers are to be stored - note: this gdb may be deleted at the end of the run if
# preserve working is set to false.
# kd_working_gdb = r'L:\Work\KernelDensity\LITS_20200729\ClusterAnalyses\KD_working.gdb'
kd_working_gdb = r'L:\Work\KernelDensity\LITS_20200729\Testing\KD_working.gdb'

# path to the gdb in which the kd results are to be stored
# kd_analysis_gdb = r'L:\Work\KernelDensity\LITS_20200729\ClusterAnalyses\KD_Analyses_08_17.gdb'
kd_analysis_gdb = r'L:\Work\KernelDensity\LITS_20200729\Testing\KD_Analyses_08_17.gdb'

# The master incident points sets to be used.  It is assumed these follow standart LIFESPAN structure.
# source_locations = {'Incidents': r"L:\Work\CoreData\NCIS\LITS_20200729\NCIS.gdb\Incidents_xy",
#                     'Residence': r"L:\Work\CoreData\NCIS\LITS_20200729\NCIS.gdb\Residence_xy"}

source_locations = {'Incidents': r"L:\Work\KernelDensity\LITS_20200729\Testing\NCIS.gdb\Incidents_xy",
                    'Residence': r"L:\Work\KernelDensity\LITS_20200729\Testing\NCIS.gdb\Residence_xy"}

# The master filter that will be applied to source locations to select only the desired timeframes and non-exclusion items.
# Using the IN filter option allows for non-sequential years to be included if desired.
PeriodFilter = "ExclusionCode NOT IN (1) AND Incident_Year IN (2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008)"

# The theme names and filters for the various analyses to be performed on the input points.
theme_filters = {'ALLAges_ALLIncidents': PeriodFilter,
                 'ALLAges_AwayIncidents': PeriodFilter + " AND Incident_Residence_Match = 'No'",
                 'ALLAges_HomeIncidents': PeriodFilter + " AND Incident_Residence_Match = 'Yes'",
                 'Elders_ALLIncidents': PeriodFilter + " AND Age > 64",
                 'Elders_AwayIncidents': PeriodFilter + " AND Age > 64 AND Incident_Residence_Match ='No'",
                 'Elders_HomeIncidents': PeriodFilter + " AND Age > 64 AND Incident_Residence_Match ='Yes'",
                 'Youth_ALLIncidents': PeriodFilter + " AND Age < 25",
                 'Youth_AwayIncidents': PeriodFilter + " AND Age < 25 AND Incident_Residence_Match ='No'",
                 'Youth_HomeIncidents': PeriodFilter + " AND Age < 25 AND Incident_Residence_Match ='Yes'"}

# The cluster method to be used
cluster_method = 'DBSCAN'

# minimum cluster size for clustering operation
minimum_cluster_size = 5

kd_resolutions = {'1K': {'cell_size': 50,
                         'search_radius': 1000},
                  '2K': {'cell_size': 75,
                         'search_radius': 2000},
                  '4K': {'cell_size': 100,
                         'search_radius': 4000}}

# privacy threshold for Kernel Density operation
privacy_threshold = 5

slices = 10

# -----------------------------CODE-------------------------------------------

# define worker classes


class LicenseError(Exception):
    pass


def _create_gdb(gdb_path):
    if arcpy.Exists(gdb_path):
        if recalculate_all:
            arcpy.Delete_management(gdb_path)
        elif use_existing:
            return gdb_path
        else:
            raise RuntimeError('GDB already exists: "{}"'.format(gdb_path))

    base_path, name = os.path.split(gdb_path)
    return arcpy.CreateFileGDB_management(base_path, name)


def delete_existing(item):
    if arcpy.Exists(item):
        arcpy.Delete_management(item)


def execute_workflow():
    print('Creating GDBs')
    _create_gdb(gdb_path=lits_gdb)
    _create_gdb(gdb_path=kd_analysis_gdb)
    _create_gdb(gdb_path=cluster_analysis_gdb)
    _create_gdb(gdb_path=kd_working_gdb)

    for source_id in source_locations.keys():
        print('Processing: {}'.format(source_id))
        _process_point_source(source_id=source_id)

    if not keep_working:
        delete_existing(kd_working_gdb)


def _process_point_source(source_id):
    for theme_id in theme_filters.keys():
        print('Processing: {}.{}'.format(source_id, theme_id))
        _process_theme(source_id=source_id, theme_id=theme_id)


def _process_theme(source_id, theme_id):
    # create filtered set of source points
    source_points = source_locations[source_id]
    theme_filter = theme_filters[theme_id]
    lits_fc_name = '{}_{}'.format(source_id, theme_id)
    lits_fc_path = os.path.join(lits_gdb, lits_fc_name)

    if arcpy.Exists(lits_fc_path):
        if use_existing:
            print('Using existing LITS points: {}'.format(lits_fc_path))
        else:
            raise RuntimeError('use_existing is False and dataset exists: {}'.format(lits_fc_path))
    else:
        print('Extracting LITS points: {}'.format(lits_fc_path))
        arcpy.FeatureClassToFeatureClass_conversion(in_features=source_points,
                                                    out_path=lits_gdb,
                                                    out_name=lits_fc_name,
                                                    where_clause=theme_filter)

    for kd_id in kd_resolutions:
        _create_kd(filtered_points=lits_fc_path, source_id=source_id, theme_id=theme_id, kd_id=kd_id)


def _create_kd(filtered_points, source_id, theme_id, kd_id):
    kd_result_name = '{}_{}_{}'.format(source_id, theme_id, kd_id)
    kd_result_path = os.path.join(kd_analysis_gdb, kd_result_name)
    if arcpy.Exists(kd_result_path):
        if use_existing:
            print('Using Existing Kernel Density Result: {}'.format(kd_result_path))
            return kd_result_path
        else:
            raise RuntimeError('use_existing is False and dataset exists: {}'.format(kd_result_path))

    print('Kernel Density Generation Steps: {}'.format(kd_result_name))

    kd_params = kd_resolutions[kd_id]
    cell_size = kd_params['cell_size']
    search_radius = kd_params['search_radius']

    clustered_points = _process_cluster(filtered_points=filtered_points, source_id=source_id, theme_id=theme_id, search_distance=search_radius)
    cluster_lyr = None
    try:
        cluster_lyr = arcpy.MakeFeatureLayer_management(in_features=clustered_points, out_layer='tmp_layer', where_clause='CLUSTER_ID > 0')

        kd_slices = _process_rasters(clustered_points=cluster_lyr, cell_size=cell_size, search_radius=search_radius,
                                     source_id=source_id, theme_id=theme_id, kd_id=kd_id)
        processed_slices = _process_slices(in_slices=kd_slices, clustered_points=cluster_lyr, source_id=source_id, theme_id=theme_id, kd_id=kd_id)
    finally:
        if cluster_lyr is not None:
            arcpy.Delete_management(cluster_lyr)

    return arcpy.FeatureClassToFeatureClass_conversion(processed_slices, kd_analysis_gdb, kd_result_name)


def _process_cluster(filtered_points, source_id, theme_id, search_distance):
    fc_name = '{}_{}_PC_{}_{}_{}m'.format(source_id, theme_id, cluster_method, minimum_cluster_size, search_distance)
    out_path = os.path.join(cluster_analysis_gdb, fc_name)
    if arcpy.Exists(out_path):
        if use_existing:
            print('Using Cluster Analysis Result: {}'.format(out_path))
            return out_path
        else:
            raise RuntimeError('use_existing is False and dataset exists: {}'.format(out_path))

    print('Performing Cluster Analysis: {}'.format(fc_name))
    search_dist = '{} Meters'.format(search_distance)
    return arcpy.gapro.FindPointClusters(input_points=filtered_points,
                                         out_feature_class=out_path,
                                         clustering_method=cluster_method,
                                         minimum_points=minimum_cluster_size,
                                         search_distance=search_dist,
                                         use_time="NO_TIME",
                                         search_duration=None)


def _process_rasters(clustered_points, cell_size, search_radius, source_id, theme_id, kd_id):
    slice_features_name = '{}_{}_{}sliced'.format(source_id, theme_id, kd_id)
    slice_features_path = os.path.join(kd_working_gdb, slice_features_name)

    # If the result already exists, return existing or raise error if return existing is not allowed.
    if arcpy.Exists(slice_features_path):
        if use_existing:
            print('Using Cluster Analysis Result: {}'.format(slice_features_path))
            return slice_features_path
        else:
            raise RuntimeError('use_existing is False and dataset exists: {}'.format(slice_features_path))

    # try to get SA license
    if arcpy.CheckExtension("Spatial") == "Available":
        arcpy.CheckOutExtension("Spatial")
    else:
        # Raise a custom exception
        raise LicenseError

    kd_raster = None
    con_raster = None
    slice_raster = None
    try:
        kd_raster = _do_kd(source_id=source_id, theme_id=theme_id, kd_id=kd_id, clustered_points=clustered_points,
                           cell_size=cell_size, search_radius=search_radius)

        con_raster = _do_con(source_id=source_id, theme_id=theme_id, kd_id=kd_id, kd_raster=kd_raster)

        slice_raster = _do_slice(source_id=source_id, theme_id=theme_id, kd_id=kd_id, con_raster=con_raster)

        print('Vectorising Raster: {}'.format(slice_features_name))
        return arcpy.RasterToPolygon_conversion(in_raster=slice_raster,
                                                out_polygon_features=slice_features_path,
                                                simplify="SIMPLIFY",
                                                raster_field="Value")
    finally:
        # Check in the ArcGIS Spatial Analyst
        arcpy.CheckInExtension("Spatial")

        # free up memory by deleting layers
        if kd_raster is not None:
            arcpy.Delete_management(kd_raster)
        if con_raster is not None:
            arcpy.Delete_management(con_raster)
        if slice_raster is not None:
            arcpy.Delete_management(slice_raster)


def _do_kd(source_id, theme_id, kd_id, clustered_points, cell_size, search_radius):
    kd_name = '{}_{}_{}kd'.format(source_id, theme_id, kd_id)
    kd_path = os.path.join(kd_working_gdb, kd_name)

    if arcpy.Exists(kd_path):
        if use_existing:
            print('Using Kernel Density Analysis Result: {}'.format(kd_path))
            return kd_path
        else:
            raise RuntimeError('use_existing is False and dataset exists: {}'.format(kd_path))

    print('Performing Kernel Density: {}'.format(kd_name))

    # If the result already exists, return existing or raise error if return existing is not allowed.
    kd_raster = KernelDensity(in_features=clustered_points,
                              population_field="NONE",
                              cell_size=cell_size,
                              search_radius=search_radius,
                              area_unit_scale_factor='SQUARE_KILOMETERS',
                              out_cell_values='DENSITIES',
                              method='PLANAR')

    if keep_working:
        kd_raster.save(kd_path)

    return kd_raster


def _do_con(source_id, theme_id, kd_id, kd_raster):
    con_name = '{}_{}_{}con'.format(source_id, theme_id, kd_id)
    con_raster_path = os.path.join(kd_working_gdb, con_name)

    # If the result already exists, return existing or raise error if return existing is not allowed.
    if arcpy.Exists(con_raster_path):
        if use_existing:
            print('Using Con Analysis Result: {}'.format(con_raster_path))
            return con_raster_path
        else:
            raise RuntimeError('use_existing is False and dataset exists: {}'.format(con_raster_path))

    print('Extracting Non-Zero values: {}'.format(con_name))
    con_raster = Con(in_conditional_raster=kd_raster,
                     in_true_raster_or_constant=kd_raster,
                     in_false_raster_or_constant="",
                     where_clause="Value > 0")

    if keep_working:
        con_raster.save(con_raster_path)

    return con_raster


def _do_slice(source_id, theme_id, kd_id, con_raster):
    slice_name = '{}_{}_{}slice'.format(source_id, theme_id, kd_id)
    slice_raster_path = os.path.join(kd_working_gdb, slice_name)

    # If the result already exists, return existing or raise error if return existing is not allowed.
    if arcpy.Exists(slice_raster_path):
        if use_existing:
            print('Using Slice Analysis Result: {}'.format(slice_raster_path))
            return slice_raster_path
        else:
            raise RuntimeError('use_existing is False and dataset exists: {}'.format(slice_raster_path))

    print('Slicing Raster: {}'.format(slice_name))
    slice_raster = Slice(in_raster=con_raster,
                         number_zones=slices,
                         slice_type='NATURAL_BREAKS')

    if keep_working:
        slice_raster.save(slice_raster_path)

    return slice_raster


def _process_slices(in_slices, clustered_points, source_id, theme_id, kd_id):
    slice_layer = in_slices
    print('Performing slice privacy updates')
    for tier in range(slices, 0, -1):
        slice_layer = _process_slice(slice_features=slice_layer, clustered_points=clustered_points, tier=tier, source_id=source_id,
                                     theme_id=theme_id, kd_id=kd_id)

    return slice_layer


def _process_slice(slice_features, clustered_points, tier, source_id, theme_id, kd_id):
    print('Processing Slice {0}'.format(tier))

    dissolve_name = '{}_{}_{}_{}dissolve'.format(source_id, theme_id, kd_id, tier)
    dissolve_path = os.path.join(kd_working_gdb, dissolve_name)
    if arcpy.Exists(dissolve_path):
        if use_existing:
            print('Using existing file: {}'.format(dissolve_path))
            return dissolve_path
        else:
            raise RuntimeError('use_existing is False and dataset exists: {}'.format(dissolve_path))

    tier_file_name = '{}_{}_{}_{}'.format(source_id, theme_id, kd_id, tier)
    print('Creating slice file: {}'.format(tier_file_name))
    tier_path = os.path.join(kd_working_gdb, tier_file_name)
    if arcpy.Exists(tier_path):
        if use_existing:
            print('Using existing slice file: {}'.format(tier_path))
        else:
            raise RuntimeError('use_existing is False and dataset exists: {}'.format(tier_path))
    else:
        arcpy.FeatureClassToFeatureClass_conversion(slice_features, kd_working_gdb, tier_file_name)

    query_layer = arcpy.MakeFeatureLayer_management(clustered_points, "tmpLyr")
    print('Reducing gridcode for features containing less than {} points'.format(privacy_threshold))
    flds = ['SHAPE@', 'gridcode']
    with arcpy.da.UpdateCursor(tier_path, flds, 'gridcode = {0}'.format(tier)) as csr:
        for row in csr:
            outer_ring = get_outer_ring(row[0])
            arcpy.SelectLayerByLocation_management(query_layer, 'INTERSECT', outer_ring)
            count_result = arcpy.GetCount_management(query_layer)
            count = int(count_result.getOutput(0))
            if count < privacy_threshold:
                new_gridcode = row[1] - 1
                row[1] = new_gridcode
                csr.updateRow(row)

    arcpy.Delete_management(query_layer)

    print('Merging reduced gridcodes: ' + dissolve_name)
    return arcpy.Dissolve_management(tier_path, dissolve_path, 'gridcode', "", 'SINGLE_PART')


def get_outer_ring(geom):
    pts = arcpy.Array()
    array = geom.getPart(0)
    for pt in array:
        if not pt:
            break
        else:
            pts.append(pt)
    return arcpy.Polygon(pts, geom.spatialReference)


execute_workflow()

print('Done')
