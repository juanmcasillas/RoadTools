#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# bl_flatten.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# 
# 
# ############################################################################

import bpy
from mathutils import Vector, Matrix, Euler
from math import radians
import bmesh   
import sys

import bl_utils 
import bl_road_utils



# some utils





class BL_FLATTEN:


    class DummyVector:
        "to add the .co attribute and work as a vertex"
        def __init__(self,v):
            self.co = v

    class nearest:
        def __init__(self, pos):
            self.pos = 'RIGHT'
            if pos != 0: self.pos = 'LEFT'
            self.face = None
            self.vertex = None
            self.edges = []
            self.distance = sys.maxsize
            self.point = None

        def __repr__(self):
            return "<Nearest face:%s vertex:%s edges:%s distance:%5.8f point:%s pos: %s>" % (
                self.face, 
                self.vertex, 
                self.edges,
                self.distance, 
                self.point,
                self.pos
            )

    # ####################################################################################################
    #
    # face_edges_by_vert
    #
    # ####################################################################################################
    
    def face_edges_by_vert(face, vert):
        "given a face, return all the edges that have the given vert index"
        r = []
        idx = vert.index if isinstance(vert, bmesh.types.BMVert) else vert
        #print("-------")
        for e in face.edges:
            for v in e.verts:
                #print(face, e, v, idx)
                if v.index == idx:
                    r.append(e.index)
        return(r)

    def __init__(self):
        pass


    # ####################################################################################################
    #
    # get_raycast
    #
    # ####################################################################################################


    def get_raycast(plane, terrain, vertices=None, DEBUG=False, LIMIT=None):

        obj_s=  bpy.data.objects[plane]
        mesh_s = obj_s.data    
        point_data = []
        pc = 0
        
        vertices = vertices if vertices else mesh_s.vertices

        for v in vertices:
        #for p in mesh_s.polygons:
    
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


            pc +=1
            if LIMIT and pc / 4 >= LIMIT:
                break

        print("ray_cast Total/Calculated Points/Polys (Quads) %d/%d/%d" % (len(mesh_s.vertices),len(point_data), int(pc / 4)))        
        return(point_data)


    # ####################################################################################################
    #
    # plane_to_vertex get the list of plane, create a mesh and iterate the vertex as planes
    #
    # ####################################################################################################

    def plane_to_vertex(plane):
        "get the vertices for plane, generate a list of all vertices as a face and calculate two median points at side"
        
        obj_s=  bpy.data.objects[plane]
        mesh_s = obj_s.data   

        pc = 0
        idx = 0
        MESH_VERTEX_LEN = int(len(mesh_s.vertices)/2)-1

        geom_edges = []
        geom_faces = []
        all_points = []
        for pc in range(MESH_VERTEX_LEN):
            
            # iterate about the number of quads
            
            edges = []
            if pc == 0:
                e_1 = [ mesh_s.vertices[0], mesh_s.vertices[1] ] # right
                e_2 = [ mesh_s.vertices[2], mesh_s.vertices[3] ] # left
                idx = 1
            elif pc == 1:
                e_1 = [ mesh_s.vertices[1], mesh_s.vertices[4] ]  # right     
                e_2 = [ mesh_s.vertices[3], mesh_s.vertices[5] ]  # left edge
                idx += 3
            else:
                e_1 = [ mesh_s.vertices[idx], mesh_s.vertices[idx+2] ]       # right 
                e_2 = [ mesh_s.vertices[idx+1], mesh_s.vertices[idx+3] ]     # left edge
                idx += 2

                
            # 0 is the right side
            # 1 is the left side 
            edges = [ e_1, e_2 ]  
            
            # calculate the center of the edges, so we have more points and avoid the "half split"
            # problem in the face selector


            c1 = BL_FLATTEN.DummyVector(e_1[0].co + (e_1[1].co - e_1[0].co)/2)
            c2 = BL_FLATTEN.DummyVector(e_2[0].co + (e_2[1].co - e_2[0].co)/2)
            c3 = BL_FLATTEN.DummyVector(e_1[0].co + (e_2[1].co - e_1[0].co)/2)
            c4 = BL_FLATTEN.DummyVector(e_2[0].co + (e_1[1].co - e_2[0].co)/2)

            all_points += [item for sublist in edges for item in sublist] + [c1, c2, c3, c4]
        
        return all_points



    # ####################################################################################################
    #
    # extend_terrain
    #
    # ####################################################################################################

    def extend_terrain(plane, terrain):
        """try to flatten a terrain, using the plane as reference plane must have ALL modifiers APPLIED"""

        EXTEND_TERRAIN = True
        TRIANGULATE = True
        EXTEND_DELETE_SELECTION = False

        DEBUG = False
        LIMIT = None
        MIN_FACE_DIST = 10

        BL_DEBUG.clear_marks()

        # build a table with the point and the face_idx, to speed up the thing
        # store the vertex only one time. use raycast to the Z down to check the
        # points, instead closest.
        # use side points, and center

        obj_s=  bpy.data.objects[plane]
        obj_t=  bpy.data.objects[terrain]
        vertices_to_raycast = BL_FLATTEN.plane_to_vertex(plane)

        point_data = BL_FLATTEN.get_raycast(plane, terrain, 
                                    vertices = vertices_to_raycast,
                                    DEBUG=DEBUG, LIMIT=LIMIT)
        
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
        # leave faces selected to process the
        # boundaries if needed

        #sel_verts = [v for v in bm.verts if v.select]
        #sel_edges = [e for e in bm.edges if e.select]
        sel_faces = [f for f in bm.faces if f.select]
        #geom = sel_verts + sel_edges + sel_faces
        geom = sel_faces
        
        if EXTEND_TERRAIN:
            ret_geom =  bmesh.ops.region_extend(bm, geom=geom,use_faces=True, use_face_step=False,use_contract=False)
            for f in ret_geom['geom']:
                if isinstance(f, bmesh.types.BMFace):
                    f.select = True

        if False:
            # subdivide too soon.
            sel_faces = [f for f in bm.faces if f.select]
            face_edges = []
            for f in sel_faces:
                for e in f.edges:
                    face_edges.append(e.index)
            face_edges = list(set(face_edges))
            face_edges_geom = [bm.edges[i] for i in face_edges]
            ret = bmesh.ops.subdivide_edges(bm, edges=face_edges_geom, cuts=2, use_grid_fill=True)
            for f in ret['geom']:
                if isinstance(f, bmesh.types.BMFace):
                    f.select = True

        if True:
            #triangulate
            geom = [f for f in bm.faces if f.select]
            ret_trig = bmesh.ops.triangulate(bm, faces=geom)        
            # select the new created triangles

            for f in ret_trig['faces']:
                    f.select = True
               


        # 0. at this point, faces are triangulated, and selected
 
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
                

        point_data = BL_FLATTEN.get_raycast(plane, terrain, 
                                    vertices = vertices_to_raycast,
                                    DEBUG=DEBUG, LIMIT=LIMIT)
        
        # at this point XD point_data has 
        # terrain_up/down, face_index, point, location)
        
        BL_DEBUG.clear_marks()

        faces_to_delete = {}
        
        ##selected_faces = [f for f in bm.faces if f.select]
        ##for f in bm.faces: f.select = False


        for item in point_data:
            terrain_down, index, point, location = item
            #print(terrain_down,index, point, location)
            #BL_DEBUG.set_mark( obj_t.matrix_world @ location.xyz, kind="PLAIN_AXES" )

            if index not in faces_to_delete.keys():
                faces_to_delete[index] = bm.faces[index]

            if True:
                # this calc takes TOO much in compute
                # select the bounding faces.
                local_faces =  bmesh.ops.region_extend(
                    bm, 
                    geom=[bm.faces[index]],
                    use_faces=True, 
                    use_face_step=False,
                    use_contract=False
                )

                # for each selected face, calculate the distance to the road point,
                # and mark for removal all the faces that meets the requerimient
                # distance = 10m
                for f in local_faces['geom']:
                    if isinstance(f, bmesh.types.BMFace) and f.index not in faces_to_delete.keys():
                        #center = BL_FLATTEN.DummyVector(f.calc_center_median())
                        for fv in f.verts:
                        #for fv in [center]:
                            vpw = obj_s.matrix_world @ point.co
                            vtw = obj_t.matrix_world @ fv.co
                            dist = (vpw.xy - vtw.xy).length
                            if dist < MIN_FACE_DIST:
                                print("Face too near: ",f.index,dist)
                                faces_to_delete[f.index] = bm.faces[f.index]

        ##for f in selected_faces: f.select = True

        # extend the selection for faces to be removed.

        EXTEND_DELETE_SELECTION = False
        if EXTEND_DELETE_SELECTION:

            for face in bm.faces: face.select = False
 
            for f in faces_to_delete.keys():
                bm.faces[f].select = True        

            #sel_verts = [v for v in bm.verts if v.select]
            #sel_edges = [e for e in bm.edges if e.select]
            sel_faces = [f for f in bm.faces if f.select]
            geom = sel_faces

            ret_geom =  bmesh.ops.region_extend(bm, geom=geom,use_faces=True, use_face_step=False,use_contract=False)
            for f in ret_geom['geom']:
                if isinstance(f, bmesh.types.BMFace):
                    faces_to_delete[f.index] = bm.faces[f.index]


        # delete the result faces        

        faces_to_delete = list(faces_to_delete.values())
        deleted_geom_edges = []
        for f in faces_to_delete:
            deleted_geom_edges += [e for e in f.edges]

        bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES_KEEP_BOUNDARY') # FACES_ONLY

        # this creates a subdivision of the inner vertex.
        if False:
            # subdivide existing edges
            keep_edges = []
            for edge in deleted_geom_edges:
                if edge.is_valid:
                    keep_edges.append(edge)

            new_edges = []
            geom_created = bmesh.ops.subdivide_edges(bm, edges=keep_edges, cuts=1, use_grid_fill=False)
            for item in geom_created['geom_split']:
                if isinstance(item, bmesh.types.BMEdge):
                    #item.select = True
                    #print(item.index)
                    new_edges.append(item)

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


    # ####################################################################################################
    #
    # add_geometry
    #
    # ####################################################################################################


    def add_geometry(plane, terrain):
      
        DEBUG = False
        LIMIT = None
        MIN_FACE_DIST = 10

        BL_DEBUG.clear_marks()

        # build a table with the point and the face_idx, to speed up the thing
        # store the vertex only one time. use raycast to the Z down to check the
        # points, instead closest.
        # use side points, and center

        obj_s=  bpy.data.objects[plane]
        mesh_s = obj_s.data
        obj_t=  bpy.data.objects[terrain]

        BL_DEBUG.clear_marks()

        bm = bmesh.new()
        bm.from_mesh(obj_t.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # here, I can flatten or move the thing
        #for f in  bm.faces:
        #    if f.select:
        #        for v in f.verts:
        #            bm.verts[v.index].co[2] += 5

        verts = []
        for v in mesh_s.vertices:
            verts.append(v.index)

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
        bm.verts.ensure_lookup_table()

        current_faces = [f.index for f in bm.faces if f.select]

        LIMIT = None
        pc = 0
        idx = 0
        GEOM_TO_DO = []
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
            #    BL_DEBUG.set_mark( obj_t.matrix_world @ e[0].co.xyz, kind='CUBE', scale=0.2 )
            #    BL_DEBUG.set_mark( obj_t.matrix_world @ e[1].co.xyz, kind='SPHERE', scale=0.2 )

            # calculate the nearest vertex for each point, get the minimum,
            # and build a face using it
            
            for edge_idx in range(len(edges)):
                edge =edges[edge_idx]       
                # for vertex0, vertex1. Pass the "left/right position"
                near_data = [ BL_FLATTEN.nearest(edge_idx), BL_FLATTEN.nearest(edge_idx) ] 
                bm.faces.ensure_lookup_table()
                for i in range(len(edge)):
                    # was sorround faces
                    for face_idx in current_faces: 
                        face = bm.faces[face_idx]

                        # get only faces for our "side"
                        A = obj_t.matrix_world @ edge[0].co
                        B = obj_t.matrix_world @ edge[1].co
                        C = obj_t.matrix_world @ face.calc_center_median()
                        normal_vec = Vector(B-A).cross(Vector(C-A))
                        normal_rl = normal_vec.z
                            
                        if near_data[i].pos == 'LEFT' and normal_rl < 0:
                            #print("badside left: normal: ", normal_rl, near_data[i].pos, idx) 
                            continue
                        if near_data[i].pos == 'RIGHT' and normal_rl > 0:
                            #print("badside right: normal: ", normal_rl, near_data[i].pos, idx) 
                            continue
                        
                        #print("normal: ", normal_rl, near_data[i].pos, idx, face_idx) 

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
                near = 0 
                if near_data[1].distance < near_data[0].distance:
                    near = 1
                print(near_data)

                #BL_DEBUG.set_mark( obj_t.matrix_world @ bm.faces[near_data[near].face].calc_center_median().xyz )
                #BL_DEBUG.set_mark( obj_t.matrix_world @ bm.verts[near_data[near].vertex].co.xyz, kind='PLAIN_AXES')

                # create a funky face here.
                if True:
                    if near_data[near].face != None:

                        new_face = [edge[0], edge[1], bm.verts[near_data[near].vertex]]
                        GEOM_TO_DO.append(new_face)
                
                # if first, or last, join vertex to end the cap
                
            if pc == 0 or pc == (MESH_VERTEX_LEN-1):
                
                if pc == 0:
                    # use first
                    edge_cap= [  edges[0][0], edges[1][0] ] # edge from right to left
                else:
                    # use last
                    edge_cap= [  edges[0][1], edges[1][1] ] # edge from right to left
                bmesh.ops.contextual_create(bm, geom= edge_cap)
                bm.edges.index_update()
                
            #if idx >= 8: break
            if LIMIT and pc >= LIMIT:
                break
            
        ## do the geom
        for new_face in GEOM_TO_DO:
            #print(new_face)
            #print(near)
            newf=bmesh.ops.contextual_create(bm, geom= new_face)
            bm.faces.index_update()
            bm.faces.ensure_lookup_table()
            
            for f in newf['faces']:
                if f.normal.z < 0:
                    bm.faces[f.index].normal_flip()        

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

    # ####################################################################################################
    #
    # fill_holes
    #
    # ####################################################################################################

    def fill_holes(terrain,sides=6):
        obj_t=  bpy.data.objects['Terrain']
        bm = bmesh.new()
        bm.from_mesh(obj_t.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bmesh.ops.holes_fill(bm, edges=bm.edges,sides=sides)
        bm.calc_loop_triangles()
        bm.to_mesh(obj_t.data)
        obj_t.data.update()  
        bm.free()        
        #return(("ERROR", "Can't found terrain below the curve"))
        return(("INFO", "Done"))

    # ####################################################################################################
    #
    # subdivide_nearest_faces
    #
    # ####################################################################################################

    def subdivide_nearest_faces(plane, terrain):
      
        DEBUG = False
        LIMIT = None
        MIN_FACE_DIST = 10

        BL_DEBUG.clear_marks()

        # build a table with the point and the face_idx, to speed up the thing
        # store the vertex only one time. use raycast to the Z down to check the
        # points, instead closest.
        # use side points, and center

        obj_s=  bpy.data.objects[plane]
        mesh_s = obj_s.data
        obj_t=  bpy.data.objects[terrain]

        BL_DEBUG.clear_marks()

        bm = bmesh.new()
        bm.from_mesh(obj_t.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # here, I can flatten or move the thing
        #for f in  bm.faces:
        #    if f.select:
        #        for v in f.verts:
        #            bm.verts[v.index].co[2] += 5

        verts = []
        mesh_vertex = []
        for v in mesh_s.vertices:
            verts.append(v.index)
            mesh_vertex.append(v)

        
        current_faces = [f.index for f in bm.faces if f.select]

        LIMIT = None
        pc = 0
        idx = 0
        MESH_VERTEX_LEN = int(len(mesh_vertex)/2)-1

        # select faces & edges to subdivide
        process_vertex = []

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
            #    BL_DEBUG.set_mark( obj_t.matrix_world @ e[0].co.xyz, kind='CUBE', scale=0.2 )
            #    BL_DEBUG.set_mark( obj_t.matrix_world @ e[1].co.xyz, kind='SPHERE', scale=0.2 )

            # calculate the nearest vertex for each point, get the minimum,
            # and build a face using it
            


            for edge_idx in range(len(edges)):
                edge =edges[edge_idx]       
                # for vertex0, vertex1. Pass the "left/right position"
                near_data = [ BL_FLATTEN.nearest(edge_idx), BL_FLATTEN.nearest(edge_idx) ] 
                bm.faces.ensure_lookup_table()
                for i in range(len(edge)):
                    # was sorround faces
                    for face_idx in current_faces: 
                        face = bm.faces[face_idx]

                        # get only faces for our "side"
                        # note that I use the Plane, not the projected ones.

                        A = obj_s.matrix_world @ edge[0].co
                        B = obj_s.matrix_world @ edge[1].co
                        C = obj_t.matrix_world @ face.calc_center_median()
                        normal_vec = Vector(B-A).cross(Vector(C-A))
                        normal_rl = normal_vec.z
                            
                        if near_data[i].pos == 'LEFT' and normal_rl < 0:
                            #print("badside left: normal: ", normal_rl, near_data[i].pos, idx) 
                            continue
                        if near_data[i].pos == 'RIGHT' and normal_rl > 0:
                            #print("badside right: normal: ", normal_rl, near_data[i].pos, idx) 
                            continue
                        
                        #print("normal: ", normal_rl, near_data[i].pos, idx, face_idx) 

                        # again, plane vs mesh
                        for facevertex in face.verts:
                            vpw = obj_s.matrix_world @ edge[i].co
                            vtw = obj_t.matrix_world @ facevertex.co                     
                            dist = (vpw.xyz - vtw.xyz).length

                            if dist < near_data[i].distance:
                                near_data[i].face = face_idx
                                near_data[i].vertex = facevertex.index
                                near_data[i].distance = dist
                                #near_data[i].edges = BL_FLATTEN.face_edges_by_vert(face, facevertex) 
                                # calculate the normal (first case, the we do the scond)

                    
                # select what vertex is near     
                near = 0 
                if near_data[1].distance < near_data[0].distance:
                    near = 1
                
                # now, build the array to work with. Store unique faces
                
               
              
                
                process_vertex.append(near_data[near].vertex)
                # if not vertex_idx in process_faces.keys():                    
                #     process_vertex[face_idx] =  [ vertex_idx ]
                # else:
                #     # now, store vertex and edge info.
                #     if not vertex_idx in process_faces[face_idx]:
                #         process_faces[face_idx].append(vertex_idx)

                #     else:
                #         # vertex exist on face, so test the edge.
                #         for edge_idx in near_data[near].edges:
                #             if not edge_idx in process_faces[face_idx][vertex_idx]:
                #                 process_faces[face_idx][vertex_idx].append(edge_idx)
                #             else:
                #                 # duplicate.
                #                 pass

                #BL_DEBUG.set_mark( obj_t.matrix_world @ bm.faces[near_data[near].face].calc_center_median().xyz )
                #BL_DEBUG.set_mark( obj_t.matrix_world @ bm.verts[near_data[near].vertex].co.xyz, kind='PLAIN_AXES')

                # here, I want only the face data, and vertex.
                # create a funky face here.
                
            #if idx >= 8: break
            if LIMIT and pc >= LIMIT:
                break

        # I get all the "nearest" vertex
        # look in current_faces faces all the edges, and 
        bm.faces.ensure_lookup_table()

        process_vertex = list(set(process_vertex))
        active_faces = [ bm.faces[i] for i in current_faces ]
        active_edges = [ ]
        for f in active_faces:
            active_edges += f.edges

        for edge in active_edges:
            # check that all the vertex are in process_vertex.
            vertex_inside = 0
            for v in edge.verts:
                if v.index in process_vertex:
                    vertex_inside += 1

            if vertex_inside == len(edge.verts):
                bmesh.ops.subdivide_edges(bm, edges=[edge], use_grid_fill=False, cuts=1)

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

    # ####################################################################################################
    #
    # move_points
    #
    # ####################################################################################################

    def move_points(plane, terrain):
      
        DEBUG = False
        LIMIT = None
        MIN_FACE_DIST = 10

        BL_DEBUG.clear_marks()

        # build a table with the point and the face_idx, to speed up the thing
        # store the vertex only one time. use raycast to the Z down to check the
        # points, instead closest.
        # use side points, and center

        obj_s=  bpy.data.objects[plane]
        mesh_s = obj_s.data
        obj_t=  bpy.data.objects[terrain]

        BL_DEBUG.clear_marks()

        bm = bmesh.new()
        bm.from_mesh(obj_t.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # here, I can flatten or move the thing
        #for f in  bm.faces:
        #    if f.select:
        #        for v in f.verts:
        #            bm.verts[v.index].co[2] += 5

        verts = []
        mesh_vertex = []
        for v in mesh_s.vertices:
            verts.append(v.index)
            mesh_vertex.append(v)

        current_faces = [f.index for f in bm.faces if f.select]

        LIMIT = None
        pc = 0
        idx = 0
        MESH_VERTEX_LEN = int(len(mesh_vertex)/2)-1

        # select faces & edges to subdivide
        process_point = {}

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
            #    BL_DEBUG.set_mark( obj_t.matrix_world @ e[0].co.xyz, kind='CUBE', scale=0.2 )
            #    BL_DEBUG.set_mark( obj_t.matrix_world @ e[1].co.xyz, kind='SPHERE', scale=0.2 )

            # calculate the nearest vertex for each point, get the minimum,
            # and build a face using it
            


            for edge_idx in range(len(edges)):
                edge =edges[edge_idx]       
                # for vertex0, vertex1. Pass the "left/right position"
                near_data = [ BL_FLATTEN.nearest(edge_idx), BL_FLATTEN.nearest(edge_idx) ] 
                bm.faces.ensure_lookup_table()
                for i in range(len(edge)):
                    # was sorround faces
                    for face_idx in current_faces: 
                        face = bm.faces[face_idx]

                        # get only faces for our "side"
                        # note that I use the Plane, not the projected ones.

                        A = obj_s.matrix_world @ edge[0].co
                        B = obj_s.matrix_world @ edge[1].co
                        C = obj_t.matrix_world @ face.calc_center_median()
                        normal_vec = Vector(B-A).cross(Vector(C-A))
                        normal_rl = normal_vec.z
                            
                        if near_data[i].pos == 'LEFT' and normal_rl < 0:
                            #print("badside left: normal: ", normal_rl, near_data[i].pos, idx) 
                            continue
                        if near_data[i].pos == 'RIGHT' and normal_rl > 0:
                            #print("badside right: normal: ", normal_rl, near_data[i].pos, idx) 
                            continue
                        
                        #print("normal: ", normal_rl, near_data[i].pos, idx, face_idx) 

                        # again, plane vs mesh
                        for facevertex in face.verts:
                            vpw = obj_s.matrix_world @ edge[i].co
                            vtw = obj_t.matrix_world @ facevertex.co                     
                            dist = (vpw.xyz - vtw.xyz).length

                            if dist < near_data[i].distance:
                                near_data[i].face = face_idx
                                near_data[i].vertex = facevertex.index
                                near_data[i].distance = dist
                                near_data[i].point = edge[i].index
                                # calculate the normal (first case, the we do the scond)

                    
                # select what vertex is near     
                near = 0 
                if near_data[1].distance < near_data[0].distance:
                    near = 1
                
                # now, build the array to work with. Store the points in the plane,
                # data about face,vertex and distance.
               
                process_point[near_data[i].point] =  (near_data[near].face, near_data[near].vertex, near_data[near].distance)
 
                
            #if idx >= 8: break
            if LIMIT and pc >= LIMIT:
                break

        # I get all the "nearest" vertex
        # look in current_faces faces all the edges, and 
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()



        for point_idx in process_point.keys():
            
            face_idx, vertex_idx, distance = process_point[point_idx]
            #
            # calculate how much I have to move the face, to put it "near the point"
            # "far" are moved less than "near". use a vector to move the face.
            #

            for v in bm.faces[face_idx].verts:
                vpw = obj_s.matrix_world @ mesh_s.vertices[point_idx].co
                vtw = obj_t.matrix_world @ v.co
                dist = (vpw.xy - vtw.xy).length
                height = vpw.z - vtw.z

                # some tunning in this parameters
                # too high and you break the geometry
                
                delta = dist - (dist *0.8)
                deltah = height*0.1

                direction = delta * (vpw.xy - vtw.xy)
                direction.resize_3d()
                direction = delta * direction.normalized()
                direction += Vector((0,0,deltah))
                local_dir = obj_t.matrix_world.inverted() @ direction

                print(distance, dist, delta, deltah, local_dir, direction)
                bmesh.ops.translate(bm, verts=[v], vec = direction)

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


# better do subdivide, then move

#BL_FLATTEN.extend_terrain('Plane','Terrain')
#BL_FLATTEN.subdivide_nearest_faces('Plane','Terrain')
#BL_FLATTEN.move_points('Plane','Terrain')
#BL_FLATTEN.add_geometry('Plane','Terrain')
#BL_FLATTEN.fill_holes('Terrain')
