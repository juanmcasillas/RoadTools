#!/usr/bin/env python3
#
#
# 2020 (C) Juan M. Casillas  <juanm.casillas@gmail.com>
# Define some global helpers, "debug" information and so on
#
#
import bpy
from mathutils import Vector, Matrix, Euler
from math import radians
import bmesh

class BL_DEBUG:
    def __init__(self):
        pass

    def set_mark(p, kind='ARROWS', scale=None):
        "add an emtpy in p point"
        # can be also PLAIN_AXES
        o = bpy.data.objects.new( "empty", None )
        o.empty_display_type = kind
        o.location = p
        bpy.context.scene.collection.objects.link( o )    
        if scale:
            o.empty_display_size = scale

    def clear_marks(self, what=None):
        "clear all the objects starting with what name"
        what = what or 'empty'
        for o in bpy.data.objects:
            if o.name.startswith(what):
                bpy.data.objects.remove(o) 


class BL_UTILS:
    def __init__(self):
        pass

    def get_3dcur():
        "return the position of the 3d cursor"
        return bpy.context.scene.cursor.location



class BL_ROAD_UTILS:
    def __init__(self):
        pass

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
        mesh_t = bpy.data.meshes[terrain]

        points = BL_ROAD_UTILS.get_curve_points(curve)
        first_point = points[0]
        print(first_point.co)
        
        #ray_cast (this is important)
        #result, boolean
        #location, The hit location of this ray cast, float array of 3 items in [-inf, inf]
        #normal, The face normal at the ray cast hit location, float array of 3 items in [-inf, inf]
        #index, The face index, -1 when original data isn’t available, int in [-inf, inf]
        #object, Ray cast object, Object
        #matrix, Matrix, float multi-dimensional array of 4 * 4 items in [-inf, inf]

        result, location, normal, index, object, matrix = bpy.context.scene.ray_cast( bpy.context.view_layer, first_point.co.xyz, (0,0,-1) )
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
        else:
            print("Can't found terrain below the curve. Check input")

        
# TEST_IT
BL_ROAD_UTILS.set_terrain_origin('outpux.gpx','Terrain')



