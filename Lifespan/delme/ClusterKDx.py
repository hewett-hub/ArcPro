import os
import arcpy
from arcpy.sa import *

# -----------------------------PARAMETERS-------------------------------------

replace_existing = False
keep_working = False

# path to the gdb in which the LITS extracts are to be stored
lits_gdb = r'L:\Work\KernelDensity\LITS_20200729\ClusterAnalyses\LITS_20200729_08_17.gdb'

# path to the gdb in which the cluster analysis results are to be stored.
cluster_analysis_gdb = r'L:\Work\KernelDensity\LITS_20200729\ClusterAnalyses\ClusterAnalyses_08_17.gdb'

# path to the gdb in which the kd working layers are to be stored - note: this gdb may be deleted at the end of the run if
# preserve working is set to false.
kd_working_gdb = r'L:\Work\KernelDensity\LITS_20200729\ClusterAnalyses\KD_working.gdb'

# path to the gdb in which the kd results are to be stored
kd_analysis_gdb = r'L:\Work\KernelDensity\LITS_20200729\ClusterAnalyses\KD_Analyses_08_17.gdb'

# ---------------------Clustering Parameters---------------------
# minimum cluster size for clustering operation
minimum_cluster_size = 5

# The master incident points sets to be used.  It is assumed these follow standart LIFESPAN structure.
source_locations = {'Incidents': r"G:\RestrictedAccess\CoreData\NCIS\LITS_20200729\NCIS.gdb\Incidents_xy",
                    'Residence': r"G:\RestrictedAccess\CoreData\NCIS\LITS_20200729\NCIS.gdb\Residence_xy"}

# The master filter that will be applied to source locations to select only the desired timeframes and non-exclusion items.
# Using the IN filter option allows for non-sequential years to be included if desired.
PeriodFilter = "ExclusionCode NOT IN (1) AND Incident_Year IN (2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008)"

# The theme names and filters for the various analyses to be performed on the input points.
theme_filters = {'ALLAges_ALLIncidents': PeriodFilter,
                 'ALLAges_AwayIncidents': PeriodFilter + " AND Incident_Residence_Match = 'No'",
                 'ALLAges_HomeIncidents': PeriodFilter + "AND Incident_Residence_Match = 'Yes'",
                 'Elders_ALLIncidents': PeriodFilter + "AND Age > 64",
                 'Elders_AwayIncidents': PeriodFilter + "AND Age > 64 AND Incident_Residence_Match ='No'",
                 'Elders_HomeIncidents': PeriodFilter + "AND Age > 64 AND Incident_Residence_Match ='Yes'",
                 'Youth_ALLIncidents': PeriodFilter + "AND Age < 25",
                 'Youth_AwayIncidents': PeriodFilter + "AND Age < 25 AND Incident_Residence_Match ='No'",
                 'Youth_HomeIncidents': PeriodFilter + "AND Age < 25 AND Incident_Residence_Match ='Yes'"}

# The cluster settings for each cluster operation to be performed:
# Distances are assumed to be in meters.
# Currently only DBSCAN are being performed, but if necessary the settings options and codebase
# can be expanded to handle other cluster options.
cluster_settings = {'DBSCAN': [500, 1000, 2000, 4000]}


# ---------------------Kernel Density Parameters------------------------------------
# privacy threshold for Kernel Density operation
privacy_threshold = 5

kd_resolutions = {'1K': {'cell_size': 50,
                         'search_radius': 1000}}

# -----------------------------CODE-------------------------------------------

# define worker classes


class LicenseError(Exception):
    pass


class Validate(object):
    @staticmethod
    def source_locations(values):
        for name, value in values:
            if not arcpy.Exists(value):
                raise RuntimeError('Expected data source not found: {}: {}'.format(name, value))

    @staticmethod
    def directory_exists(value):
        if not value:
            raise RuntimeError('Directory Path cannot be None or empty.')
        if not arcpy.Exists(value):
            raise RuntimeError('Expected directory not found: "{}"'.format(value))

    @staticmethod
    def gdb_does_not_exist(gdb_path):
        if arcpy.Exists(gdb_path):
            raise RuntimeError('GDB already exists: "{}"'.format(gdb_path))


class KernelDensityHelper(object):
    def __init__(self, threshold, resolutions, slices, results_gdb, working_gdb, preserve_working=False):
        self.privacy_threshold = threshold
        self.resolutions = resolutions
        self.results_gdb = results_gdb
        self.working_gdb = working_gdb
        self.slices = slices
        self.preserve_working = preserve_working

        self._theme_name = None

    def working_path(self, base_name, suffix):
        return os.path.join(self.working_gdb, base_name + suffix)

    def create_kds(self, point_features, name_base):
        for resolution_name, params in self.resolutions.items():
            kd_name = '{}_{}'.format(name_base, resolution_name)
            cell_size = params['cell_size']
            search_radius = params['search_radius']

            try:
                arcpy.AddMessage('Processing: {}'.format(kd_name))
                # try to get SA license
                if arcpy.CheckExtension("Spatial") == "Available":
                    arcpy.CheckOutExtension("Spatial")
                else:
                    # Raise a custom exception
                    raise LicenseError

                arcpy.AddMessage('Performing Kernel Density')
                kd_result = KernelDensity(in_features=point_features,
                                          population_field="NONE",
                                          cell_size=cell_size,
                                          search_radius=search_radius,
                                          area_unit_scale_factor='SQUARE_KILOMETERS',
                                          out_cell_values='DENSITIES',
                                          method='PLANAR')
                if keep_working:
                    kd_raster_path = self.working_path(kd_name, 'kd')
                    GeneralHelper.delete_existing(kd_raster_path)
                    kd_result.save(kd_raster_path)

                arcpy.AddMessage('Extracting Non-Zero values')
                con_result = Con(in_conditional_raster=kd_result,
                                 in_true_raster_or_constant=kd_result,
                                 in_false_raster_or_constant="",
                                 where_clause="Value > 0")
                if keep_working:
                    con_raster_path = self.working_path(kd_name, 'con')
                    GeneralHelper.delete_existing(con_raster_path)
                    con_result.save(con_raster_path)

                arcpy.AddMessage('Slicing Data')
                slice_result = Slice(in_raster=con_result,
                                     number_zones=self.slices,
                                     slice_type='NATURAL_BREAKS')
                if keep_working:
                    slice_raster_path = self.working_path(kd_name, 'slice')
                    GeneralHelper.delete_existing(slice_raster_path)
                    slice_result.save(slice_raster_path)

                slice_features_path = self.working_path(kd_name, 'sliced')
                GeneralHelper.delete_existing(slice_features_path)
                arcpy.AddMessage('Vectorising Data: {0}'.format(slice_features_path))
                arcpy.RasterToPolygon_conversion(in_raster=slice_result,
                                                 out_polygon_features=slice_features_path,
                                                 simplify="SIMPLIFY",
                                                 raster_field="Value")

            except LicenseError:
                print("Spatial license is unavailable")
            except arcpy.ExecuteError:
                print(arcpy.GetMessages(2))
            finally:
                # Check in the ArcGIS Spatial Analyst
                arcpy.CheckInExtension("Spatial")

    def process_tiers(self, point_features, sliced_features, ):



class WorkflowHelper(object):
    def __init__(self, location_params, theme_params, cluster_params, min_cluster_size, lits_target,
                 clusters_target, kd_helper):
        self.themes = theme_params
        self.locations = location_params
        self.cluster_params = cluster_params
        self.cluster_min = min_cluster_size
        self.cluster_gdb = clusters_target
        self.lits_gdb = lits_target
        self.kd_helper = kd_helper

        self._location_type = None
        self._theme_name = None

    def execute_workflow(self):
        for location_type, locations_fc in self.locations.items():
            self._location_type = location_type
            print('Processing {} locations.'.format(location_type))
            self.process_themes(location_type=location_type, locations_fc=locations_fc)

    def process_themes(self, location_type, locations_fc):
        for theme, filter_value in self.themes.items():
            self._theme_name = theme
            print('Processing {} theme.'.format(theme))
            lits_fc_name = '{}_{}'.format(location_type, theme)
            lits_fc = arcpy.FeatureClassToFeatureClass_conversion(in_features=locations_fc, out_path=self.lits_gdb, out_name=lits_fc_name,
                                                                  where_clause=filter_value)
            print('Created: {}'.format(lits_fc))
            self.do_cluster_analysis(points_source=lits_fc)

    def do_cluster_analysis(self, points_source):
        for analysis_type, analysis_params in self.cluster_params.items():
            if analysis_type.upper() == 'DBSCAN':
                for dist_m in analysis_params:
                    fc_name = '{}_{}_PC_DBScan_{}_{}m'.format(self._location_type, self._theme_name, self.cluster_min, dist_m)
                    out_path = os.path.join(self.cluster_gdb, fc_name)
                    search_dist = '{} Meters'.format(dist_m)
                    print('Performing DBSCAN ' + search_dist)
                    result = arcpy.gapro.FindPointClusters(input_points=points_source, out_feature_class=out_path, clustering_method='DBSCAN',
                                                           minimum_points=5, search_distance=search_dist, use_time="NO_TIME", search_duration=None)
                    print('Created: {}'.format(result))
            else:
                raise RuntimeError('Unsupported Cluster Method: {}'.format(analysis_type))


class GeneralHelper(object):
    @staticmethod
    def create_gdb(gdb_path, replace_existing_gdb):
        if arcpy.Exists(gdb_path):
            if replace_existing_gdb:
                arcpy.Delete_management(gdb_path)
            else:
                raise RuntimeError('GDB already exists: "{}"'.format(gdb_path))

        base_path, name = os.path.split(gdb_path)
        return arcpy.CreateFileGDB_management(base_path, name)

    @staticmethod
    def delete_existing(item):
        if arcpy.Exists(item):
            arcpy.Delete_management(item)


# validate parameters before execution where possible.
Validate.source_locations(source_locations)

# create new lits and cluster gdb instances
lits_gdb = GeneralHelper.create_gdb(lits_gdb, replace_existing)
cluster_gdb = GeneralHelper.create_gdb(cluster_analysis_gdb, replace_existing)
kd_working_gdb = GeneralHelper.create_gdb(kd_working_gdb, replace_existing)
kd_gdb = GeneralHelper.create_gdb(kd_analysis_gdb, replace_existing)

workflow = WorkflowHelper(location_params=source_locations,
                          theme_params=theme_filters,
                          cluster_params=cluster_settings,
                          min_cluster_size=minimum_cluster_size,
                          lits_target=lits_gdb,
                          clusters_target=cluster_gdb)

workflow.execute_workflow()

print('Done')
