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

        # make Feature Layer of the layer where the FACILITY_C is NULL
        arcpy.MakeFeatureLayer_management(
            in_features=input_pipes,
            out_layer='Layer_FacCodeNull',
            where_clause='FACILITY_C IS NULL')
        
        if int(arcpy.GetCount_management(in_rows='Layer_FacCodeNull')[0]) > 0:
            
            # make Feature Layer of the Parks Layer with requisite query
            arcpy.MakeFeatureLayer_management(
                in_features=param3,
                out_layer='Parks_Layer',
                where_clause="FACILITY_C IS NOT NULL AND STATUS = 'Existing'")

            # spatial join Parks Layer to the Feature Class copy of the layer to re-add the PARK_NAME and FACILITY_C fields
            arcpy.SpatialJoin_analysis(
                target_features=r'Layer_FacCodeNull',
                join_features=r'Parks_Layer',
                out_feature_class=r'memory\FC_Parks_SpatialJoin',
                field_mapping=r'PARK_NAME_1 "PARK_NAME" true true false 80 Text 0 0,First,#,GIS1.all_parks,PARK_NAME,0,80;FACILITY_C_1 "FACILITY_C" true true false 3 Text 0 0,First,#,GIS1.all_parks,FACILITY_C,0,3',
                match_option='CLOSEST')
            
            # # create nested dictionary of objectid and fields' key/value pairs from spatial join result
            search_dict = dict()
            with arcpy.da.SearchCursor(
                in_table=r'memory\FC_Parks_SpatialJoin',
                field_names=['TARGET_FID', 'PARK_NAME_1', 'FACILITY_C_1']) as cursor:
                        
                for row in cursor:
                    target_fid = row[0]
                    park_name = row[1]
                    facility_c = row[2]

                    search_dict[target_fid] = {'PARK_NAME': park_name, 'FACILITY_C': facility_c}

            # delete the Feature Class copy of the layer from memory
            arcpy.Delete_management(
                in_data=r'memory\FC_Parks_SpatialJoin')
            
            # update null data from dictionary
            with arcpy.da.UpdateCursor(
                in_table='Layer_FacCodeNull',
                field_names=['OBJECTID', 'PARK_NAME', 'FACILITY_C']) as cursor:
                
                for row in cursor:
                    object_id = row[0]
                        
                    row[1] = search_dict[object_id]['PARK_NAME']
                    row[2] = search_dict[object_id]['FACILITY_C']
                    cursor.updateRow(row)
        
        # delete the feature layer from memory
        arcpy.Delete_management(
            in_data='Layer_FacCodeNull')
        
        # make Feature Layer of the layer where the WATERSHED is NULL
        arcpy.MakeFeatureLayer_management(
            in_features=input_pipes,
            out_layer='Layer_WatershedNull',
            where_clause='WATERSHED IS NULL')
        
        if int(arcpy.GetCount_management(in_rows='Layer_WatershedNull')[0]) > 0:
            
            # spatial join Parks Layer to the Feature Class copy of the layer to re-add the WATERSHED field
            arcpy.SpatialJoin_analysis(
                target_features='Layer_WatershedNull',
                join_features=input_watersheds,
                out_feature_class=r'memory\FC_Watershed_SpatialJoin',
                field_mapping='MD12DIG_N "MD12DIG NAME" true true false 60 Text 0 0,First,#,https://mcatlas.org/arcgis3/rest/services/overlays/Watersheds/FeatureServer/3,MD12DIG_N,0,60',
                match_option='CLOSEST')

            # create dictionary of objectid and watershed key/value pairs from spatial join result
            search_dict = dict()
            with arcpy.da.SearchCursor(
                in_table=r'memory\FC_Watershed_SpatialJoin',
                field_names=['TARGET_FID', 'MD12DIG_N']) as cursor:
                        
                for row in cursor:
                    target_fid = row[0]
                    watershed = row[1]

                    search_dict[target_fid] = watershed
            
            # delete the spatial join result from memory
            arcpy.Delete_management(
                in_data=r'memory\FC_Watershed_SpatialJoin')
            
            # update null data from dictionary
            with arcpy.da.UpdateCursor(
                in_table='Layer_WatershedNull',
                field_names=['OBJECTID', 'WATERSHED']) as cursor:
                for row in cursor:
                    object_id = row[0]
                        
                    row[1] = search_dict[object_id]
                    cursor.updateRow(row)

        # delete the feature layer from memory
        arcpy.Delete_management(
            in_data='Layer_WatershedNull')
        
        # make Feature Layer of the entire layer
        layer = 'Layer'
        arcpy.MakeFeatureLayer_management(
            in_features=input_pipes,
            out_layer=layer)
        
        parkID_dict = dict()

        # iterate through rows of layer of not NULL PARK_ID features to create dictionary of PARK_IDs
        with arcpy.da.SearchCursor(
            in_table=layer,
            field_names=['PARK_ID'],
            where_clause='PARK_ID IS NOT NULL') as cursor:
            
            for row in cursor:
                parkID = row[0]
                fac_code, ID = parkID[:3], parkID[4:]
                if fac_code in parkID_dict:
                    ID_list = parkID_dict[fac_code]
                    ID_list.append(int(ID))
                    parkID_dict[fac_code] = ID_list
                else:
                    parkID_dict[fac_code] = [int(ID)]
        
        # iterate through rows of layer of NULL PARK_ID features to populate PARK_IDs
        with arcpy.da.UpdateCursor(
            in_table=layer,
            field_names=['PARK_ID', 'FACILITY_C'],
            where_clause='PARK_ID IS NULL',
            sql_clause=(None, "ORDER BY DATE_CREATED ASC")) as cursor:
            
            for row in cursor:
                fac_code = row[1]
                if fac_code in parkID_dict:
                    ID_list = parkID_dict[fac_code]
                    ID = max(ID_list) + 1
                    ID_list.append(ID)
                    if ID >= 100:
                        ID_str = str(ID)
                    elif ID >= 10:
                        ID_str = '0' + str(ID)
                    else:
                        ID_str = '00' + str(ID)
                    row[0] = fac_code + 'L' + ID_str
                else:
                    row[0] = fac_code + 'L001'
                    parkID_dict[fac_code] = [1]
                cursor.updateRow(row)