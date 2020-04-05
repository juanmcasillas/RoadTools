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
    print(face_idx)
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
        bmesh.ops.translate(bm, verts=face.verts, vec= distance * face.normal)
        bmesh.update_edit_mesh(mesh)
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
       

def rotate_mesh_face ( objname, face_idx, target_vector, point):
    
    obj_t=  bpy.data.objects[objname]
    mesh_t = bpy.data.meshes[objname] 

    face_t = mesh_t.polygons[face_idx]
    face_t.select = True
 
    #empty_on(obj_t.matrix_world @ face_t.center)

    #bpy.ops.object.mode_set(mode = 'EDIT')
    #obj_t.select_set(True)

    #
    # with the face selected, try some manual rotations
    # first, get the bmesh, and do some visual representation
    #
    #bm = bmesh.new()
    #bm.from_mesh(mesh_t)
    bm = bmesh.from_edit_mesh(mesh_t)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bface = bm.faces[face_t.index]
    bface.select = True
    verts_selected = [v for v in bface.verts]
    #for v in verts_selected:
    #    empty_on(obj_t.matrix_world @ v.co, kind='PLAIN_AXES',scale=0.1)

    # this is how to rotate a face based on angles
    #
    # rad_x = radians(0)
    # rad_y = radians(0)
    # rad_z = radians(30)
    # mat_rot = Euler((rad_x, rad_y, rad_z),'XYZ').to_matrix().to_4x4()
    # print("mat_rot ", mat_rot)
    
    #target_v = Vector((0.1835, -0.2740, 0.9441))
    # face#47 normal <Vector (-0.0029, 0.0351, 0.9994)>
    # face#56 normal <Vector (0.1835, -0.2740, 0.9441)>
        
    # move first down
    distance = point.z - bface.calc_center_median().z
    if distance > 0:
        #print("not needed")
        #bpy.ops.object.mode_set(mode='OBJECT')
        pass
    else:
        print("moving: %3.2f" % distance)
        bmesh.ops.translate(bm, verts=verts_selected, vec = distance * bface.normal)

    print(face_t.index)
    print("source ", bface.normal)
    print("target ", target_vector)

    mat_rot = bface.normal.rotation_difference(target_vector).to_euler().to_matrix().to_4x4()
    print("quat ", mat_rot)

    bmesh.ops.rotate( bm, cent=bface.calc_center_median(), matrix=mat_rot, verts=verts_selected)
    print("normal rotated ", bface.normal)
    
    # some debug
    #verts_selected = [v for v in bface.verts]
    #for v in verts_selected:
    #    empty_on(obj_t.matrix_world @ v.co, kind='PLAIN_AXES',scale=0.1)
        
    #bmesh.update_mesh(mesh_t)
    bmesh.update_edit_mesh(mesh_t)
 
##

init()

objname_s = 'Plane'
objname_t = 'Terrain'

obj_s=  bpy.data.objects[objname_s]
mesh_s = obj_s.data

obj_t=  bpy.data.objects[objname_t]
mesh_t = bpy.data.meshes[objname_t]

#bpy.ops.object.mode_set(mode = 'EDIT')
#bm = bmesh.from_edit_mesh(mesh_t)
#bm.verts.ensure_lookup_table()
#bm.faces.ensure_lookup_table()
# get the required normal from plane, first of all
# do error checking later

count=0

for p in mesh_s.polygons:
    face_idx = get_terrain_face( objname_t, obj_s.matrix_world @ p.center)
    bpy.ops.object.mode_set(mode = 'EDIT')
    #empty_on(obj_s.matrix_world @ p.center)
    if face_idx != -1:    
        face_s = mesh_t.polygons[face_idx]
        rotate_mesh_face(objname_t, face_idx, p.normal, obj_s.matrix_world @ p.center)
     
    bpy.ops.object.mode_set(mode = 'OBJECT')
    count +=1
    #if count > 20:
    #    break
    