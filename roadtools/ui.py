import bpy

_isBlender280 = bpy.app.version[1] >= 80

# ------------------------------------------------------------------------
# first panel. Select the GPX file, smooth it and calculate the 
# bounding box for the terrain
# ------------------------------------------------------------------------

class OBJECT_PT_Panel_LoadGPX(bpy.types.Panel):
    bl_idname = "OBJECT_PT_Panel_LoadGPX"
    bl_label = "Load GPX"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoadTools"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        col = layout.column()
        roadtools = scene.roadtools

        col.prop_search(roadtools, "gpx_file", context.scene, "objects", text="File GPX",icon="MESH_GRID")
        self.layout.operator("roadtools.load_gpx", icon='SCRIPT', text="Load GPX")


# ------------------------------------------------------------------------
# first panel. Select the terrain bounding box, and set the optional
# extender in meters 
# ------------------------------------------------------------------------

class OBJECT_PT_Panel_BoundingBox(bpy.types.Panel):
    bl_idname = "OBJECT_PT_Panel_BoundingBox"
    bl_label = "Set the terrain bounding box"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "RoadTools"

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        roadtools = addon = scene.roadtools

        box = layout.box()
        row = box.row()
        row.alignment = "CENTER"
        row.label(text="Upper: Extend(m)")
        row = box.row(align=True)
        #extend in meters
        row = box.row(align=True)
        split = box.split(factor=0.25) if _isBlender280 else box.split(percentage=0.25)
        split.label(text="")
        ( split.split(factor=0.67) if _isBlender280 else split.split(percentage=0.67) ).prop(addon, "top")

        row = box.row(align=True)
        split = box.split(factor=0.25) if _isBlender280 else box.split(percentage=0.25)
        split.label(text="")
        ( split.split(factor=0.67) if _isBlender280 else split.split(percentage=0.67) ).prop(addon, "maxLat")

        # extend
        row = box.row()
        row.prop(addon, "left")
        row.prop(addon, "right")

        row = box.row()
        row.prop(addon, "minLon")
        row.prop(addon, "maxLon")

        split = box.split(factor=0.25) if _isBlender280 else box.split(percentage=0.25)
        split.label(text="")
        ( split.split(factor=0.67) if _isBlender280 else split.split(percentage=0.67) ).prop(addon, "minLat")

        row = box.row(align=True)
        split = box.split(factor=0.25) if _isBlender280 else box.split(percentage=0.25)
        split.label(text="")
        ( split.split(factor=0.67) if _isBlender280 else split.split(percentage=0.67) ).prop(addon, "bottom")


        box = layout.box()
        row = box.row(align=True)
        row.operator("roadtools.extend_terrain", icon='ARROW_LEFTRIGHT', text="Extend Terrain")  
        row = box.row(align=True)        
        row.operator("roadtools.download_terrain", icon='BLANK1', text="Download Terrain") 
        row = box.row(align=True)        
        row.operator("roadtools.fake_terrain", icon='AUTO', text="Create Fake Terrain")           





class PanelBlosmExtent(bpy.types.Panel):
    def draw(self, context):
        layout = self.layout
        addon = context.scene.blender_osm
        
        if (addon.dataType == "osm" and addon.osmSource == "server") or\
            (addon.dataType == "overlay" and not bpy.data.objects.get(addon.terrainObject)) or\
            addon.dataType == "terrain" or\
            (addon.dataType == "geojson" and addon.coordinatesAsFilter):
            box = layout.box()
            row = box.row()
            row.alignment = "CENTER"
            row.label(text="Extent:")
            row = box.row(align=True)
            row.operator("blender_osm.select_extent")
            row.operator("blender_osm.paste_extent")
            row.operator("blender_osm.extent_from_active")
            
            split = box.split(factor=0.25) if _isBlender280 else box.split(percentage=0.25)
            split.label(text="")
            ( split.split(factor=0.67) if _isBlender280 else split.split(percentage=0.67) ).prop(addon, "maxLat")
            row = box.row()
            row.prop(addon, "minLon")
            row.prop(addon, "maxLon")
            split = box.split(factor=0.25) if _isBlender280 else box.split(percentage=0.25)
            split.label(text="")
            ( split.split(factor=0.67) if _isBlender280 else split.split(percentage=0.67) ).prop(addon, "minLat")
        
        box = layout.box()
        row = box.row(align=True)
        row.prop(addon, "dataType", text="")
        row.operator("blender_osm.import_data", text="import")



# ------------------------------------------------------------------------
# Second panel. Select the terrain and gpx and calculate the thing, 
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
        roadtools = scene.roadtools

        col.prop_search(roadtools, "terrain_mesh", context.scene, "objects", text="Terrain",icon="MESH_GRID")
        col.prop_search(roadtools, "road_curve", context.scene, "objects", text="Road Curve", icon="FCURVE")
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
        roadtools = scene.roadtools

        col.prop_search(roadtools, 
                    "terrain_mesh", 
                    context.scene, 
                    "objects", 
                    text="Terrain", 
                    icon="ANIM_DATA"
                )

        col.prop_search(roadtools, 
                    "road_plane", 
                    context.scene, 
                    "objects", 
                    text="Road Plane", 
                    icon="MESH_PLANE"
                )
        self.layout.operator("roadtools.flatten_terrain", icon='SCRIPT', text="Flatten Terrain Road")

# ------------------------------------------------------------------------
# register / unregister
# ------------------------------------------------------------------------

classes = (
    OBJECT_PT_Panel_LoadGPX,
    OBJECT_PT_Panel_BoundingBox,
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
    
