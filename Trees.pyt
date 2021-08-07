# -*- coding: utf-8 -*-

import arcpy
import datetime


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Trees"
        self.alias = "Trees"

        # List of tool classes associated with this toolbox
        self.tools = [YearlyTreeSiteMigration, StumpSiteMigration]


class YearlyTreeSiteMigration(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Yearly Tree Site Migration"
        self.description = "Tool to perform the yearly tree site migration where the current year's completed planting sites migrate into aftercare sites and the oldest aftercare sites FY migrate to TreeKeeper"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        input_planting_sites = arcpy.Parameter(
            name = 'input_planting_sites',
            displayName = 'Planting Sites',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input')
        
        input_aftercare_sites = arcpy.Parameter(
            name = 'input_aftercare_sites',
            displayName = 'Aftercare Sites',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input')
        
        default_in_fiscal_year = int(datetime.datetime.now().year)
        default_out_fiscal_year = default_in_fiscal_year - 2
        
        in_fiscal_year = arcpy.Parameter(
            name = 'in_fiscal_year',
            displayName = 'Fiscal Year',
            datatype = 'GPLong',
            parameterType = 'Required',
            direction = 'Input')
        in_fiscal_year.value = default_in_fiscal_year
        
        out_fiscal_year = arcpy.Parameter(
            name = 'out_fiscal_year',
            displayName = 'Out Fiscal Year',
            datatype = 'GPLong',
            parameterType = 'Required',
            direction = 'Input')
        out_fiscal_year.value = default_out_fiscal_year
        
        treekeeper_folder = arcpy.Parameter(
            name = 'treekeeper_folder',
            displayName = 'TreeKeeper Output Folder',
            datatype = 'DEFolder',
            parameterType = 'Required',
            direction = 'Input')
        
        params = [input_planting_sites, input_aftercare_sites, in_fiscal_year, out_fiscal_year, treekeeper_folder]
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
        input_planting_sites = parameters[0].valueAsText
        input_aftercare_sites = parameters[1].valueAsText
        in_fiscal_year = parameters[2].value
        out_fiscal_year = parameters[3].value
        treekeeper_folder = parameters[4].valueAsText
        
        in_fiscal_year_str = str(in_fiscal_year) + 'FY'
        out_fiscal_year_str = str(out_fiscal_year) + 'FY'

        # selects the migrating planting sites to append and delete
        fiscal_year_field = arcpy.AddFieldDelimiters(input_planting_sites, 'FISCAL_YEAR')
        arcpy.SelectLayerByAttribute_management(input_planting_sites, 'NEW_SELECTION', f'{fiscal_year_field} = "{in_fiscal_year_str}"')
        
        arcpy.Append_management(inputs=[input_planting_sites], target=input_aftercare_sites)

        arcpy.DeleteFeatures_management(input_planting_sites)

        # selects the outgoing aftercare sites to export and delete
        fiscal_year_field = arcpy.AddFieldDelimiters(input_aftercare_sites, 'FISCAL_YEAR')
        arcpy.SelectLayerByAttribute_management(input_aftercare_sites, 'NEW_SELECTION', f'{fiscal_year_field} = "{out_fiscal_year_str}"')

        arcpy.MakeFeatureLayer_management(input_aftercare_sites, 'output_aftercare_sites')

        arcpy.DeleteFeatures_management(input_aftercare_sites)

        arcpy.AddFields_management('output_aftercare_sites', [['X', 'DOUBLE', None, None, None, None], ['Y', 'DOUBLE', None, None, None, None]])

        arcpy.CalculateGeometryAttributes_management('output_aftercare_sites', [['X', 'POINT_X'], ['Y', 'POINT_Y']], coordinate_format='DD')

        arcpy.TableToExcel('output_aftercare_sites', treekeeper_folder + '/Aftercare Sites for TreeKeeper - ' + str(out_fiscal_year) + 'FY')


class StumpSiteMigration(object):
    
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Stump Site Migration"
        self.description = "Tool to perform the quarterly stump site migration where TreeKeeper stump sites are migrated into the Stump Sites layer"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        input_stump_sites = arcpy.Parameter(
            name = 'input_stump_sites',
            displayName = 'Stump Sites',
            datatype = 'GPFeatureLayer',
            parameterType = 'Required',
            direction = 'Input')
        
        input_treekeeper = arcpy.Parameter(
            name = 'input_treekeeper',
            displayName = 'TreeKeeper Shapefile',
            datatype = 'DEShapefile',
            parameterType = 'Required',
            direction = 'Input')
        
        params = [input_stump_sites, input_treekeeper]
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
        input_stump_sites = parameters[0].valueAsText
        input_treekeeper = parameters[1].valueAsText

        fms = arcpy.FieldMappings()

        fm_parkname = arcpy.FieldMap()
        fm_parkname.addInputField(input_treekeeper, 'FLAT_GEOG4')
        park_name = fm_parkname.outputField
        park_name.name = 'PARK_NAME'
        fm_parkname.outputField = park_name
        fms.addFieldMap(fm_parkname)

        fm_date = arcpy.FieldMap()
        fm_date.addInputField(input_treekeeper, 'INSPECT_DT')
        date_ = fm_date.outputField
        date_.name = 'DATE_'
        fm_date.outputField = date_
        fms.addFieldMap(fm_date)

        fm_notes = arcpy.FieldMap()
        fm_notes.addInputField(input_treekeeper, 'NOTES')
        notes = fm_notes.outputField
        notes.name = 'NOTES'
        fm_notes.outputField = notes
        fms.addFieldMap(fm_notes)

        arcpy.FeatureClassToFeatureClass_conversion(
            in_features=input_treekeeper,
            out_path=r'memory/',
            out_name='stumps',
            where_clause="SPP = 'Stump'",
            field_mapping=fms)

        arcpy.CalculateField_management(in_table=r'memory/stumps',
            field='STATUS',
            expression="'Stump to Grind'",
            expression_type='PYTHON3',
            field_type='TEXT')

        arcpy.Append_management(
            inputs=r'memory/stumps',
            target=input_stump_sites,
            schema_type='NO_TEST')

        arcpy.Delete_management(input_treekeeper)