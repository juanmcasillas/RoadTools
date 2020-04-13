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
from math import radians
import bmesh   
import sys
import time

import bl_utils
from bl_utils import BL_DEBUG



def get_curve_points(curve):

    obj_s=  bpy.data.objects[curve]

    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_pattern(pattern=obj_s.name)

    if obj_s.type != 'CURVE':
        bpy.ops.object.convert(target='MESH', keep_original=True)
        newobj= bpy.context.object
        #points = list(map(lambda p: (p.co.x, p.co.y, p.co.z) ,new_obj.data.vertices))
        points = list(new_obj.data.vertices)
        bpy.data.objects.remove(newobj, do_unlink=True) 
    else:
        #points = list(map(lambda p: (p.co.x, p.co.y, p.co.z) ,newobj.data.splines.active.points))
        points = list(obj_s.data.splines.active.points)

    return(points)

def get_closest_point( target, point ):

    obj = bpy.data.objects[target]
    return (obj.closest_point_on_mesh( point ))
    #result, Whether closest point on geometry was found, boolean
    #location, The location on the object closest to the point, float array of 3 items in [-inf, inf]
    #normal, The face normal at the closest point, float array of 3 items in [-inf, inf]
    #index, The face index, -1 when original data isn’t available, int in [-inf, inf]

def set_terrain_origin(curve,terrain):
    """get curve object, get the first point, set the origin of the curve, then project it over the
    terrain, set the terrain origin, move both things to the world origin. This is very helpful to
    automatically align GPX + OSM terrain. If you plan to add a texture, do it BEFORE calling this
    function
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
        bpy.data.meshes[terrain].polygons[index].select = True
        origin = bpy.data.meshes[terrain].polygons[index].center
        obj_t.data.transform(Matrix.Translation(-origin))
        obj_t.matrix_world.translation += origin

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
    obj_t = bpy.data.objects[terrain]

    # move upwards too high so we can 
    # 1) ray cast
    # 2) do a full projection
    
    obj_s.location = obj_s.location + Vector((0,0,height))
    #bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    BL_DEBUG.set_mark(Vector((0,0,0)))

        
    
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

    obj_s.location = obj_s.location - Vector((0,0,height))    
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    #bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    
        
# TEST_IT
#if False:
    #BL_ROAD_UTILS.set_terrain_origin('outpux.gpx','Terrain')
    #BL_ROAD_UTILS.cut_road('Plane','Terrain')


#BL_ROAD_UTILS.cut_road('Plane','Terrain')
