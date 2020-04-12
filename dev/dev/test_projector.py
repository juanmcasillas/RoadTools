# ############################################################################
#
# test_projector.py
# (c) 11/04/2020 Juan M. Casillas
#
# THIS is the real working copy for Road Projection into a surface
# 
#
# ############################################################################

import bpy
from mathutils import Vector, Matrix, Euler, kdtree
from math import radians
import bmesh   
import sys

from bl_utils import BL_DEBUG,BL_UTILS,BL_ROAD_UTILS
from bl_tools import BL_TOOLS

class BL_PROJECTOR:
    def __init__(self, plane, terrain, DEBUG=False, LIMIT=None, delay_raycast=False):

        self.time_it = BL_TOOLS.TimeIt()

        self.DEBUG=DEBUG
        self.LIMIT=LIMIT

        self.plane = plane
        self.terrain = terrain
        self.obj_s  =  bpy.data.objects[plane]
        self.mesh_s = self.obj_s.data    
        self.obj_t  =  bpy.data.objects[terrain]

        if not delay_raycast:
            self.do_the_raycast()



        self.time_it.stop()
        print("[t] __init__(): ", self.time_it)

    def do_the_raycast(self):
        r = BL_TOOLS.plane_to_vertex(self.plane, calc_centers=True)

        self.plane_points = r['points']
        self.plane_edges = r['edges']
        
        self.raycast_points =  BL_TOOLS.get_raycast(self.plane, self.terrain, 
                                    vertices = self.plane_points,
                                    DEBUG=self.DEBUG, LIMIT=self.LIMIT)


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


    def delete_faces_from_plane(self):

        "this deletes the faces and the edges for a plane, and leaves only the verts, ready to work with raycast"
        DEBUG = False
        self.time_it = BL_TOOLS.TimeIt()

        bm = bmesh.new()
        bm.from_mesh(self.obj_s.data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        
        bmesh.ops.delete(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), context='EDGES_FACES') 
        
        bpy.context.view_layer.update()
        bm.calc_loop_triangles()
        bm.to_mesh(self.obj_s.data)
        self.obj_s.data.update()  
        bm.free()

        self.time_it.stop()
        print("[t] add_geometry(): ", self.time_it)
        #return(("ERROR", "Can't found terrain below the curve"))
        return(("INFO", "Done"))

    def match_raycast_vertex(self):
        self.bm = bmesh.new()
        self.bm.from_mesh(self.obj_t.data)
        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()
        
        bmesh.ops.remove_doubles(self.bm, verts=list(self.bm.verts),dist=3)

        size = len(self.bm.verts)
        kd = kdtree.KDTree(size)

        for i, vtx in enumerate(self.bm.verts):
            v = Vector((vtx.co.x, vtx.co.y, 0.0))
            kd.insert( v, i)
        kd.balance()

        plane = bpy.data.objects['Plane.001']
        self.bm.verts.ensure_lookup_table()
        self.bm.edges.ensure_lookup_table()
        self.bm.faces.ensure_lookup_table()

        for p in plane.data.vertices:
            wp = plane.matrix_world @ p.co
            lp = self.obj_t.matrix_world.inverted() @ wp

            #BL_DEBUG.set_mark(self.obj_t.matrix_world @ location)
            #BL_DEBUG.set_mark(plane.matrix_world @ p.co)
            location = Vector((lp.x, lp.y, 0.0))
            co, index, dist = kd.find( location)  # dist is the distance
            #print("Found", co, index, dist)
            #BL_DEBUG.set_mark(self.obj_t.matrix_world @ co)
            self.bm.verts[index].co[2] = lp.z ## translated coords

            # tune this. There are more space (2-4m)
            if dist > 0.4:
                self.bm.verts[index].co[0] = lp.x ## translated coords
                self.bm.verts[index].co[1] = lp.y ## translated coords
        self.update_bm(freeit=True)



if True:
    tool = BL_PROJECTOR('Plane','Terrain')
    BL_ROAD_UTILS.cut_road('Plane','Terrain')
    tool.match_raycast_vertex()
