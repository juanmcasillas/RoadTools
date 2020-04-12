import bpy
from bl_flatten import BL_FLATTEN

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

class ROADTOOLS_OT_FlattenTerrain(Operator):
    bl_idname = 'roadtools.flatten_terrain'
    bl_description = "Uses a road PLANE to flatten the terrain MESH"
    bl_label = 'Flatten terrain using a road plane'

    def execute(self, context):
        scene = context.scene
        roadtools = scene.roadtools

        #
        # get the types, check they are fine
        #
 
        if not roadtools.terrain_mesh or not roadtools.road_plane \
           or roadtools.terrain_mesh.type != 'MESH' or roadtools.road_plane.type != 'MESH':
            self.report({'ERROR'}, 'Invalid Input Data. Terrain should be a MESH, Road should be a MESH')
            return {"FINISHED"}

        ret, msg = BL_FLATTEN.flatten_terrain(
            roadtools.road_plane.name,
            roadtools.terrain_mesh.name
            )
        
        level = 'INFO'
        if not ret: level = 'ERROR'
        self.report({level}, 'RoadTools: Flatten Terrain: %s' % msg)
        return {"FINISHED"}

# ------------------------------------------------------------------------
# register / unregister
# ------------------------------------------------------------------------

classes = (
    ROADTOOLS_OT_FlattenTerrain,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

   