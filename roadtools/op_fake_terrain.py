import bpy
from bl_utils import BL_ROAD_UTILS
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

from bl_import_gpx import BL_IMPORTGPX
# ------------------------------------------------------------------------
# load_gpx
# See the ROADTOOLS_OT_MatchTerrain convention, to roadtools.match_terrain Function.
# the name MUST BE follow allways this convention
# ------------------------------------------------------------------------

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

        from bl_fake_terrain import BL_FAKETERRAIN

        a = BL_FAKETERRAIN(roadtools.maxLat, roadtools.minLon, roadtools.maxLon, roadtools.minLat)
        a.create('Terrain',  roadtools.top, roadtools.left, roadtools.right, roadtools.bottom)       

        scene.roadtools.maxLat =  a.BB.top
        scene.roadtools.minLon =  a.BB.left
        scene.roadtools.maxLon =  a.BB.right
        scene.roadtools.minLat =  a.BB.bottom

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

   