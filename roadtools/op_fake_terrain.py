#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# op_fake_terrain.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# operator for blender to create a fake (synthetic) terrain at 0 elevation, 
# to do your our custom tracks
# 
# TODO:
#    * set the elevation (height) from variable, instead of hardcoding it
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
from bl_fake_terrain import BL_FAKETERRAIN

class ROADTOOLS_OT_Fake_Terrain(Operator):
    bl_idname = 'roadtools.fake_terrain'
    bl_description = "Calculate a new bounding box based on coords loaded"
    bl_label = 'Extend Bounding Box'

    def execute(self, context):
        scene = context.scene
        roadtools = scene.roadtools

        #
        # get the types, check they are fine
        #



        a = BL_FAKETERRAIN(roadtools.maxLat, roadtools.minLon, roadtools.maxLon, roadtools.minLat)
        ret, msg, obj = a.create('Terrain',  roadtools.top, roadtools.left, roadtools.right, roadtools.bottom)       

        scene.roadtools.maxLat =  a.BB.top
        scene.roadtools.minLon =  a.BB.left
        scene.roadtools.maxLon =  a.BB.right
        scene.roadtools.minLat =  a.BB.bottom
        scene.roadtools.terrain_mesh = obj

        if roadtools.satellite:
            print("getting satellite images")
            bpy.context.scene.blender_osm.terrainObject = obj.name
            bpy.context.scene.blender_osm.maxLat = scene.roadtools.maxLat
            bpy.context.scene.blender_osm.minLon = scene.roadtools.minLon
            bpy.context.scene.blender_osm.maxLon = scene.roadtools.maxLon
            bpy.context.scene.blender_osm.minLat = scene.roadtools.minLat
            # download the satellite texture
            # see here https://github.com/vvoovv/blender-osm/wiki/Documentation#custom-url
            # get the satellite texture from google
            bpy.context.scene.blender_osm.dataType = 'overlay'
            bpy.context.scene.blender_osm.overlayType = 'custom'
            bpy.context.scene.blender_osm.overlayUrl = "http://mt.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
            bpy.ops.blender_osm.import_data()   

            
        # get the value and set my pointer to the terrain



        level = 'INFO'
        msg = "new size: %3.2f width (m) x %3.2f height(m) " % (a.BB.width, a.BB.height)
        self.report({level}, 'RoadTools: Extend terrain: %s' % msg)
        return {"FINISHED"}

# ------------------------------------------------------------------------
# register / unregister
# ------------------------------------------------------------------------

classes = (
    ROADTOOLS_OT_Fake_Terrain,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

   