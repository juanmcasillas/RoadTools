import bpy
from mathutils import Vector, Matrix, Euler
from math import radians
import bmesh

from bl_utils import BL_DEBUG,BL_UTILS,BL_ROAD_UTILS

class BL_FLATTEN:
    def __init__(self):
        pass

    def flatten_terrain(plane, terrain):
        """try to flatten a terrain, using the plane as reference plane must have ALL modifiers APPLIED"""
        
        BL_DEBUG.clear_marks()

        # build a table with the point and the face_idx, to speed up the thing
        # store the vertex only one time. use raycast to the Z down to check the
        # points, instead closest.
        # use side points, and center

        obj_s=  bpy.data.objects[plane]
        mesh_s = obj_s.data

        point_data = []
        found_dict = {}

        pc = 0

        for p in mesh_s.polygons:

            # first point, first vert, is 0.
            #check_points = [ ("c_%d" % p.index, p.center) ]
            check_points = [  ]
            
                
            for v in p.vertices:
                check_points.append( (v,mesh_s.vertices[v].co) )

            #
            # ok, process them mesh can be Down (should be)
            # but can be up. so check the results and save the
            # data. (raycast done in local coords and works)
            # maybe due it's on (0,0,0) ?
            #
            # retrieve i the index of the point, v the point

            for key,v in check_points:

                if key in found_dict.keys():
                    continue


                terrain_down = True
                BL_DEBUG.set_mark( obj_s.matrix_world @ v.xyz )
                result, location, normal, index, object, matrix = bpy.context.scene.ray_cast( 
                    bpy.context.view_layer, 
                    obj_s.matrix_world @ v.xyz, 
                    (0,0,-1) # Z Down
                )
                print("R", result,index, object, obj_s.matrix_world @ v.xyz  )
                if result: BL_DEBUG.set_mark( location, kind="SPHERE")
                if not result:
                    result, location, normal, index, object, matrix = bpy.context.scene.ray_cast( 
                        bpy.context.view_layer, 
                        obj_s.matrix_world @v.xyz, 
                        (0,0,1) # Z Up
                    )
                    if not result:
                        # something bizarre happens with that point
                        print("Point %s doesn't match terrain geometry" % v.xyz)
                        BL_DEBUG.set_mark(obj_s.matrix_world @ v.xyz)
                        continue
                    #print("R2", result,index, object )
                    BL_DEBUG.set_mark(location, kind="CUBE")
                    ## terrain is upwards
                    terrain_down = False
        
                # terrain is downwards
                
                found_dict[key] = True
                point_data.append( (terrain_down, index, v )) # terrain is down, faceindex, point

            pc +=1
            #if pc >= 10:
            #    break

        #for terrain_down, faceindex, p in point_data:
            #print(terrain_down, faceindex, p)
        #    BL_DEBUG.set_mark(obj_s.matrix_world  @ p.xyz)
        print("Calculated Points/Polys %d/%d" % (len(point_data), pc))

        # at this point XD point_data has 
        # terrain_up/down, face_index, point)




        #return(("ERROR", "Can't found terrain below the curve"))
        return(("INFO", "Done"))

BL_FLATTEN.flatten_terrain('Plane','Terrain')        