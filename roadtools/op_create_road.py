#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# op_create_road.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# create a road in high or low res
# High res means using the point-by-point template, low res
# uses an array modifier and curve one to create a low poly road
# 
# ############################################################################
import bpy
import math

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

import bl_road_utils

class ROADTOOLS_OT_CreateRoad(Operator):
    bl_idname = 'roadtools.create_road'
    bl_description = "create a road in high or low res"
    bl_label = 'Create Road'

    def execute(self, context):
        scene = context.scene
        roadtools = scene.roadtools

        #
        # get the types, check they are fine
        #
        if not roadtools.road_curve:
            self.report({'ERROR'}, 'Invalid Input Data. Road should be a CURVE')
            return {"FINISHED"}

        ret, msg, obj = bl_road_utils.create_road(
                roadtools.road_curve.name, 
                roadtools.road_width, 
                roadtools.road_height,
                roadtools.gpx_length, 
                hires=roadtools.road_hires
            )

        # to the thing here
        level = 'INFO'
        if not ret: level = 'ERROR'
        self.report({level}, 'RoadTools: Create Road: %s' % msg)
        return {"FINISHED"}

# ------------------------------------------------------------------------
# register / unregister
# ------------------------------------------------------------------------

classes = (
    ROADTOOLS_OT_CreateRoad,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

   