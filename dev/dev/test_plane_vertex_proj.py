import bpy
import bmesh
import sys
from mathutils import Vector


def get_verts():
    m = bpy.data.meshes['Grid']
    verts = []
    for v in m.vertices:
        if v.select: verts.append(str(v.index))

    # define my sample object

    print("verts = [")
    print(",".join(verts))
    print("]")
        
def get_faces():
    m = bpy.data.meshes['Grid']
    polygons = []
    for p in m.polygons:
        if p.select: polygons.append(str(p.index))

    # define my sample object

    print("faces = [")
    print(",".join(polygons))
    print("]")
            
def set_mark(p, kind='ARROWS', scale=None):
    "add an emtpy in p point"
    # can be also PLAIN_AXES
    o = bpy.data.objects.new( "empty", None )
    o.empty_display_type = kind
    o.location = p
    bpy.context.scene.collection.objects.link( o )    
    if scale:
        o.empty_display_size = scale

def clear_marks(what=None):
    "clear all the objects starting with what name"
    what = what or 'empty'
    for o in bpy.data.objects:
        if o.name.startswith(what):
            bpy.data.objects.remove(o)         


def get_verts_real():
    m = bpy.data.meshes['Plane']
    verts = []
    for v in m.vertices:
        verts.append(v.index)

    return(verts)    
# vertex in the center
#verts = [100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141]


verts = get_verts_real()


# sorrounding faces (to speed up)
sorround_faces = [29,30,37,38,39,40,41,42,44,45,47,48,49,50,51,52,72,74,75,76,77,80,81,82,83]

print("STARTING--------------------------------------------------------")
    
obj_s = bpy.data.objects['Plane']
obj_t = bpy.data.objects['Grid']

bm = bmesh.new()
bm.from_mesh(obj_t.data)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

for vert in bm.verts: bm.verts[vert.index].select = False
for f in sorround_faces:
    bm.faces[f].select = True
    
clear_marks()

## some calcs

#A = Vector((8.7741, 2.3201, 0.0000))
#B = Vector ((8.4202, 2.5813, -0.0000))
#C = Vector ((8.2353, -0.4844, 0.0000))
#C2 = Vector((10.022, 3.20, 0.0))

#C = Vector(( 8.23, -0.48, 0))
#A = Vector(( 0.67, 0.17,0))
#B = Vector(( 0.64, 0.19, 0))

#A = obj_t.matrix_world @ A0
#B = obj_t.matrix_world @ B0
#C = obj_t.matrix_world @ C0

#print(A,B,C)
#normal_rl = Vector(B-A) @ (Vector(C-A))
#print(normal_rl)
#raise Exception("X")


# first, project Plane verts in MESH verts, and get their mapping index.
# then work with THAT points

mesh_vertex = []
for v_idx in verts:
    world_point = obj_s.matrix_world @ obj_s.data.vertices[v_idx].co
    local_point = obj_t.matrix_world.inverted() @ world_point

    #set_mark( obj_s.matrix_world @ obj_s.data.vertices[v_idx].co, kind='PLAIN_AXES', scale=0.2 )
    #set_mark( obj_t.matrix_world @ local_point,  scale=0.2 )
    
    vnew = bm.verts.new( local_point )
    mesh_vertex.append(vnew)

# update the index of the new created verts. WTF ???
bm.verts.index_update()

LIMIT = None
bm.verts.ensure_lookup_table()

pc = 0
idx = 0
MESH_VERTEX_LEN = int(len(mesh_vertex)/2)-1
for pc in range(MESH_VERTEX_LEN):
    
    # iterate about the number of quads
    
    edges = []
    if pc == 0:
        e_1 = ( mesh_vertex[0], mesh_vertex[1] ) # right
        e_2 = ( mesh_vertex[2], mesh_vertex[3] ) # left
        idx = 1
    elif pc == 1:
         e_1 = ( mesh_vertex[1], mesh_vertex[4] )  # right     
         e_2 = ( mesh_vertex[3], mesh_vertex[5] )  # left edge
         idx += 3
    else:
         e_1 = ( mesh_vertex[idx], mesh_vertex[idx+2] )       # right 
         e_2 = ( mesh_vertex[idx+1], mesh_vertex[idx+3] )     # left edge
         idx += 2

         
    # 0 is the right side
    # 1 is the left side 
    edges = [ e_1, e_2 ]  

    #for e in edges:
    #    set_mark( obj_t.matrix_world @ e[0].co.xyz, kind='CUBE', scale=0.2 )
    #    set_mark( obj_t.matrix_world @ e[1].co.xyz, kind='SPHERE', scale=0.2 )

    
    # calculate the nearest vertex for each point, get the minimum,
    # and build a face using it
    
    class nearest:
        def __init__(self, pos):
            self.pos = 'RIGHT'
            if pos != 0: self.pos = 'LEFT'
            self.face = None
            self.vertex = None
            self.distance = sys.maxsize

        def __repr__(self):
            return "<Nearest face:%s vertex:%s distance:%5.8f pos: %s>" % (self.face, self.vertex, self.distance, self.pos)
    

    for edge_idx in range(len(edges)):
        edge =edges[edge_idx]       
        near_data = [ nearest(edge_idx), nearest(edge_idx) ] # for vertex0, vertex1. Pass the "left/right position"

        
        bm.faces.ensure_lookup_table()
        
        for i in range(len(edge)):
        
            for face_idx in sorround_faces:
                face = bm.faces[face_idx]

                # get only faces for our "side"
                A = obj_t.matrix_world @ edge[0].co
                B = obj_t.matrix_world @ edge[1].co
                C = obj_t.matrix_world @ face.calc_center_median()
                normal_vec = Vector(B-A).cross(Vector(C-A))
                normal_rl = normal_vec.z
                
                if face_idx == 41:
                    print("***", A,B,C,normal_rl)
                    
                if near_data[i].pos == 'LEFT' and normal_rl < 0:
                    #print("badside left: normal: ", normal_rl, near_data[i].pos, idx) 
                    continue
                if near_data[i].pos == 'RIGHT' and normal_rl > 0:
                    #print("badside right: normal: ", normal_rl, near_data[i].pos, idx) 
                    continue
                
                print("normal: ", normal_rl, near_data[i].pos, idx, face_idx) 

                for facevertex in face.verts:
                    vpw = obj_t.matrix_world @ edge[i].co
                    vtw = obj_t.matrix_world @ facevertex.co                     
                    dist = (vpw.xyz - vtw.xyz).length

                    if dist < near_data[i].distance:
                        near_data[i].face = face_idx
                        near_data[i].vertex = facevertex.index
                        near_data[i].distance = dist

                        # calculate the normal (first case, the we do the scond)

            
        # select what vertex is near    
        print(near_data)        
        near = 0 
        if near_data[1].distance < near_data[0].distance:
            near = 1
            
        set_mark( obj_t.matrix_world @ bm.faces[near_data[near].face].calc_center_median().xyz, scale=0.2 )
        set_mark( obj_t.matrix_world @ bm.verts[near_data[near].vertex].co.xyz, kind='PLAIN_AXES', scale=0.2 )

        # create a funky face here.
        new_face = [edge[0], edge[1], bm.verts[near_data[near].vertex]]

        newf=bmesh.ops.contextual_create(bm, geom= new_face)
        bm.faces.index_update()
        bm.faces.ensure_lookup_table()
        
        for f in newf['faces']:
            if f.normal.z < 0:
                bm.faces[f.index].normal_flip()
        
        # if first, or last, join vertex to end the cap
        
        if pc == 0 or pc == (MESH_VERTEX_LEN-1):
            
            if pc == 0:
                # use first
                edge_cap= [  edges[0][0], edges[1][0] ] # edge from right to left
            else:
                # use last
                edge_cap= [  edges[0][1], edges[1][1] ] # edge from right to left
            new_edge =bmesh.ops.contextual_create(bm, geom= edge_cap)
            bm.edges.index_update()
        
    #if idx >= 8: break
    if LIMIT and pc >= LIMIT:
        break

## end it

bm.calc_loop_triangles()
bm.to_mesh(obj_t.data)
obj_t.data.update()  
bm.free()