#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# bl_tools.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# Some helpers to create the raycast points from a plane, etc
#
# ############################################################################

import bpy
from mathutils import Vector, Matrix, Euler
import math
import bmesh
import sys
import time
import copy





import bl_utils
from bl_utils import BL_DEBUG

def cut_road(plane, terrain, height=9000):

    #
    # must be in OBJECT mode to work.
    # run on isolation
    # a face on the terrain must be selected in order to zoom works
    # and the cut is well done
    # face selected on mesh is the first point of the plane, so first do a set_terrain_origin()
    #
    bpy.ops.object.select_all(action='DESELECT')

    obj_s = bpy.data.objects[plane]

    # move upwards too high so we can
    # 1) ray cast
    # 2) do a full projection

    obj_s.location = obj_s.location + Vector((0, 0, height))
    #bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    BL_DEBUG.set_mark(Vector((0, 0, 0)))



    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = bpy.data.objects[terrain]

    oContextOverride = bl_utils.AssembleOverrideContextForView3dOps()
    bpy.data.objects['empty'].select_set(True)
    bpy.ops.view3d.view_selected(oContextOverride)
    bpy.ops.object.delete()

    bpy.data.objects[plane].select_set(True)
    bpy.data.objects[terrain].select_set(True)
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    oContextOverride = bl_utils.AssembleOverrideContextForView3dOps()
    bpy.ops.view3d.view_axis(oContextOverride, type='TOP')
    bpy.ops.view3d.zoom(oContextOverride,delta=50000)
    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    bpy.ops.mesh.knife_project(oContextOverride)

    bpy.data.objects[plane].select_set(False)
    bpy.ops.mesh.delete(type='FACE')

    obj_s.location = obj_s.location - Vector((0, 0, height))
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    #bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)



##
## used methods (try to document it)
##



def get_curve_points(curve):
    """get all the points for a given point

    Arguments:
        curve {string} -- the blender's object name with the curve

    returns a list with the points
    """

    obj_s=  bpy.data.objects[curve]

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_pattern(pattern=obj_s.name)

    if obj_s.type != 'CURVE':
        bpy.ops.object.convert(target='MESH', keep_original=True)
        newobj= bpy.context.object
        points = list(new_obj.data.vertices)
        bpy.data.objects.remove(newobj, do_unlink=True)
    else:
        points = list(obj_s.data.splines.active.points)

    return(points)



def set_terrain_origin(curve,terrain):
    """Get curve object, get the first point, set the origin of the curve, then project it over the
    terrain, set the terrain origin, move both things to the world origin. This is very helpful to
    automatically align GPX + OSM terrain. If you plan to add a texture, do it BEFORE calling this
    function

    Arguments:
        curve {string} -- name of the blender object with the curve modelling the road
        terrain {string} -- name of the blender object with the terrain

    curve must have their origin at the beginning (the first point of the curve)
    this function changes the origin of the terrain to the point of the raycast
    you should get materials, etc right BEFORE calling this method

    """

    obj_s=  bpy.data.objects[curve]
    obj_t=  bpy.data.objects[terrain]
    mesh_t = bpy.data.meshes[obj_t.data.name]

    points = get_curve_points(curve)
    first_point = points[0]

    #ray_cast (this is important)
    #result, boolean
    #location, The hit location of this ray cast, float array of 3 items in [-inf, inf]
    #normal, The face normal at the ray cast hit location, float array of 3 items in [-inf, inf]
    #index, The face index, -1 when original data isn’t available, int in [-inf, inf]
    #object, Ray cast object, Object
    #matrix, Matrix, float multi-dimensional array of 4 * 4 items in [-inf, inf]

    result, location, normal, index, object, matrix = bpy.context.scene.ray_cast(
        bpy.context.view_layer,
        first_point.co.xyz,
        (0,0,-1) # Z Down
    )
    #BL_DEBUG.set_mark( obj_s.matrix_world @ location )

    if result:

        # move the terrain
        # bpy.data.meshes[terrain].polygons[index].select = True
        #origin = bpy.data.meshes[terrain].polygons[index].center
        origin = location
        obj_t.data.transform(Matrix.Translation(-origin))
        obj_t.matrix_world.translation += origin
        obj_t.location = (0,0,0)

        # move the curve
        origin = first_point
        bpy.context.scene.cursor.location = obj_s.matrix_world @ first_point.co.xyz
        bpy.context.view_layer.objects.active = obj_s
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        obj_s.location = (0,0,0)
        bpy.context.scene.cursor.location = (0,0,0)

    else:
        return(("ERROR", "Can't found terrain below the curve"))
    return(("INFO", "Done"))





def create_low_res_road(curve, width, height, length):
    """creates a simple low res road based on array modifiers

    Arguments:
        curve {string} -- the curve's object name
        width {float} -- the width of the road
        height {float} -- the height of the road

    """
    curve_obj, origin = bl_utils.set_origin_to_beginning(curve)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.mesh.primitive_plane_add(location=origin, size=width)
    obj = bpy.context.active_object

    obj.dimensions[0] = width
    obj.dimensions[1] = 1.0 # so we can use the length calculator.

    # create the two modifiers. Note that I calculate the length of the road
    # based on the curve, and fit it.
    calc_len =  bl_utils.get_curve_length(curve)
    cur_len = length if length > calc_len else calc_len
    #print(calc_len, cur_len)

    obj.modifiers.new("Array","ARRAY")
    ##obj.modifiers["Array"].count = 0
    obj.modifiers["Array"].merge_threshold = 0
    obj.modifiers["Array"].use_merge_vertices = True
    obj.modifiers["Array"].offset_u = 1
    obj.modifiers["Array"].fit_type = 'FIT_LENGTH'
    obj.modifiers["Array"].fit_length = cur_len

    obj.modifiers.new("Curve","CURVE")
    obj.modifiers['Curve'].object = curve_obj

    bpy.ops.object.modifier_apply(modifier="Array")
    bpy.ops.object.modifier_apply(modifier="Curve")

    return(obj)



def create_high_res_road(curve, width):

    ob = bpy.data.objects[curve]
    bpy.context.view_layer.objects.active = ob

    # convert the spline to BEZIER and handlers to FREE_ALIGN
    #if bpy.ops.object.mode != 'EDIT':
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    bpy.ops.curve.select_all()
    bpy.ops.curve.spline_type_set(type='BEZIER')
    # changing to bezier and adding free_align the resolution increases A LOT
    # we don't need so many points now
    bpy.ops.curve.handle_type_set(type='FREE_ALIGN')  # FREE_ALIGN
    bpy.ops.curve.normals_make_consistent()


    # set some parameters
    #bpy.ops.curve.select_all()
    #bpy.ops.curve.subdivide()
    #bpy.ops.curve.subdivide()
    #bpy.ops.curve.subdivide()
    #bpy.ops.curve.smooth()

    #bpy.ops.curve.smooth()
    #bpy.ops.curve.normals_make_consistent()
    # save origin, move to first point, asign the origin to it

    cur = copy.copy(bpy.context.scene.cursor.location)

    # first point
    if len(ob.data.splines.active.points) == 0:
        first_point = ob.data.splines.active.bezier_points[0].co
    else:
        first_point = ob.data.splines.active.points[0].co

    bpy.context.scene.cursor.location = first_point.xyz

    # set the origin of the geometry
    bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    ob.location = (0, 0, 0) # to the world origin, for AC

    # restore 3d cursor
    bpy.context.scene.cursor.location = cur.xyz

    road_mesh = bl_utils.RoadMesh(name="road-temp", width=width)

    #
    # transform to a MESH, calculate distance.
    #

    bpy.ops.object.convert(target='MESH', keep_original=False)
    ve = ob.data.vertices

    total_len = 0.0

    for i in range(len(ob.data.edges)-1):

        p = ob.data.edges[i]
        dd = ve[p.vertices[0]].co - ve[p.vertices[1]].co
        segment_length = dd.length
        total_len += segment_length
        road_mesh.add_face(segment_length)


    bpy.ops.object.convert(target='CURVE', keep_original=False)

    ##remove ## bpy.ops.object.mode_set(mode = 'OBJECT')
    bpy.ops.object.transform_apply(location = True, scale = True, rotation = True)
    ob.data.resolution_u = 24
    ob.data.twist_mode = 'Z_UP'

    print("length in meters: %3.2f" % total_len)
    road = road_mesh.build()
    road.modifiers.new("Curve","CURVE")
    road.modifiers['Curve'].object = ob

    return(road)


def create_road(curve, width, height, length, hires=False):
    """Creates a mesh for the road. check if high-or low res (two different algorithms).
    The road is done by adding new segments, or usign array modifiers/curves

    Arguments:
        curve {string} -- blender's object name for the curve
        width {float} -- width of the road (Y value)
        height {float} -- height of the roead (X value)
        length {float} -- length of the road, read from the GPX (if not 0)
    """

    the_name = "Road_HiRes"
    if not hires:
        the_name = "Road_LowRes"
        obj = create_low_res_road(curve, width, height, length)

    else:
        obj = create_high_res_road(curve, width)

    ren_obj = bpy.context.scene.objects[obj.name]
    ren_obj.name = the_name
    ren_obj.data.name = the_name


    #return(("ERROR", "Can't found terrain below the curve"))
    return(("INFO", "Done",obj))

