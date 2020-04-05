#
# adjust the terrain, and adjust normals from faces,
# so the terrain matches the road
#
# this is last and working script
#


import bpy
from mathutils import Vector, Matrix, Euler
from math import radians
import bmesh


def empty_on(p, kind='ARROWS', scale=None):
    o = bpy.data.objects.new( "empty", None )
    o.empty_display_type = kind
    o.location = p
    bpy.context.scene.collection.objects.link( o )    
    if scale:
        o.empty_display_size = scale


def init():
    for o in bpy.data.objects:
        if o.name.startswith('empty'):
            bpy.data.objects.remove(o)  


def get_terrain_face( terrain_name, point ):

    #point = bpy.context.scene.cursor.location
    obj = bpy.data.objects[terrain_name]
    face_idx = obj.closest_point_on_mesh( point )[-1]
    #print(face_idx)
    return(face_idx)


def adjust_face_terrain( terrain_name, point ):

    #point = bpy.context.scene.cursor.location
    obj = bpy.data.objects[terrain_name]
    mesh = bpy.data.meshes[terrain_name]

    faceIdx = obj.closest_point_on_mesh( point )[-1]

    if faceIdx != -1:
        
        obj.data.polygons[ faceIdx ].select = True
        #obj.data.polygons[ faceIdx ].center
        
        bpy.ops.object.mode_set(mode='EDIT')
        
        distance = point.z - obj.data.polygons[ faceIdx ].center.z
        if distance > 0:
            print("not needed")
            bpy.ops.object.mode_set(mode='OBJECT')
            return
        else:
            print("moving: %3.2f" % distance)
        
        bm = bmesh.from_edit_mesh(mesh)
        bm.faces.ensure_lookup_table()
        face = bm.faces[faceIdx]
        bmesh.ops.translate(bm, verts=face.verts, vec= (distance-0.5) * face.normal)
        bmesh.update_edit_mesh(mesh)
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
       

def rotate_mesh_face ( bm, face_idx, target_vector, point):
    
    bface = bm.faces[face_idx]
    bface.select = True
    verts_selected = [v for v in bface.verts]



    mat_rot = bface.normal.rotation_difference(target_vector).to_euler().to_matrix().to_4x4()

    if False:
        print("face index: ",face_idx)
        print("source ", bface.normal)
        print("target ", target_vector)
        print("quat ", mat_rot)

    bmesh.ops.rotate( bm, cent=bface.calc_center_median(), matrix=mat_rot, verts=verts_selected)


    # move first down (what about world xlation?)
    distance = point.z - bface.calc_center_median().z
    if distance > 0:
    #    #print("not needed")
    #    #bpy.ops.object.mode_set(mode='OBJECT')
         pass
    else:
        print("moving: %3.2f m" % distance)
        bmesh.ops.translate(bm, verts=verts_selected, vec = (distance) * bface.normal)
    
    if False:        
        print("normal rotated ", bface.normal)
    
    # some debug
    #verts_selected = [v for v in bface.verts]
    #for v in verts_selected:
    #    empty_on(obj_t.matrix_world @ v.co, kind='PLAIN_AXES',scale=0.1)
        
    #bmesh.update_mesh(mesh_t)
 
##

init()

objname_s = 'Plane'
objname_t = 'Terrain'

obj_s=  bpy.data.objects[objname_s]
mesh_s = obj_s.data

obj_t=  bpy.data.objects[objname_t]
mesh_t = bpy.data.meshes[objname_t]

# build a table with the point and the face_idx, to speed up the thing
count = 0
count2 = 0
data = []
for p in mesh_s.polygons:
    face_idx = get_terrain_face( objname_t, obj_s.matrix_world @ p.center)
    if face_idx != -1:
        data.append( (face_idx, obj_s.matrix_world @ p.center, p.normal))
        count2 +=1
        
    for v in p.vertices:
        p_co = mesh_s.vertices[v].co
        p_normal = mesh_s.vertices[v].normal

        face_idx = get_terrain_face( objname_t, obj_s.matrix_world @ p_co)
        if face_idx != -1:
            data.append( (face_idx, p_co, p_normal))
            count2 +=1


    count += 1
print("%d/%d points loaded" % (count2, count))




# create the object to work with
bpy.ops.object.mode_set(mode = 'EDIT')
bm = bmesh.new()
bm.from_mesh(mesh_t)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
# get the required normal from plane, first of all
# do error checking later


# first run, only select the faces, select more, and subdivide

count=0
for d in data:
    face_idx,p_center,p_normal = d
    bface = bm.faces[face_idx]
    bmesh.ops.subdivide_edges(bm, edges=face.edges[:], cuts=1)




count=0
for d in data:
    face_idx,p_center,p_normal = d
    rotate_mesh_face(bm, face_idx, p_normal, obj_s.matrix_world @ p_center)    
    count +=1
    #if count > 20:
    #    break

print("%d faces updated" % count)   
bpy.ops.object.mode_set(mode = 'OBJECT') 
bm.to_mesh(mesh_t)
mesh_t.update()

