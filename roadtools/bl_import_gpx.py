#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# bl_import_gpx.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# Read a GPX file and process it, smoothing and calculating the bounding box
# creates a curve (mesh) in blender so we can work on it after that.
#
# TODO:
#  * add the curve to the roadtools properties
#  * set a global name instead the filename
#
# a = BL_IMPORT_GPX()
# a.import_gpx("/Archive/Src/RoadTools/gpx/mijares.gpx")
# print(a.bounding_box)
# a.bounding_box.expand(1000,500,500,1000)
# print(a.bounding_box)
#
# ############################################################################
import os, sys
import bpy, bmesh
import math
import mathutils

from default_projection import DefaultProjection
import core.smooth


_isBlender280 = bpy.app.version[1] >= 80

class BL_IMPORT_GPX():

    def __init__(self, ignoreGeoreferencing=False, useElevation=True, importType='curve',
                expand_top = 0.0, expand_left = 0.0, expand_right = 0.0, expand_bottom = 0.0):

        class expand_class:
            def __init__(self,top,left,right,bottom):
                self.top = top
                self.left = left
                self.right = right
                self.bottom = bottom

        # to expand the bounding box, if needed. # can be called later, if you need to.
        self.expand = expand_class(expand_top, expand_left, expand_right, expand_bottom)
        self.ignoreGeoreferencing = ignoreGeoreferencing
        self.useElevation = useElevation
        self.importType = importType
        self.projection = DefaultProjection(self.ignoreGeoreferencing)

        self.bounding_box = None
        self.points = None

    def import_gpx(self, filepath, name="gpx_curve", height_offset=0.0, optimize=True, ground=False):
        """import a gpx file smoothing it and leveling the altitudes
        also adjusts the origin of the object to the first point

        Arguments:
            filepath {string} -- full path to the gpx file

        Keyword Arguments:
            name {string} -- the object name in blender (default: {None})
        """

        self.filepath = filepath

        # setting active object if there is no active object
        if  bpy.context.mode != "OBJECT":
            # if there is no object in the scene, only "OBJECT" mode is provided
            if _isBlender280:
                if not bpy.context.view_layer.objects.active:
                    bpy.context.view_layer.objects.active = bpy.context.scene.collection.objects[0]
            else:
                if not bpy.ontext.scene.objects.active:
                    bpy.context.scene.objects.active = bpy.context.scene.objects[0]
            bpy.ops.object.mode_set(mode="OBJECT")

        bpy.ops.object.select_all(action="DESELECT")

        name = name or os.path.basename(self.filepath)

        if self.importType == "curve":
            obj, length = self.makeCurve(bpy.context, name, height_offset, optimize, ground)
        else:
            obj, length = self.makeMesh(bpy.context, name, height_offset, optimize, ground)

        if _isBlender280:
            bpy.context.scene.collection.objects.link(obj)
        else:
            bpy.context.scene.objects.link(obj)

        # remove double vertices
        if _isBlender280:
            bpy.context.view_layer.objects.active = obj
        else:
            bpy.context.scene.objects.active = obj

        if _isBlender280:
            obj.select_set(True)
        else:
            obj.select = True
            bpy.context.scene.update()

        # put the origin of the object in the first point
        # new_origin = obj.data.splines.active.points[0].co.xyz
        # obj.data.transform(mathutils.Matrix.Translation(-new_origin))
        # obj.matrix_world.translation += new_origin

        # apply all transformations
        # obj.data.transform(obj.matrix_world)
        # obj.matrix_world = mathutils.Matrix()



        return(("INFO", "Done", obj, length))


    def read_gpx_file(self, context, height_offset=0.0, optimize=True, ground=False):

        points, bb, length = core.smooth.smooth_gpx(self.filepath,
                            optimize=optimize,
                            zero=False,
                            geoid=ground,
                            output=None,
                            height_offset=height_offset)

        self.points = points
        self.bounding_box = bb

        bb.expand(self.expand.top,self.expand.left,self.expand.right,self.expand.bottom)

        segment = [ (p.latitude, p.longitude, p.elevation) for p in points ]

        #bb.expand(1000,500,500,1000)
        minLat = bb.bounds.min_latitude
        maxLat = bb.bounds.max_latitude
        minLon = bb.bounds.min_longitude
        maxLon = bb.bounds.max_longitude

        #projection = self.getProjection(context,
        projection = self.projection.getProjection(context,lat = (minLat + maxLat)/2, lon = (minLon + maxLon)/2)

        return [segment], projection, length

    def makeMesh(self, context, name, height_offset, optimize, ground):
        self.bm = bmesh.new()

        segments, projection, length = self.read_gpx_file(context, height_offset=height_offset, optimize=optimize, ground=ground)

        # create vertices and edges for the track segments
        for segment in segments:
            prevVertex = None
            for point in segment:
                v = projection.fromGeographic(point[0], point[1])
                v = self.bm.verts.new((v[0], v[1], point[2] if self.useElevation and len(point)==3 else 0))
                if prevVertex:
                    self.bm.edges.new([prevVertex, v])
                prevVertex = v

        # finalize
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)

        # cleanup
        self.bm.free()
        self.bm = None

        return (bpy.data.objects.new(name, mesh), length)

    def makeCurve(self, context, name, height_offset, optimize, ground):
        curve = bpy.data.curves.new(name, 'CURVE')
        curve.dimensions = '3D'
        curve.twist_mode = 'Z_UP'
        curve.resolution_u = 24
        self.curve = curve

        segments, projection, length = self.read_gpx_file(context, height_offset=height_offset, optimize=optimize, ground=ground)

        for segment in segments:
            self.createSpline()
            for i, point in enumerate(segment):
                if i:
                    self.spline.points.add(1)
                v = projection.fromGeographic(point[0], point[1])
                self.setSplinePoint((v[0], v[1], point[2] if self.useElevation and len(point)==3 else 0))

        # cleanup
        self.curve = None
        self.spline = None

        return (bpy.data.objects.new(name, curve), length)


    def createSpline(self, curve=None):
        if not curve:
            curve = self.curve
        self.spline = curve.splines.new('POLY')
        self.pointIndex = 0

    def setSplinePoint(self, point):
        self.spline.points[self.pointIndex].co = (point[0], point[1], point[2], 1.)
        self.pointIndex += 1



#a = BL_IMPORT_GPX()
#a.import_gpx("/Archive/Src/RoadTools/gpx/mijares.gpx")
#print(a.bounding_box)
#a.bounding_box.expand(1000,500,500,1000)
#print(a.bounding_box)


