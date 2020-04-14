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

class BL_FLATTEN:

    def flatten_terrain(plane, terrain, height=9000):
        """try to flatten a terrain, using the plane as reference plane must have 
        ALL modifiers APPLIED

        1) get the road
        2) copy it, hide original
        3) move the current high over (9000 meters is enough)
        4) delete from this road the faces, so we get only vertex
        5) do a raycast
        6) identify terrain faces
        7) TBD - extend - triangulate - whatever

        Arguments:
            plane {string} -- blender's object name
            terrain {string} -- blender's object name
        """

        timeit = bl_utils.TimeIt()

        EXTEND_TERRAIN = True
        SUBDIVIDE = False

        obj_s = bpy.data.objects[plane]
        obj_t = bpy.data.objects[terrain]

        copy_obj = bl_utils.copy_obj(obj_s)

        # check for modifiers, if so, apply them
        copy_obj.select_set(True)
        bpy.context.view_layer.objects.active = copy_obj

        for modifier in copy_obj.modifiers:
            bpy.ops.object.modifier_apply(modifier=modifier.name)

        bpy.ops.object.select_all(action='DESELECT')
        copy_obj.location = copy_obj.location + Vector((0, 0, height))

        bl_utils.delete_faces_from_object(copy_obj.name)
        vertices_to_raycast = bl_utils.plane_to_vertex(copy_obj.name)['points']

        point_data = bl_utils.get_raycast(
            copy_obj.name,
            terrain,
            vertices=vertices_to_raycast
        )


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

        selected_faces = []
        for point in point_data:
            terrain_down, index, point, location = point
            bm.faces[index].select = True
            selected_faces.append(index)

        ###
        ### maintain order if needed but remove dupes
        ### geom_faces = list(collections.OrderedDict.fromkeys(geom_faces).keys())


        # extend the faces
        # leave faces selected to process the
        # boundaries if needed


        # return object visibility and delete the copy object
        bpy.data.objects.remove(copy_obj)
        obj_s.hide_set(False)

        selected_faces = [f.index for f in bm.faces if f.select]

        bm.faces.ensure_lookup_table()
        target_vector = (.0, .0, 1.)

        # do the rotation
        if False:
            for f in selected_faces:
                bface = bm.faces[f]
                mat_rot = bface.normal.rotation_difference(target_vector).to_euler().to_matrix().to_4x4()
                bmesh.ops.rotate( bm, cent=bface.calc_center_median(), matrix=mat_rot, verts=list(bface.verts))

        selected_faces = list(set(selected_faces))
        geom = [bm.faces[f] for f in selected_faces]    
        if EXTEND_TERRAIN:
            ret_geom =  bmesh.ops.region_extend(
                bm,
                geom=geom,
                use_faces=True, 
                use_face_step=False,
                use_contract=False
            )
            for f in ret_geom['geom']:
                if isinstance(f, bmesh.types.BMFace):
                    f.select = True

        if SUBDIVIDE:
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

        # do here the flatten
        # if False:
        #     obj_t.select_set(True)
        #     bpy.context.view_layer.objects.active = obj_t
        #     bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        #     bpy.ops.mesh.looptools_flatten(influence=100, plane='best_fit')  #best_fit
        #     bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

            
        timeit.stop()
        print("[t] flatten_terrain(): ", timeit)
        #return(("ERROR", "Can't found terrain below the curve"))
        return ("INFO", "Done")





    # def flatten_terrain(plane, terrain, height=9000):
    #     """try to flatten a terrain, using the plane as reference plane must have 
    #     ALL modifiers APPLIED

    #     1) get the road
    #     2) copy it, hide original
    #     3) move the current high over (9000 meters is enough)
    #     4) delete from this road the faces, so we get only vertex
    #     5) do a raycast
    #     6) identify terrain faces
    #     7) TBD - extend - triangulate - whatever

    #     Arguments:
    #         plane {string} -- blender's object name
    #         terrain {string} -- blender's object name
    #     """

    #     timeit = bl_utils.TimeIt()

    #     EXTEND_TERRAIN = True


    #     obj_s = bpy.data.objects[plane]
    #     obj_t = bpy.data.objects[terrain]

    #     copy_obj = bl_utils.copy_obj(obj_s)

    #     # check for modifiers, if so, apply them
    #     copy_obj.select_set(True)
    #     bpy.context.view_layer.objects.active = copy_obj

    #     for modifier in copy_obj.modifiers:
    #         bpy.ops.object.modifier_apply(modifier=modifier.name)

    #     bpy.ops.object.select_all(action='DESELECT')
    #     copy_obj.location = copy_obj.location + Vector((0, 0, height))

    #     bl_utils.delete_faces_from_object(copy_obj.name)
    #     vertices_to_raycast = bl_utils.plane_to_vertex(copy_obj.name)['points']

    #     point_data = bl_utils.get_raycast(
    #         copy_obj.name,
    #         terrain,
    #         vertices=vertices_to_raycast
    #     )


    #     bm = bmesh.new()
    #     bm.from_mesh(obj_t.data)
    #     bm.verts.ensure_lookup_table()
    #     bm.edges.ensure_lookup_table()
    #     bm.faces.ensure_lookup_table()

    #     # unselect all
    #     for face in bm.faces: face.select = False
    #     for vert in bm.verts: vert.select = False
    #     for edge in bm.edges: edge.select = False


    #     # step 1. get marked, extend and subdivide

    #     selected_faces = []
    #     for point in point_data:
    #         terrain_down, index, point, location = point
    #         bm.faces[index].select = True
    #         selected_faces.append(index)

    #     selected_faces = list(set(selected_faces))
    #     geom = [bm.faces[f] for f in selected_faces]

    #     ret_geom =  bmesh.ops.region_extend(
    #         bm,
    #         geom=geom,
    #         use_faces=True, 
    #         use_face_step=False,
    #         use_contract=False
    #     )
    #     for f in ret_geom['geom']:
    #         if isinstance(f, bmesh.types.BMFace):
    #             f.select = True


    #     sel_faces = [f for f in bm.faces if f.select]
    #     face_edges = []
    #     for f in sel_faces:
    #         for e in f.edges:
    #             face_edges.append(e.index)
    #     face_edges = list(set(face_edges))
    #     face_edges_geom = [bm.edges[i] for i in face_edges]
    #     ret = bmesh.ops.subdivide_edges(bm, edges=face_edges_geom, cuts=2, use_grid_fill=True)
    #     for f in ret['geom']:
    #         if isinstance(f, bmesh.types.BMFace):
    #             f.select = True

    #     point_data = bl_utils.get_raycast(
    #         copy_obj.name,
    #         terrain,
    #         vertices=vertices_to_raycast
    #     )
    #     copy_obj.location = copy_obj.location - Vector((0, 0, height))
    #     # till here

    #     # select faces tracked
    #     # iterative work.

    #     faces = {}
    #     target_vector = (.0, .0, 1.0)

    #     bm.faces.ensure_lookup_table()


    #     for point in point_data:
    #         terrain_down, index, point, location = point
    #         bm.faces[index].select = True
    #         if index in faces.keys():
    #             if not point.index in faces[index].keys():
    #                 faces[index][point.index] = True
    #         else:
    #             faces[index] = {} 
    #             faces[index][point.index] = True

    #     for f_index in faces.keys():
    #         # calculate average height of points
    #         count = 0
    #         z_sum = 0
    #         z_avg = 0
    #         for point in faces[f_index].keys():
    #             z_sum += copy_obj.data.vertices[point].co.z
    #             count +=1
    #         z_avg = z_sum/count

    #         world_point = obj_s.matrix_world @ Vector((.0, .0, z_avg))
    #         local_point = obj_t.matrix_world.inverted() @ world_point

    #         bface = bm.faces[f_index]
    #         #mat_rot = bface.normal.rotation_difference(target_vector).to_euler().to_matrix().to_4x4()
    #         #bmesh.ops.rotate( bm, cent=bface.calc_center_median(), matrix=mat_rot, verts=list(bface.verts))            

    #         for v in bface.verts:
    #             v.co[2] = local_point.z

    #         print(".")




    #     # return object visibility and delete the copy object
    #     bpy.data.objects.remove(copy_obj)
    #     obj_s.hide_set(False)


    #     bpy.context.view_layer.update()
    #     bm.calc_loop_triangles()
    #     bm.to_mesh(obj_t.data)
    #     obj_t.data.update()
    #     bm.free()

    #     timeit.stop()
    #     print("[t] flatten_terrain(): ", timeit)
    #     #return(("ERROR", "Can't found terrain below the curve"))
    #     return ("INFO", "Done")





#BL_FLATTEN.flatten_terrain('Road_HiRes','Terrain')
