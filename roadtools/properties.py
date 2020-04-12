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

