#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# op_download_terrain.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# operator for blender to download terrain invoking the blender-osm module
# also sets the bounding box.
#
# TODO:
#    * terrain type is for now hardcoded
#    * set the terrain to the roadtools property
# 
# ############################################################################
import bpy
import os.path

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )

from bl_import_gpx import BL_IMPORT_GPX

# ---------------------------------------------------------------------------
# Note about class naming
# See the ROADTOOLS_OT_Download_Terrain convention, to 
# roadtools.download_terrain Function.
# the name MUST BE follow allways this convention
# ---------------------------------------------------------------------------

class ROADTOOLS_OT_Download_Terrain(Operator):
    bl_idname = 'roadtools.download_terrain'
    bl_description = "Download terrain using OSM"
    bl_label = 'Download Terrain'

    def execute(self, context):
        scene = context.scene
        roadtools = scene.roadtools

        #
        # get the types, check they are fine
        #

        terrain_type = 'terrain'
        bpy.context.scene.blender_osm.dataType = terrain_type
        bpy.context.scene.blender_osm.maxLat = roadtools.maxLat
        bpy.context.scene.blender_osm.minLon = roadtools.minLon
        bpy.context.scene.blender_osm.maxLon = roadtools.maxLon
        bpy.context.scene.blender_osm.minLat = roadtools.minLat
        bpy.ops.blender_osm.import_data()   


        if roadtools.satellite:
            # download the satellite texture
            # see here https://github.com/vvoovv/blender-osm/wiki/Documentation#custom-url
            # get the satellite texture from google
            bpy.context.scene.blender_osm.dataType = 'overlay'
            bpy.context.scene.blender_osm.overlayType = 'custom'
            bpy.context.scene.blender_osm.overlayUrl = "http://mt.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
            bpy.ops.blender_osm.import_data()   

        # get the value and set my pointer to the terrain
        scene.roadtools.terrain_mesh = bpy.data.objects[bpy.context.scene.blender_osm.terrainObject]
        

        
        level = 'INFO'
        msg = "Terrain Downloaded type='%s'" % terrain_type
        self.report({level}, 'RoadTools: Download Terrain: %s' % msg)
        return {"FINISHED"}

# ------------------------------------------------------------------------
# register / unregister
# ------------------------------------------------------------------------

classes = (
    ROADTOOLS_OT_Download_Terrain,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

   