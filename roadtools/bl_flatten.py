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
        
        DEBUG = False

        BL_DEBUG.clear_marks()

        # build a table with the point and the face_idx, to speed up the thing
        # store the vertex only one time. use raycast to the Z down to check the
        # points, instead closest.
        # use side points, and center

        obj_s=  bpy.data.objects[plane]
        mesh_s = obj_s.data

        obj_t=  bpy.data.objects[terrain]
        mesh_t = bpy.data.meshes[obj_t.name]


        point_data = []
        found_dict = {}

        pc = 0

        for p in mesh_s.polygons:

            # first point, first vert, is 0.
            # skip center in quads
            #check_points = [ ("c_%d" % p.index, p.center) ]
            check_points = [  ]
                
            for v in p.vertices:
                check_points.append( (v,mesh_s.vertices[v]) )

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
                DEBUG and BL_DEBUG.set_mark( obj_s.matrix_world @ v.co.xyz )
                result, location, normal, index, object, matrix = bpy.context.scene.ray_cast( 
                    bpy.context.view_layer, 
                    obj_s.matrix_world @ v.co.xyz, 
                    #v.normal * -1 # Z Down
                    obj_s.matrix_world @ Vector((0,0,-1.0))
                )
                #print("R", result,index, object, obj_s.matrix_world @ v.co.xyz  )
                if result and object.name == terrain: 
                    DEBUG and BL_DEBUG.set_mark( location, kind="SPHERE")
                
                if not result:
                    result, location, normal, index, object, matrix = bpy.context.scene.ray_cast( 
                        bpy.context.view_layer, 
                        obj_s.matrix_world @v.co.xyz, 
                        #v.normal # Z Up
                        obj_s.matrix_world @ Vector((0,0,1.0))
                    )
                    if not result:
                        # something bizarre happens with that point
                        print("Point %s doesn't match terrain geometry" % v.co.xyz)
                        DEBUG and BL_DEBUG.set_mark(obj_s.matrix_world @ v.co.xyz)
                        continue
                    #print("R2", result,index, object )
                    if result and object.name == terrain: 
                        DEBUG and BL_DEBUG.set_mark(location, kind="CUBE")
                    ## terrain is upwards
                    terrain_down = False
        
                # terrain is downwards

                if object.name == terrain:
                    found_dict[key] = True
                    point_data.append( (terrain_down, index, v, location )) # terrain is down, faceindex, point
                #else:
                #    pass
                    #point_data.append( (terrain_down, index, v, location ))
                    # insert a fake point, but use face index 
                    # don't know what I'm going to do with that.
                    #_,index,_,_ = point_data[-1]
                    #point_data.append( (None, index, v, None )) # fake point

            pc +=1
            #if pc >= 2:
            #    break

        #for terrain_down, faceindex, p in point_data:
            #print(terrain_down, faceindex, p)
        #    BL_DEBUG.set_mark(obj_s.matrix_world  @ p.xyz)
        print("Calculated Points/Polys %d/%d" % (len(point_data), pc))

        # at this point XD point_data has 
        # terrain_up/down, face_index, point, location)

        bpy.ops.object.mode_set(mode = 'EDIT')
        
        bm = bmesh.new()
        bm.from_mesh(mesh_t)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # unselect all
        for face in bm.faces: face.select = False

        # do some testing here.
        for point in point_data:
            terrain_down, index, point, location = point
            bface = bm.faces[index]
            bface.select = True

        # extend the faces
        sel_verts = [v for v in bm.verts if v.select]
        sel_edges = [e for e in bm.edges if e.select]
        sel_faces = [f for f in bm.faces if f.select]
        geom = sel_verts + sel_edges + sel_faces

        ret_geom =  bmesh.ops.region_extend(bm, geom=geom,use_faces=True, use_face_step=False,use_contract=False)
        for f in ret_geom['geom']:
            if isinstance(f, bmesh.types.BMFace):
                f.select = True

        geom = [f for f in bm.faces if f.select]
        bmesh.ops.triangulate(bm, faces=geom)

        # get the nearest point in the mesh, move it to the point.

        sel_faces = [f for f in bm.faces if f.select]
        sel_verts = []
        for f in sel_faces:
            sel_verts += f.verts

        #print(sel_verts)
        for point in point_data:
            terrain_down, index, point, location = point
            
            shortest = None
            shortestDist = 99999999999999

            for v in sel_verts: #go throught all vertices ... in the selected faces!
                dist = (Vector( obj_s.matrix_world @ v.co.xyz ) - location).length  #calculate the distance
                if dist < shortestDist : #test if better so far
                    shortest = v
                    shortestDist = dist
            
            if shortest:
                BL_DEBUG.set_mark(location, kind="CUBE")
                BL_DEBUG.set_mark(shortest.co.xyz, kind="SPHERE")
                ##dist = (Vector( obj_s.matrix_world @ point.co.xyz ) - obj_t.matrix_world @ shortest.co.xyz).length
                ##!z
                #p1 = obj_s.matrix_world @ point.co.xyz
                #p2 = obj_t.matrix_world @ shortest.co.xyz               
                # dist =  point.co.z - shortest.co.z
                shortest.co[2] = point.co.z
                print(shortest, shortest.index, shortest.co)
                #bmesh.ops.translate(bm, verts=[shortest], vec= (dist) * shortest.normal)



        # faces are triangulated, so now can do the calculation again, and move the face vertex to the desired point
        #bmesh.closest_point_on_mesh(point, max_dist=1.84467e+19)

        #odd_points = list(zip( point_data[::2], point_data[2::2]))
        #even_points = list(zip( point_data[1::2], point_data[2::2]))

        # do my own vertex mapping (odd / even)
        # i=0
        # while i < len(point_data)-3:

        #     o1 = i
        #     o2 = i+3

        #     if i==0:
        #         e1 = 1
        #         e2 = 2
        #     else:
        #         e1 = i+1
        #         e2 = i+2

        #     _,_,_,location_a = point_data[o1]
        #     _,_,_,location_b = point_data[o2]

        #     _,_,_,location_c = point_data[e1]
        #     _,_,_,location_d = point_data[e2]


        #     vo1 = bm.verts.new( obj_t.matrix_world.inverted() @ location_a )
        #     vo2 = bm.verts.new( obj_t.matrix_world.inverted() @ location_b )

        #     ve1 = bm.verts.new( obj_t.matrix_world.inverted() @ location_c )
        #     ve2 = bm.verts.new( obj_t.matrix_world.inverted() @ location_d )

        #     i += 3

        # edges = []
        # for p_pair in odd_points:
        #     a,b = p_pair
        #     terrain_down_a, index_a, point_a, location_a = a
        #     terrain_down_b, index_b, point_b, location_b = b
            
        #     #bm.faces[index].select = True
        #     va = bm.verts.new( obj_t.matrix_world.inverted() @ location_a )
        #     vb = bm.verts.new( obj_t.matrix_world.inverted() @ location_b )
            
        #     #edges.append(bm.edges.new((va, vb)))
        #     #v.select = True

        #bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True )            
        
        bpy.ops.object.mode_set(mode = 'OBJECT') 
        bm.to_mesh(mesh_t)
        mesh_t.update()

        #return(("ERROR", "Can't found terrain below the curve"))
        return(("INFO", "Done"))

#BL_FLATTEN.flatten_terrain('Plane','Terrain')        