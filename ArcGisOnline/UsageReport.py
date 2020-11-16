import argparse
import logging
import sys
import pprint

from arcgis.gis import Item
from arcgis.gis import GIS

"""
This script can form the basis for an automated usage reporting process for Online projects.
- Create an online table with:
    - ItemID
    - Item Name
    - Date
    - Uses (int)
    
Then create a dashboard app that uses the table as its source, and apply appropriate chart(s) and filters to allow review
Do an initial run to capture data from start date (or as far back as wanted up to 60 days - longer will result in aggregation by month)
Run the script every day or so using the 7 Day setting, and update the days with changed or new values.  Changes should only occurr in the last
date of the last run.
"""
def get_item_usage(gis_object, item_id, date_range='24H', as_df=False):
    # ref: https://developers.arcgis.com/python/api-reference/arcgis.gis.toc.html
    item = Item(gis=gis_object, itemid=item_id)
    return item.usage(date_range=date_range, as_df=as_df)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile",
                        required=False,
                        default='agol_graphc',
                        help="Local Profile used to access the ArcGIS Online instance.")

    parser.add_argument("-o", "--outfile",
                        required=False,
                        default=r'E:\Documents2\tmp\usage.csv',
                        help='CSV file to be created or used.')

    args = parser.parse_args()

    gis = GIS(profile=args.profile)
    id_val = '465d9e0cd44247b488b8431a56691417'
    pprint.pprint(get_item_usage(gis_object=gis, item_id=id_val, date_range='60D'))