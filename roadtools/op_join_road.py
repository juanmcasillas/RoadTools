#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# op_join_road.py
# 04/14/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# join the road with the terrain, using the Knife Project and some tools
#
# ############################################################################

import bpy

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
import bl_join_road

class ROADTOOLS_OT_JoinRoad(Operator):
    bl_idname = 'roadtools.join_road'
    bl_description = "Join the road plane with the terrain, moving the terrain next to the road"
    bl_label = 'Join Road to Terrain'

    def execute(self, context):
        scene = context.scene
        roadtools = scene.roadtools

        #
        # get the types, check they are fine
        #
        if not roadtools.terrain_mesh or not roadtools.road_plane:
            self.report({'ERROR'}, 'Invalid Input Data. Terrain should be a MESH, Road should be a MESH')
            return {"FINISHED"}

        # do some tests here to match errors, or so
        tool = bl_join_road.BL_JOINER(roadtools.road_plane.name, roadtools.terrain_mesh.name)
        tool.do_the_cut()

        ret = True
        msg = "Done"
        level = 'INFO'
        if not ret: level = 'ERROR'
        self.report({level}, 'RoadTools: Join Road: %s' % msg)
        return {"FINISHED"}

# ------------------------------------------------------------------------
# register / unregister
# ------------------------------------------------------------------------

classes = (
    ROADTOOLS_OT_JoinRoad,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

