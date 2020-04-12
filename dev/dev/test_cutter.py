# ############################################################################
#
# test_cutter.py
# (c) 11/04/2020 Juan M. Casillas
#
# ############################################################################

import bpy
from mathutils import Vector, Matrix, Euler, kdtree
from math import radians
import bmesh   
import sys

from bl_utils import BL_DEBUG,BL_UTILS,BL_ROAD_UTILS
from bl_tools import BL_TOOLS

class BL_HOLEMAKER:
    def __init__(self, plane, terrain, DEBUG=False, LIMIT=None):

        self.time_it = BL_TOOLS.TimeIt()

        self.DEBUG=DEBUG
        self.LIMIT=LIMIT

        self.plane = plane
        self.terrain = terrain
        self.obj_s  =  bpy.data.objects[plane]
        self.mesh_s = self.obj_s.data    
        self.obj_t  =  bpy.data.objects[terrain]

        r = BL_TOOLS.plane_to_vertex(self.plane, calc_centers=True)

        self.plane_points = r['points']
        self.plane_edges = r['edges']
        
        self.raycast_points =  BL_TOOLS.get_raycast(self.plane, self.terrain, 
                                    vertices = self.plane_points,
                                    DEBUG=self.DEBUG, LIMIT=self.LIMIT)
    
        self.bm = bmesh.new()
        self.bm.from_mesh(self.obj_t.data)
        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()

        self.time_it.stop()
        print("[t] __init__(): ", self.time_it)

    def plane_to_terrain_point(self, point):
        "translate a point in the plane to a point in the terrain (coords)"
        world_point = self.obj_s.matrix_world @ point
        local_point = self.obj_t.matrix_world.inverted() @ world_point
        return(local_point)


    def update_bm(self, freeit=False):
        "update the blender mesh"
             
        bpy.context.view_layer.update()
        self.bm.calc_loop_triangles()
        self.bm.to_mesh(self.obj_t.data)
        self.obj_t.data.update()  
        #bpy.ops.object.mode_set(mode = 'OBJECT')                 
        #bpy.ops.object.mode_set(mode = 'EDIT')   

        if freeit: self.bm.free()

    def unselect_all(self):
        for face in self.bm.faces: face.select = False
        for vert in self.bm.verts: vert.select = False
        for edge in self.bm.edges: edge.select = False
                
    # ####################################################################################################
    #
    # project the plane into the terrain, and do some optimizations to cut holes from the faces
    # (first of all, select all the faces that are below the plane)
    #
    # ####################################################################################################

    def do_holes(self):
        "get the plane, generate the info to raycast in the grid, select the matching faces"
        
        self.time_it = BL_TOOLS.TimeIt()

        EXTEND_SELECTION = True
        TRIANGULATE_FACES = False # True
        SUBDIVIDE_INNER_FACES = False
        EXTEND_DELETE_SELECTION = False
        SUBDIVIDE_INNER_EDGES = True
        CALCULATE_NEAR_FACES = True
        MIN_FACE_DIST = 3

        BL_DEBUG.clear_marks()

        # at this point XD point_data has 
        # terrain_up/down, face_index, point, location)
              
        self.unselect_all()

        self.selected_faces = []
        # select faces tracked
        for point in self.raycast_points:
            terrain_down, index, point, location = point
            self.bm.faces[index].select = True
            if self.bm.faces[index] not in self.selected_faces:
                self.selected_faces.append(self.bm.faces[index])
        
        if EXTEND_SELECTION:
            ret_geom =  bmesh.ops.region_extend(self.bm, 
                geom=self.selected_faces,
                use_faces=True, 
                use_face_step=False,
                use_contract=False)
            
            for f in ret_geom['geom']:
                if isinstance(f, bmesh.types.BMFace):
                    f.select = True
                    self.selected_faces.append(f)

        if SUBDIVIDE_INNER_FACES:
            # subdivide the inner faces
            #el_faces = [f for f in self.bm.faces if f.select]
            face_edges = []
            for f in self.selected_faces:
                for e in f.edges:
                    face_edges.append(e.index)
            face_edges = list(set(face_edges))
            face_edges_geom = [self.bm.edges[i] for i in face_edges]
            ret = bmesh.ops.subdivide_edges(self.bm, edges=face_edges_geom, cuts=2, use_grid_fill=True)
            for f in ret['geom']:
                if isinstance(f, bmesh.types.BMFace):
                    f.select = True
                    self.selected_faces.append(f)


        if TRIANGULATE_FACES:
            #triangulate
            geom = [f for f in self.bm.faces if f.select]
            ret_trig = bmesh.ops.triangulate(self.bm, faces=geom)        
            # select the new created triangles

            for f in ret_trig['faces']:
                    f.select = True
                    self.selected_faces.append(f)
               

        # 0. at this point, faces are triangulated, and selected
 
        ##############################################################
        #
        # 1. delete the faces recalculate again the faces
        # this version only deletes the nearest faces from the 
        # road. Maybe it's a little narrow
        # 
        ##############################################################
   
        self.update_bm()

        #self.bm.verts.ensure_lookup_table()
        #self.bm.edges.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()
        
        #        
        # I have to CHANGE to OBJECT in order to keep working on that
        # and update the structure. After change, return to edit and
        # keep working, it works.
        # 
              
                

        # after triangulate, or adding more faces, there's a need of recalculate again the affected
        # faces to make the hole

        self.raycast_points =  BL_TOOLS.get_raycast(self.plane, self.terrain, 
                                    vertices = self.plane_points,
                                    DEBUG=self.DEBUG, LIMIT=self.LIMIT)
        
        # at this point XD point_data has 
        # terrain_up/down, face_index, point, location)
        
        BL_DEBUG.clear_marks()

        faces_to_delete = {}

        for item in self.raycast_points:
            terrain_down, index, point, location = item
            #print(terrain_down,index, point, location)
            #BL_DEBUG.set_mark( obj_t.matrix_world @ location.xyz, kind="PLAIN_AXES" )

            if index not in faces_to_delete.keys():
                faces_to_delete[index] = self.bm.faces[index]

        if EXTEND_DELETE_SELECTION:

            for face in self.bm.faces: face.select = False
 
            for f in faces_to_delete.keys():
                self.bm.faces[f].select = True        

            #sel_verts = [v for v in self.bm.verts if v.select]
            #sel_edges = [e for e in self.bm.edges if e.select]
            selected_faces_local = [f for f in self.bm.faces if f.select]
            geom = selected_faces_local

            ret_geom =  bmesh.ops.region_extend(self.bm, 
                        geom=selected_faces_local,
                        use_faces=True, 
                        use_face_step=False,
                        use_contract=False)

            for f in ret_geom['geom']:
                if isinstance(f, bmesh.types.BMFace):
                    faces_to_delete[f.index] = self.bm.faces[f.index]


        # delete the result faces        

        faces_to_delete = list(faces_to_delete.values())
        deleted_geom_edges = []
        for f in faces_to_delete:
            deleted_geom_edges += [e for e in f.edges]

        bmesh.ops.delete(self.bm, geom=faces_to_delete, context='FACES_KEEP_BOUNDARY') # FACES_ONLY

        # remove deleted faces from the selected container
        #temp_faces = [f for f in self.selected_faces if f.is_valid]
        #self.selected_faces = temp_faces
        

        # this creates a subdivision of the inner vertex.
        if SUBDIVIDE_INNER_EDGES:
            # subdivide existing edges
            keep_edges = []
            for edge in deleted_geom_edges:
                if edge.is_valid:
                    keep_edges.append(edge)

            self.inner_edges = []
            print("Inner edges: %d" % (len(keep_edges)*2))

            geom_created = bmesh.ops.subdivide_edges(self.bm, edges=keep_edges, cuts=1, use_grid_fill=True)
            for item in geom_created['geom_split']:
                if isinstance(item, bmesh.types.BMVert):
                    pass
                    #item.select = True
                    #print(item.index)
                    #self.inner_edges.append(item)                
                if isinstance(item, bmesh.types.BMEdge):
                    #item.select = True
                    #print(item.index)
                    self.inner_edges.append(item)
                if isinstance(item, bmesh.types.BMFace):
                    #item.select = True
                    print(item.index)
                    item.select = True
                    self.selected_faces.append(item)
           

            print("Inner edges Subdivide: %d" % (len(self.inner_edges)*2) )

        self.update_bm()

        # create a KD tree for faces. add the center, and get only faces that are "near" in radious

        if CALCULATE_NEAR_FACES:

            valid_faces = [face for face in self.selected_faces if face.is_valid]
            kd = kdtree.KDTree(len(valid_faces))
            for face in valid_faces:
                kd.insert(face.calc_center_median(), face.index)
            kd.balance()

            faces_to_delete = {}
            verts_to_delete = {}
            edges_to_delete = {}
            self.bm.faces.ensure_lookup_table()
            self.bm.verts.ensure_lookup_table()
            self.bm.edges.ensure_lookup_table()

            for item in self.raycast_points:
                terrain_down, index, point, location = item
                
                local_faces = []
                local_point = self.plane_to_terrain_point(point.co)
           
                for (co, index, dist) in kd.find_range(local_point, 200):
                    #print("face_local", index)
                    local_faces.append(self.bm.faces[index])

                for f in local_faces:
                    # check for deleted faces!
                    if f.is_valid and f.index not in faces_to_delete.keys():
                        #center = BL_FLATTEN.DummyVector(f.calc_center_median())
                        for fv in f.verts:
                        #for fv in [center]:
                            vpw = self.obj_s.matrix_world @ point.co
                            vtw = self.obj_t.matrix_world @ fv.co
                            dist = (vpw.xy - vtw.xy).length
                            if dist < MIN_FACE_DIST:
                                #print("Face too near: ",f.index,dist)
                                faces_to_delete[f.index] = self.bm.faces[f.index]        
                                for e in f.edges:
                                    edges_to_delete[e.index] = self.bm.edges[e.index]
                                for v in f.verts:
                                    verts_to_delete[v.index] = self.bm.verts[v.index]

            faces_to_delete = list(faces_to_delete.values())
            verts_to_delete = list(verts_to_delete.values())
            edges_to_delete = list(edges_to_delete.values())
            # FACES_ONLY
            bmesh.ops.delete(self.bm, geom=verts_to_delete + edges_to_delete + faces_to_delete, context='FACES') 

        self.update_bm()

        # now, just select the faces that are not select, but are in the edges.
        # also select all the vertex in the keep edges that are not selected by default.

        for e in self.inner_edges:
            if not e.is_valid:
                continue
            for v in e.verts: 
                if not v.is_valid: 
                    continue
                v.select = True
                for f in v.link_faces:
                    f.select = True
                    if f not in self.selected_faces:
                        self.selected_faces.append(f)

        # select vertex that are in a boundary (internal)
        self.selected_vertex = []
        for e in self.bm.edges:
            if e.is_valid and e.is_boundary:
                for v in e.verts:
                    self.selected_vertex.append(v)

        ##############################################################
        #
        # End
        # update the meshes
        # 
        ##############################################################  

        self.time_it.stop()
        self.update_bm()

        print("[t] do_holes(): ", self.time_it)

        
        #return(("ERROR", "Can't found terrain below the curve"))
        return(("INFO", "Done"))        


    # ####################################################################################################
    #
    # project_vertex
    # project the plane points into the mesh. 
    #
    # ####################################################################################################

    def project_vertex(self):
        
        self.time_it = BL_TOOLS.TimeIt()
        
        BL_DEBUG.clear_marks()
        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()

        # here, I can flatten or move the thing
        #for f in  bm.faces:
        #    if f.select:
        #        for v in f.verts:
        #            bm.verts[v.index].co[2] += 5


        self.mesh_vertex = []
        verts = []
        pc = 0
        for edge in self.plane_edges:
            e_1 = edge[0]    
            e_2 = edge[1]
            #verts += [v.index for v in e_1] + [v.index for v in e_2]

            #print(e_1,e_2)
            mesh_e1 = []
            for e in e_1:
                local_point = self.plane_to_terrain_point(e.co)
                #set_mark( obj_s.matrix_world @ obj_s.data.vertices[v_idx].co, kind='PLAIN_AXES', scale=0.2 )
                #set_mark( obj_t.matrix_world @ local_point,  scale=0.2 )
                vnew = self.bm.verts.new( local_point )
                mesh_e1.append(vnew)

            mesh_e2 = []
            for e in e_2:
                local_point = self.plane_to_terrain_point(e.co)
                #set_mark( obj_s.matrix_world @ obj_s.data.vertices[v_idx].co, kind='PLAIN_AXES', scale=0.2 )
                #set_mark( obj_t.matrix_world @ local_point,  scale=0.2 )
                vnew = self.bm.verts.new( local_point )
                mesh_e2.append(vnew)

            self.mesh_vertex.append( [ mesh_e1, mesh_e2 ] )

            if pc == 0 or pc == len(self.plane_edges)-1:
                if pc == 0:
                    # use first
                    edge_cap= [  mesh_e1[0], mesh_e2[0] ] # edge from right to left
                else:
                    # use last
                    edge_cap= [  mesh_e1[1], mesh_e2[1] ] # edge from right to left
                bmesh.ops.contextual_create(self.bm, geom= edge_cap)
                self.bm.edges.index_update()

            pc+=1


        # update the index of the new created verts. WTF ???
        self.update_bm()
        self.time_it.stop()
        print("[t] add_geometry(): ", self.time_it)
        #return(("ERROR", "Can't found terrain below the curve"))
        return(("INFO", "Done"))

    # ####################################################################################################
    #
    # add_geometry
    # try to match the vertex in the mesh with the new created vertex
    #
    # ####################################################################################################

    def add_geometry(self):
        
        DEBUG = False
        self.time_it = BL_TOOLS.TimeIt()
        BL_DEBUG.clear_marks()
        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()
        
        # create a kd tree with the vertex positions



        vertex = []
        for v in self.selected_vertex:
            if v.is_valid:
                vertex.append(v.index)
        
        # remove dupes
        vertex = list(set(vertex))

        kd = kdtree.KDTree(len(vertex))
        for v in vertex:
            ##BL_DEBUG.set_mark(self.bm.verts[v].co,kind="CUBE",scale=0.2)
            kd.insert(self.bm.verts[v].co, v)
        kd.balance()

        def nearest_points(kd, edge, v0, side, Nitems=7):
            nearest = []
            for (co, index, dist) in kd.find_n(v0, Nitems):
                # calculate normals
                A = self.obj_t.matrix_world @ edge[0].co
                B = self.obj_t.matrix_world @ edge[1].co
                C = self.obj_t.matrix_world @ co
                normal_vec = Vector(B-A).cross(Vector(C-A))
                normal_rl = normal_vec.z
                if normal_rl < 0.0 and side.upper() == 'RIGHT':
                    nearest.append( (co, index, dist) )
                if normal_rl > 0.0 and side.upper() == 'LEFT':
                    nearest.append( (co, index, dist) )
            return(nearest)

        # iterate my vertex, and find the nearest point my vertex

        side_keys = { 0: 'right', 1: 'left', 'right': 0, 'left': 1}
        
        count = 0
        B = C = None

        for plane in self.mesh_vertex:
            print(plane)
            nearest = {}
            # calculate the nearest point for each point, for each side
            for i in range(len(plane)):
                if i == 0:
                    #right ARROWS->CUBES
                    kind = 'ARROWS'
                else:
                    #left AXES->SPHERES
                    kind = 'PLAIN_AXES'
                #BL_DEBUG.set_mark(self.obj_t.matrix_world @ plane[i][0].co,kind=kind)
                #BL_DEBUG.set_mark(self.obj_t.matrix_world @ plane[i][1].co,kind=kind)

                nearest[side_keys[i]] = [   
                    nearest_points(kd, plane[i], self.obj_t.matrix_world @ plane[i][0].co, side_keys[i]),
                    nearest_points(kd, plane[i], self.obj_t.matrix_world @ plane[i][1].co, side_keys[i]) 
                ]

            A = plane[0][1]
            D = plane[0][0]

            # lower point
            if not C:   
                _,C,_ = nearest['right'][0][0]
                _,B,_ = nearest['right'][1][0]
                if B == C:
                    _,B,_ = nearest['right'][1][1]

            else:
                C = B
                _,B,_ = nearest['right'][1][0]
                if B == C:
                    _,B,_ = nearest['right'][1][1]

            print(A,B,C,D)
            # if not B in used_points.keys(): used_points[B] = 1
            # if not C in used_points.keys(): used_points[C] = 1

            # if B in used_points.keys() and used_points[B] < 2:
            #      used_points[B] += 1
            # else:
            #     B = None

            # if C in used_points.keys() and used_points[C] < 2:
            #     used_points[C] += 1
            # else:
            #     C = None
            
          

            # first point: nearest from top, and in nearest of bottom one.

            a = nearest['right'][0]
            print("r0-")
            for i in a:
                co,idx,dist = i
                print(co,idx,dist)
                DEBUG and BL_DEBUG.set_mark(co,kind="ARROWS")

            a = nearest['right'][1]
            print("r1-")            
            for i in a:
                co,idx,dist = i
                print(co,idx,dist)
                DEBUG and BL_DEBUG.set_mark(co,kind="ARROWS")

            a = nearest['left'][0]
            print("l0-")            
            for i in a:
                co,idx,dist = i
                print(co,idx,dist)
                DEBUG and BL_DEBUG.set_mark(co,kind="PLAIN_AXES")

            a = nearest['left'][1]
            print("l1-")
            for i in a:
                co,idx,dist = i
                print(co,idx,dist)
                DEBUG and BL_DEBUG.set_mark(co,kind="PLAIN_AXES")


            ## right side

            # top_vertex_list = []
            # for _,idx,_ in nearest['right'][1]:
            #     top_vertex_list.append(idx)

            # bottom_vertex_list = []
            # for _,idx,_ in nearest['right'][0]:
            #     bottom_vertex_list.append(idx)
            
            # # default, first item
            # # bottom
            
            # pB = None
            # get_next = False
            # _,pA,_ = nearest['right'][0][0]
            # for data in nearest['right'][0]:
            #     co,idx,dist = data
            #     if get_next:
            #         pA = idx
            #         break
            #     if idx in top_vertex_list and not pB:
            #         pB = pA
            #         get_next = True
  
            # if not pB:
            #     _,pB,_ = nearest['right'][1][0]
            #     for data in nearest['right'][1]:
            #         co,idx,dist = data
            #         pB = idx
            #         break

            if B and C:
                pBv = self.bm.verts[B]
                pCv = self.bm.verts[C]
                DEBUG and BL_DEBUG.set_mark(pBv.co,kind="CUBE")
                DEBUG and BL_DEBUG.set_mark(pCv.co,kind="CUBE")

                bmesh.ops.contextual_create(self.bm, geom=[A, pBv, pCv, D])
                self.bm.faces.index_update()            

            # ## left side
            # top_vertex_list = []
            # for i in nearest['left'][1]:
            #     co,idx,dist = i
            #     top_vertex_list.append(idx)

            # bottom_vertex_list = []
            # for i in nearest['left'][0]:
            #     co,idx,dist = i
            #     bottom_vertex_list.append(idx)

            # # default, first item
            # # bottom
            
            # pD = None
            # get_next = False
            # _,pC,_ = nearest['left'][0][0]
            # for data in nearest['left'][0]:
            #     co,idx,dist = data
            #     if get_next:
            #         pC = idx
            #         break
            #     if idx in top_vertex_list and not pD:
            #         pD = pC
            #         get_next = True
  
            # if not pD:
            #     _,pD,_ = nearest['left'][1][0]
            #     for data in nearest['left'][1]:
            #         co,idx,dist = data
            #         pD = idx
            #         break
        
            # pCv = self.bm.verts[pC]
            # pDv = self.bm.verts[pD]
            # DEBUG and BL_DEBUG.set_mark(pCv.co,kind="SPHERE")
            # DEBUG and BL_DEBUG.set_mark(pDv.co,kind="SPHERE")

            # if plane[0][1] != pBv and  pBv != pAv and pAv != plane[0][0]:
            #     bmesh.ops.contextual_create(self.bm, geom=[plane[0][0], pAv, pBv, plane[0][1]])
            #     self.bm.faces.index_update()
            # if plane[1][1] != pCv and  pCv != pDv and pDv != plane[1][0]:
            #     bmesh.ops.contextual_create(self.bm, geom=[plane[1][1], plane[1][0], pDv, pCv])
            #     self.bm.faces.index_update()
            

            # do just ones
            count +=1
            if count > 5:
                break



      # update the index of the new created verts. WTF ???
        self.update_bm()
        self.time_it.stop()
        print("[t] add_geometry(): ", self.time_it)
        #return(("ERROR", "Can't found terrain below the curve"))
        return(("INFO", "Done"))


    def add_geometry_edge(self):

        "try to match near edges"

        def edge_median(edge):
                v0,v1 = edge.verts
                median = v0.co + ((v0.co-v1.co)/2.0)
                return(median)

        def nearest_points(kd, edge, v0, side, Nitems=7):
            nearest = []
            for (co, index, dist) in kd.find_n(v0, Nitems):
                # calculate normals
                A = self.obj_t.matrix_world @ edge[0].co
                B = self.obj_t.matrix_world @ edge[1].co
                C = self.obj_t.matrix_world @ co
                normal_vec = Vector(B-A).cross(Vector(C-A))
                normal_rl = normal_vec.z
                if normal_rl < 0.0 and side.upper() == 'RIGHT':
                    nearest.append( (co, index, dist) )
                if normal_rl > 0.0 and side.upper() == 'LEFT':
                    nearest.append( (co, index, dist) )
            return(nearest)

        def nearest_edge(kd, edge, side, Nitems=7):
            
            nearest = []
            median = edge_median(edge)

            for (co, index, dist) in kd.find_n(self.obj_t.matrix_world @ median, Nitems):
                # calculate normals
                A = self.obj_t.matrix_world @ edge.verts[0].co
                B = self.obj_t.matrix_world @ edge.verts[1].co
                C = self.obj_t.matrix_world @ co
                normal_vec = Vector(B-A).cross(Vector(C-A))
                normal_rl = normal_vec.z
                if normal_rl < 0.0 and side.upper() == 'RIGHT':
                    nearest.append( (co, index, dist) )
                if normal_rl > 0.0 and side.upper() == 'LEFT':
                    nearest.append( (co, index, dist) )
            return(nearest)

        DEBUG = False
        self.time_it = BL_TOOLS.TimeIt()
        BL_DEBUG.clear_marks()
        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()
        
        # create a kd tree with the median edge positions.

        median_edges = []
        for edge in self.inner_edges:
            if edge.is_valid and edge.is_boundary:
                median = edge_median(edge)
                median_edges.append( (median, edge.index) )
        
        kd = kdtree.KDTree(len(median_edges))
        for median,idx in median_edges:
            kd.insert(median, idx)
        kd.balance()

        # iterate my vertex, and find the nearest point my vertex

        side_keys = { 0: 'right', 1: 'left', 'right': 0, 'left': 1}
        
        count = 0
        for plane in self.mesh_vertex:
            print("plane", plane)
            nearest = {}
            # calculate the nearest point for each point, for each side
            for i in range(len(plane)):
                if i == 0:
                    #right ARROWS->CUBES
                    kind = 'ARROWS'
                else:
                    #left AXES->SPHERES
                    kind = 'PLAIN_AXES'
          

                #nearest[side_keys[i]] = [   
                #    nearest_points(kd, plane[i], self.obj_t.matrix_world @ plane[i][0].co, side_keys[i]),
                #    nearest_points(kd, plane[i], self.obj_t.matrix_world @ plane[i][1].co, side_keys[i]) 
                #]
                
                # create the working edge
                edge = [ plane[i][0], plane[i][1] ] 
                

                ret_geom = bmesh.ops.contextual_create(self.bm, geom= edge)
                self.bm.edges.index_update()
                self.update_bm()
                for f in ret_geom['edges']:
                    if isinstance(f, bmesh.types.BMEdge):
                        edge = f

                median = edge_median(edge)
                BL_DEBUG.set_mark(self.obj_t.matrix_world @ median,kind='CUBE') ## mesh edge

                n_edge = nearest_edge(kd, edge, side_keys[i])

                
              
                # build the face, rebuild the tree
                co,idx,_ = n_edge[0]
                self.bm.verts.ensure_lookup_table()
                self.bm.edges.ensure_lookup_table()
                self.bm.faces.ensure_lookup_table()

                BL_DEBUG.set_mark(self.obj_t.matrix_world @ co,kind='SPHERE') ## found edge



                #ret_geom = bmesh.ops.contextual_create(self.bm, geom= [edge, self.bm.edges[idx]])
                self.bm.edges.index_update()
                self.update_bm()
                # remove the edge from the table.

                edges_tmp = []
                for edge in self.inner_edges:
                    if edge.is_valid and edge.index != idx:
                        edges_tmp.append(edge)

                self.inner_edges = edges_tmp
                median_edges = []
                for edge in self.inner_edges:
                    if edge.is_valid and edge.is_boundary:
                        median = edge_median(edge)
                        median_edges.append( (median, edge.index) )
                
                kd = kdtree.KDTree(len(median_edges))
                for median,idx in median_edges:
                    kd.insert(median, idx)
                kd.balance()                
        
            # do just ones
            count +=1
            if count >=1:
                break



      # update the index of the new created verts. WTF ???
        self.update_bm()
        self.time_it.stop()
        print("[t] add_geometry_edges(): ", self.time_it)
        #return(("ERROR", "Can't found terrain below the curve"))
        return(("INFO", "Done"))



    def fill_holes(self):
        DEBUG = False
        self.time_it = BL_TOOLS.TimeIt()
        BL_DEBUG.clear_marks()
        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()

        boundary_edges = [edge for edge in self.bm.edges if edge.is_boundary]
        print("%d boundary edge founds" % len(boundary_edges))

        self.update_bm()
        self.time_it.stop()
        print("[t] add_geometry(): ", self.time_it)
        #return(("ERROR", "Can't found terrain below the curve"))
        return(("INFO", "Done"))













if True:
    tool = BL_HOLEMAKER('Plane','Terrain')
    tool.do_holes()
    tool.project_vertex()
    tool.add_geometry_edge()
    #tool.fill_holes()

    tool.update_bm(freeit=True)
    