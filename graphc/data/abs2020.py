from graphc.da.arcgis_helpers import TableBase


class LGA2020(TableBase):
    def __init__(self, source):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """
        self.source = source
        self.lga_code_field = 'LGA_CODE20'
        self.lga_name_field = 'LGA_NAME20'
        self.ste_code_field = 'STE_CODE16'
        self.ste_name_field = 'STE_NAME16'
        self.area_sqkm_field = 'AREASQKM20'

        super().__init__(source=source, id_field=self.lga_code_field)

    @staticmethod
    def polygons(source=r'E:\Documents2\Data\ABS\2020\ABS2020_LGA.gdb\Simplified_Boundaries'):
        return LGA2020(source=source)

    @staticmethod
    def centroids(source=r'E:\Documents2\Data\ABS\2020\ABS2020_LGA.gdb\Centroids'):
        return LGA2020(source=source)