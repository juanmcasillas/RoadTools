# ############################################################################
#
# bl_tools.py
# Some helpers to create the raycast points from a plane, etc
# (c) 11/04/2020 Juan M. Casillas
#
# ############################################################################

import bpy
from mathutils import Vector, Matrix, Euler
from math import radians
import bmesh   
import sys
import time


from bl_utils import BL_DEBUG


class BL_TOOLS:

    class TimeIt:
        def __init__(self):
            self.t_start = time.time()
            self.t_stop = None

        def stop(self):
            self.t_stop = time.time()
            self.t_delta = self.t_stop - self.t_start

        def convert(self, seconds): 
            min, sec = divmod(seconds, 60) 
            hour, min = divmod(min, 60) 
            return "%d:%02d:%03.2f" % (hour, min, sec) 

        def __repr__(self):
            s_start = time.strftime('%H:%M:%S', time.localtime(self.t_start))
            s_stop = time.strftime('%H:%M:%S', time.localtime(self.t_stop))
            s_delta = self.convert(self.t_delta)
            s = "start=%s stop=%s delta=%s" % (s_start, s_stop, s_delta)
            return(s)


    class DummyVector:
        "to add the .co attribute and work as a vertex"
        def __init__(self,v):
            self.co = v

    class nearest:
        "stores the nearest data from a point to a vertex"
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

        print("ray_cast: total_points %d" % (len(mesh_s.vertices)))
        return(point_data)

    # ####################################################################################################
    #
    # plane_to_vertex get the list of plane, create a mesh and iterate the vertex as planes
    #
    # ####################################################################################################

    def plane_to_vertex(plane, calc_centers=False):
        "get the vertices for plane, generate a list of all vertices as a face and calculate two median points at side"
        
        obj_s=  bpy.data.objects[plane]
        mesh_s = obj_s.data   

        pc = 0
        idx = 0
        MESH_VERTEX_LEN = int(len(mesh_s.vertices)/2)-1

        all_edges = []
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
            all_edges.append(edges)
            
            # calculate the center of the edges, so we have more points and avoid the "half split"
            # problem in the face selector

            all_points += [item for sublist in edges for item in sublist]
            if calc_centers:
                c1 = BL_TOOLS.DummyVector(e_1[0].co + (e_1[1].co - e_1[0].co)/2) # right median
                c2 = BL_TOOLS.DummyVector(e_2[0].co + (e_2[1].co - e_2[0].co)/2) # left median
                #c3 = BL_TOOLS.DummyVector(e_1[0].co + (e_2[1].co - e_1[0].co)/2) # avg center
                #c4 = BL_TOOLS.DummyVector(e_2[0].co + (e_1[1].co - e_2[0].co)/2) # avg center
                #c5 = BL_TOOLS.DummyVector(e_2[1].co + (e_2[1].co - e_1[1].co)/2) # top median
                #c6 = BL_TOOLS.DummyVector(e_2[0].co + (e_2[0].co - e_1[0].co)/2) # bottom median
                #all_points += [c1, c2, c3, c4, c5, c6]
                all_points += [c1, c2]
        
        return { 'points': all_points, 'edges': all_edges }
