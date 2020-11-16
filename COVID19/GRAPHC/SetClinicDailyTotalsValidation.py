import arcpy


class ToolValidator(object):
    """Class for validating a tool's parameter values and controlling
    the behavior of the tool's dialog."""

    def __init__(self):
        """Setup arcpy and the list of tool parameters."""
        self.params = arcpy.GetParameterInfo()
        self.fcfield = (None, None)

    def initializeParameters(self):
        """Refine the properties of a tool's parameters.
        This method is called when the tool is opened."""

    def updateParameters(self):
        """Modify the values and properties of parameters before internal
        validation is performed. This method is called whenever a parameter
        has been changed."""

        if self.params[0].value and self.params[1].value:
            fc, col = str(self.params[0].value), str(self.params[1].value)
            if self.fcfield != (fc, col):
                self.fcfield = (fc, col)
                self.params[3].filter.list = [str(val) for val in
                                              sorted(
                                                  set(
                                                      row.getValue(col)
                                                      for row in arcpy.SearchCursor(fc,
                                                                                    fields=col)
                                                  )
                                              )
                                              ]
                if self.params[3].value not in self.params[3].filter.list:
                    self.params[3].value = self.params[3].filter.list[0]

    def updateMessages(self):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

