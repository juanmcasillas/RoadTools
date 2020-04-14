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

    # ####################################################################################################
    #
    # extend_terrain
    #
    # ####################################################################################################

    def flatten_terrain(plane, terrain):
        """try to flatten a terrain, using the plane as reference plane must have ALL modifiers APPLIED"""

        EXTEND_TERRAIN = True

        # build a table with the point and the face_idx, to speed up the thing
        # store the vertex only one time. use raycast to the Z down to check the
        # points, instead closest.
        # use side points, and center

        obj_s=  bpy.data.objects[plane]
        obj_t=  bpy.data.objects[terrain]
        vertices_to_raycast = bl_utils.plane_to_vertex(plane)

        point_data = bl_utils.get_raycast(plane, terrain,
                                    vertices = vertices_to_raycast,
                                    DEBUG=DEBUG, LIMIT=LIMIT)


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

        if EXTEND_TERRAIN:
            ret_geom =  bmesh.ops.region_extend(bm, geom=sel_faces,use_faces=True, use_face_step=False,use_contract=False)
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

        bpy.context.view_layer.update()
        bm.calc_loop_triangles()
        bm.to_mesh(obj_t.data)
        obj_t.data.update()
        bm.free()

        #return(("ERROR", "Can't found terrain below the curve"))
        return(("INFO", "Done"))







#BL_FLATTEN.flatten_terrain('Plane','Terrain')
