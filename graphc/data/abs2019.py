from graphc.da.arcgis_helpers import TableBase


class LGA2019(TableBase):
    def __init__(self, source):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        self.source = source
        self.lga_code_field = 'LGA_CODE19'
        self.lga_name_field = 'LGA_NAME19'
        self.ste_code_field = 'STE_CODE16'
        self.ste_name_field = 'STE_NAME16'
        self.area_sqkm_field = 'AREASQKM19'

        super().__init__(source=source, id_field=self.lga_code_field)

    @staticmethod
    def polygons(source=r'E:\Documents2\Data\ABS\2019\ABS2019_LGA.gdb\Simplified_Boundaries'):
        return LGA2019(source=source)

    @staticmethod
    def centroids(source=r'E:\Documents2\Data\ABS\2019\ABS2019_LGA.gdb\Centroids'):
        return LGA2019(source=source)