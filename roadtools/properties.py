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
    bpy.types.Scene.roadtools_properties = PointerProperty(type=ROADTools_Properties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
    del bpy.types.Scene.roadtools_properties

