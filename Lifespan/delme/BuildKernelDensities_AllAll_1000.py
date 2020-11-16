import arcpy
import os
from datetime import datetime

# This script will not run if the mapData.gdb exists.
# It has been constructed under the guidance that new release versions of the data will be processed as a separate project.
# As such, the project can be run as many times as needed during a product development cycle provided the mapData.gdb
# is deleted prior to each run.

# Source data will be imported if the source does not already exist in the source.gdb
# To force a reload of data for items that already exist in the source.gdb delete the 
# appropriate dataset from the source.gdb, or the whole source.gdb to force a full reload.

class LicenseError(Exception):
    pass
    
# ------------------------ PARAMETERS ------------------------ 

# Polygons intersecting less items that the privacy threshold value will be dropped one or more tiers
# until they are either tier zero or the threshold is met.
def privacyThreshold():
    return 5

# Ensure that the mask environment reflects the region of interest: 
# DefaultMask = r"G:\RestrictedAccess\CoreData\Sites\SitesExtents.gdb\Aust_Extent_Main"
ThisMask =  r"G:\RestrictedAccess\CoreData\Sites\SitesExtents.gdb\Aust_Extent_Main"
    
# The collection of data to be imported to the project Source gdb
# The datasets can be pre-filtered if desired, NB the themes definition Query section is available also below.
# The name given to the data source will be used as the feature class name in the project database.
# The dataSources are referred to by name in the themes parameters
# {datasourceName : {'database' : 'the path to the authority database from which data can be loaded or reloaded',
#                    'featureclass' : 'the name of the authority featureclass from which data can be loaded or reloaded',
#                    'filter' : 'an optional where clause filter string to limit the source data imported.  Any data excluded at this point will not be available to any themes'}
#
# This revised script uses pre-defined set of points based on Density Based Clustering. This should reult in improved obfuscation as only cluster candidate points (as defined 
# by the Density Based Cluster analyses method (probably Optics with min features = 5 and relying on the Kullback-Leibler divergence algorthms to determine sensitivity.
# The Optics DBC delivers clusters based on defined search distances. This results in different feature classes for each distance so the iterative nature of this script is 
# redundent and replaced by multiple calls to scripts pointing at different distance based feature classes.
# it is important to note that the Source Points referred to here represent cluster candidates as defined by both the definition query and the DBC parameters that is prepared before 
# running this code.

ThisRun_FC = 'Residence_ALLAges_ALLIncidents'
ThisRun_Dist = '_1000m'
ThisRun =  ThisRun_FC + ThisRun_Dist

def dataSources():
    return {'Points' : {'database' : r'G:\RestrictedAccess\Work\KernelDensity\LITS_20200729\ClusterAnalyses\ClusterAnalyses_08_17.gdb',
                        'featureclass' : ThisRun_FC + '_PC_DBScan_5' + ThisRun_Dist,
                        'filter' : "CLUSTER_ID > 0"}}

# The named resolutions available to the project.
# resolution settings are referred to by name in 
# the themes parameters    
def resolutions():
    return {'1K' : {'cell_size' : 50,
                    'search_radius' : 1000}}

# defines the themes to be processed.  Each theme is derived from a named source, with an optional filter, and 
# one or more resloutions.  The output for each theme will be one or more feature classes with the naming convention 'themeName_resolutionName'                   
def themes():
    return {'All' : {'source' : 'Points',
                     'filter' : None,
                     'resolutions' : ['1K']}}
   
# The number of slices to be created.                     
def slices():
    return 10

# if True, and preserveWorking is true, then the 
# rasters will be preserved in the working database    
def preserveRasters():
    return False
    
# if True, the working database will not be deleted
# at the end of the script run.
# if False, the working database will be deleted.
def preserveWorking():
    return False
    
# ------------------------ CODE ------------------------     
# Project Folders  
def pyFileLocation():
    # the location of this file when executed
    return os.path.dirname(os.path.abspath(__file__))

def projectFolder():
    # the project base directory
    return os.path.dirname(pyFileLocation())
    
def workingFolder():
    folder = os.path.join(projectFolder(), 'Working')
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder
  
# Project databases    
def workingGDB(replaceExisting):
    dir = workingFolder()
    gdb = 'working_' + ThisRun + '.gdb'
    
    workingGDB = os.path.join(dir, gdb)
    
    # if the gdb exists and replaceExisting evaluates to true
    # delete the existing database
    if arcpy.Exists(workingGDB) and replaceExisting:
        arcpy.Delete_management(workingGDB)
    
    # if the gdb was deleted or did not already exists
    # create the gdb
    if not arcpy.Exists(workingGDB):
        arcpy.CreateFileGDB_management(dir, gdb)
    
    return workingGDB    

def sourceGDB():
    dir = projectFolder()
    gdb = 'source_' + ThisRun + '.gdb'
    
    sourceGDB = os.path.join(dir, gdb)
    # if the gdb was deleted or did not already exists
    # create the gdb
    if not arcpy.Exists(sourceGDB):
        arcpy.CreateFileGDB_management(dir, gdb)
    
    return sourceGDB   
    
def mapdataGDB(createDatabase):
    dir = projectFolder()
    gdbName = 'mapData_' + ThisRun + '.gdb'
    
    gdb = os.path.join(dir, gdbName)
    
    # if the gdb does not already exist
    # create the gdb
    if createDatabase:
        arcpy.CreateFileGDB_management(dir, gdbName)
    
    return gdb   

def mapdataGDBExistsenceTest():
    gdb = mapdataGDB(False)
    if arcpy.Exists(gdb):
        sys.exit('The output database must not already exist: ' + gdb)
        
# Resource Testing    
def testResource(item):
    # test to see if item is full path to valid item
    if arcpy.Exists(item):
        return item
             
                  
    
    # test for paths relative to the pyfile location.
    relPath = os.path.join(pyFileLocation(), item)
    if arcpy.Exists(relPath):
        return relPath
        
    sys.exit("Expected resource not found: " + item)

def testResourceTable(db, tbl):
    dbPath = testResource(db)
    tblPath = os.path.join(db, tbl)
    return testResource(tblPath)

# fcNameBuilders

def slicedFeaturesName(themeName, resolution):
    return '{0}_{1}sliced'.format(themeName, resolution)
   
def dissolveTierName(themeName, resolution, tier):
    return '{0}_{1}_tier{2}dissolve'.format(themeName, resolution, tier)
    
def workingTierName(themeName, resolution, tier):
    return '{0}_{1}_tier{2}wkg'.format(themeName, resolution, tier)
    
# Working
def deleteExisting(item):
    if arcpy.Exists(item):
        arcpy.Delete_management(item)
        
def importSource():
    arcpy.AddMessage("Importing Source Data")
    
    gdb = sourceGDB()
           
    for outName, source in dataSources().items():
        target = os.path.join(gdb, outName)
        if arcpy.Exists(target):
            arcpy.AddMessage('Previously Loaded: {0}'.format(outName))
        else:
            arcpy.AddMessage('Importing {0}'.format(outName))
            sourceData =  testResourceTable(source['database'], source['featureclass'])
            arcpy.FeatureClassToFeatureClass_conversion(sourceData, gdb, outName, source['filter'])     

def processThemes():
    arcpy.AddMessage('Processing Themes')
    for themeName in themes().keys():
        arcpy.AddMessage('Theme: ' + themeName)
        processTheme(themeName)
        
    if not preserveWorking():
        arcpy.Delete_management(workingGDB(False))

def processTheme(themeName): 
    
    themeParams = themes()[themeName]
    
    wkgGDB = workingGDB(False)
    
    # get the source data for the theme - Create in wkggdb to allow review if desired.
    fcThemeName = themeParams['source'] + themeName
    dataSource = os.path.join(sourceGDB(), themeParams['source'])
    
    # create theme feature by filtering source to wkggdb fc.
    themeFeatures = os.path.join(wkgGDB, themeName)    
    deleteExisting(themeFeatures)
    arcpy.FeatureClassToFeatureClass_conversion(dataSource, wkgGDB, themeName, themeParams['filter'])  
    
    for resolution in themeParams['resolutions']:
        arcpy.AddMessage('Resolution: ' + resolution)
        arcpy.AddMessage(str(datetime.now()))
        processResolution(themeName, resolution)
 
def processResolution(themeName, resolution):
    
    wkgGDB = workingGDB(False)
    
    resolutionParameters = resolutions()[resolution]
    themeFeatures = os.path.join(wkgGDB, themeName)
    
    # perform raster processing in this block so that 
    # the license is guaranteed to be checked back in
    # if it is checked out.
    try:
        # try to get SA license
        if arcpy.CheckExtension("Spatial") == "Available":
            arcpy.CheckOutExtension("Spatial")
        else:
            # Raise a custom exception
            raise LicenseError
            
        # perform KernelDensity  
        kdRasterName = '{0}_{1}kd'.format(themeName, resolution)
        arcpy.AddMessage('Performing Kernel Density: {0}'.format(kdRasterName))
        kdRasterPath = os.path.join(wkgGDB, kdRasterName)
        deleteExisting(kdRasterPath)
		
        # arcpy.env.mask = ThisMask
        kdRaster = arcpy.gp.KernelDensity_sa(themeFeatures, "NONE", kdRasterPath, resolutionParameters['cell_size'], resolutionParameters['search_radius'], "SQUARE_KILOMETERS", "DENSITIES", "PLANAR")
        arcpy.ResetEnvironments()
        
		# perform conditional extract to remove zero values.
        conRasterName = '{0}_{1}con'.format(themeName, resolution)
        arcpy.AddMessage('Extracting Non-Zero values: {0}'.format(conRasterName))
        conRasterPath = os.path.join(wkgGDB, conRasterName)
        deleteExisting(conRasterPath)
        conRaster = arcpy.gp.Con_sa(kdRaster, kdRaster, conRasterPath, "", "Value > 0") 
        
        # perform raster slice
        sliceRasterName = '{0}_{1}slice'.format(themeName, resolution)
        arcpy.AddMessage('Slicing Data: {0}'.format(sliceRasterName))
        sliceRasterPath = os.path.join(wkgGDB, sliceRasterName)
        deleteExisting(sliceRasterPath)
        arcpy.gp.Slice_sa(conRaster, sliceRasterPath, slices(), "NATURAL_BREAKS")
 
    except LicenseError:
        print("Spatial license is unavailable")
    except arcpy.ExecuteError:
        print(arcpy.GetMessages(2))
    finally:
        # Check in the ArcGIS Spatial Analyst
        arcpy.CheckInExtension("Spatial")
        
    # Vectorise the Sliced Raster
    slicedFeatures = slicedFeaturesName(themeName, resolution)
    arcpy.AddMessage('Vectorising Data: {0}'.format(slicedFeatures))
    slicedFeaturesPath = os.path.join(wkgGDB, slicedFeatures)
    deleteExisting(slicedFeaturesPath)
    arcpy.RasterToPolygon_conversion(sliceRasterPath, slicedFeaturesPath, simplify="SIMPLIFY", raster_field="Value")
    
    if not preserveRasters():
        arcpy.Delete_management(kdRasterPath)
        arcpy.Delete_management(conRasterPath)
        arcpy.Delete_management(sliceRasterPath)
     
    # process Tiers
    processedTiers = processTiers(themeName, resolution)
    
    # copy final tier result to MapData database
    
    outName = '{0}_{1}'.format(themeName, resolution)
    arcpy.AddMessage('Finalizing ' + outName)
    gdb = mapdataGDB(False)
    arcpy.FeatureClassToFeatureClass_conversion(processedTiers, gdb, outName)  
      
def processTiers(themeName, resolution):

    wkgGDB = workingGDB(False)
    
    sourceName = slicedFeaturesName(themeName, resolution)
    sourcePath = os.path.join(wkgGDB, sourceName)
    
    arcpy.AddMessage('Processing Tiers: ' + sourceName)
    
    ptSource = os.path.join(wkgGDB, themeName)
    threshold = privacyThreshold()
    for tier in range(slices(), 0, -1):    
        arcpy.AddMessage('Tier {0}'.format(tier))
        
        # Do not alter source - make a copy for working
        tierFileName = workingTierName(themeName, resolution, int(tier))
        arcpy.AddMessage('Working file: ' + tierFileName)
        tierFilePath = os.path.join(wkgGDB, tierFileName)
        deleteExisting(tierFilePath)
        arcpy.FeatureClassToFeatureClass_conversion(sourcePath, wkgGDB, tierFileName)  
        
        qryLyr = arcpy.MakeFeatureLayer_management(ptSource, "tmpLyr")
        
        flds = ['SHAPE@', 'gridcode']
        with arcpy.da.UpdateCursor(tierFilePath, flds, 'gridcode = {0}'.format(tier)) as csr:
            for row in csr:
                outerRing = getOuterRing(row[0])
                arcpy.SelectLayerByLocation_management(qryLyr, 'INTERSECT', outerRing)
                countResult = arcpy.GetCount_management(qryLyr)
                count = int(countResult.getOutput(0))
                if count < threshold:
                    newGridcode = row[1] - 1
                    row[1] = newGridcode
                    csr.updateRow(row)
           
        arcpy.Delete_management(qryLyr)
        
        dissolveName = dissolveTierName(themeName, resolution, int(tier))
        arcpy.AddMessage('Dissolve Result: ' + dissolveName)
        dissolvePath = os.path.join(wkgGDB, dissolveName)
        deleteExisting(dissolvePath)
        arcpy.Dissolve_management(tierFilePath, dissolvePath, 'gridcode', "", 'SINGLE_PART') 
        
        # set the source for the next iteration to the dissolve output of this iteration.
        sourcePath = dissolvePath

    return sourcePath
    
def getOuterRing(geom):
    pts = arcpy.Array()
    array = geom.getPart(0)
    for pt in array:
        if not pt:
            break
        else:
            pts.append(pt)
    return arcpy.Polygon(pts, geom.spatialReference)   
    
if __name__ == "__main__":
    startTime = datetime.now()
    print startTime
    
    # test the output database doesn't already exist and abort if it does.
    mapdataGDBExistsenceTest()
    
    # create the mapdataGDB    
    mapdataGDB(True)
    
    # import Source data
    importSource()
    
    # process the themes.
    processThemes()
    
    print 'Start Time: {0}'.format(startTime)
    print 'Completed: {0}'.format(datetime.now())    
#    in_txt = raw_input("Completed and waiting")