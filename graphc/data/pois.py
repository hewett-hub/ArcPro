from graphc.da.arcgis_helpers import TableBase


class StateCapitals(TableBase):
    def __init__(self, source=r'E:\Documents2\Data\POIs\ReferenceLocations.gdb\StateCapitals'):
        """
        :param source: The source feature class or feature layer to be used.  Must already exist.
        :type source: path to features or a feature layer.
        """

        self.ste_code_field = 'STE_CODE16'
        self.ste_name_field = 'STE_NAME16'
        self.ste_abbv_field = 'STE_ABBV'
        self.name_field = 'Name'

        super().__init__(source=source, id_field=self.ste_abbv_field)

