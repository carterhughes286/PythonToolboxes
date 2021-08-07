# -*- coding: utf-8 -*-

import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [OverwriteFeatureClass]


class OverwriteFeatureClass(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Overwrite Feature Class"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        input_fc = arcpy.Parameter(
            name = 'input_parks',
            displayName = 'Input Feature Class',
            datatype = 'DEFeatureClass',
            parameterType = 'Required',
            direction = 'Input'
        )

        input_sql = arcpy.Parameter(
            name = 'input_sql',
            displayName = 'Where Clause',
            datatype = 'GPSQLExpression',
            parameterType = 'Optional',
            direction = 'Input'
        )
        input_sql.parameterDependencies = [input_fc.name]

        input_fms = arcpy.Parameter(
            name = 'input_fms',
            displayName = 'Field Mapping',
            datatype = 'GPFieldMapping',
            parameterType = 'Optional',
            direction = 'Input'
        )
        input_fms.parameterDependencies = [input_fc.name]

        params = [input_fc, input_sql, input_fms]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        # if the input table view is changed
        if parameters[0].altered and not parameters[0].hasBeenValidated:
            inputTable = parameters[0].value

            # add a temporary item to the field mappings list
            # can be removed later by calling parameters[1].value.removeFieldMap(0)
            parameters[2].value = str('Empty')

            # add table fields
            parameters[2].value.addTable(inputTable)

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        input_fc = parameters[0].valueAsText
        input_sql = parameters[1].valueAsText
        input_fms = parameters[2].valueAsText

        fc_describe = arcpy.Describe(input_fc)
        out_path = fc_describe.path
        out_name = fc_describe.name
        out_path = out_path.replace('\\' + out_name, '')
        temp_path = r'memory'
        temp_fc = temp_path + '\\' + out_name

        arcpy.env.overwriteOutput = True

        arcpy.FeatureClassToFeatureClass_conversion(
            in_features=input_fc,
            out_path=temp_path,
            out_name=out_name,
            where_clause=input_sql,
            field_mapping=input_fms
        )

        arcpy.FeatureClassToFeatureClass_conversion(
            in_features=temp_fc,
            out_path=out_path,
            out_name=out_name
        )


        return
