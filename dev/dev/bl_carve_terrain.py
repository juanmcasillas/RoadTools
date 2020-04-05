import bpy
from mathutils import Vector
import bmesh



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
 
# test
#
#point = bpy.context.scene.cursor.location
#adjust_face_terrain( "Terrain", point )

curve = bpy.data.objects['outpux.gpx']
bpy.ops.object.mode_set(mode = 'OBJECT')
curve.select_set(True)
bpy.ops.object.convert(target='MESH', keep_original=False)
ve = curve.data.vertices

count =0
for i in range(len(curve.data.edges)):
    p = curve.data.edges[i]
    point_calc = ve[p.vertices[0]].co
    adjust_face_terrain( "Terrain", point_calc )
    bpy.context.scene.cursor.location = point_calc
    #print(point_calc)
    count +=1
    #if count > 20:
    #    break
    
bpy.ops.object.select_all(action='DESELECT')
#bpy.ops.object.mode_set(mode = 'EDIT') 
#bpy.ops.object.convert(target='CURVE', keep_original=False)
bpy.ops.object.mode_set(mode = 'OBJECT')   
print("Finished: %d points done" % count)
