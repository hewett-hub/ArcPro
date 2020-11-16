"""
Note:  This script is intended to be run as a scheduled task.  In order to protect your credentials (ie, not have them visible in the
script or in the Task Manager parameters) the script uses a Profile to access your credentials.  If you haven't already created a profile to
hold these credentials on your computer you must create one before running this script.  You can do this by copying the following snippet into
the python window of ArcGIS Pro, replacing the **** placeholders with values appropriate to you, and running the snippet.

from arcgis.gis import GIS
my_new_profile =  GIS(url="https://graphc.maps.arcgis.com/", username='****', password='****', profile='****')



Once you have run the snippet your profile will be created on the computer you ran the snippet on.

See the 'Storing your credentials locally' section on the following web-page for more information:
https://developers.arcgis.com/python/guide/working-with-different-authentication-schemes/

Refs:
https://developers.arcgis.com/python/guide/editing-features/
https://developers.arcgis.com/python/guide/working-with-different-authentication-schemes/

NOTE: Beautiful Soup must be installed for this to run.
"""

import csv
#from urllib.request import urlopen
import html5lib
import requests
from bs4 import BeautifulSoup as soup
import io
import logging
import datetime
import copy
import argparse
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
import pprint
import re


src = r'https://www.dhhs.vic.gov.au/coronavirus-update-victoria-2-july-2020'
r = requests.get(src)
page_soup = soup(r.content, 'html5lib')
items = page_soup.findAll('div', {'class': 'field field--name-field-dhhs-rich-text-text field--type-text-long field--label-hidden field--item'})
for item in items:
    txt = str(item.text)
    x = re.search("Victoria is [0-9]+ with [0-9]+ new cases reported yesterday", txt)
    print(x.group())
    d = re.findall('[0-9]+', x.group())
    print(d)

    """paras = item.findAll('p')
    for para in paras:
        txt = para.text
        if 
        print('---------------')
        print(para.text)"""


"""with urlopen(src) as response:
    document = html5lib.parse(response, transport_encoding=response.info().get_content_charset())
    for child in document:
        print(child.tag, child.attrib)

    for body in document.iter('body'):
        print(body.attrib)
    #content = response.read().decode('utf-8')
    #pprint.pprint(document)
"""