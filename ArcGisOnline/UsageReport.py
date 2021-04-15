import datetime
import argparse
import logging
import sys
import pprint

from arcgis.gis import Item
from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from arcgis.features import FeatureLayerCollection

# ref: https://developers.arcgis.com/python/guide/accessing-and-managing-groups/
# ref: https://developers.arcgis.com/python/api-reference/arcgis.gis.toc.html


profile = 'agol_graphc'
report_group_id = '0f52ac8faace4945a752cc8cd603d32b'
usage_tracking_url = r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/UsageTrackingTables_gdb/FeatureServer/0'



"""
This script can form the basis for an automated usage reporting process for Online projects.
- Create an online table with:
    - ItemID (str 50)
    - ItemType (str 100)
    - Name (str 255)
    - Date (Date)
    - Uses (int)
    
Then create a dashboard app that uses the table as its source, and apply appropriate chart(s) and filters to allow review
Do an initial run to capture data from start date (or as far back as wanted up to 60 days - longer will result in aggregation by month)
Run the script every day or so using the 7 Day setting, and update the days with changed or new values.  Changes should only occurr in the last
date of the last run.
"""


def get_item_usage(gis_object, item_id, date_range='24H', as_df=False):
    item = Item(gis=gis_object, itemid=item_id)
    return item.usage(date_range=date_range, as_df=as_df)


def get_group_items_usage(group_id, date_range='7D', as_data_frame=False):
    # get the group
    ago_group = gis.groups.get(group_id)
    group_items = ago_group.content()
    result = {}
    for item in group_items:
        item_info = {'id': item.id,
                     'name': item.title,
                     'type': item.type}
        try:
            data = item.usage(date_range=date_range, as_df=as_data_frame)['data']
            for data_item in data:
                if data_item['etype'] == 'svcusg':
                    usage = {}
                    usage_stats = data_item['num']
                    for stat in usage_stats:
                        use_count = int(stat[1])
                        if use_count > 0:
                            usage[int(stat[0])] = use_count
                    if usage:
                        item_info['usage'] = usage
                        result[item.id] = item_info
        except IndexError:
            pass

    return result


def list_groups():
    """
    returns the collection of groups visible to the signed in user
    :return: [arcgis.gis.Group]
    :rtype: [arcgis.gis.Group]
    """
    return gis.groups.search()


class UsageTable(object):
    def __init__(self, url):
        self.url = url
        self.id_field = 'ItemID'
        self.type_field = 'ItemType'
        self.name_field = 'Name'
        self.date_field = 'Date'
        self.uses_field = 'Uses'

    def update_item(self, table, item_data):
        item_id = item_data['id']
        item_uses = item_data['usage']

        updates = []
        adds = []

        where_clause = "{}='{}'".format(self.id_field, item_id)
        query_result = table.query(where=where_clause)
        for row in query_result.features:
            date_value = row.attributes[self.date_field]
            update_value = item_uses.pop(date_value, None)
            if update_value and update_value != row.attributes[self.uses_field]:
                row.attributes[self.uses_field] = update_value
                updates.append(row)

        if item_uses:
            for use_date, use_count in item_uses.items():
                adds.append({"attributes": {self.id_field: item_id,
                                            self.type_field: item_data['type'],
                                            self.name_field: item_data['name'],
                                            self.date_field: use_date,
                                            self.uses_field: use_count}})

        if adds or updates:
            pprint.pprint(table.edit_features(adds=adds, updates=updates))

    def update_records(self):
        table = FeatureLayer(self.url)
        for item in usage_data.values():
            self.update_item(table, item)


gis = GIS(profile=profile)


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

    parser.add_argument("-t", "--target",
                        required=False,
                        default=r'https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/UsageTrackingTables_gdb/FeatureServer/0',
                        help="Target usage statistics table.")

    args = parser.parse_args()

    gis = GIS(profile=args.profile)
    # Valid date range values: 24H,7D,14D,30D,60D,6M,1Y
    usage_data = get_group_items_usage('ce3382520b4342489f4822430e03603b', date_range='14D')
    tbl = UsageTable(usage_tracking_url)
    tbl.update_records()
    #id_val = '465d9e0cd44247b488b8431a56691417'
    #pprint.pprint(get_item_usage(gis_object=gis, item_id=id_val, date_range='60D'))