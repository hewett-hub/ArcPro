import arcpy
import os

arcpy.env.overwriteOutput = True
replaceExisting = False
dir = os.getcwd()

## IMPORTANT- Review Lines: 11,12, 14, 29, 46

# Incidents
Master_I = r"G:\RestrictedAccess\CoreData\NCIS\LITS_20200729\NCIS.gdb\Incidents_xy"
Master_R = r"G:\RestrictedAccess\CoreData\NCIS\LITS_20200729\NCIS.gdb\Residence_xy"

gdbC = 'ClusterAnalyses_08_17.gdb'
workingGDB = os.path.join(dir, gdbC)
    
# if the gdb exists and replaceExisting evaluates to true
# delete the existing database
if arcpy.Exists(workingGDB) and replaceExisting:
   arcpy.Delete_management(workingGDB)
    
   # if the gdb was deleted or did not already exists
   # create the gdb
if not arcpy.Exists(workingGDB):
   arcpy.CreateFileGDB_management(dir, gdbC)
else:
   print('The output database already exists: ' + gdbC)
   i = input('Delete it 1st or change replaceExisting to True! ')
   sys.exit('Exiting')

gdbL = 'LITS_20200729_08_17.gdb'
workingGDB = os.path.join(dir, gdbL)
    
# if the gdb exists and replaceExisting evaluates to true
# delete the existing database
if arcpy.Exists(workingGDB) and replaceExisting:
   arcpy.Delete_management(workingGDB)
    
 # if the gdb was deleted or did not already exists
 # create the gdb
if not arcpy.Exists(workingGDB):
   arcpy.CreateFileGDB_management(dir, gdbL)
else:
   print('The output database already exists: ' + gdbL)
   i = input('Delete it 1st or change replaceExisting to True! ')
   sys.exit('Exiting')

ClustersGDB = r'G:\RestrictedAccess\Work\KernelDensity\LITS_20200729\ClusterAnalyses\\' + gdbC
LITSGDB = r'G:\RestrictedAccess\Work\KernelDensity\LITS_20200729\ClusterAnalyses\\' + gdbL
PeriodFilter = "ExclusionCode NOT IN (1) AND Incident_Year IN (2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2009, 2008)"

params = [{'Master': Master_I, 
		   'TargetFC': 'Incidents_ALLAges_ALLIncidents',
		   'Filter': PeriodFilter + "",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_I, 
		   'TargetFC': 'Incidents_ALLAges_AwayIncidents',
		   'Filter': PeriodFilter + "AND Incident_Residence_Match = 'No' ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_I, 
		   'TargetFC': 'Incidents_ALLAges_HomeIncidents',
		   'Filter': PeriodFilter + "AND Incident_Residence_Match = 'Yes' ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_R, 
		   'TargetFC': 'Residence_ALLAges_ALLIncidents',
		   'Filter': PeriodFilter + "",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_R, 
		   'TargetFC': 'Residence_ALLAges_AwayIncidents',
		   'Filter': PeriodFilter + "AND Incident_Residence_Match = 'No' ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_R, 
		   'TargetFC': 'Residence_ALLAges_HomeIncidents',
		   'Filter': PeriodFilter + "AND Incident_Residence_Match = 'Yes' ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_I, 
		   'TargetFC': 'Incidents_Elders_ALLIncidents',
		   'Filter': PeriodFilter + "AND Age > 64 ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_I, 
		   'TargetFC': 'Incidents_Elders_AwayIncidents',
		   'Filter': PeriodFilter + "AND Age > 64 AND Incident_Residence_Match ='No' ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_I, 
		   'TargetFC': 'Incidents_Elders_HomeIncidents',
		   'Filter': PeriodFilter + "AND Age > 64 AND Incident_Residence_Match ='Yes' ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_R, 
		   'TargetFC': 'Residence_Elders_ALLIncidents',
		   'Filter': PeriodFilter + "AND Age > 64 ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_R, 
		   'TargetFC': 'Residence_Elders_AwayIncidents',
		   'Filter': PeriodFilter + "AND Age > 64 AND Incident_Residence_Match ='No' ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_R, 
		   'TargetFC': 'Residence_Elders_HomeIncidents',
		   'Filter': PeriodFilter + "AND Age > 64 AND Incident_Residence_Match ='Yes' ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_I, 
		   'TargetFC': 'Incidents_Youth_ALLIncidents',
		   'Filter': PeriodFilter + "AND Age < 25 ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_I, 
		   'TargetFC': 'Incidents_Youth_AwayIncidents',
		   'Filter': PeriodFilter + "AND Age < 25 AND Incident_Residence_Match ='No' ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_I, 
		   'TargetFC': 'Incidents_Youth_HomeIncidents',
		   'Filter': PeriodFilter + "AND Age < 25 AND Incident_Residence_Match ='Yes' ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_R, 
		   'TargetFC': 'Residence_Youth_ALLIncidents',
		   'Filter': PeriodFilter + "AND Age < 25 ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_R, 
		   'TargetFC': 'Residence_Youth_AwayIncidents',
		   'Filter': PeriodFilter + "AND Age < 25 AND Incident_Residence_Match ='No' ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]},
		 {'Master': Master_R, 
		   'TargetFC': 'Residence_Youth_HomeIncidents',
		   'Filter': PeriodFilter + "AND Age < 25 AND Incident_Residence_Match ='Yes' ",
		   'Dests': [['_PC_DBScan_5_500m', "500 Meters", "DBSCAN"], 
		             ['_PC_DBScan_5_1000m', "1000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_2000m', "2000 Meters", "DBSCAN"], 
					 ['_PC_DBScan_5_4000m', "4000 Meters", "DBSCAN"],
                     ['_PC_HDBScan_5', None, "HDBSCAN"]]}]

for param in params:
	
	master = param['Master']
	source_fc =param['TargetFC']
	filter = param['Filter']
	source = arcpy.conversion.FeatureClassToFeatureClass(master, LITSGDB, source_fc, filter)

	for cluster in param['Dests']:
		
		clusterFC = os.path.join(ClustersGDB, source_fc + cluster[0])
		clusterDist = cluster[1]
		clusterMethod = cluster[2]
		
		print("source: " + LITSGDB + "\\" + source_fc)
		print("clusterFC: " + clusterFC)
		print("clusterMethod: " + clusterMethod)
		
		arcpy.gapro.FindPointClusters(source, clusterFC, clusterMethod, 5, clusterDist, "NO_TIME", None)
		
print('Done')

	
	
	
