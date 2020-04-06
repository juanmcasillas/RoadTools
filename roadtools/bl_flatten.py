import bpy
from mathutils import Vector, Matrix, Euler
from math import radians
import bmesh   

from bl_utils import BL_DEBUG,BL_UTILS,BL_ROAD_UTILS

class BL_FLATTEN:
    def __init__(self):
        pass

    def get_raycast(plane, terrain, DEBUG, LIMIT):

        obj_s=  bpy.data.objects[plane]
        mesh_s = obj_s.data    
        point_data = []
        pc = 0
        #for p in mesh_s.polygons:
        for v in mesh_s.vertices:
            # first point, first vert, is 0.
            # skip center in quads
            #check_points = [ ("c_%d" % p.index, p.center) ]
            #check_points = [  ]
                
            #for v in p.vertices:
            #    print(v)
            #    check_points.append( (v.index,v) )

            #
            # ok, process them mesh can be Down (should be)
            # but can be up. so check the results and save the
            # data. (raycast done in world coords and works)
            # maybe due it's on (0,0,0) ?
            #
            # retrieve i the index of the point, v the point

            # in order to get this working, I have to DELETE the 
            # faces from the polygon, and use the vertex.
            # Delete "Only Edges & Faces"

            terrain_down = True
            DEBUG and BL_DEBUG.set_mark( obj_s.matrix_world @ v.co.xyz, kind="PLAIN_AXES" )
            result, location, normal, index, r_object, matrix = bpy.context.scene.ray_cast( 
                bpy.context.view_layer, 
                obj_s.matrix_world @ v.co.xyz, 
                #v.normal * -1 # Z Down
                (0,0,-1.0)
            )
            #print("R", result,index, r_object, obj_s.matrix_world @ v.co.xyz  )
            if result and r_object.name == terrain: 
                DEBUG and BL_DEBUG.set_mark( location, kind="SPHERE")
            
            if not result:
                result, location, normal, index, r_object, matrix = bpy.context.scene.ray_cast( 
                    bpy.context.view_layer, 
                    obj_s.matrix_world @ v.co.xyz, 
                    #v.normal # Z Up
                    (0,0,1.0)
                )
                if not result:
                    # something bizarre happens with that point
                    print("Point %s doesn't match terrain geometry" % v.co.xyz)
                    DEBUG and BL_DEBUG.set_mark(obj_s.matrix_world @ v.co.xyz)
                    continue
                #print("R2", result,index, r_object )
                if result and r_object.name == terrain: 
                    DEBUG and BL_DEBUG.set_mark(location, kind="CUBE")
                ## terrain is upwards
                terrain_down = False
    
            # terrain is downwards

            if r_object.name == terrain:
                #found_dict[key] = True
                point_data.append( (terrain_down, index, v, location )) # terrain is down, faceindex, point
            #else:
            #    pass
                #point_data.append( (terrain_down, index, v, location ))
                # insert a fake point, but use face index 
                # don't know what I'm going to do with that.
                #_,index,_,_ = point_data[-1]
                #point_data.append( (None, index, v, None )) # fake point

            pc +=1
            if LIMIT and pc / 4 >= LIMIT:
                break

        #for terrain_down, faceindex, p in point_data:
            #print(terrain_down, faceindex, p)
        #    BL_DEBUG.set_mark(obj_s.matrix_world  @ p.xyz)
        print("extend_terrain Total/Calculated Points/Polys (Quads) %d/%d/%d" % (len(mesh_s.vertices),len(point_data), int(pc / 4)))        
        return(point_data)







    def extend_terrain(plane, terrain):
        """try to flatten a terrain, using the plane as reference plane must have ALL modifiers APPLIED"""
        
        DEBUG = False
        LIMIT = None

        BL_DEBUG.clear_marks()

        # build a table with the point and the face_idx, to speed up the thing
        # store the vertex only one time. use raycast to the Z down to check the
        # points, instead closest.
        # use side points, and center


        obj_s=  bpy.data.objects[plane]
        mesh_s = obj_s.data
        obj_t=  bpy.data.objects[terrain]
    

        #for p in mesh_s.polygons:

        point_data = BL_FLATTEN.get_raycast(plane,terrain, DEBUG, LIMIT)
        
        # at this point XD point_data has 
        # terrain_up/down, face_index, point, location)

        BL_DEBUG.clear_marks()

        bm = bmesh.new()
        bm.from_mesh(obj_t.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        
        # unselect all
        for face in bm.faces: face.select = False
        for vert in bm.verts: vert.select = False
        for edge in bm.edges: edge.select = False

        # select faces tracked
        for point in point_data:
            terrain_down, index, point, location = point
            bm.faces[index].select = True

        # extend the faces
        #sel_verts = [v for v in bm.verts if v.select]
        #sel_edges = [e for e in bm.edges if e.select]
        sel_faces = [f for f in bm.faces if f.select]
        #geom = sel_verts + sel_edges + sel_faces
        geom = sel_faces

        ret_geom =  bmesh.ops.region_extend(bm, geom=geom,use_faces=True, use_face_step=False,use_contract=False)
        for f in ret_geom['geom']:
            if isinstance(f, bmesh.types.BMFace):
                f.select = True

        geom = [f for f in bm.faces if f.select]
        bmesh.ops.triangulate(bm, faces=geom)        

        for f in ret_geom['geom']:
                f.select = True
                
        ##############################################################
        #
        # 0. at this point, faces are triangulated, and selected
        # 
        ##############################################################
    
 
        ##############################################################
        #
        # 1. delete the faces recalculate again the faces
        # this version only deletes the nearest faces from the 
        # road. Maybe it's a little narrow
        # 
        ##############################################################
        
        bm.calc_loop_triangles()
        bm.to_mesh(obj_t.data)
        obj_t.data.update()  

        #bm.verts.ensure_lookup_table()
        #bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        
        #        
        # I have to CHANGE to OBJECT in order to keep working on that
        # and update the structure. After change, return to edit and
        # keep working, it works.
        # 
        bpy.ops.object.mode_set(mode = 'OBJECT')                 
        bpy.ops.object.mode_set(mode = 'EDIT')                 
                
        point_data = BL_FLATTEN.get_raycast(plane, terrain, DEBUG, LIMIT)

        # at this point XD point_data has 
        # terrain_up/down, face_index, point, location)
        
        BL_DEBUG.clear_marks()

        faces_to_delete = {}
        
        for item in point_data:
                terrain_down, index, point, location = item
                #print(terrain_down,index, point, location)
                #BL_DEBUG.set_mark( obj_t.matrix_world @ location.xyz, kind="PLAIN_AXES" )

                if index not in faces_to_delete.keys():
                    faces_to_delete[index] = bm.faces[index]
    
        # extend the selection

        EXTEND_SELECTION = False
        if EXTEND_SELECTION:

            for face in bm.faces: face.select = False
            for vert in bm.verts: vert.select = False
            for edge in bm.edges: edge.select = False        

            for f in faces_to_delete.keys():
                bm.faces[f].select = True        

            #sel_verts = [v for v in bm.verts if v.select]
            #sel_edges = [e for e in bm.edges if e.select]
            sel_faces = [f for f in bm.faces if f.select]
            #geom = sel_verts + sel_edges + sel_faces
            geom = sel_faces

            ret_geom =  bmesh.ops.region_extend(bm, geom=geom,use_faces=True, use_face_step=False,use_contract=False)
            for f in ret_geom['geom']:
                if isinstance(f, bmesh.types.BMFace):
                    faces_to_delete[f.index] = bm.faces[f.index]

        
        bmesh.ops.delete(bm, geom=list(faces_to_delete.values()), context='FACES_KEEP_BOUNDARY') # FACES_ONLY

        ##############################################################
        #
        # 2. create new geometry
        # 
        ##############################################################        
    
        if False:    
            print("Points/faces: ", len(point_data), len(point_data)/4)
        
            for plane_faces in list(BL_UTILS.chunk(point_data,4)):
                #print(plane_faces)

                for vertex in plane_faces:
                    terrain_down, index, point, location = vertex
                    #bm.verts.new( obj_t.matrix_world.inverted() @ location_a )        
                    bm.verts.new( location )         
            

        ##############################################################
        #
        # 3. Some tests. Disabled
        # 
        ##############################################################  

        if False:

            #
            # test test test
            # this method triangulates the face selected.
            # demo, don't use it for now.
            #
            for item in point_data:
                terrain_down, index, point, location = item
                BL_DEBUG.set_mark(obj_s.matrix_world @ point.co.xyz, kind="PLAIN_AXES")
                BL_DEBUG.set_mark(location, kind="CUBE")
                BL_UTILS.triangulate_face_quad(bm, index)
                
            #
            # test test test
            # this calculates the nearest point, and moves the 
            # vertex to the height of the point
            #
            
            sel_faces = [f for f in bm.faces if f.select]
            sel_verts = []
            for f in sel_faces:
                sel_verts += f.verts

            #
            # delete all the empties
            #

            BL_DEBUG.clear_marks()

            for item in point_data:
                terrain_down, index, point, location = item
                
                shortest = None
                shortestDist = 99999999999999

                for v in sel_verts: #go throught all vertices ... in the selected faces!
                    dist = (Vector( v.co.xyz ) - location).length  #calculate the distance
                    #print(dist)
                    if dist < shortestDist : #test if better so far
                        shortest = v
                        shortestDist = dist
                
                if shortest:
                    BL_DEBUG.set_mark(obj_s.matrix_world @ point.co.xyz, kind="PLAIN_AXES")
                    BL_DEBUG.set_mark(location, kind="CUBE")
                    BL_DEBUG.set_mark(shortest.co.xyz, kind="SPHERE")
                    ##dist = (Vector( obj_s.matrix_world @ point.co.xyz ) - obj_t.matrix_world @ shortest.co.xyz).length
                    ##!z
                    #p1 = obj_s.matrix_world @ point.co.xyz
                    #p2 = obj_t.matrix_world @ shortest.co.xyz               
                    # dist =  point.co.z - shortest.co.z
                    shortest.co[2] = point.co.z

                    connected_verts = {}
                    marked_edges = []
                    print("---")
                    BL_FLATTEN.findConnectedVerts(shortest.index, bm, connected_verts, marked_edges, maxdepth=1)
                    # print(",".join([str(v) for v in connected_verts.keys()]))
                    for near in connected_verts.keys():
                        print("near", near)
                        near.co[2] = point.co.z
                        BL_DEBUG.set_mark(near.co.xyz)

                    #print(shortest, shortest.index, shortest.co)
                    #bmesh.ops.translate(bm, verts=[shortest], vec= (dist) * shortest.normal)   


        ##############################################################
        #
        # End
        # update the meshes
        # free the bmesh
        # 
        ##############################################################  

        bm.calc_loop_triangles()
        bm.to_mesh(obj_t.data)
        obj_t.data.update()  
        bm.free()
  
        #return(("ERROR", "Can't found terrain below the curve"))
        return(("INFO", "Done"))

#BL_FLATTEN.extend_terrain('Plane','Terrain')        
