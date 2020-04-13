#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# ui.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# RoadTools UI (user interface, panels) definitions
# 
# ############################################################################

import bpy

_isBlender280 = bpy.app.version[1] >= 80
#addon_name = __name__ # when single file
addon_name = __package__ # when a file in package

# ------------------------------------------------------------------------
# GPX Panel. Select the GPX file, smooth it and calculate the 
# bounding box for the terrain
# ------------------------------------------------------------------------

class OBJECT_PT_Panel_LoadGPX(bpy.types.Panel):
    bl_idname = "OBJECT_PT_Panel_LoadGPX"
    bl_label = "Load GPX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoadTools"

    # panel in object mode
    @classmethod
    def poll(self,context):
        return context.mode == 'OBJECT'


    def draw(self, context):
        scene = context.scene
        layout = self.layout
        col = layout.column()
        roadtools = scene.roadtools

        col.prop(roadtools, "gpx_file", text="File GPX",icon="MESH_GRID")
        self.layout.operator("roadtools.load_gpx", icon='SCRIPT', text="Load GPX")


# ------------------------------------------------------------------------
# Terrain Loading. Select the terrain bounding box, and set the optional
# extender in meters. Configure if you want to download satellite image
# from google, or if you prefer create a fake terrain (flat)
# ------------------------------------------------------------------------

class OBJECT_PT_Panel_BoundingBox(bpy.types.Panel):
    bl_idname = "OBJECT_PT_Panel_BoundingBox"
    bl_label = "Set the terrain bounding box"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoadTools"

    # panel in object mode
    @classmethod
    def poll(self,context):
        return context.mode == 'OBJECT'


    def draw(self, context):
        scene = context.scene
        layout = self.layout
        roadtools = addon = scene.roadtools

        box = layout.box()
        row = box.row()
        row.alignment = "CENTER"
        row.label(text="Upper: Extend(m)")
        row = box.row(align=True)
        #extend in meters
        row = box.row(align=True)
        split = box.split(factor=0.25) if _isBlender280 else box.split(percentage=0.25)
        split.label(text="")
        ( split.split(factor=0.67) if _isBlender280 else split.split(percentage=0.67) ).prop(addon, "top")

        row = box.row(align=True)
        split = box.split(factor=0.25) if _isBlender280 else box.split(percentage=0.25)
        split.label(text="")
        ( split.split(factor=0.67) if _isBlender280 else split.split(percentage=0.67) ).prop(addon, "maxLat")

        # extend
        row = box.row()
        row.prop(addon, "left")
        row.prop(addon, "right")

        row = box.row()
        row.prop(addon, "minLon")
        row.prop(addon, "maxLon")

        split = box.split(factor=0.25) if _isBlender280 else box.split(percentage=0.25)
        split.label(text="")
        ( split.split(factor=0.67) if _isBlender280 else split.split(percentage=0.67) ).prop(addon, "minLat")

        row = box.row(align=True)
        split = box.split(factor=0.25) if _isBlender280 else box.split(percentage=0.25)
        split.label(text="")
        ( split.split(factor=0.67) if _isBlender280 else split.split(percentage=0.67) ).prop(addon, "bottom")


        box = layout.box()
        row = box.row(align=True)
        row.prop(addon,"satellite")
       
        row = box.row(align=True)
        row.operator("roadtools.expand_terrain", icon='ARROW_LEFTRIGHT', text="Expand Terrain")  
        row = box.row(align=True)        
        row.operator("roadtools.download_terrain", icon='BLANK1', text="Download Terrain") 
        row = box.row(align=True)        
        row.operator("roadtools.fake_terrain", icon='AUTO', text="Create Fake Terrain")           


# ------------------------------------------------------------------------
# Match the GPX and the terrain in the same point, and move it to the 
# (0,0,0) (world origin)
# ------------------------------------------------------------------------

class OBJECT_PT_Panel_TerrainMatch(bpy.types.Panel):
    bl_idname = "OBJECT_PT_Panel_TerrainMatch"
    bl_label = "Match Terrain & GPX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoadTools"

    # panel in object mode
    @classmethod
    def poll(self,context):
        return context.mode == 'OBJECT'


    def draw(self, context):
        scene = context.scene
        layout = self.layout
        col = layout.column()
        roadtools = scene.roadtools

        col.prop_search(roadtools, "terrain_mesh", bpy.data, "meshes", text="Terrain",icon="MESH_GRID")
        col.prop_search(roadtools, "road_curve", bpy.data, "curves", text="Road Curve", icon="FCURVE")
        self.layout.operator("roadtools.match_terrain", icon='SCRIPT', text="Match Terrain Road")



# ------------------------------------------------------------------------
# Road Panel. Creates a road using the curve provided
# ------------------------------------------------------------------------

class OBJECT_PT_Panel_CreateRoad(bpy.types.Panel):
    bl_idname = "OBJECT_PT_Panel_CreateRoad"
    bl_label = "Create a Road"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoadTools"

    # panel in object mode
    @classmethod
    def poll(self,context):
        return context.mode == 'OBJECT'

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        col = layout.column()
        roadtools = scene.roadtools

        col.prop(roadtools, "road_width", text="Road Width")
        col.prop(roadtools, "road_height",text="Road Height")
        col.prop(roadtools, "gpx_length",text="Road Length")
        col.prop(roadtools, "road_hires", text="Road in High Res")
        col.prop_search(roadtools, "road_curve", bpy.data, "curves", text="Road Curve", icon="FCURVE")
        self.layout.operator("roadtools.create_road", icon='SCRIPT', text="Create Road")







class OBJECT_PT_Panel_TerrainFlatten(bpy.types.Panel):
    bl_idname = "OBJECT_PT_Panel_TerrainFlatten"
    bl_label = "Flatten Terrain with Plane"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoadTools"

    # panel in object mode
    @classmethod
    def poll(self,context):
        return context.mode == 'OBJECT'

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        col = layout.column()
        roadtools = scene.roadtools

        col.prop_search(roadtools, 
                    "terrain_mesh", 
                    context.scene, 
                    "objects", 
                    text="Terrain", 
                    icon="ANIM_DATA"
                )

        col.prop_search(roadtools, 
                    "road_plane", 
                    context.scene, 
                    "objects", 
                    text="Road Plane", 
                    icon="MESH_PLANE"
                )
        self.layout.operator("roadtools.flatten_terrain", icon='SCRIPT', text="Flatten Terrain Road")


# ------------------------------------------------------------------------
# register / unregister
# ------------------------------------------------------------------------

classes = (
    OBJECT_PT_Panel_LoadGPX,
    OBJECT_PT_Panel_BoundingBox,
    OBJECT_PT_Panel_TerrainMatch,
    OBJECT_PT_Panel_CreateRoad,


    OBJECT_PT_Panel_TerrainFlatten
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    
def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
