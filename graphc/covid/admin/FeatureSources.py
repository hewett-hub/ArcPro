import arcpy


class FeatureSources(object):
    """A factory class to create FeatureSource objects"""
    def __init__(self):
        self._state_capital_points = None
        self._postcode_points = None
        self._postcode_polygons = None

    def postcode_points(self):
        if self._postcode_points is None:
            self._postcode_points = PostcodePoints()

        return self._postcode_points

    def postcode_polygons(self):
        if self._postcode_polygons is None:
            self._postcode_polygons = PostcodePolygons()

        return self._postcode_polygons

    def state_capital_points(self):
        if self._state_capital_points is None:
            self._state_capital_points = StateCapitalPoints()

        return self._state_capital_points


class PostcodePoints(object):
    def __init__(self, source=r'E:\Documents2\Data\ABS\2016\WGS84wmas\ASGS3_NonABSStructures.gdb\POA_2016_AUST_Centroids', id_field='POA_CODE16'):
        self.source = source
        self.id_field = id_field
        self._items = None

    def items(self):
        """
        Returns the geometries indexed by the id_field
        :return:
        :rtype:
        """
        if not self._items:
            result = {}

            fields = [self.id_field, 'SHAPE@']
            with arcpy.da.SearchCursor(self.source, fields) as cursor:
                for row in cursor:
                    result[row[0].upper()] = row[1]

            self._items = result

        return self._items


class PostcodePolygons(object):
    def __init__(self, source=r'E:\Documents2\Data\ABS\2016\WGS84wmas\ASGS3_NonABSStructures_Simp100.gdb\POA_2016_AUST', id_field='POA_CODE16'):
        self.source = source
        self.id_field = id_field
        self._items = None

    def items(self):
        """
        Returns the geometries indexed by the id_field
        :return:
        :rtype:
        """
        if not self._items:
            result = {}

            fields = [self.id_field, 'SHAPE@']
            with arcpy.da.SearchCursor(self.source, fields) as cursor:
                for row in cursor:
                    result[row[0].upper()] = row[1]

            self._items = result

        return self._items


class StateCapitalPoints(object):
    def __init__(self, source=r'E:\Documents2\Data\POIs\ReferenceLocations.gdb\StateCapitals', id_field='STE_ABBV'):
        self.source = source
        self.id_field = id_field
        self._items = None

    def items(self):
        """
        Returns the geometries indexed by the id_field
        :return:
        :rtype:
        """
        if not self._items:
            result = {}

            fields = [self.id_field, 'SHAPE@']
            with arcpy.da.SearchCursor(self.source, fields) as cursor:
                for row in cursor:
                    result[row[0].upper()] = row[1]

            self._items = result

        return self._items
