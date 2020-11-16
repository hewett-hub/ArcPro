import arcpy
arcpy.server.ExportWebMap('{
    "operationalLayers": [
        {
            "id": "SSC_2076",
            "layerType": "ArcGISFeatureLayer",
            "url": "https://geo.abs.gov.au/arcgis/rest/services/ASGS2016/SSC/MapServer/0",
            "visibility": false,
            "opacity": 1,
            "mode": 1,
            "title": "Suburbs",
            "layerDefinition": {
                "drawingInfo": {
                    "renderer": {
                        "type": "simple",
                        "label": "",
                        "description": "",
                        "symbol": {
                            "color": null,
                            "outline": {
                                "color": [
                                    230,
                                    152,
                                    0,
                                    255
                                ],
                                "width": 1,
                                "type": "esriSLS",
                                "style": "esriSLSSolid"
                            },
                            "type": "esriSFS",
                            "style": "esriSFSSolid"
                        }
                    },
                    "labelingInfo": [
                        {
                            "labelExpression": null,
                            "labelExpressionInfo": {
                                "expression": "$feature[\"SSC_NAME_2016\"]",
                                "value": "{SSC_NAME_2016}"
                            },
                            "useCodedValues": true,
                            "maxScale": 0,
                            "minScale": 505744,
                            "where": null,
                            "labelPlacement": "esriServerPolygonPlacementAlwaysHorizontal",
                            "symbol": {
                                "color": [
                                    255,
                                    140,
                                    0,
                                    255
                                ],
                                "type": "esriTS",
                                "backgroundColor": null,
                                "borderLineColor": null,
                                "haloSize": 0.75,
                                "haloColor": [
                                    105,
                                    105,
                                    105,
                                    255
                                ],
                                "horizontalAlignment": "center",
                                "rightToLeft": false,
                                "angle": 0,
                                "xoffset": 0,
                                "yoffset": 0,
                                "text": "",
                                "rotated": false,
                                "kerning": true,
                                "font": {
                                    "size": 9.75,
                                    "style": "normal",
                                    "decoration": "none",
                                    "weight": "bold",
                                    "family": "Arial"
                                }
                            }
                        }
                    ]
                },
                "minScale": 1024905,
                "maxScale": 0
            },
            "showLabels": true,
            "popupInfo": {
                "title": "Suburb: {SSC_NAME_2016}",
                "fieldInfos": [
                    {
                        "fieldName": "OBJECTID",
                        "label": "OBJECTID",
                        "tooltip": "",
                        "visible": false,
                        "stringFieldOption": "textbox"
                    },
                    {
                        "fieldName": "Shape",
                        "label": "Shape",
                        "tooltip": "",
                        "visible": false,
                        "stringFieldOption": "textbox"
                    },
                    {
                        "fieldName": "SSC_CODE_2016",
                        "label": "SSC_CODE_2016",
                        "tooltip": "",
                        "visible": false,
                        "stringFieldOption": "textbox"
                    },
                    {
                        "fieldName": "Shape_Length",
                        "label": "Shape_Length",
                        "tooltip": "",
                        "visible": false,
                        "stringFieldOption": "textbox",
                        "format": {
                            "places": 2,
                            "digitSeparator": true
                        }
                    },
                    {
                        "fieldName": "Shape_Area",
                        "label": "Shape_Area",
                        "tooltip": "",
                        "visible": false,
                        "stringFieldOption": "textbox",
                        "format": {
                            "places": 2,
                            "digitSeparator": true
                        }
                    },
                    {
                        "fieldName": "SSC_NAME_2016",
                        "label": "SSC_NAME_2016",
                        "tooltip": "",
                        "visible": false,
                        "stringFieldOption": "textbox"
                    }
                ],
                "description": null,
                "showAttachments": true,
                "mediaInfos": []
            }
        },
        {
            "id": "PHUs_2499",
            "layerType": "ArcGISFeatureLayer",
            "url": "https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/PHUs/FeatureServer/0",
            "visibility": false,
            "opacity": 1,
            "title": "Public Health Unit areas",
            "itemId": "c50281358f9c459d96fa39307715a249",
            "layerDefinition": {
                "drawingInfo": {
                    "renderer": {
                        "type": "simple",
                        "symbol": {
                            "color": null,
                            "outline": {
                                "color": [
                                    76,
                                    230,
                                    0,
                                    255
                                ],
                                "width": 1.5,
                                "type": "esriSLS",
                                "style": "esriSLSSolid"
                            },
                            "type": "esriSFS",
                            "style": "esriSFSSolid"
                        }
                    },
                    "labelingInfo": [
                        {
                            "labelExpression": null,
                            "labelExpressionInfo": {
                                "expression": "$feature[\"PHU_Name\"]",
                                "value": "{PHU_Name}"
                            },
                            "useCodedValues": true,
                            "maxScale": 0,
                            "minScale": 0,
                            "where": null,
                            "labelPlacement": "esriServerPolygonPlacementAlwaysHorizontal",
                            "symbol": {
                                "color": [
                                    127,
                                    255,
                                    0,
                                    255
                                ],
                                "type": "esriTS",
                                "backgroundColor": null,
                                "borderLineColor": null,
                                "haloSize": 0,
                                "haloColor": null,
                                "horizontalAlignment": "center",
                                "rightToLeft": false,
                                "angle": 0,
                                "xoffset": 0,
                                "yoffset": 0,
                                "text": "",
                                "rotated": false,
                                "kerning": true,
                                "font": {
                                    "size": 9.75,
                                    "style": "normal",
                                    "decoration": "none",
                                    "weight": "bold",
                                    "family": "Arial"
                                }
                            }
                        }
                    ]
                }
            },
            "showLabels": true
        },
        {
            "id": "ABS2020_LGA_Simplified_3477",
            "layerType": "ArcGISFeatureLayer",
            "url": "https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/ABS2020_LGA_Simplified/FeatureServer/0",
            "visibility": false,
            "opacity": 1,
            "title": "Local Government Areas (LGA)",
            "itemId": "400d928f6cf942ec98d6fdc6056a11bc",
            "layerDefinition": {
                "drawingInfo": {
                    "renderer": {
                        "type": "simple",
                        "symbol": {
                            "color": null,
                            "outline": {
                                "color": [
                                    0,
                                    92,
                                    230,
                                    255
                                ],
                                "width": 0.7,
                                "type": "esriSLS",
                                "style": "esriSLSSolid"
                            },
                            "type": "esriSFS",
                            "style": "esriSFSSolid"
                        }
                    },
                    "scaleSymbols": true
                }
            },
            "popupInfo": {
                "title": "LGA: {LGA_CODE20}",
                "fieldInfos": [
                    {
                        "fieldName": "OBJECTID",
                        "visible": false,
                        "isEditable": false,
                        "label": "OBJECTID"
                    },
                    {
                        "fieldName": "LGA_CODE20",
                        "visible": false,
                        "isEditable": true,
                        "label": "LGA CODE"
                    },
                    {
                        "fieldName": "LGA_NAME20",
                        "visible": true,
                        "isEditable": true,
                        "label": "LGA NAME"
                    },
                    {
                        "fieldName": "STE_CODE16",
                        "visible": false,
                        "isEditable": true,
                        "label": "STE_CODE16"
                    },
                    {
                        "fieldName": "STE_NAME16",
                        "visible": true,
                        "isEditable": true,
                        "label": "State"
                    },
                    {
                        "fieldName": "AREASQKM20",
                        "visible": false,
                        "isEditable": true,
                        "label": "AREASQKM20",
                        "format": {
                            "places": 2,
                            "digitSeparator": true
                        }
                    },
                    {
                        "fieldName": "Shape__Area",
                        "label": "Shape__Area",
                        "isEditable": false,
                        "visible": false,
                        "format": {
                            "places": 2,
                            "digitSeparator": true
                        }
                    },
                    {
                        "fieldName": "Shape__Length",
                        "label": "Shape__Length",
                        "isEditable": false,
                        "visible": false,
                        "format": {
                            "places": 2,
                            "digitSeparator": true
                        }
                    }
                ],
                "description": null,
                "showAttachments": false,
                "mediaInfos": []
            }
        },
        {
            "id": "ABS2016_POA_7653",
            "layerType": "ArcGISFeatureLayer",
            "url": "https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/ABS2016_POA/FeatureServer/0",
            "visibility": false,
            "opacity": 1,
            "title": "Postcodes",
            "itemId": "27e6993efb524000ad12b1e18a047bc3",
            "layerDefinition": {
                "drawingInfo": {
                    "renderer": {
                        "type": "simple",
                        "symbol": {
                            "color": null,
                            "outline": {
                                "color": [
                                    255,
                                    115,
                                    223,
                                    255
                                ],
                                "width": 0.375,
                                "type": "esriSLS",
                                "style": "esriSLSSolid"
                            },
                            "type": "esriSFS",
                            "style": "esriSFSSolid"
                        }
                    },
                    "scaleSymbols": true
                }
            },
            "popupInfo": {
                "title": "{POA_NAME16}",
                "fieldInfos": [
                    {
                        "fieldName": "OBJECTID",
                        "visible": false,
                        "isEditable": false,
                        "label": "FID"
                    },
                    {
                        "fieldName": "POA_CODE16",
                        "visible": false,
                        "isEditable": true,
                        "label": "POA_CODE16"
                    },
                    {
                        "fieldName": "POA_NAME16",
                        "visible": true,
                        "isEditable": true,
                        "label": "Postcode"
                    },
                    {
                        "fieldName": "AREASQKM16",
                        "visible": false,
                        "isEditable": true,
                        "label": "AREASQKM16",
                        "format": {
                            "places": 2,
                            "digitSeparator": true
                        }
                    },
                    {
                        "fieldName": "Shape__Area",
                        "label": "Shape__Area",
                        "isEditable": false,
                        "visible": false,
                        "format": {
                            "places": 2,
                            "digitSeparator": true
                        }
                    },
                    {
                        "fieldName": "Shape__Length",
                        "label": "Shape__Length",
                        "isEditable": false,
                        "visible": false,
                        "format": {
                            "places": 2,
                            "digitSeparator": true
                        }
                    }
                ],
                "description": null,
                "showAttachments": false,
                "mediaInfos": []
            }
        },
        {
            "id": "COVID_19_Postcode_Statistic_Polygons_8809",
            "layerType": "ArcGISFeatureLayer",
            "url": "https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Postcode_Statistic_Polygons/FeatureServer/0",
            "visibility": false,
            "opacity": 1,
            "title": "Postcodes With no Reported Cases",
            "itemId": "63f51f79e6784d83870cc0d7b9a81c75",
            "layerDefinition": {
                "definitionExpression": "(MostRecentNewCases IS NULL) AND (Postcode LIKE '2%')",
                "drawingInfo": {
                    "renderer": {
                        "type": "simple",
                        "symbol": {
                            "color": [
                                214,
                                214,
                                214,
                                255
                            ],
                            "outline": {
                                "color": [
                                    255,
                                    115,
                                    223,
                                    67
                                ],
                                "width": 0.75,
                                "type": "esriSLS",
                                "style": "esriSLSSolid"
                            },
                            "type": "esriSFS",
                            "style": "esriSFSSolid"
                        }
                    }
                }
            },
            "popupInfo": {
                "title": "Postcode: {Postcode}",
                "fieldInfos": [
                    {
                        "fieldName": "OBJECTID",
                        "visible": false,
                        "isEditable": false,
                        "format": {
                            "places": 0,
                            "digitSeparator": false
                        },
                        "label": "OBJECTID"
                    },
                    {
                        "fieldName": "Postcode",
                        "visible": false,
                        "isEditable": true,
                        "label": "Postcode"
                    },
                    {
                        "fieldName": "MostRecentDateCode",
                        "visible": false,
                        "isEditable": true,
                        "label": "DateCode"
                    },
                    {
                        "fieldName": "TotalCases",
                        "visible": true,
                        "isEditable": true,
                        "format": {
                            "places": 0,
                            "digitSeparator": false
                        },
                        "label": "Total Cases"
                    },
                    {
                        "fieldName": "MostRecentCaseDate",
                        "visible": true,
                        "isEditable": true,
                        "label": "Last Case Date",
                        "format": {
                            "dateFormat": "shortDateLE",
                            "timezone": "utc"
                        }
                    },
                    {
                        "fieldName": "MostRecentNewCases",
                        "visible": true,
                        "isEditable": true,
                        "format": {
                            "places": 0,
                            "digitSeparator": false
                        },
                        "label": "Last Case Count"
                    },
                    {
                        "fieldName": "Shape__Area",
                        "visible": false,
                        "isEditable": false,
                        "format": {
                            "places": 6,
                            "digitSeparator": false
                        },
                        "label": "Shape__Area"
                    },
                    {
                        "fieldName": "Shape__Length",
                        "visible": false,
                        "isEditable": false,
                        "format": {
                            "places": 6,
                            "digitSeparator": false
                        },
                        "label": "Shape__Length"
                    }
                ],
                "description": null,
                "showAttachments": false,
                "mediaInfos": []
            }
        },
        {
            "id": "COVID_19_Postcode_Statistic_Polygons_4798",
            "layerType": "ArcGISFeatureLayer",
            "url": "https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Postcode_Statistic_Polygons/FeatureServer/0",
            "visibility": false,
            "opacity": 0.8,
            "title": "Cumulative cases and last reported cases by date",
            "itemId": "63f51f79e6784d83870cc0d7b9a81c75",
            "layerDefinition": {
                "definitionExpression": "MostRecentNewCases >= 1",
                "drawingInfo": {
                    "renderer": {
                        "visualVariables": [
                            {
                                "type": "colorInfo",
                                "field": "TotalCases",
                                "valueExpression": null,
                                "stops": [
                                    {
                                        "value": 1,
                                        "color": [
                                            255,
                                            255,
                                            178,
                                            255
                                        ],
                                        "label": "< 1"
                                    },
                                    {
                                        "value": 30.25,
                                        "color": [
                                            254,
                                            204,
                                            92,
                                            255
                                        ],
                                        "label": null
                                    },
                                    {
                                        "value": 59.5,
                                        "color": [
                                            253,
                                            141,
                                            60,
                                            255
                                        ],
                                        "label": "59"
                                    },
                                    {
                                        "value": 88.75,
                                        "color": [
                                            240,
                                            59,
                                            32,
                                            255
                                        ],
                                        "label": null
                                    },
                                    {
                                        "value": 118,
                                        "color": [
                                            189,
                                            0,
                                            38,
                                            255
                                        ],
                                        "label": "> 118"
                                    }
                                ]
                            }
                        ],
                        "authoringInfo": {
                            "visualVariables": [
                                {
                                    "type": "colorInfo",
                                    "minSliderValue": 1,
                                    "maxSliderValue": 118,
                                    "theme": "high-to-low"
                                }
                            ]
                        },
                        "type": "classBreaks",
                        "field": "TotalCases",
                        "minValue": -9007199254740991,
                        "classBreakInfos": [
                            {
                                "symbol": {
                                    "color": [
                                        170,
                                        170,
                                        170,
                                        255
                                    ],
                                    "outline": {
                                        "color": [
                                            255,
                                            115,
                                            223,
                                            64
                                        ],
                                        "width": 0.75,
                                        "type": "esriSLS",
                                        "style": "esriSLSSolid"
                                    },
                                    "type": "esriSFS",
                                    "style": "esriSFSSolid"
                                },
                                "classMaxValue": 9007199254740991
                            }
                        ]
                    }
                }
            },
            "popupInfo": {
                "title": "Postcode: {Postcode}",
                "fieldInfos": [
                    {
                        "fieldName": "OBJECTID",
                        "visible": false,
                        "isEditable": false,
                        "format": {
                            "places": 0,
                            "digitSeparator": false
                        },
                        "label": "OBJECTID"
                    },
                    {
                        "fieldName": "Postcode",
                        "visible": false,
                        "isEditable": true,
                        "label": "Postcode"
                    },
                    {
                        "fieldName": "MostRecentDateCode",
                        "visible": false,
                        "isEditable": true,
                        "label": "DateCode"
                    },
                    {
                        "fieldName": "TotalCases",
                        "visible": true,
                        "isEditable": true,
                        "format": {
                            "places": 0,
                            "digitSeparator": false
                        },
                        "label": "Total Cases"
                    },
                    {
                        "fieldName": "MostRecentCaseDate",
                        "visible": true,
                        "isEditable": true,
                        "label": "Last Case Date",
                        "format": {
                            "dateFormat": "shortDateLE",
                            "timezone": "utc"
                        }
                    },
                    {
                        "fieldName": "MostRecentNewCases",
                        "visible": true,
                        "isEditable": true,
                        "format": {
                            "places": 0,
                            "digitSeparator": false
                        },
                        "label": "Last Case Count"
                    },
                    {
                        "fieldName": "Shape__Area",
                        "visible": false,
                        "isEditable": false,
                        "format": {
                            "places": 6,
                            "digitSeparator": false
                        },
                        "label": "Shape__Area"
                    },
                    {
                        "fieldName": "Shape__Length",
                        "visible": false,
                        "isEditable": false,
                        "format": {
                            "places": 6,
                            "digitSeparator": false
                        },
                        "label": "Shape__Length"
                    }
                ],
                "description": null,
                "showAttachments": false,
                "mediaInfos": []
            }
        },
        {
            "id": "Aged_Care_Facilities_2019_7230",
            "layerType": "ArcGISFeatureLayer",
            "url": "https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/Aged_Care_Facilities_2019/FeatureServer/0",
            "visibility": false,
            "opacity": 0.65,
            "title": "Aged Care Facilities 2019",
            "itemId": "775a6b5cf52241dca157ef326f493734"
        },
        {
            "id": "Case_Locations_By_Postcode_1037",
            "layerType": "ArcGISFeatureLayer",
            "url": "https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/Case_Locations_By_Postcode/FeatureServer/0",
            "visibility": true,
            "opacity": 1,
            "title": "Cases by Locality",
            "itemId": "13ac948c62d04066984d48b440517faa",
            "refreshInterval": 30,
            "layerDefinition": {
                "drawingInfo": {
                    "renderer": {
                        "type": "simple",
                        "symbol": {
                            "color": [
                                255,
                                0,
                                0,
                                128
                            ],
                            "size": 4,
                            "angle": 0,
                            "xoffset": 0,
                            "yoffset": 0,
                            "type": "esriSMS",
                            "style": "esriSMSCircle",
                            "outline": {
                                "color": [
                                    230,
                                    0,
                                    0,
                                    255
                                ],
                                "width": 0.9975,
                                "type": "esriSLS",
                                "style": "esriSLSSolid"
                            }
                        }
                    },
                    "scaleSymbols": true
                },
                "featureReduction": {
                    "type": "cluster",
                    "clusterRadius": 46.578947368421055,
                    "popupInfo": {
                        "title": "",
                        "fieldInfos": [
                            {
                                "fieldName": "cluster_count",
                                "label": "Cases in vicinity:",
                                "visible": true,
                                "format": {
                                    "digitSeparator": false,
                                    "places": 0
                                }
                            }
                        ],
                        "description": null,
                        "showAttachments": false
                    }
                }
            },
            "popupInfo": {
                "title": "{PostCode} : {ReportDate}",
                "fieldInfos": [
                    {
                        "fieldName": "OBJECTID",
                        "label": "OBJECTID",
                        "isEditable": false,
                        "visible": false
                    },
                    {
                        "fieldName": "DateString",
                        "label": "DateString",
                        "isEditable": true,
                        "visible": false,
                        "stringFieldOption": "textbox"
                    },
                    {
                        "fieldName": "PostCode",
                        "label": "PostCode",
                        "isEditable": true,
                        "visible": true,
                        "stringFieldOption": "textbox"
                    },
                    {
                        "fieldName": "ReportDate",
                        "label": "ReportDate",
                        "isEditable": true,
                        "visible": true,
                        "format": {
                            "dateFormat": "shortDateLE",
                            "timezone": "utc"
                        }
                    },
                    {
                        "fieldName": "LikelySource",
                        "label": "Likely Source",
                        "isEditable": true,
                        "visible": true,
                        "stringFieldOption": "textbox"
                    }
                ],
                "description": null,
                "showAttachments": false,
                "mediaInfos": []
            }
        },
        {
            "id": "COVID_19_Alerts_2192",
            "layerType": "ArcGISFeatureLayer",
            "url": "https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Alerts/FeatureServer/1",
            "visibility": false,
            "opacity": 1,
            "title": "Historical NSW COVID-19 Alert Locations",
            "itemId": "b6bb815b177943f4a041a2094f299817",
            "layerDefinition": {
                "drawingInfo": {
                    "renderer": {
                        "type": "uniqueValue",
                        "field1": "Alert",
                        "defaultSymbol": {
                            "angle": 0,
                            "xoffset": 0,
                            "yoffset": 0,
                            "type": "esriPMS",
                            "url": "http://static.arcgis.com/images/Symbols/Shapes/PurpleStarLargeB.png",
                            "imageData": "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAZdEVYdFNvZnR3YXJlAEFkb2JlIEltYWdlUmVhZHlxyWU8AAADImlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS4wLWMwNjAgNjEuMTM0Nzc3LCAyMDEwLzAyLzEyLTE3OjMyOjAwICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdFJlZj0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgQ1M1IE1hY2ludG9zaCIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpEMkI3OTNERUQzM0MxMUUwQUU5NUVFMEYwMTY0NzUwNSIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDpEMkI3OTNERkQzM0MxMUUwQUU5NUVFMEYwMTY0NzUwNSI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ4bXAuaWlkOkQyQjc5M0RDRDMzQzExRTBBRTk1RUUwRjAxNjQ3NTA1IiBzdFJlZjpkb2N1bWVudElEPSJ4bXAuZGlkOkQyQjc5M0RERDMzQzExRTBBRTk1RUUwRjAxNjQ3NTA1Ii8+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQg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",
                            "contentType": "image/png",
                            "width": 24,
                            "height": 24
                        },
                        "defaultLabel": "Other",
                        "uniqueValueInfos": [
                            {
                                "value": "Monitor for symptoms",
                                "symbol": {
                                    "angle": 0,
                                    "xoffset": 0,
                                    "yoffset": 0,
                                    "type": "esriPMS",
                                    "url": "http://static.arcgis.com/images/Symbols/Shapes/BlueStarLargeB.png",
                                    "imageData": "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAZdEVYdFNvZnR3YXJlAEFkb2JlIEltYWdlUmVhZHlxyWU8AAADImlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS4wLWMwNjAgNjEuMTM0Nzc3LCAyMDEwLzAyLzEyLTE3OjMyOjAwICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdFJlZj0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgQ1M1IE1hY2ludG9zaCIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDo2MzI2NjFBRkQzMzkxMUUwQUU5NUVFMEYwMTY0NzUwNSIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDo2MzI2NjFCMEQzMzkxMUUwQUU5NUVFMEYwMTY0NzUwNSI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ4bXAuaWlkOjYzMjY2MUFERDMzOTExRTBBRTk1RUUwRjAxNjQ3NTA1IiBzdFJlZjpkb2N1bWVudElEPSJ4bXAuZGlkOjYzMjY2MUFFRDMzOTExRTBBRTk1RUUwRjAxNjQ3NTA1Ii8+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQg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",
                                    "contentType": "image/png",
                                    "width": 24,
                                    "height": 24
                                },
                                "label": "Monitor for symptoms"
                            },
                            {
                                "value": "Self-isolate and get tested immediately",
                                "symbol": {
                                    "angle": 0,
                                    "xoffset": 0,
                                    "yoffset": 0,
                                    "type": "esriPMS",
                                    "url": "http://static.arcgis.com/images/Symbols/Shapes/OrangeStarLargeB.png",
                                    "imageData": "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAZdEVYdFNvZnR3YXJlAEFkb2JlIEltYWdlUmVhZHlxyWU8AAADImlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS4wLWMwNjAgNjEuMTM0Nzc3LCAyMDEwLzAyLzEyLTE3OjMyOjAwICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdFJlZj0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlUmVmIyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgQ1M1IE1hY2ludG9zaCIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpFMEVFRERERUQyODExMUUwQUU5NUVFMEYwMTY0NzUwNSIgeG1wTU06RG9jdW1lbnRJRD0ieG1wLmRpZDpFMEVFRERERkQyODExMUUwQUU5NUVFMEYwMTY0NzUwNSI+IDx4bXBNTTpEZXJpdmVkRnJvbSBzdFJlZjppbnN0YW5jZUlEPSJ4bXAuaWlkOkUwRUVERERDRDI4MTExRTBBRTk1RUUwRjAxNjQ3NTA1IiBzdFJlZjpkb2N1bWVudElEPSJ4bXAuZGlkOkUwRUVERERERDI4MTExRTBBRTk1RUUwRjAxNjQ3NTA1Ii8+IDwvcmRmOkRlc2NyaXB0aW9uPiA8L3JkZjpSREY+IDwveDp4bXBtZXRhPiA8P3hwYWNrZXQg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",
                                    "contentType": "image/png",
                                    "width": 24,
                                    "height": 24
                                },
                                "label": "Self-isolate and get tested immediately"
                            }
                        ]
                    }
                }
            },
            "popupInfo": {
                "title": "{Date}",
                "fieldInfos": [
                    {
                        "fieldName": "OBJECTID",
                        "visible": false,
                        "isEditable": false,
                        "format": {
                            "places": 0,
                            "digitSeparator": false
                        },
                        "label": "OBJECTID"
                    },
                    {
                        "fieldName": "Date",
                        "visible": true,
                        "isEditable": true,
                        "label": "Date",
                        "format": {
                            "dateFormat": "shortDateLE",
                            "timezone": "utc"
                        }
                    },
                    {
                        "fieldName": "Venue",
                        "visible": true,
                        "isEditable": true,
                        "label": "Venue"
                    },
                    {
                        "fieldName": "Address",
                        "visible": true,
                        "isEditable": true,
                        "label": "Address"
                    },
                    {
                        "fieldName": "Suburb",
                        "visible": true,
                        "isEditable": true,
                        "label": "Suburb"
                    },
                    {
                        "fieldName": "Dates",
                        "visible": true,
                        "isEditable": true,
                        "label": "Dates"
                    },
                    {
                        "fieldName": "Times",
                        "visible": true,
                        "isEditable": true,
                        "label": "Times"
                    },
                    {
                        "fieldName": "Alert",
                        "visible": true,
                        "isEditable": true,
                        "label": "Alert"
                    }
                ],
                "description": null,
                "showAttachments": false,
                "mediaInfos": []
            }
        },
        {
            "id": "COVID_19_Alerts_3408",
            "layerType": "ArcGISFeatureLayer",
            "url": "https://services9.arcgis.com/7eQuDPPaB6g9029K/arcgis/rest/services/COVID_19_Alerts/FeatureServer/0",
            "visibility": true,
            "opacity": 1,
            "title": "Current NSW COVID-19 Alert Locations",
            "itemId": "8a04da3e42ea4ef6bf1f06828ca33a00",
            "layerDefinition": {
                "drawingInfo": {
                    "renderer": {
                        "type": "uniqueValue",
                        "field1": "Alert",
                        "defaultSymbol": {
                            "angle": 0,
                            "xoffset": 0,
                            "yoffset": 20.25,
                            "type": "esriPMS",
                            "url": "http://static.arcgis.com/images/Symbols/Basic/PurpleStickpin.png",
                            "imageData": "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",
                            "contentType": "image/png",
                            "width": 24,
                            "height": 24
                        },
                        "defaultLabel": "Other",
                        "uniqueValueInfos": [
                            {
                                "value": "Monitor for symptoms",
                                "symbol": {
                                    "angle": 0,
                                    "xoffset": 0,
                                    "yoffset": 21,
                                    "type": "esriPMS",
                                    "url": "http://static.arcgis.com/images/Symbols/Basic/BlueStickpin.png",
                                    "imageData": "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",
                                    "contentType": "image/png",
                                    "width": 24,
                                    "height": 24
                                },
                                "label": "Monitor for symptoms"
                            },
                            {
                                "value": "Self-isolate and get tested immediately",
                                "symbol": {
                                    "angle": 0,
                                    "xoffset": 0,
                                    "yoffset": 19.5,
                                    "type": "esriPMS",
                                    "url": "http://static.arcgis.com/images/Symbols/Basic/OrangeStickpin.png",
                                    "imageData": "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",
                                    "contentType": "image/png",
                                    "width": 24,
                                    "height": 24
                                },
                                "label": "Self-isolate and get tested immediately"
                            }
                        ]
                    }
                }
            },
            "popupInfo": {
                "title": "{Venue}",
                "fieldInfos": [
                    {
                        "fieldName": "OBJECTID",
                        "visible": false,
                        "isEditable": false,
                        "format": {
                            "places": 0,
                            "digitSeparator": false
                        },
                        "label": "OBJECTID"
                    },
                    {
                        "fieldName": "Venue",
                        "visible": true,
                        "isEditable": true,
                        "label": "Venue"
                    },
                    {
                        "fieldName": "Address",
                        "visible": true,
                        "isEditable": true,
                        "label": "Address"
                    },
                    {
                        "fieldName": "Suburb",
                        "visible": true,
                        "isEditable": true,
                        "label": "Suburb"
                    },
                    {
                        "fieldName": "Dates",
                        "visible": true,
                        "isEditable": true,
                        "label": "Dates"
                    },
                    {
                        "fieldName": "Times",
                        "visible": true,
                        "isEditable": true,
                        "label": "Times"
                    },
                    {
                        "fieldName": "Alert",
                        "visible": true,
                        "isEditable": true,
                        "label": "Alert"
                    }
                ],
                "description": null,
                "showAttachments": false,
                "mediaInfos": []
            }
        }
    ],
    "baseMap": {
        "baseMapLayers": [
            {
                "id": "VectorTile_2846",
                "type": "VectorTileLayer",
                "layerType": "VectorTileLayer",
                "title": "Dark Gray Base",
                "styleUrl": "https://cdn.arcgis.com/sharing/rest/content/items/5e9b3685f4c24d8781073dd928ebda50/resources/styles/root.json",
                "visibility": true,
                "opacity": 1
            },
            {
                "id": "VectorTile_1645",
                "type": "VectorTileLayer",
                "layerType": "VectorTileLayer",
                "title": "Dark Gray Reference",
                "styleUrl": "https://cdn.arcgis.com/sharing/rest/content/items/747cb7a5329c478cbe6981076cc879c5/resources/styles/root.json",
                "isReference": true,
                "visibility": true,
                "opacity": 1
            }
        ],
        "title": "Dark Gray Canvas"
    },
    "spatialReference": {
        "wkid": 102100,
        "latestWkid": 3857
    },
    "authoringApp": "WebMapViewer",
    "authoringAppVersion": "8.3",
    "version": "2.18",
    "bookmarks": [
        {
            "extent": {
                "spatialReference": {
                    "wkid": 102100,
                    "latestWkid": 3857
                },
                "xmax": 18523341.368249368,
                "xmin": 14910621.663379757,
                "ymax": -3101201.7429867825,
                "ymin": -4913676.5576844
            },
            "name": "NSW"
        },
        {
            "extent": {
                "spatialReference": {
                    "wkid": 102100,
                    "latestWkid": 3857
                },
                "xmax": 16894355.53442113,
                "xmin": 16781458.043643884,
                "ymax": -3980214.197271071,
                "ymin": -4036854.035230408
            },
            "name": "Sydney Region"
        },
        {
            "extent": {
                "spatialReference": {
                    "wkid": 102100,
                    "latestWkid": 3857
                },
                "xmax": 17107705.60141512,
                "xmin": 15301345.748980312,
                "ymax": -3942055.9135923623,
                "ymin": -4848293.320941171
            },
            "name": "VIC"
        },
        {
            "extent": {
                "spatialReference": {
                    "wkid": 102100,
                    "latestWkid": 3857
                },
                "xmax": 16275688.548531175,
                "xmin": 16049893.566976871,
                "ymax": -4500581.279272003,
                "ymin": -4613860.95519058
            },
            "name": "Melbourne Region"
        }
    ]
}', r"C:\tmp\Printed.pdf", "PDF", None, "MAP_ONLY")
