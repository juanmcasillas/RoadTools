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
        
       

def rotate_mesh_face ( bm, face_idx, target_vector, point,  m_obj):
    
    bface = bm.faces[face_idx]
    #bface.select = True
    verts_selected = [v for v in bface.verts]
    
    if False:
        

        mat_rot = bface.normal.rotation_difference(target_vector).to_euler().to_matrix().to_4x4()

        if False:
            print("face index: ",face_idx)
            print("source ", bface.normal)
            print("target ", target_vector)
            print("quat ", mat_rot)

        bmesh.ops.rotate( bm, cent=bface.calc_center_median(), matrix=mat_rot, verts=verts_selected)


    # move first down (what about world xlation?)
    distance = point.z - bface.calc_center_median().z
    #distance = (point - m_obj.matrix_world @ bface.calc_center_median()).length 
    #distance = (point - bface.calc_center_median()).length 
    
    empty_on(point)
    empty_on(bface.calc_center_median(),kind='PLAIN_AXES')
    return

    
    
    # if distance > 0:
    #    #point is over the track lift it
    #    #print("not needed")
    #    #bpy.ops.object.mode_set(mode='OBJECT')
    #     pass
    # else:
    #     print("moving: %3.2f m" % distance)
    #     bmesh.ops.translate(bm, verts=verts_selected, vec = (distance) * bface.normal)
    
    verts_selected = [v for v in bface.verts]
    offset = 1.0
    distance = distance - offset
    print("moving: %3.2f m" % distance)
    bmesh.ops.translate(bm, verts=verts_selected, vec = (distance) * bface.normal)
    
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
face_dict = {}

for p in mesh_s.polygons:

    face_idx = get_terrain_face( objname_t, obj_s.matrix_world @ p.center)

    if face_idx != -1:
        key = "%s_%d" % ("c", face_idx)
        if key not in face_dict.keys():
            data.append( (face_idx, obj_s.matrix_world @ p.center, p.normal))
            count2 +=1
            face_dict[key] = True
    else:
        print("warning, point not found")

    v_index = 0            
    for v in p.vertices:
        p_co = mesh_s.vertices[v].co
        p_normal = mesh_s.vertices[v].normal

        face_idx = get_terrain_face( objname_t, obj_s.matrix_world @ p_co)
        if face_idx != -1:
            key = "%s_%d_%d" % ("v", face_idx, v_index)
            if key not in face_dict.keys():
                data.append( (face_idx, p_co, p_normal))
                count2 +=1
                face_dict[key] = True
        else:
            print("warning, point not found")

        v_index += 1
        
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

# extend the selection

count=0
for d in data:
    face_idx,p_center,p_normal = d
    bface = bm.faces[face_idx]
    bface.select = True

# extend the faces
sel_verts = [v for v in bm.verts if v.select]
sel_edges = [e for e in bm.edges if e.select]
sel_faces = [f for f in bm.faces if f.select]
geom = sel_verts + sel_edges + sel_faces

print("Selected faces: %d" % len(sel_faces))

ret_geom =  bmesh.ops.region_extend(bm, geom=geom,use_faces=True, use_face_step=False,use_contract=False)
for f in ret_geom['geom']:
    if isinstance(f, bmesh.types.BMFace):
        f.select = True
    
# subdivide faces

geom = [f for f in bm.faces if f.select]

print("Selected faces (after extension): %d" % len(geom))

# deselect all
#for face in bm.faces:
#     face.select = False

count=0
bmesh.ops.triangulate(bm, faces=geom)

## Subdivide faces. Maybe this is not needed.
if False:
    for bface in geom:
        #bface.select = True
        
        print("face edges: ", bface.index, len(bface.edges), bface.select)
        bmesh.ops.subdivide_edges(bm, edges=bface.edges, cuts=1, use_grid_fill=True ) # quad_corner_type='FAN'
        count +=1
        #if count >= 1:
        #    break

#
# I need to remap again the available faces with the faces in the polygon
# sync the mesh, do the work again
#

bpy.ops.object.mode_set(mode = 'OBJECT') 
bm.to_mesh(mesh_t)
mesh_t.update()

count  = 0
count2 = 0
data = []
face_dict = {}

for p in mesh_s.polygons:
    face_idx = get_terrain_face( objname_t, obj_s.matrix_world @ p.center)
    if face_idx != -1:

        key = "%s_%d" % ("c", face_idx)

        if key not in face_dict.keys():
            data.append( (face_idx, obj_s.matrix_world @ p.center, p.normal))
            count2 +=1
            face_dict[key] = True

    v_index = 0            
    for v in p.vertices:
        p_co = mesh_s.vertices[v].co
        p_normal = mesh_s.vertices[v].normal

        

        face_idx = get_terrain_face( objname_t, obj_s.matrix_world @ p_co)
        if face_idx != -1:

            key = "%s_%d_%d" % ("v", face_idx, v_index)
            if key not in face_dict.keys():
                data.append( (face_idx, p_co, p_normal))
                count2 +=1
                face_dict[key] = True

        v_index += 1
        
    count += 1



print("(2nd time) %d/%d points loaded" % (count2, count))

# create the object to work with
bpy.ops.object.mode_set(mode = 'EDIT')
bm = bmesh.new()
bm.from_mesh(mesh_t)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()

#
# move the faces
#
count=0
for d in data:
    face_idx,p_center,p_normal = d
    
    rotate_mesh_face(bm, face_idx, p_normal, obj_s.matrix_world @ p_center, obj_t)    
    count +=1
    #if count > 1:
    #    break

print("%d faces updated" % count)   
bpy.ops.object.mode_set(mode = 'OBJECT') 
bm.to_mesh(mesh_t)
mesh_t.update()
