bl_info = {
    "name": "Road Tools",
    "description": "Road Tools Helpers",
    "author": "Juan M. Casillas",
    "version": (0, 0, 3),
    "blender": (2, 80, 0),
    "location": "3D View > UI",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}

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

class ROAD_Properties(PropertyGroup):

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
# sample operator 
# See the ROADTOOLS_OT_MatchTerrain convention, to roadtools.match_terrain Function.
# the name MUST BE follow allways this convention
# ------------------------------------------------------------------------

class ROADTOOLS_OT_MatchTerrain(Operator):
    bl_idname = 'roadtools.match_terrain'
    bl_description = "Matches a CURVE road with a MESH terrain, set the origin to WORLD_ORIGIN"
    bl_label = 'Add Cube'

    def execute(self, context):
        scene = context.scene
        road_properties = scene.road_properties

        #
        # get the types, check they are fine
        #
        if not road_properties.terrain_mesh or not road_properties.road_curve \
           or road_properties.terrain_mesh.type != 'MESH' or road_properties.road_curve.type != 'CURVE':
            self.report({'ERROR'}, 'Invalid Input Data. Terrain should be a MESH, Road should be a CURVE')
            return {"FINISHED"}

        # to the thing here
        self.report({'INFO'}, 'Matching Terrain')
        return {"FINISHED"}


# ------------------------------------------------------------------------
# first panel. Select the terrain and gpx and calculate the thing, 
# pressing the button
# ------------------------------------------------------------------------

class OBJECT_PT_Panel_Terrain(bpy.types.Panel):
    bl_idname = "OBJECT_PT_Panel_Terrain"
    bl_label = "Match Terrain & GPX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Road"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        col = layout.column()
        road_properties = scene.road_properties

        col.prop_search(road_properties, "terrain_mesh", context.scene, "objects", text="Terrain",icon="MESH_GRID")
        col.prop_search(road_properties, "road_curve", context.scene, "objects", text="Road Curve", icon="CURVE_PATH")
        self.layout.operator("roadtools.match_terrain", icon='SCRIPT', text="Match Terrain Road")


# ------------------------------------------------------------------------
# second panel. Select the terrain and gpx and calculate the thing, 
# pressing the button
# ------------------------------------------------------------------------

class OBJECT_PT_Panel_Road(bpy.types.Panel):
    bl_idname = "OBJECT_PT_Panel_Road"
    bl_label = "Road Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Road"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        col = layout.column()
        self.layout.operator("wm.match_terrain", icon='MESH_CUBE', text="Add Cube x")


# ------------------------------------------------------------------------
# setup zone to register the classes, addons, etc
# ------------------------------------------------------------------------

classes = (
    ROAD_Properties,
    ROADTOOLS_OT_MatchTerrain,
    OBJECT_PT_Panel_Terrain,
    OBJECT_PT_Panel_Road
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    # custom properties
    bpy.types.Scene.road_properties = PointerProperty(type=ROAD_Properties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    
    del bpy.types.Scene.road_tools

if __name__ == "__main__" :
    register()
    