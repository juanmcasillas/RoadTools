# ############################################################################
#
# test_cutter.py
# (c) 11/04/2020 Juan M. Casillas
#
# ############################################################################

import bpy
from mathutils import Vector, Matrix, Euler
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

            new_edges = []
            print("Inner edges: %d" % (len(keep_edges)*2))

            geom_created = bmesh.ops.subdivide_edges(self.bm, edges=keep_edges, cuts=1, use_grid_fill=True)
            for item in geom_created['geom_split']:
                if isinstance(item, bmesh.types.BMEdge):
                    #item.select = True
                    #print(item.index)
                    new_edges.append(item)
                if isinstance(item, bmesh.types.BMFace):
                    #item.select = True
                    print(item.index)
                    item.select = True
                    self.selected_faces.append(item)
           

            print("Inner edges Subdivide: %d" % (len(new_edges)*2) )

        self.update_bm()

        if False:
            faces_to_delete = {}
            verts_to_delete = {}
            edges_to_delete = {}
            self.bm.faces.ensure_lookup_table()
            self.bm.verts.ensure_lookup_table()
            self.bm.edges.ensure_lookup_table()

            for item in self.raycast_points:
                terrain_down, index, point, location = item

                for f in self.selected_faces:
                    # check for deleted faces!
                    if isinstance(f, bmesh.types.BMFace) and f.is_valid and f.index not in faces_to_delete.keys():
                        #center = BL_FLATTEN.DummyVector(f.calc_center_median())
                        for fv in f.verts:
                        #for fv in [center]:
                            vpw = self.obj_s.matrix_world @ point.co
                            vtw = self.obj_t.matrix_world @ fv.co
                            dist = (vpw.xy - vtw.xy).length
                            if dist < MIN_FACE_DIST:
                                print("Face too near: ",f.index,dist)
                                faces_to_delete[f.index] = self.bm.faces[f.index]        
                                for e in f.edges:
                                    edges_to_delete[e.index] = self.bm.edges[e.index]
                                for v in f.verts:
                                    verts_to_delete[v.index] = self.bm.verts[v.index]

            faces_to_delete = list(faces_to_delete.values())
            verts_to_delete = list(verts_to_delete.values())
            edges_to_delete = list(edges_to_delete.values())
            bmesh.ops.delete(self.bm, geom=verts_to_delete + edges_to_delete + faces_to_delete, context='FACES') # FACES_ONLY

        self.update_bm()

        # now, just select the faces that are not select, but are in the edges.
        # also select all the vertex in the keep edges that are not selected by default.

        for e in new_edges:
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
    # add_geometry
    # project the plane points into the mesh. 
    #
    # ####################################################################################################

    def add_geometry(self):
        
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
        for edge in self.plane_edges:
            e_1 = edge[0]    
            e_2 = edge[1]
            verts += [v.index for v in e_1] + [v.index for v in e_2]

            #print(e_1,e_2)
        for v_idx in verts:
            world_point = self.obj_s.matrix_world @ self.mesh_s.vertices[v_idx].co
            local_point = self.obj_t.matrix_world.inverted() @ world_point

            #set_mark( obj_s.matrix_world @ obj_s.data.vertices[v_idx].co, kind='PLAIN_AXES', scale=0.2 )
            #set_mark( obj_t.matrix_world @ local_point,  scale=0.2 )
            
            vnew = self.bm.verts.new( local_point )
            self.mesh_vertex.append(vnew)

        # update the index of the new created verts. WTF ???
        self.update_bm()
        self.time_it.stop()
        print("[t] add_geometry(): ", self.time_it)
        #return(("ERROR", "Can't found terrain below the curve"))
        return(("INFO", "Done"))



if True:
    tool = BL_HOLEMAKER('Plane','Terrain')
    tool.do_holes()
    tool.add_geometry()
    tool.update_bm(freeit=True)
    