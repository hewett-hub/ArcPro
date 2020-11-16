import arcpy


def execute(in_rows):
    i = 0
    fields = ["OID@"]
    with arcpy.da.SearchCursor(in_rows, fields) as cursor:
        for row in cursor:
            i += 1

    return i


if __name__ == "__main__":
    sourceTable = arcpy.GetParameterAsText(0)

    row_count = execute(sourceTable)

    arcpy.SetParameter(1, row_count)
