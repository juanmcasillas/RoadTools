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

class ROADTOOLS_OT_Extend_Terrain(Operator):
    bl_idname = 'roadtools.extend_terrain'
    bl_description = "Calculate a new bounding box based on coords loaded"
    bl_label = 'Extend Bounding Box'

    def execute(self, context):
        scene = context.scene
        roadtools = scene.roadtools

        #
        # get the types, check they are fine
        #

        from core.gpxbb import GPX_BB_bounds, GPX_BB

        bounds = GPX_BB_bounds(roadtools.maxLat, roadtools.minLon, roadtools.maxLon, roadtools.minLat)
        gpx_bb = GPX_BB( bounds )
        gpx_bb.expand( roadtools.top, roadtools.left, roadtools.right, roadtools.bottom )

        scene.roadtools.maxLat =  gpx_bb.top
        scene.roadtools.minLon =  gpx_bb.left
        scene.roadtools.maxLon =  gpx_bb.right
        scene.roadtools.minLat =  gpx_bb.bottom

        level = 'INFO'
        msg = "new size: %3.2f width (m) x %3.2f height(m) " % (gpx_bb.width, gpx_bb.height)
        self.report({level}, 'RoadTools: Extend terrain: %s' % msg)
        return {"FINISHED"}

# ------------------------------------------------------------------------
# register / unregister
# ------------------------------------------------------------------------

classes = (
    ROADTOOLS_OT_Extend_Terrain,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

   