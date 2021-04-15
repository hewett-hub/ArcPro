import os
import json
from arcgis import GIS


def _get_service_gdb(item_folder, item):
    exName = 'gdb' + item.id
    item.export(exName, 'File Geodatabase', parameters=None, wait=True)
    items = gis.content.search(exName)
    fgdb = gis.content.get(items[0].itemid)
    fgdb.download(save_path=item_folder)
    fgdb.delete()


def save_json(target_folder, item_id):
    item = gis.content.get(item_id)

    d = item.dependent_upon()
    print(d)

    out_dir = os.path.join(target_folder, item_id)
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    out_file = os.path.join(out_dir, 'info.json')
    with open(out_file, 'w') as f:
        f.write(json.dumps(item, indent=4))

    data = item.get_data(try_json=True)
    if data:
        out_file = os.path.join(out_dir, 'data.json')
        with open(out_file, 'w') as f:
            f.write(json.dumps(data, indent=4))

    item.download_thumbnail(out_dir)

    if item.type == "Feature Service":
        _get_service_gdb(out_dir, item)


id_val = '4071068fe442459f87b276caf563e73c'
save_dir = r'C:\tmp\aaa'


gis = GIS(profile="agol_graphc")

save_json(save_dir, id_val)

print('Done')
