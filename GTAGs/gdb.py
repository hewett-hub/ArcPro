import arcpy
import os


def schema(workspace):
    return {
        'workspace': workspace,
        'srid': 4326,
        'datasets': {
            'GtagPoints': {
                'geometry_type': 'POINT',
                'fields': ['GTAG', 'ATAG', 'OTAG', 'Address', 'Shareable', 'HasLine', 'HasPolygon', 'DateCreated','DateModified'],
                'field_properties': {
                    'GTAG': {
                        'field_type': 'GUID'
                    },
                    'ATAG': {
                        'field_type': 'GUID'
                    },
                    'OTAG': {
                        'field_type': 'GUID'
                    },
                    'Address': {
                        'field_type': 'TEXT',
                        'field_length': 200
                    },
                    'Shareable':  {
                        'field_type': 'SHORT'
                    },
                    'HasLine': {
                        'field_type': 'SHORT'
                    },
                    'HasPolygon':  {
                        'field_type': 'SHORT'
                    },
                    'DateCreated': {
                        'field_type': 'DATE'
                    },
                    'DateModified': {
                        'field_type': 'DATE'
                    }
                },
                'tracking': {
                    'creation_date_field': 'DateCreated',
                    'last_edit_date_field': 'DateModified'
                },
                'indexes': {
                    'idx_GTAG': {
                        'fields': ['GTAG'],
                        'unique': 'UNIQUE'
                    },
                    'idx_ATAG': {
                        'fields': ['ATAG'],
                        'unique': 'UNIQUE'
                    },
                    'idx_OTAG': {
                        'fields': ['OTAG'],
                        'unique': 'UNIQUE'
                    }
                }
            },
            'GtagLines': {
                'geometry_type': 'POLYLINE',
                'field_order': ['GTAG', 'DateCreated', 'DateModified'],
                'fields': {
                    'GTAG': {
                        'field_type': 'GUID'
                    },
                    'DateCreated': {
                        'field_type': 'DATE'
                    },
                    'DateModified': {
                        'field_type': 'DATE'
                    }
                },
                'tracking': {
                    'creation_date_field': 'DateCreated',
                    'last_edit_date_field': 'DateModified'
                },
                'indexes': {
                    'idx_GTAG': {
                        'fields': ['GTAG'],
                        'unique': 'UNIQUE'
                    }
                }
            },
            'GtagPolygons': {
                'geometry_type': 'POLYGON',
                'field_order': ['GTAG', 'DateCreated', 'DateModified'],
                'fields': {
                    'GTAG': {
                        'field_type': 'GUID'
                    },
                    'DateCreated': {
                        'field_type': 'DATE'
                    },
                    'DateModified': {
                        'field_type': 'DATE'
                    }
                },
                'tracking': {
                    'creation_date_field': 'DateCreated',
                    'last_edit_date_field': 'DateModified'
                },
                'indexes': {
                    'idx_GTAG': {
                        'fields': ['GTAG'],
                        'unique': 'UNIQUE'
                    }
                }
            },
            'Geocodes': {
                'geometry_type': 'POINT',
                'field_order': ['Address', 'ProviderResult', 'Provider', 'ProviderCost', 'DateCreated'],
                'fields': {
                    'Address': {
                        'field_type': 'TEXT',
                        'field_length': 200
                    },
                    'ProviderResult': {
                        'field_type': 'BLOB'
                    },
                    'Provider': {
                        'field_type': 'TEXT',
                        'field_length': 100
                    },
                    'ProviderCost': {
                        'field_type': 'FLOAT',
                        'field_scale': 3,
                        'field_precision': 6
                    },
                    'DateCreated': {
                        'field_type': 'DATE'
                    },
                    'DateModified': {
                        'field_type': 'DATE'
                    }
                },
                'indexes': {
                    'idx_Address': {
                        'fields': ['Address'],
                        'unique': 'NON_UNIQUE'
                    },
                    'idx_Provider': {
                        'fields': ['Provider'],
                        'unique': 'NON_UNIQUE'
                    }
                }
            },
            'GtagGroups': {
                'geometry_type': None,
                'field_order': ['GTAG', 'GROUP', 'DateCreated'],
                'fields': {
                    'GTAG': {
                        'field_type': 'GUID'
                    },
                    'GROUP': {
                        'field_type': 'GUID'
                    },
                    'DateCreated': {
                        'field_type': 'DATE'
                    }
                },
                'indexes': {
                    'idx_GTAG': {
                        'fields': ['GTAG'],
                        'unique': 'NON_UNIQUE'
                    },
                    'idx_GROUP': {
                        'fields': ['GROUP'],
                        'unique': 'NON_UNIQUE'
                    },
                    'idx_GTAGGROUP': {
                        'fields': ['GTAG', 'GROUP'],
                        'unique': 'UNIQUE'
                    }
                }
            }
        }
    }


def add_fields(dataset, field_order, field_properties):
    for field_name in field_order:
        properties = field_properties[field_name]
        field_type = properties['field_type']
        field_length = properties.get('field_length', None)
        field_scale = properties.get('field_scale', None)
        field_precision = properties.get('field_precision', None)
        field_alias = properties.get('field_alias', field_name)
        field_is_nullable = properties.get('field_is_nullable', 'NULLABLE')
        field_is_required = properties.get('field_is_required', 'NON_REQUIRED')

        arcpy.AddField_management(in_table=dataset, field_name=field_name, field_type=field_type, field_precision=field_precision,
                                  field_scale=field_scale, field_length=field_length, field_alias=field_alias, field_is_nullable=field_is_nullable,
                                  field_is_required=field_is_required)

        return dataset


def add_indexes(dataset, indexes_schema):
    for index_name, index_properties in indexes_schema:
        fields = index_properties['fields']
        unique = index_properties['unique']
        arcpy.AddIndex_management(in_table=dataset, fields=fields, index_name=index_name, unique=unique)

    return dataset


def enable_tracking(dataset, tracking_schema):
    creator_field = tracking_schema.get('creator_field', None)
    creation_date_field = tracking_schema.get('creation_date_field', None)
    last_editor_field = tracking_schema.get('last_editor_field', None)
    last_edit_date_field = tracking_schema.get('last_edit_date_field', None)
    add_fields_value = tracking_schema.get('last_editor_field', 'NO_ADD_FIELDS')
    record_dates_in = tracking_schema.get('record_dates_in', 'UTC')

    arcpy.EnableEditorTracking_management(in_dataset=dataset, creator_field=creator_field, creation_date_field=creation_date_field,
                                          last_editor_field=last_editor_field, last_edit_date_field=last_edit_date_field,
                                          add_fields=add_fields_value, record_dates_in=record_dates_in)

    return dataset


def create_dataset(workspace, dataset_name, dataset_schema, sr):
    tmp_ds = None
    try:
        ds_type = dataset_schema.get('geometry_type')
        if ds_type is None:
            tmp_ds = arcpy.CreateTable_management(out_path=workspace, out_name=dataset_name)
        else:
            tmp_ds = arcpy.CreateFeatureclass_management(out_path=workspace, out_name=dataset_name, geometry_type=ds_type, spatial_reference=sr)

        add_fields(tmp_ds, dataset_schema['field_order'], dataset_schema['fields'])

        out_path = os.path.join(workspace, dataset_name)
        arcpy.CopyFeatures_management(in_features=tmp_ds, out_feature_class=out_path)

        # enable tracking after copy
        if 'tracking' in dataset_schema:
            enable_tracking(out_path, dataset_schema['tracking'])

        # add indexes after copy so they aren't dropped
        if 'indexes' in dataset_schema:
            add_indexes(out_path, dataset_schema['indexes'])

    finally:
        if tmp_ds:
            arcpy.Delete_management(tmp_ds)


def create_database(database_schema):
    workspace = database_schema['workspace']
    sr = arcpy.SpatialReference(database_schema['srid'])

    for dataset_name, dataset_schema in database_schema['datasets']:
        create_dataset(workspace, dataset_name, dataset_schema, sr)

    return workspace
