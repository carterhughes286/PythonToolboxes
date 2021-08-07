# -*- coding: utf-8 -*-

import arcpy
import pandas as pd
from arcgis.features import GeoAccessor as GA
import numpy as np
import os

class clsField(object):
    """ Class to hold properties and behavior of the output fields """

    @property
    def alias(self):
        return self._field.aliasName

    @property
    def name(self):
        return self._field.name

    @property
    def domain(self):
        return self._field.domain

    @property
    def type(self):
        return self._field.type

    @property
    def length(self):
        return self._field.length

    def __init__(self, f, i, subtypes, cvdomains):
        """ Create the object from a describe field object """
        self._field = f
        self.subtype_field = ''
        self.domain_desc = {}
        self.subtype_desc = {}
        self.index = i

        # Get coded value domain info from field
        if f.domain:
            for cvd in cvdomains:
                if cvd.name == f.domain:
                    self.domain_desc = {0: cvd.codedValues}

        # Get coded value domain info from subtype
        for st_key in subtypes.keys():
            st_val = subtypes[st_key]
            if st_val['SubtypeField'] == f.name:
                self.subtype_desc[st_key] = st_val['Name']
                self.subtype_field = f.name
            for k in st_val['FieldValues'].keys():
                v = st_val['FieldValues'][k]
                if k == f.name:
                    if len(v) == 2:
                        if v[1]:
                            self.domain_desc[st_key] = v[1].codedValues
                            self.subtype_field = st_val['SubtypeField']

    def __repr__(self):
        """ Nice representation for debugging  """
        return '<clsfield object name={}, alias={}, domain_desc={}>'.format(
            self.name, self.alias, self.domain_desc)

    def updateValue(self, row, fields):
        """ Update value based on domain description """
        value = row[self.index]
        if self.subtype_field:
            subtype_val = row[fields.index(self.subtype_field)]
        else:
            subtype_val = 0

        if self.subtype_desc:
            value = self.subtype_desc[row[self.index]]

        if self.domain_desc:
            try:
                value = self.domain_desc[subtype_val][row[self.index]]
            except:
                pass  # not all subtypes will have domain

        # Return the validated value
        return value

def get_field_defs(in_table):
    """ returns nice field definition """
    desc = arcpy.Describe(in_table)

    subtypes = {}
    cvdomains = {}

    fields = []
    for i, field in enumerate([f for f in desc.fields
                               if f.type in ["Date", "Double", "Guid",
                                             "Integer", "OID", "Single",
                                             "SmallInteger", "String",
                                             "GlobalID"]]):
        fields.append(clsField(field, i, subtypes, cvdomains))

    return fields

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "EAM"
        self.alias = "EAM"

        # List of tool classes associated with this toolbox
        self.tools = [IdentifyAssetDiscrepancies, TableToUploadSheet]


class IdentifyAssetDiscrepancies(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Identify Asset Discrepancies"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        input_asset_layer = arcpy.Parameter(
            name = 'input_asset_layer',
            displayName = 'Asset Layer',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input')

        input_excel_file = arcpy.Parameter(
            name = 'input_excel_file',
            displayName = 'Asset Excel File',
            datatype = 'DEFile',
            parameterType = 'Required',
            direction = 'Input')
        output_table = arcpy.Parameter(
            name = 'output_table',
            displayName = 'Output EAM Discrepancy Table',
            datatype = 'DETable',
            parameterType = 'Required',
            direction = 'Output')

        params = [input_asset_layer, input_excel_file, output_table]
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
        
        input_asset_layer = parameters[0].valueAsText
        input_excel_file = parameters[1].valueAsText
        output_table = parameters[2].valueAsText

        eam_assets_df = pd.read_excel(input_excel_file, sheet_name='Sheet1')
        where_clause = 'ASSET IN ' + str(eam_assets_df['Category'].unique()).replace("[", "(").replace("]", ")")
        asset_layer_sdf = GA.from_featureclass(input_asset_layer, where_clause=where_clause)

        merged_df = pd.merge(asset_layer_sdf, eam_assets_df, how='outer', left_on='GISOBJID', right_on='GIS ID')

        layer_nomatch_df = merged_df[merged_df['OBJECTID'].notnull() & merged_df['Category'].isnull()]
        layer_nomatch_df= layer_nomatch_df.drop(columns=eam_assets_df.columns)

        eam_nomatch_df = merged_df[merged_df['OBJECTID'].isnull() & merged_df['Category'].notnull()]
        eam_nomatch_df = eam_nomatch_df.drop(columns=layer_nomatch_df.columns)
        eam_nomatch_df['Location'] = eam_nomatch_df['Location'].str.replace('L-MC-', '')

        suggested_matches_df = pd.merge(layer_nomatch_df, eam_nomatch_df, how='outer', left_on=['ASSET', 'FACILITY_C'], right_on=['Category', 'Location'])
        suggested_matches_df.drop(columns=['ASSET', 'GISOBJID', 'ASSET_TYPE', 'PARK_NAME', 'FACILITY_C', 'TYPE_', 'MGMT_AREA', 'MGMT_REGION', 'SHAPE'])
        suggested_matches_df['Asset'].fillna('No Suggestion', inplace=True)

        x = np.array(np.rec.fromrecords(suggested_matches_df.values))
        names = suggested_matches_df.dtypes.index.tolist()
        x.dtype.names = tuple(names)
        arcpy.da.NumPyArrayToTable(x, output_table)

        arcpy.AddJoin_management(input_asset_layer, 'OBJECTID', output_table, 'OBJECTID', 'KEEP_COMMON')

class TableToUploadSheet(object):
    
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Table to Upload Sheet"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""

        input_asset_layer = arcpy.Parameter(
            name = 'input_asset_layer',
            displayName = 'Asset Layer',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input')

        output_excel_file = arcpy.Parameter(
            name = 'input_excel_file',
            displayName = 'Output Upload Sheet',
            datatype = 'DEFile',
            parameterType = 'Required',
            direction = 'Output')

        params = [input_asset_layer, output_excel_file]
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
        
        input_asset_layer = parameters[0].valueAsText
        output_excel_file = parameters[1].valueAsText
        
        fields = get_field_defs(input_asset_layer)
        field_names = [i.name for i in fields]

        # Loop through input rows
        with arcpy.da.SearchCursor(input_asset_layer, field_names) as cursor:
            for row in cursor:
                # convert to list which allows item assignment
                rowUpdated = list(row)

                for col_index, value in enumerate(row):
                    if fields[col_index].domain_desc or fields[
                        col_index].subtype_desc:
                        value = fields[col_index].updateValue(row, field_names)

                        # update
                        rowUpdated[col_index] = value
                worksheet.append(rowUpdated)