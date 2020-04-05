import bpy, mathutils
from mathutils import Vector
import copy

## main code to generate road
# do some bizarre calculations, in order to create a element,
# with the current distances.
#

class RoadMesh:
    def __init__(self, name="road", width=10):
        self.width = width
        self.half_width = self.width/2.0
        self.vertex = []
        self.faces = []
        self.name = name
        
        self.mymesh = bpy.data.meshes.new(self.name)
        self.myobject = bpy.data.objects.new(self.name, self.mymesh)
        scene = bpy.context.scene
        scene.collection.objects.link(self.myobject)
        
        
        # 3D cursor location
        # we use only X,Y increments :D
        
        self.cursor = bpy.context.scene.cursor.location
        self.cursor_orig = copy.copy(bpy.context.scene.cursor.location) 
  
    
    def add_face(self, distance):
        "add a new poly at distance"
    
        
        v0 = (self.cursor.x, self.cursor.y - self.half_width, self.cursor.z) # top left
        v1 = (self.cursor.x, self.cursor.y + self.half_width, self.cursor.z) # bottom left
        v2 = (self.cursor.x + distance, self.cursor.y + self.half_width, self.cursor.z) # bottom right
        v3 = (self.cursor.x + distance, self.cursor.y - self.half_width, self.cursor.z) # top right
    
        
        if len(self.faces) == 0:
            # add four vertex, and create face
            self.vertex.extend([v0,v1,v2,v3])
            face = [(0, 3, 2, 1)]
        else:
            # we have vertex created, so only add 2
            self.vertex.extend([v2,v3])
            l = len(self.vertex)
            face = [(l-3, l-1, l-2, l-4)]
            
        self.faces.extend(face)
        
        #print(self.vertex)
        #print(self.faces)
        
        bpy.context.scene.cursor.location.x += distance
        #self.cursor = bpy.context.scene.cursor.location
        
        
    def build(self):
        self.mymesh.from_pydata(self.vertex, [], self.faces)
        self.mymesh.update(calc_edges=True)
        bpy.context.scene.cursor.location = self.cursor_orig
       
        return(self.myobject)



def create_road_from_gpx(name, width):

    ob = bpy.context.active_object
    
    if ob == None or ob.type != 'CURVE':
        print("can't get a bezier curve")
        return

    # remove Bevel
    if "gpx_bevel" in bpy.data.objects.keys():
        bpy.data.objects.remove( bpy.data.objects["gpx_bevel"] )

    # convert the spline to BEZIER and handlers to FREE_ALIGN
    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.curve.select_all()
    bpy.ops.curve.spline_type_set(type='BEZIER')
    # changing to bezier and adding free_align the resolution increases A LOT
    # we don't need so many points now
    bpy.ops.curve.handle_type_set(type='FREE_ALIGN')  # FREE_ALIGN  
    bpy.ops.curve.normals_make_consistent()

    
    # set some parameters
    #bpy.ops.curve.select_all()
    #bpy.ops.curve.subdivide()
    #bpy.ops.curve.subdivide()
    #bpy.ops.curve.subdivide()
    #bpy.ops.curve.smooth()
    
    #bpy.ops.curve.smooth()
    #bpy.ops.curve.normals_make_consistent()
    
    # save origin, move to first point, asign the origin to it
    
    cur = copy.copy(bpy.context.scene.cursor.location) 
    
    # first point
    if len(ob.data.splines.active.points) == 0:
        first_point = ob.data.splines.active.bezier_points[0].co
    else:    
        first_point = ob.data.splines.active.points[0].co
    
    
    bpy.context.scene.cursor.location = first_point.xyz
     
    # set the origin of the geometry
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
   
    ob.location = (0, 0, 0) # to the world origin, for AC
    
    # restore 3d cursor
    bpy.context.scene.cursor.location = cur.xyz
    
    
   
    road_mesh = RoadMesh(name=name, width=width)

    #
    # transform to a MESH, calculate distance.
    # put the origin on (0,0,0) or you build the road anywhere
    # 
    bpy.context.scene.cursor.location = (0,0,0)
    bpy.ops.object.convert(target='MESH', keep_original=False)
    ve = ob.data.vertices

    total_len = 0.0
        
    for i in range(len(ob.data.edges)-1):
    
        p = ob.data.edges[i]
        dd = ve[p.vertices[0]].co - ve[p.vertices[1]].co
        segment_length = dd.length
        total_len += segment_length
        road_mesh.add_face(segment_length)


    bpy.ops.object.convert(target='CURVE', keep_original=False)
    
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.transform_apply(location = True, scale = True, rotation = True)
    ob.data.resolution_u = 24
    ob.data.twist_mode = 'Z_UP'
    
    print("length in meters: %3.2f" % total_len)
    road = road_mesh.build()   
    road.modifiers.new("Curve","CURVE")
    road.modifiers['Curve'].object = ob


create_road_from_gpx("road",7)
    
#def calculate():
#    le=0.0
#    ob = bpy.context.active_object

#    if ob == None or ob.type != 'CURVE':
#        raise Exception("can't get distance")
#        

#    em = (ob.mode == 'EDIT')
#    bpy.ops.object.mode_set()
#    bpy.ops.object.convert(target='MESH', keep_original=False)
#    ve = ob.data.vertices
#    dd = le = 0
#    for i in ob.data.edges:
#        dd = ve[i.vertices[0]].co - ve[i.vertices[1]].co
#        le += dd.length
#    le = round(le,4)
#    bpy.ops.ed.undo()
#    if em: bpy.ops.object.mode_set(mode='EDIT', toggle=False)

#    print(le)



#### create the menu add in




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

    my_width: FloatProperty(
        name = "Road Width",
        description = "Road Width (m)",
        default = 7,
        min = 1,
        max = 15
        )


    my_name: StringProperty(
        name="Road Name",
        description="road name",
        default="road",
        maxlen=1024
        )
        
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
        print("Generating road")
        print("GPX FILE: ", bpy.path.abspath(mytool.my_path))
        imported_object = bpy.ops.import_scene.gpx(filepath=bpy.path.abspath(mytool.my_path))
        
        create_road_from_gpx(mytool.my_name, mytool.my_width)
        # print the values to the console
        #print("Generate Road")
        #print("string value:", mytool.my_path)
        return {'FINISHED'}



# ------------------------------------------------------------------------
#    Panel in Object Mode
# ------------------------------------------------------------------------

class OBJECT_PT_CustomPanel(Panel):
    bl_label = "Create Road"
    bl_idname = "OBJECT_PT_custom_panel"
    bl_space_type = "VIEW_3D"   
    bl_region_type = "UI"
    bl_category = "Tools"
    bl_context = "objectmode"   

    #@classmethod
    #def poll(self,context):
    #   return context.object is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        layout.prop(mytool, "my_name")
        layout.prop(mytool, "my_width")
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
    #create_road_from_gpx("myroad",6)



