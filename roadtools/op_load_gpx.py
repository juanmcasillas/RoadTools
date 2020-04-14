#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# op_load_gpx.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# operator for blender to invoke or load_gpx function, smooth it, calculate
# the bounding box, and create the curve in blender. 
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
# ------------------------------------------------------------------------
# load_gpx
# See the ROADTOOLS_OT_MatchTerrain convention, to roadtools.match_terrain Function.
# the name MUST BE follow allways this convention
# ------------------------------------------------------------------------

class ROADTOOLS_OT_Load_Gpx(Operator):
    bl_idname = 'roadtools.load_gpx'
    bl_description = "Load a GPX file, smooth it, and calculates it's bounding box"
    bl_label = 'Load GPX'

    def execute(self, context):
        scene = context.scene
        roadtools = scene.roadtools

        #
        # get the types, check they are fine
        #
        if not roadtools.gpx_file:
            self.report({'ERROR'}, "GPX file must be not empty")
            return {"FINISHED"}
            

        if not os.path.exists(roadtools.gpx_file):
            self.report({'ERROR'}, "GPX file doesn't exists")
            return {"FINISHED"}

        level = 'INFO'
        gpx = BL_IMPORT_GPX()
        try:
            ret, msg, obj, length = gpx.import_gpx(roadtools.gpx_file,
                                height_offset=roadtools.gpx_altitude_offset,
                                optimize=roadtools.gpx_optimize)
            #a.bounding_box.expand(1000,500,500,1000)
            #print(a.bounding_box)
            scene.roadtools.maxLat =  gpx.bounding_box.top
            scene.roadtools.minLon =  gpx.bounding_box.left
            scene.roadtools.maxLon =  gpx.bounding_box.right
            scene.roadtools.minLat =  gpx.bounding_box.bottom
            scene.roadtools.road_curve = obj
            scene.roadtools.gpx_length = length

        except Exception as e:
            level = 'ERROR'
            msg = str(e)

        self.report({level}, 'RoadTools: Load GPX: %s' % msg)
        return {"FINISHED"}

# ------------------------------------------------------------------------
# register / unregister
# ------------------------------------------------------------------------

classes = (
    ROADTOOLS_OT_Load_Gpx,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

   