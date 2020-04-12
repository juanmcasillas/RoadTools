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

class ROADTOOLS_OT_Download_Terrain(Operator):
    bl_idname = 'roadtools.download_terrain'
    bl_description = "Download terrain using OSM"
    bl_label = 'Download Terrain'

    def execute(self, context):
        scene = context.scene
        roadtools = scene.roadtools

        #
        # get the types, check they are fine
        #

        terrain_type = 'terrain'
        bpy.context.scene.blender_osm.dataType = terrain_type
        bpy.context.scene.blender_osm.maxLat = roadtools.maxLat
        bpy.context.scene.blender_osm.minLon = roadtools.minLon
        bpy.context.scene.blender_osm.maxLon = roadtools.maxLon
        bpy.context.scene.blender_osm.minLat = roadtools.minLat
        bpy.ops.blender_osm.import_data()        

        level = 'INFO'
        msg = "Terrain Downloaded type='%s'" % terrain_type
        self.report({level}, 'RoadTools: Download Terrain: %s' % msg)
        return {"FINISHED"}

# ------------------------------------------------------------------------
# register / unregister
# ------------------------------------------------------------------------

classes = (
    ROADTOOLS_OT_Download_Terrain,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

   