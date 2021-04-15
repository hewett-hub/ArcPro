from arcgis.gis import GIS

portal_url = "https://graphc-portal1.anu.edu.au/portal"
user_name = ''
password = ''
profile_name = ''

gis = GIS(portal_url, username=user_name, password=password, profile=profile_name)
