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
    


def rotate_mesh_face ( objname, face_idx, target_vector):
    
    obj_t=  bpy.data.objects[objname]
    mesh_t = bpy.data.meshes[objname] 

    face_t = mesh_t.polygons[face_idx]
    face_t.select = True
    print(face_t.index)
    empty_on(obj_t.matrix_world @ face_t.center)

    bpy.ops.object.mode_set(mode = 'EDIT')
    #obj_t.select_set(True)

    #
    # with the face selected, try some manual rotations
    # first, get the bmesh, and do some visual representation
    #
    bm = bmesh.from_edit_mesh(mesh_t)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bface = bm.faces[face_t.index]
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
        

    print("source ", bface.normal)
    print("target ", target_vector)

    mat_rot = bface.normal.rotation_difference(target_vector).to_euler().to_matrix().to_4x4()
    print("quat ", mat_rot)

    bmesh.ops.rotate( bm, cent=bface.calc_center_median(), matrix=mat_rot, verts=verts_selected)
    print("normal rotated ", bface.normal)
    
    # some debug
    verts_selected = [v for v in bface.verts]
    for v in verts_selected:
        empty_on(obj_t.matrix_world @ v.co, kind='PLAIN_AXES',scale=0.1)
        
    bmesh.update_edit_mesh(mesh_t)
        
#
# init 
    
init() 
cur3d = bpy.context.scene.cursor.location

objname_t = 'Grid'
objname_s = 'Plane'

obj_s=  bpy.data.objects[objname_s]
mesh_s = obj_s.data

# get the required normal from plane, first of all
# do error checking later


face_s = None
for p in mesh_s.polygons:
     if p.select:
         face_s = p
         break

empty_on(obj_s.matrix_world @ face_s.center)

# now, process the face we need in the grid

rotate_mesh_face(objname_t, 8, face_s.normal)

#for i in range(40, 41):
    #rotate_mesh_face(objname_t, i, face_s.normal)




#import bpy
#from mathutils import Vector, Matrix, Euler


##def scale_from_vector(v):
##    mat = Matrix.Identity(4)
##    for i in range(3):
##        mat[i][i] = v[i]
##    return mat   

##def align_face_to( source, dest):
##    
##    obj_src = bpy.data.objects[source]
##    mesh_src = bpy.data.meshes[source] 

##    obj_dst = bpy.data.objects[dest]
##    mesh_dst = bpy.data.meshes[dest] 


##    loc_src, rot_src, scale_src = obj_src.matrix_world.decompose()
##    loc_dst, rot_dst, scale_dst = obj_dst.matrix_world.decompose()

##    face_src = mesh_src.polygons[0]
##    face_dst = mesh_dst.polygons[0]
##        
##    obj_dst.matrix_world = (
##        Matrix.Translation(loc_dst) @
##        rot_src.to_matrix().to_4x4() @ 
##        scale_from_vector(scale_dst)
##    )
##    


##bpy.ops.object.select_all(action='DESELECT')


##source = 'Plane'
##dest = 'Grid'

##obj_src = bpy.data.objects[source]
##mesh_src = obj_src.data

##obj_dst = bpy.data.objects[dest]
##mesh_dst = obj_dst.data


##loc_src, rot_src, scale_src = obj_src.matrix_world.decompose()
##loc_dst, rot_dst, scale_dst = obj_dst.matrix_world.decompose()

##        
##for p in mesh_src.polygons:
##    print(p.center)
##    o = bpy.data.objects.new( "empty", None )
##    o.location = p.center
##    o.empty_display_type = 'ARROWS'
##    bpy.context.scene.collection.objects.link( o )
##    
##    faceIdx = obj_dst.closest_point_on_mesh( p.center )[-1]
##    if faceIdx != -1:
##        print("face found")
##        face_src = p
##        face_dst = mesh_dst.polygons[faceIdx]
##        face_dst.select = True
##        
##        obj_dst.matrix_world = (
##            Matrix.Translation(loc_dst) @
##            rot_src.to_matrix().to_4x4() @ 
##            scale_from_vector(scale_dst)
##        )
#        

#bpy.ops.object.select_all(action='DESELECT')        
#source = 'Plane'
#dest = 'Grid'

#obj_src = bpy.data.objects[source]
#mesh_src = obj_src.data

#obj_dst = bpy.data.objects[dest]
#mesh_dst = obj_dst.data

## source face

#face_src = mesh_src.polygons[0]
#face_src.select = True

#o = bpy.data.objects.new( "empty", None )
#o.empty_display_type = 'ARROWS'
#o.location = face_src.center
#bpy.context.scene.collection.objects.link( o )

### target

#face_dst = mesh_dst.polygons[12]
#face_dst.select = True

#o = bpy.data.objects.new( "empty", None )
#o.empty_display_type = 'ARROWS'
#o.location = face_src.center
#bpy.context.scene.collection.objects.link( o )


##quat = face_src.normal.to_track_quat('Z', 'Y')
##mat = quat.to_matrix().to_4x4()
###mat.translation = face_dst.center

##verts = mesh_dst.vertices

##for v in face_dst.vertices:
##    verts[v].co = mat  @ verts[v].co
##    



#vec = obj_src.matrix_world @ face_src.normal
#print("direction = ",vec/vec.length)

#quat = face_src.normal.to_track_quat('Z', 'Y')
#print(quat)
#euler = obj_src.matrix_world.to_euler()# if only a not subdivided Plane is used.
#euler = Euler(vec)
#print(face_src.normal,euler)

##cube = bpy.data.objects['Cube']
##cube.rotation_euler = euler

def scale_from_vector(v):
    mat = Matrix.Identity(4)
    for i in range(3):
        mat[i][i] = v[i]
    return mat   

def align_face_to( source, face_src_n, dest, face_dst_n):
    
    

    obj_src = bpy.data.objects[source]
    mesh_src = obj_src.data

    obj_dst = bpy.data.objects[dest]
    mesh_dst = obj_dst.data

    face_src = mesh_src.polygons[face_src_n]
    face_src.select = True

    o = bpy.data.objects.new( "empty", None )
    o.empty_display_type = 'ARROWS'
    o.location = face_src.center
    bpy.context.scene.collection.objects.link( o )

    ## target

    face_dst = mesh_dst.polygons[face_dst_n]
    face_dst.select = True

    o = bpy.data.objects.new( "empty", None )
    o.empty_display_type = 'ARROWS'
    o.location = face_dst.center
    bpy.context.scene.collection.objects.link( o )

    # to the thing

    loc_src, rot_src, scale_src = obj_src.matrix_world.decompose()
    loc_dst, rot_dst, scale_dst = obj_dst.matrix_world.decompose()

    face_src = mesh_src.polygons[0]
    face_dst = mesh_dst.polygons[0]
        
    obj_dst.matrix_world = (
        Matrix.Translation(loc_dst) @
        rot_src.to_matrix().to_4x4() @ 
        scale_from_vector(scale_dst)
    )
    

align_face_to('Plane', 0, 'Grid', 12)


