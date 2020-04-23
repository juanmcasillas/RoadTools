#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# properties.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# RoadTools blender add on class properties to store values
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

# ------------------------------------------------------------------------
# Scene Properties
# put in this class all the properties related to the panels
# ------------------------------------------------------------------------

class ROADTools_Properties(PropertyGroup):

    gpx_file: StringProperty(
        name = "GPX File",
        description="Choose GPX File",
        default="",
        maxlen=4096,
        subtype='FILE_PATH' 
    )

    gpx_length: bpy.props.FloatProperty(
        name="gpx length in meters",
        description="GPX length (read from import)",
        default=0.0
    )

    gpx_altitude_offset: bpy.props.FloatProperty(
        name="gpx altitude offset",
        description="GPX altitude offset to apply on import",
        default=0.0
    )

    gpx_xy_offset: bpy.props.FloatProperty(
        name="gpx XY offset",
        description="GPX XY offset to apply on import",
        default=0.0
    )

    gpx_optimize: bpy.props.BoolProperty(
        name="Use the point optimizator",
        description="If true, use point optimizator. Else read original points",
        default=True
    )

    gpx_ortometric: bpy.props.BoolProperty(
        name="Calculate ortometric value",
        description="If true, the geoid value to calculate ortometric value",
        default=True
    )

    # the bounding box
    
    minLat: bpy.props.FloatProperty(
        name="min lat (bottom)",
        description="Minimum latitude of the imported extent",
        precision = 4,
        min = -89.,
        max = 89.,
        default=40.309865
    )

    maxLat: bpy.props.FloatProperty(
        name="max lat (top)",
        description="Maximum latitude of the imported extent",
        precision = 4,
        min = -89.,
        max = 89.,
        default=40.326585
    )

    minLon: bpy.props.FloatProperty(
        name="min lon (left)",
        description="Minimum longitude of the imported extent",
        precision = 4,
        min = -180.,
        max = 180.,
        default=-4.577988
    )

    maxLon: bpy.props.FloatProperty(
        name="max lon (right)",
        description="Maximum longitude of the imported extent",
        precision = 4,
        min = -180.,
        max = 180.,
        default= -4.516253
    )

    ## the extend
    bottom: bpy.props.FloatProperty(
        name="extend bottom",
        description="extend minimum latitude (m)",
        precision = 4,
        min = 0.,
        max = 99999999.,
        default=500
    )

    top: bpy.props.FloatProperty(
        name="extend top",
        description="extend maximum latitude (m)",
        precision = 4,
        min = 0.,
        max = 99999999.,
        default=500
    )

    left: bpy.props.FloatProperty(
        name="extend left",
        description="extend maximum longitude (m)",
        precision = 4,
        min = 0.,
        max = 99999999.,
        default=500
    )

    right: bpy.props.FloatProperty(
        name="extend right",
        description="extend minimum longitude (m)",
        precision = 4,
        min = 0.,
        max = 99999999.,
        default=500
    )

    satellite: bpy.props.BoolProperty(
        name="Download Satellite terrain",
        description="If true, donwload satellite texture",
        default=False
    )

    road_hires: bpy.props.BoolProperty(
        name="Generate a road in high resolution",
        description="If true, generate a road in high resolution",
        default=False
    )

    road_width: bpy.props.FloatProperty(
        name="road width, in meters (segment)",
        description="road width (m)",
        precision = 2,
        min = 0.,
        max = 100.,
        default=6
    )
    
    road_height: bpy.props.FloatProperty(
        name="road height, in meters (segment)",
        description="road height (m)",
        precision = 2,
        min = 0.,
        max = 100.,
        default=4
    )


    terrain_mesh: PointerProperty(
        type=bpy.types.Object,
        name="terrain_mesh",
        description="Select a MESH with the terrain"
    )
    road_curve: PointerProperty(
        type=bpy.types.Object,
        name="road_curve",
        description="Select a CURVE with the road"
    )              

    road_plane: PointerProperty(
        type=bpy.types.Object,
        name="road_plane",
        description="Select a PLANE (apply array)"
    )           

# ------------------------------------------------------------------------
# register / unregister
# ------------------------------------------------------------------------

classes = (
    ROADTools_Properties,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    # custom properties
    bpy.types.Scene.roadtools = PointerProperty(type=ROADTools_Properties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
    del bpy.types.Scene.roadtools

