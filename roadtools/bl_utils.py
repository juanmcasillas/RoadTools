#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# bl_utils.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# Define some helper class, and lot of useful function
#
# ############################################################################

import time
import bpy
from mathutils import Vector, Matrix, Euler
from math import radians
import bmesh
from itertools import islice
import copy

class BL_DEBUG:

    def set_mark(p, kind='ARROWS', scale=None):
        "add an emtpy in p point to test the position"
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


class TimeIt:
    "measures the time between the creation of the class, and calling stop()"
    def __init__(self):
        self.t_start = time.time()
        self.t_stop = None

    def stop(self):
        self.t_stop = time.time()
        self.t_delta = self.t_stop - self.t_start

    def convert(self, seconds):
        min, sec = divmod(seconds, 60)
        hour, min = divmod(min, 60)
        return "%d:%02d:%03.2f" % (hour, min, sec)

    def __repr__(self):
        s_start = time.strftime('%H:%M:%S', time.localtime(self.t_start))
        s_stop = time.strftime('%H:%M:%S', time.localtime(self.t_stop))
        s_delta = self.convert(self.t_delta)
        s = "start=%s stop=%s delta=%s" % (s_start, s_stop, s_delta)
        return(s)


class DummyVector:
    "to add the .co attribute and work as a vertex"
    def __init__(self,v):
        self.co = v


class NearestData:
    "stores the nearest data from a point to a vertex"
    def __init__(self, pos):
        self.pos = 'RIGHT'
        if pos != 0: self.pos = 'LEFT'
        self.face = None
        self.vertex = None
        self.edges = []
        self.distance = sys.maxsize
        self.point = None

    def __repr__(self):
        return "<Nearest face:%s vertex:%s edges:%s distance:%5.8f point:%s pos: %s>" % (
            self.face,
            self.vertex,
            self.edges,
            self.distance,
            self.point,
            self.pos
        )



class RoadMesh:
    """implements a very basic road builder, based on point and distance.
    """
    def __init__(self, name="road", width=10):
        self.width = width
        self.half_width = self.width/2.0
        self.vertex = []
        self.faces = []
        self.name = name

        self.mymesh = bpy.data.meshes.new(self.name)
        self.myobject = bpy.data.objects.new(self.name, self.mymesh)
        scene = bpy.context.scene
        scene.collection.objects.link(self.myobject)

        # 3D cursor location
        # we use only X,Y increments :D

        self.cursor = bpy.context.scene.cursor.location
        self.cursor_orig = copy.copy(bpy.context.scene.cursor.location)


    def add_face(self, distance):
        "add a new poly at distance"

        v0 = (self.cursor.x, self.cursor.y - self.half_width, self.cursor.z) # top left
        v1 = (self.cursor.x, self.cursor.y + self.half_width, self.cursor.z) # bottom left
        v2 = (self.cursor.x + distance, self.cursor.y + self.half_width, self.cursor.z) # bottom right
        v3 = (self.cursor.x + distance, self.cursor.y - self.half_width, self.cursor.z) # top right


        if len(self.faces) == 0:
            # add four vertex, and create face
            self.vertex.extend([v0,v1,v2,v3])
            face = [(0, 3, 2, 1)]
        else:
            # we have vertex created, so only add 2
            self.vertex.extend([v2,v3])
            l = len(self.vertex)
            face = [(l-3, l-1, l-2, l-4)]

        self.faces.extend(face)

        #print(self.vertex)
        #print(self.faces)

        bpy.context.scene.cursor.location.x += distance
        #self.cursor = bpy.context.scene.cursor.location


    def build(self):
        self.mymesh.from_pydata(self.vertex, [], self.faces)
        self.mymesh.update(calc_edges=True)
        bpy.context.scene.cursor.location = self.cursor_orig

        return(self.myobject)


def copy_obj(obj, linkit=True, hideit=False, hideorig=True):
    """creates a full copy of the object
    
    Arguments:
        obj {object} -- blender object
    
    Keyword Arguments:
        linkit {bool} -- link the object in the tree (default: {True})
        hideit {bool} -- hide the copy (default: {False})
        hideorig {bool} -- hide the original (default: {True})
    
    Returns:
        object -- the copied object
    """

    copy_obj = obj.copy()
    copy_obj.data = obj.data.copy()

    if linkit:
        bpy.context.collection.objects.link(copy_obj)
    if hideit:
        copy_obj.hide_set(True)
    if hideorig:
        obj.hide_set(True)
    
    return copy_obj 


def delete_faces_from_object(objname):
    """this deletes the faces and the edges for a object, and leaves only the verts, ready to work with raycast

    Arguments:
        objname {string} -- blender's object name
    """

    obj_s = bpy.data.objects[objname]

    bm = bmesh.new()
    bm.from_mesh(obj_s.data)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    bmesh.ops.delete(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), context='EDGES_FACES')

    bpy.context.view_layer.update()
    bm.calc_loop_triangles()
    bm.to_mesh(obj_s.data)
    obj_s.data.update()
    bm.free()

    return obj_s



def rotate_mesh_face ( objname, face_index, target_vector, point=None):
    
    obj_t = bpy.data.objects[objname]

    # if int, run once, else run on the list (to speed up)
    work_faces = []
    if isinstance(face_index, int):
        work_faces.append(face_index)
    else:
        work_faces = face_index

    bm = bmesh.new()
    bm.from_mesh(obj_t.data)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    for face_idx in work_faces:
        #face_t = mesh_t.polygons[face_idx]
        #face_t.select = True
    
        #empty_on(obj_t.matrix_world @ face_t.center)

        #bpy.ops.object.mode_set(mode = 'EDIT')
        #obj_t.select_set(True)

        #
        # with the face selected, try some manual rotations
        # first, get the bmesh, and do some visual representation
        #
        #bm = bmesh.new()
        #bm.from_mesh(mesh_t)

        bface = bm.faces[face_idx]
        #bface.select = True
        verts_selected = [v for v in bface.verts]
        #for v in verts_selected:
        #    empty_on(obj_t.matrix_world @ v.co, kind='PLAIN_AXES',scale=0.1)

        # this is how to rotate a face based on angles
        #
        # rad_x = radians(0)
        # rad_y = radians(0)
        # rad_z = radians(30)
        # mat_rot = Euler((rad_x, rad_y, rad_z),'XYZ').to_matrix().to_4x4()
        # print("mat_rot ", mat_rot)
        
        #target_v = Vector((0.1835, -0.2740, 0.9441))
        # face#47 normal <Vector (-0.0029, 0.0351, 0.9994)>
        # face#56 normal <Vector (0.1835, -0.2740, 0.9441)>
            
        # move first down
        if point:
            distance = point.z - bface.calc_center_median().z
            if distance > 0:
                #print("not needed")
                #bpy.ops.object.mode_set(mode='OBJECT')
                pass
            else:
                print("moving: %3.2f" % distance)
                bmesh.ops.translate(bm, verts=verts_selected, vec = distance * bface.normal)

        #print(bface.index)
        #print("source ", bface.normal)
        #print("target ", target_vector)

        mat_rot = bface.normal.rotation_difference(target_vector).to_euler().to_matrix().to_4x4()
        #print("quat ", mat_rot)

        bmesh.ops.rotate( bm, cent=bface.calc_center_median(), matrix=mat_rot, verts=verts_selected)
        #print("normal rotated ", bface.normal)
        
        # some debug
        #verts_selected = [v for v in bface.verts]
        #for v in verts_selected:
        #    empty_on(obj_t.matrix_world @ v.co, kind='PLAIN_AXES',scale=0.1)
        
    #bmesh.update_mesh(mesh_t)
    bm.to_mesh(obj_t.data)
    obj_t.data.update()
    bm.free()



def flatten_mesh(mesh_name, faces, influence=100):
    """flatten some faces using the normal, with looptools
    
    Arguments:
        mesh_name {string} -- the name of the mesh (terrain)
        faces {list of ints} -- the face indexes going to be flattened
    """
    obj = bpy.data.objects[mesh_name]
    mesh = obj.data

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    bpy.ops.object.mode_set(mode='EDIT', toggle=False)

    bm = bmesh.from_edit_mesh(mesh)
    bm.faces.ensure_lookup_table()
    for f in faces:
        bm.faces[f].select = True

    bpy.ops.mesh.looptools_flatten(influence=influence, plane='normal')  #best_fit
    bmesh.update_edit_mesh(mesh, True)



    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    #bpy.ops.object.select_all(action='DESELECT')

def chunk(it, size):
    "chunk an array in sizes of size elements"

    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())

def get_3dcur():
    "return the position of the 3d cursor"
    return bpy.context.scene.cursor.location

def getEdgesForVertex(v_index, mesh, marked_edges):
    "get all the edges for a given vertex"
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
    "find all the conected vertex (loop). Recursive function"
    if level >= maxdepth:
        return

    edges = getEdgesForVertex(v_index, mesh, marked_edges)

    for e in edges:
        othr_v_index = [idx for idx in mesh.edges[e.index].verts if idx != v_index][0]
        connected_verts[othr_v_index] = True
        marked_edges.append(e.index)
        findConnectedVerts(othr_v_index, mesh, connected_verts, marked_edges, maxdepth=maxdepth, level=level+1)

    # connected_verts = {}
    # marked_edges = []
    # findConnectedVerts(0, mesh, connected_verts, marked_edges, maxdepth=1)
    # print(",".join([str(v) for v in connected_verts.keys()]))


def triangulate_face_quad(bm, face_idx):
    "triangulates a face. Can be a triange or a quad"

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
    "overrides the environment so we can call knife-project from a script"
    #=== Iterates through the blender GUI's windows, screens, areas, regions to find the View3D
    # space and its associated window.  Populate an 'oContextOverride context' that can be used
    # with bpy.ops that require to be used from within a View3D (like most addon code that
    # runs of View3D panels)
    # Tip: If your operator fails the log will show an "PyContext: 'xyz' not found".
    # To fix stuff 'xyz' into the override context and try again!
    ###IMPROVE: Find way to avoid doing four levels of traversals at every request!!
    for oWindow in bpy.context.window_manager.windows:
        oScreen = oWindow.screen
        for oArea in oScreen.areas:
            if oArea.type == 'VIEW_3D':
                ###LEARN: Frequently, bpy.ops operators are called from View3d's
                # toolbox or property panel.  By finding that window/screen/area we can
                # fool operators in thinking they were called from the View3D!
                for oRegion in oArea.regions:
                    if oRegion.type == 'WINDOW':
                        ###LEARN: View3D has several 'windows' like 'HEADER' and 'WINDOW'.
                        # Most bpy.ops require 'WINDOW'
                        #=== Now that we've (finally!) found the damn View3D stuff all that into a
                        # dictionary bpy.ops operators can accept to specify their context.
                        # I stuffed extra info in there like selected objects, active objects,
                        # etc as most operators require them.  (If anything is missing operator will
                        # fail and log a 'PyContext: error on the log with what is
                        # missing in context override) ===
                        oContextOverride = {
                                'window': oWindow,
                                'screen': oScreen,
                                'area': oArea,
                                'region': oRegion,
                                'scene': bpy.context.scene,
                                'edit_object': bpy.context.edit_object,
                                'active_object': bpy.context.active_object,
                                'selected_objects': bpy.context.selected_objects}
                                # Stuff the override context with very common requests by operators.  MORE COULD BE NEEDED!
                        #print("-AssembleOverrideContextForView3dOps() created override context: ", oContextOverride)
                        return oContextOverride
    raise Exception("ERROR: AssembleOverrideContextForView3dOps() could not find a VIEW_3D with WINDOW region to create override context to enable View3D operators.  Operator cannot function.")

# ####################################################################################################
#
# face_edges_by_vert
#
# ####################################################################################################

def face_edges_by_vert(face, vert):
    "given a face, return all the edges that have the given vert index"
    r = []
    idx = vert.index if isinstance(vert, bmesh.types.BMVert) else vert
    #print("-------")
    for e in face.edges:
        for v in e.verts:
            #print(face, e, v, idx)
            if v.index == idx:
                r.append(e.index)
    return(r)

# ####################################################################################################
#
# get_raycast
#
# ####################################################################################################

def get_raycast(plane, terrain, vertices=None, DEBUG=False, LIMIT=None):
    "generates a raycast from the points of the plane, to the terrain and store data. Must be only verts"
    obj_s=  bpy.data.objects[plane]
    mesh_s = obj_s.data
    point_data = []
    pc = 0

    vertices = vertices if vertices else mesh_s.vertices

    for v in vertices:
        #
        # ok, process them mesh can be Down (should be)
        # but can be up. so check the results and save the
        # data. (raycast done in world coords and works)
        # maybe due it's on (0,0,0) ?
        #
        # retrieve i the index of the point, v the point

        # in order to get this working, I have to DELETE the
        # faces from the polygon, and use the vertex.
        # Delete "Only Edges & Faces"

        terrain_down = True
        DEBUG and BL_DEBUG.set_mark( obj_s.matrix_world @ v.co.xyz, kind="PLAIN_AXES" )
        result, location, normal, index, r_object, matrix = bpy.context.scene.ray_cast(
            bpy.context.view_layer,
            obj_s.matrix_world @ v.co.xyz,
            #v.normal * -1 # Z Down
            (0,0,-1.0)
        )
        #print("R", result,index, r_object, obj_s.matrix_world @ v.co.xyz  )
        if result and r_object.name == terrain:
            DEBUG and BL_DEBUG.set_mark( location, kind="SPHERE")

        if not result:
            result, location, normal, index, r_object, matrix = bpy.context.scene.ray_cast(
                bpy.context.view_layer,
                obj_s.matrix_world @ v.co.xyz,
                #v.normal # Z Up
                (0,0,1.0)
            )
            if not result:
                # something bizarre happens with that point
                print("Point %s doesn't match terrain geometry" % v.co.xyz)
                DEBUG and BL_DEBUG.set_mark(obj_s.matrix_world @ v.co.xyz)
                continue
            #print("R2", result,index, r_object )
            if result and r_object.name == terrain:
                DEBUG and BL_DEBUG.set_mark(location, kind="CUBE")
            ## terrain is upwards
            terrain_down = False

        # terrain is downwards

        if r_object.name == terrain:
            #found_dict[key] = True
            point_data.append( (terrain_down, index, v, location )) # terrain is down, faceindex, point


        pc +=1
        if LIMIT and pc / 4 >= LIMIT:
            break

    print("ray_cast: total_points %d" % (len(mesh_s.vertices)))
    return(point_data)

# ####################################################################################################
#
# plane_to_vertex get the list of plane, create a mesh and iterate the vertex as planes
#
# ####################################################################################################

def plane_to_vertex(plane, calc_centers=False):
    "get the vertices for plane, generate a list of all vertices as a face and calculate two median points at side"

    obj_s=  bpy.data.objects[plane]
    mesh_s = obj_s.data

    pc = 0
    idx = 0
    MESH_VERTEX_LEN = int(len(mesh_s.vertices)/2)-1

    all_edges = []
    all_points = []

    for pc in range(MESH_VERTEX_LEN):

        # iterate about the number of quads

        edges = []
        if pc == 0:
            e_1 = [ mesh_s.vertices[0], mesh_s.vertices[1] ] # right
            e_2 = [ mesh_s.vertices[2], mesh_s.vertices[3] ] # left
            idx = 1
        elif pc == 1:
            e_1 = [ mesh_s.vertices[1], mesh_s.vertices[4] ]  # right
            e_2 = [ mesh_s.vertices[3], mesh_s.vertices[5] ]  # left edge
            idx += 3
        else:
            e_1 = [ mesh_s.vertices[idx], mesh_s.vertices[idx+2] ]       # right
            e_2 = [ mesh_s.vertices[idx+1], mesh_s.vertices[idx+3] ]     # left edge
            idx += 2


        # 0 is the right side
        # 1 is the left side
        edges = [ e_1, e_2 ]
        all_edges.append(edges)

        # calculate the center of the edges, so we have more points and avoid the "half split"
        # problem in the face selector

        all_points += [item for sublist in edges for item in sublist]
        if calc_centers:
            c1 = DummyVector(e_1[0].co + (e_1[1].co - e_1[0].co)/2) # right median
            c2 = DummyVector(e_2[0].co + (e_2[1].co - e_2[0].co)/2) # left median
            #c3 = DummyVector(e_1[0].co + (e_2[1].co - e_1[0].co)/2) # avg center
            #c4 = DummyVector(e_2[0].co + (e_1[1].co - e_2[0].co)/2) # avg center
            #c5 = DummyVector(e_2[1].co + (e_2[1].co - e_1[1].co)/2) # top median
            #c6 = DummyVector(e_2[0].co + (e_2[0].co - e_1[0].co)/2) # bottom median
            #all_points += [c1, c2, c3, c4, c5, c6]
            all_points += [c1, c2]

    return { 'points': all_points, 'edges': all_edges }

def get_curve_length(curve):
    """return the approx length of a curve

    Arguments:
        curve {string} -- the name of the object's curve

    Returns:
        float -- the length

    """
    obj = bpy.data.objects[curve]
    points = bpy.data.curves[curve].splines.active.points
    distance = 0.0

    for i in range(len(points)-1):
        v0 = obj.matrix_world @ points[i].co.xyz
        v1 = obj.matrix_world @ points[i+1].co.xyz

        distance += (v0 - v1).length
    return(distance)


def set_origin_to_beginning(curve):
    """set the origin of the curve to the first point

    Arguments:
        curve {string} -- The blender's object name of the curve
    """

    obj = bpy.data.objects[curve]
    #put the origin of the object in the first point
    new_origin = obj.data.splines.active.points[0].co.xyz
    obj.data.transform(Matrix.Translation(-new_origin))
    obj.matrix_world.translation += new_origin
    return(obj, new_origin)
    # if you apply, you go to (0,0,0)
    # apply all transformations
    # obj.data.transform(obj.matrix_world)
    # obj.matrix_world = mathutils.Matrix()
