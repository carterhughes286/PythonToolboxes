# -*- coding: utf-8 -*-

import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [OverwriteFeatureClass, SpatialJoinAlterInput]


class OverwriteFeatureClass(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Overwrite Feature Class"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        param0 = arcpy.Parameter(
            name = 'param0',
            displayName = 'Input Feature Class',
            datatype = 'DEFeatureClass',
            parameterType = 'Required',
            direction = 'Input'
        )

        param1 = arcpy.Parameter(
            name = 'param1',
            displayName = 'Where Clause',
            datatype = 'GPSQLExpression',
            parameterType = 'Optional',
            direction = 'Input'
        )
        param1.parameterDependencies = [param0.name]

        param2 = arcpy.Parameter(
            name = 'param2',
            displayName = 'Field Mapping',
            datatype = 'GPFieldMapping',
            parameterType = 'Optional',
            direction = 'Input'
        )
        param2.parameterDependencies = [param0.name]

        params = [param0, param1, param2]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        # altered is true if the value of a parameter is changed.
        # hasBeenValidated is false if a parameter's value has been modified by the user since the last time updateParameters...
        # and internal validate were called. Once internal validate has been called, geoprocessing automatically sets...
        # hasBeenValidated to true for every parameter.
        if parameters[0].altered and not parameters[0].hasBeenValidated: # if the input table view is changed
            inputTable = parameters[0].value

            # add a temporary item to the field mappings list
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
        param0 = parameters[0].valueAsText # input feature class
        param1 = parameters[1].valueAsText # input SQL where clause
        param2 = parameters[2].valueAsText # input field mappings

        # derive assumed parameters
        fc_describe = arcpy.Describe(param0)
        out_path = fc_describe.path
        out_name = fc_describe.name
        out_path = out_path.replace('\\' + out_name, '')
        temp_path = r'memory'
        temp_fc = temp_path + '\\' + out_name

        # export input feature class to memory with changes as defined by the tool parameters
        arcpy.FeatureClassToFeatureClass_conversion(
            in_features=param0,
            out_path=temp_path,
            out_name=out_name,
            where_clause=param1,
            field_mapping=param2
        )

        # delete input feature class
        arcpy.Delete_management(
            in_data=param0
        )

        # export the modified feature class in memory to original location
        arcpy.FeatureClassToFeatureClass_conversion(
            in_features=temp_fc,
            out_path=out_path,
            out_name=out_name
        )

        return param0

class SpatialJoinAlterInput(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Spatial Join - Alter Input"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            name = 'param0',
            displayName = 'Target Features',
            datatype = 'DEFeatureClass',
            parameterType = 'Required',
            direction = 'Input'
        )

        param1 = arcpy.Parameter(
            name = 'param1',
            displayName = 'Target Features - Where Clause',
            datatype = 'GPSQLExpression',
            parameterType = 'Optional',
            direction = 'Input'
        )
        param1.parameterDependencies = [param0.name]

        param2 = arcpy.Parameter(
            name = 'param2',
            displayName = 'Join Features',
            datatype = 'DEFeatureClass',
            parameterType = 'Required',
            direction = 'Input'
        )

        param3 = arcpy.Parameter(
            name = 'param3',
            displayName = 'Join Features - Where Clause',
            datatype = 'GPSQLExpression',
            parameterType = 'Optional',
            direction = 'Input'
        )
        param3.parameterDependencies = [param2.name]

        param4 = arcpy.Parameter(
            name = 'param4',
            displayName = 'Field Mapping',
            datatype = 'GPFieldMapping',
            parameterType = 'Required',
            direction = 'Input'
        )
        param4.parameterDependencies = [param0.name, param2.name]

        param5 = arcpy.Parameter(
            name = 'param5',
            displayName = 'Match Option',
            datatype = 'GPString',
            parameterType = 'Required',
            direction = 'Input'
        )
        param5.filter.type = 'ValueList'
        param5.filter.list = ['INTERSECT', 'INTERSECT_3D', 'WITHIN_A_DISTANCE', 'WITHIN_A_DISTANCE_GEODESIC', 'CONTAINS', 'COMPLETELY_CONTAINS', 'CONTAINS_CLEMENTINI', 'WITHIN', 'COMPLETELY_WITHIN', 'WITHIN_CLEMENTINI', 'ARE_IDENTICAL_TO', 'BOUNDARY_TOUCHES', 'SHARE_A_LINE_SEGMENT_WITH', 'CROSSED_BY_THE_OUTLINE_OF', 'HAVE_THEIR_CENTER_IN', 'CLOSEST', 'CLOSEST_GEODESIC', ]

        param6 = arcpy.Parameter(
            name = 'param6',
            displayName = 'Search Radius',
            datatype = 'GPLinearUnit',
            parameterType = 'Required',
            direction = 'Input'
        )

        params = [param0, param1, param2, param3, param4, param5, param6]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        target_features = parameters[0].valueAsText
        target_sql = parameters[1].valueAsText
        join_features = parameters[2].valueAsText
        target_sql = parameters[3].valueAsText
        field_mapping = parameters[4].valueAsText
        match_option = parameters[5].valueAsText
        search_radius = parameters[6].valueAsText

        