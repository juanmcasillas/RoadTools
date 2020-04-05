bl_info = {
    "name": "GPX Road Creator",
    "description": "Create a road (shape) from GPX",
    "author": "Juan M. Casillas",
    "version": (0, 0, 3),
    "blender": (2, 80, 0),
    "location": "3D View > Tools",
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
#    Scene Properties
# ------------------------------------------------------------------------

class MyProperties(PropertyGroup):


    my_path: StringProperty(
        name = "GPX File",
        description="Choose GPX File",
        default="",
        maxlen=1024,
        subtype='FILE_PATH' # FILE_PATH
        )
        
   


# ------------------------------------------------------------------------
#    Operators
# ------------------------------------------------------------------------

class WM_OT_GenerateRoad(Operator):
    bl_label = "Generate Road"
    bl_idname = "wm.generate_road"

    def execute(self, context):
        scene = context.scene
        mytool = scene.my_tool
        print("string value:", mytool.my_path)
        imported_object = bpy.ops.import_scene.gpx(filepath=mytool.my_path)
        
        # print the values to the console
        print("Generate Road")
        print("string value:", mytool.my_path)
        return {'FINISHED'}



# ------------------------------------------------------------------------
#    Panel in Object Mode
# ------------------------------------------------------------------------

class OBJECT_PT_CustomPanel(Panel):
    bl_label = "My Panel"
    bl_idname = "OBJECT_PT_custom_panel"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "Tools"
    bl_context = "objectmode"   


    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        layout.prop(mytool, "my_path")
        layout.operator("wm.generate_road")
        layout.separator()

# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    MyProperties,
    WM_OT_GenerateRoad,
    OBJECT_PT_CustomPanel
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool


if __name__ == "__main__":
    register()