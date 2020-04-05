import bpy

# ------------------------------------------------------------------------
# first panel. Select the terrain and gpx and calculate the thing, 
# pressing the button
# ------------------------------------------------------------------------

class OBJECT_PT_Panel_TerrainMatch(bpy.types.Panel):
    bl_idname = "OBJECT_PT_Panel_TerrainMatch"
    bl_label = "Match Terrain & GPX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoadTools"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        col = layout.column()
        roadtools_properties = scene.roadtools_properties

        col.prop_search(roadtools_properties, "terrain_mesh", context.scene, "objects", text="Terrain",icon="MESH_GRID")
        col.prop_search(roadtools_properties, "road_curve", context.scene, "objects", text="Road Curve", icon="FCURVE")
        self.layout.operator("roadtools.match_terrain", icon='SCRIPT', text="Match Terrain Road")


# ------------------------------------------------------------------------
# second panel. Select the terrain and gpx and calculate the thing, 
# pressing the button
# TODO
# ------------------------------------------------------------------------

class OBJECT_PT_Panel_TerrainFlatten(bpy.types.Panel):
    bl_idname = "OBJECT_PT_Panel_TerrainFlatten"
    bl_label = "Flatten Terrain with Plane"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoadTools"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        col = layout.column()
        roadtools_properties = scene.roadtools_properties

        col.prop_search(roadtools_properties, "terrain_mesh", context.scene, "objects", text="Terrain",icon="MESH_GRID")
        col.prop_search(roadtools_properties, "road_plane", context.scene, "objects", text="Road Plane", icon="MESH_PLANE")
        self.layout.operator("roadtools.flatten_terrain", icon='SCRIPT', text="Flatten Terrain Road")


# ------------------------------------------------------------------------
# register / unregister
# ------------------------------------------------------------------------

classes = (
    OBJECT_PT_Panel_TerrainMatch,
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
    
