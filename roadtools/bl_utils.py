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
from itertools import islice
import copy

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

    def clear_marks(what=None):
        "clear all the objects starting with what name"
        what = what or 'empty'
        for o in bpy.data.objects:
            if o.name.startswith(what):
                bpy.data.objects.remove(o) 


class BL_UTILS:
    def __init__(self):
        pass

    def chunk(it, size):
        "chunk an array in sizes of size elements"
        
        it = iter(it)
        return iter(lambda: tuple(islice(it, size)), ())
        
    def get_3dcur():
        "return the position of the 3d cursor"
        return bpy.context.scene.cursor.location


    def getEdgesForVertex(v_index, mesh, marked_edges):

        all_edges = []
        for e in mesh.edges:
            for v in e.verts:
                if v.index == v_index:
                    all_edges.append(e)

        #all_edges = [e for e in mesh.edges if v_index in e.verts]
        #print("all_edges", all_edges)
        #print(mesh.edges[0].verts[0])

        unmarked_edges = [e for e in all_edges if e.index not in marked_edges]
        return unmarked_edges

    def findConnectedVerts(v_index, mesh, connected_verts, marked_edges, maxdepth=1, level=0):  
        if level >= maxdepth:
            return

        edges = BL_UTILS.getEdgesForVertex(v_index, mesh, marked_edges)

        for e in edges:
            othr_v_index = [idx for idx in mesh.edges[e.index].verts if idx != v_index][0]
            connected_verts[othr_v_index] = True
            marked_edges.append(e.index)
            BL_UTILS.findConnectedVerts(othr_v_index, mesh, connected_verts, marked_edges, maxdepth=maxdepth, level=level+1)

    # connected_verts = {}
    # marked_edges = []
    # findConnectedVerts(0, mesh, connected_verts, marked_edges, maxdepth=1)
    # print(",".join([str(v) for v in connected_verts.keys()]))


    def triangulate_face_quad(bm, face_idx):

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # work on selected face
        f = bm.faces[face_idx]
        
        verts = []
        for v in f.verts:
            verts.append(bm.verts[v.index])
            
        vcenter = bm.verts.new(f.calc_center_median())
        bmesh.ops.delete(bm, geom=[f], context='FACES_ONLY')

        bm.verts.ensure_lookup_table()
        for v in verts:
            bm.edges.new((v, vcenter))

        # ugly, but works XD

        if len(verts) == 3:
            f1 = [verts[0], verts[1], vcenter]
            f2 = [verts[1], verts[2], vcenter]
            f3 = [verts[2], verts[0], vcenter]
            bmesh.ops.contextual_create(bm, geom= f1)
            bmesh.ops.contextual_create(bm, geom= f2)
            bmesh.ops.contextual_create(bm, geom= f3)

        if len(verts) == 4:
            f1 = [verts[0], verts[1], vcenter]
            f2 = [verts[1], verts[2], vcenter]
            f3 = [verts[2], verts[3], vcenter]
            f4 = [verts[3], verts[0], vcenter]
            bmesh.ops.contextual_create(bm, geom= f1)
            bmesh.ops.contextual_create(bm, geom= f2)
            bmesh.ops.contextual_create(bm, geom= f3)
            bmesh.ops.contextual_create(bm, geom= f4)

        bm.verts.index_update()
        bm.faces.index_update()

    # ####################################################################################################
    #
    # AssembleOverrideContextForView3dOps
    # override the enviroment so knife_project can be run on python script
    #
    # ####################################################################################################
    def AssembleOverrideContextForView3dOps():
        #=== Iterates through the blender GUI's windows, screens, areas, regions to find the View3D space and its associated window.  Populate an 'oContextOverride context' that can be used with bpy.ops that require to be used from within a View3D (like most addon code that runs of View3D panels)
        # Tip: If your operator fails the log will show an "PyContext: 'xyz' not found".  To fix stuff 'xyz' into the override context and try again!
        for oWindow in bpy.context.window_manager.windows:          ###IMPROVE: Find way to avoid doing four levels of traversals at every request!!
            oScreen = oWindow.screen
            for oArea in oScreen.areas:
                if oArea.type == 'VIEW_3D':                         ###LEARN: Frequently, bpy.ops operators are called from View3d's toolbox or property panel.  By finding that window/screen/area we can fool operators in thinking they were called from the View3D!
                    for oRegion in oArea.regions:
                        if oRegion.type == 'WINDOW':                ###LEARN: View3D has several 'windows' like 'HEADER' and 'WINDOW'.  Most bpy.ops require 'WINDOW'
                            #=== Now that we've (finally!) found the damn View3D stuff all that into a dictionary bpy.ops operators can accept to specify their context.  I stuffed extra info in there like selected objects, active objects, etc as most operators require them.  (If anything is missing operator will fail and log a 'PyContext: error on the log with what is missing in context override) ===
                            oContextOverride = {'window': oWindow, 'screen': oScreen, 'area': oArea, 'region': oRegion, 'scene': bpy.context.scene, 'edit_object': bpy.context.edit_object, 'active_object': bpy.context.active_object, 'selected_objects': bpy.context.selected_objects}   # Stuff the override context with very common requests by operators.  MORE COULD BE NEEDED!
                            #print("-AssembleOverrideContextForView3dOps() created override context: ", oContextOverride)
                            return oContextOverride
        raise Exception("ERROR: AssembleOverrideContextForView3dOps() could not find a VIEW_3D with WINDOW region to create override context to enable View3D operators.  Operator cannot function.")




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
        mesh_t = bpy.data.meshes[obj_t.data.name]

        points = BL_ROAD_UTILS.get_curve_points(curve)
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

        oContextOverride = BL_UTILS.AssembleOverrideContextForView3dOps()      
        bpy.data.objects['empty'].select_set(True)
        bpy.ops.view3d.view_selected(oContextOverride) 
        bpy.ops.object.delete()

        bpy.data.objects[plane].select_set(True)
        bpy.data.objects[terrain].select_set(True)
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        oContextOverride = BL_UTILS.AssembleOverrideContextForView3dOps()      
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
if False:
    #BL_ROAD_UTILS.set_terrain_origin('outpux.gpx','Terrain')
    BL_ROAD_UTILS.cut_road('Plane','Terrain')


#BL_ROAD_UTILS.cut_road('Plane','Terrain')
