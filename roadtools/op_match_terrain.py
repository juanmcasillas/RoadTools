import bpy
from bl_utils import BL_ROAD_UTILS

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
# sample operator 
# See the ROADTOOLS_OT_MatchTerrain convention, to roadtools.match_terrain Function.
# the name MUST BE follow allways this convention
# ------------------------------------------------------------------------

class ROADTOOLS_OT_MatchTerrain(Operator):
    bl_idname = 'roadtools.match_terrain'
    bl_description = "Matches a CURVE road with a MESH terrain, set the origin to WORLD_ORIGIN"
    bl_label = 'Match Terrain & Road Curve'

    def execute(self, context):
        scene = context.scene
        roadtools = scene.roadtools

        #
        # get the types, check they are fine
        #
        if not roadtools.terrain_mesh or not roadtools.road_curve \
           or roadtools.terrain_mesh.type != 'MESH' or roadtools.road_curve.type != 'CURVE':
            self.report({'ERROR'}, 'Invalid Input Data. Terrain should be a MESH, Road should be a CURVE')
            return {"FINISHED"}

        # to the thing here
        ret, msg = BL_ROAD_UTILS.set_terrain_origin(
            roadtools.road_curve.name,
            roadtools.terrain_mesh.name
        )

        level = 'INFO'
        if not ret: level = 'ERROR'
        self.report({level}, 'RoadTools: Matching Terrain: %s' % msg)
        return {"FINISHED"}

# ------------------------------------------------------------------------
# register / unregister
# ------------------------------------------------------------------------

classes = (
    ROADTOOLS_OT_MatchTerrain,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

   