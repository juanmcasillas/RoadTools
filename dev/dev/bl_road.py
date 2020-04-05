import bpy, mathutils
from mathutils import Vector
import copy

#
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
    #

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
    
    
create_road_from_gpx("myroad",6)




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

