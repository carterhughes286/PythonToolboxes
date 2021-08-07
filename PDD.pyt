# -*- coding: utf-8 -*-

import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "PDD"
        self.alias = "PDD"

        # List of tool classes associated with this toolbox
        self.tools = [StormDrainPipes_FieldCompletion, StormDrainStructures_FieldCompletion]


class StormDrainPipes_FieldCompletion(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Storm Drain Pipes - Fields Completion"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        default_input_pipes = r'https://services1.arcgis.com/HbzrdBZjOwNHp70P/arcgis/rest/services/NPDES_Storm_Drain_Intern_Edits_2019/FeatureServer/0'
        input_pipes = arcpy.Parameter(
            name = 'input_pipes',
            displayName = 'Storm Drain Pipes Layer',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input')
        input_pipes.value = default_input_pipes

        default_input_parks = r'Q:\Layer Files\GIS Database3.sde\GIS1.parks\GIS1.all_parks'
        input_parks = arcpy.Parameter(
            name = 'input_parks',
            displayName = 'Parks Feature Class',
            datatype = 'DEFeatureClass',
            parameterType = 'Required',
            direction = 'Input')
        input_parks.value = default_input_parks

        default_input_watersheds = r'https://mcatlas.org/arcgis3/rest/services/overlays/Watersheds/FeatureServer/3'
        input_watersheds = arcpy.Parameter(
            name = 'input_watersheds',
            displayName = '12-Digit Watershed Layer',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input')
        input_watersheds.value = default_input_watersheds

        params = [input_pipes, input_parks, input_watersheds]
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
        input_pipes = parameters[0].valueAsText
        input_parks = parameters[1].valueAsText
        input_watersheds = parameters[2].valueAsText

        # make Feature Layer of the layer where the FACILITY_C is NULL
        arcpy.MakeFeatureLayer_management(
            in_features=input_pipes,
            out_layer='Layer_FacCodeNull',
            where_clause='FACILITY_C IS NULL')
        
        if int(arcpy.GetCount_management(in_rows='Layer_FacCodeNull')[0]) > 0:
            
            # make Feature Layer of the Parks Layer with requisite query
            arcpy.MakeFeatureLayer_management(
                in_features=input_parks,
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

class StormDrainStructures_FieldCompletion(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Storm Drain Structures - Fields Completion"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        default_input_structures = r'https://services1.arcgis.com/HbzrdBZjOwNHp70P/arcgis/rest/services/NPDES_Storm_Drain_Intern_Edits_2019/FeatureServer/1'
        input_structures = arcpy.Parameter(
            name = 'input_structures',
            displayName = 'Storm Drain Structures Layer',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input')
        input_structures.value = default_input_structures

        default_input_parks = r'Q:\Layer Files\GIS Database3.sde\GIS1.parks\GIS1.all_parks'
        input_parks = arcpy.Parameter(
            name = 'input_parks',
            displayName = 'Parks Feature Class',
            datatype = 'DEFeatureClass',
            parameterType = 'Required',
            direction = 'Input')
        input_parks.value = default_input_parks

        default_input_watersheds = r'https://mcatlas.org/arcgis3/rest/services/overlays/Watersheds/FeatureServer/3'
        input_watersheds = arcpy.Parameter(
            name = 'input_watersheds',
            displayName = '12-Digit Watershed Layer',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input')
        input_watersheds.value = default_input_watersheds

        params = [input_structures, input_parks, input_watersheds]
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
        input_structures = parameters[0].valueAsText
        input_parks = parameters[1].valueAsText
        input_watersheds = parameters[2].valueAsText

        # make Feature Layer of the layer where the FACILITY_C is NULL
        arcpy.MakeFeatureLayer_management(
            in_features=input_structures,
            out_layer='Layer_FacCodeNull',
            where_clause='FACILITY_C IS NULL')
        
        if int(arcpy.GetCount_management(in_rows='Layer_FacCodeNull')[0]) > 0:
            
            # make Feature Layer of the Parks Layer with requisite query
            arcpy.MakeFeatureLayer_management(
                in_features=input_parks,
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
            in_features=input_structures,
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
            in_features=input_structures,
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
                    row[0] = fac_code + 'P' + ID_str
                else:
                    row[0] = fac_code + 'P001'
                    parkID_dict[fac_code] = [1]
                cursor.updateRow(row)