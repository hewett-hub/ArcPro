from graphc.da.arcgis_helpers import TableBase


class POA2016(TableBase):
    def __init__(self, source):
        self.source = source
        self.poa_code_field = 'POA_CODE16'
        self.poa_name_field = 'POA_NAME16'
        self.area_sqkm_field = 'AREA_SQKM16'

        super().__init__(source=source, id_field=self.poa_code_field)

    @staticmethod
    def polygons(source=r'E:\Documents2\Data\ABS\2016\WGS84wmas\ASGS3_NonABSStructures_Simp100.gdb\POA_2016_AUST'):
        return POA2016(source=source)

    @staticmethod
    def centroids(source=r'E:\Documents2\Data\ABS\2016\WGS84wmas\ASGS3_NonABSStructures.gdb\POA_2016_AUST_Centroids'):
        return POA2016(source=source)