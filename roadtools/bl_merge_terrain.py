#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# bl_merge_terrain.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# cut the hole in the mesh, then merge the road over the terrain.
#
# ############################################################################

import bpy
from mathutils import Vector, Matrix, Euler, kdtree
import bmesh
import sys

import bl_utils
import bl_road_utils


class BL_PROJECTOR:
    def __init__(self, plane, terrain, DEBUG=False, LIMIT=None, delay_raycast=True):

        self.time_it = bl_utils.TimeIt()

        self.DEBUG=DEBUG
        self.LIMIT=LIMIT

        self.plane = plane
        self.terrain = terrain
        self.obj_s  =  bpy.data.objects[plane]
        self.mesh_s = self.obj_s.data
        self.obj_t  =  bpy.data.objects[terrain]

        if not delay_raycast:
            self.do_the_raycast()

        # if the plane has any modifiers without apply, apply them
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        
        self.obj_s.select_set(True)
        bpy.context.view_layer.objects.active = self.obj_s

        for modifier in self.obj_s.modifiers:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            print("Applying modifier %s on %s" % (modifier.name, self.obj_s.name))

        self.obj_s.select_set(False)


        # copy the plane for later use. Copy OBJECT and MESH data.
        self.obj_copy = self.obj_s.copy()
        self.obj_copy.data = self.obj_s.data.copy()
        bpy.context.collection.objects.link(self.obj_copy)
        self.obj_copy.hide_set(True)

        #  do another copy, due the CUT deletes all the elements
        self.obj_copy_cut = self.obj_s.copy()
        self.obj_copy_cut.data = self.obj_s.data.copy()
        bpy.context.collection.objects.link(self.obj_copy_cut)
        self.obj_copy_cut.hide_set(True)


        # stop it
        self.time_it.stop()
        print("[t] __init__(): ", self.time_it)


    def do_the_raycast(self):

        self.time_it = bl_utils.TimeIt()
        r = bl_utils.plane_to_vertex(self.plane, calc_centers=True)

        self.plane_points = r['points']
        self.plane_edges = r['edges']

        self.raycast_points =  bl_utils.get_raycast(self.plane, self.terrain,
                                    vertices = self.plane_points,
                                    DEBUG=self.DEBUG, LIMIT=self.LIMIT)

        self.time_it.stop()
        print("[t] do_the_raycast(): ", self.time_it)

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
        self.time_it = bl_utils.TimeIt()

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
        return(("INFO", "Done"))

    def match_raycast_vertex(self, plane):

        self.time_it = bl_utils.TimeIt()

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

        plane = bpy.data.objects[plane]
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
            if dist > 0.2:
                self.bm.verts[index].co[0] = lp.x ## translated coords
                self.bm.verts[index].co[1] = lp.y ## translated coords
        self.update_bm(freeit=True)

        self.time_it.stop()
        print("[t] match_raycast_vertex(): ", self.time_it)
        return(("INFO", "Done"))

    def do_the_cut(self):
        """do the knife project, but first copy the object, hide it and restore
        it after in order to get the road working again.
        """
        self.time_it = bl_utils.TimeIt()
        self.obj_copy.hide_set(False)

        bl_road_utils.cut_road(self.obj_copy.name, 'Terrain')
        self.match_raycast_vertex(self.plane)

        # delete things but get name
        # remove the "original object (converted to vertices)"
        # and keep the copy version renamed as old.
        obj_name = self.obj_s.name
        obj_mesh_name = self.obj_s.data.name

        ##bpy.context.collection.objects.unlink(self.obj_copy)
        bpy.data.objects.remove(self.obj_s)
        bpy.data.objects.remove(self.obj_copy)
        
        self.obj_copy_cut.name = obj_name
        self.obj_copy_cut.data.name = obj_mesh_name
        self.obj_copy_cut.hide_set(False)

        self.time_it.stop()
        print("[t] do_the_cut(): ", self.time_it)


if False:
    ## apply the curve in the ROAD before doing anything else!

    tool = BL_PROJECTOR('Road_HiRes','Terrain')
    tool.delete_faces_from_plane()
    tool.do_the_raycast()
    tool.do_the_cut()


