#
# This class is a rewritten of blender-gpx to support my gpx optimizations
# uses gpxpy, and a custom smooth function. Also support expanding the
# bounding box and 
#
# Juan M. Casillas <juanm.casillas@gmail.com>
#
#
# a = BL_IMPORTGPX()
# a.import_gpx("/Archive/Src/RoadTools/gpx/mijares.gpx")
# print(a.bounding_box)
# a.bounding_box.expand(1000,500,500,1000)
# print(a.bounding_box)
#
import os, sys
import bpy, bmesh
import math
from default_projection import DefaultProjection
from mathutils import Vector
from core.gpxbb import GPX_BB,GPX_BB_bounds

_isBlender280 = bpy.app.version[1] >= 80


class BL_FAKETERRAIN():

    def __init__(self, max_latitude, min_longitude, max_longitude, min_latitude, height=0.0, ignoreGeoreferencing=False):

        self.BB = GPX_BB( GPX_BB_bounds(max_latitude, min_longitude, max_longitude, min_latitude) )
        self.ignoreGeoreferencing = ignoreGeoreferencing
        self.height = height
        self.projection = DefaultProjection(self.ignoreGeoreferencing)
        
        self.grid_sz_x = 25.0
        self.grid_sz_y = 35.0
        

    def create(self, objname, top=0.0, left=0.0, bottom=0.0, right=0.0):
        
        # setting active object if there is no active object
        if  bpy.context.mode != "OBJECT":
            # if there is no object in the scene, only "OBJECT" mode is provided
            if _isBlender280:
                if not bpy.context.view_layer.objects.active:
                    bpy.context.view_layer.objects.active = bpy.context.scene.collection.objects[0]
            else:
                if not cbpy.ontext.scene.objects.active:
                    bpy.context.scene.objects.active = bpy.context.scene.objects[0]
            bpy.ops.object.mode_set(mode="OBJECT")
        
        bpy.ops.object.select_all(action="DESELECT")
        
        obj = self.makeMesh(bpy.context, objname, top=top, left=left, bottom=bottom, right=right)
        
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
        
        return {"FINISHED"}

   
    def makeMesh(self, context, name, top=0.0, left=0.0, bottom=0.0, right=0.0):
       
        
        # mesh arrays
        verts = []
        faces = []

        # mesh variables

        
        self.BB.expand(top,left,bottom,right)
        
        numX = math.ceil(self.BB.width/float(self.grid_sz_x))
        numY = math.ceil(self.BB.height/float(self.grid_sz_y))


        # variance and scale variables

        # fill verts array
        for i in range (0, numX):
            for j in range(0,numY):
                # nomalize range
                vert = (i*self.grid_sz_x,j*self.grid_sz_y,self.height)
                verts.append(vert)

        # fill faces array
        count = 0
        for i in range (0, numY *(numX-1)):
            if count < numY-1:
                A = i
                B = i+1
                C = (i+numY)+1
                D = (i+numY)
                face = (A,B,C,D)
                faces.append(face)
                count = count + 1
            else:
                count = 0

        # create mesh and object
        mesh = bpy.data.meshes.new(name)
        object = bpy.data.objects.new(name,mesh)
        mesh.from_pydata(verts,[],faces)
        mesh.update(calc_edges=True)      
        
        

        
        # move to the geolocalization place. 

        projection = self.projection.getProjection(
            context, 
            lat = (self.BB.top + self.BB.bottom)/2, 
            lon = (self.BB.left + self.BB.right)/2
        )

        # object is created bottom left, so move here.
        v = projection.fromGeographic(self.BB.bottom,self.BB.left)

        object.location = (v[0], v[1], self.height)
        return(object)    

        
#a = BL_FAKETERRAIN(40.335921,-4.849929,-4.805058,40.253744)
#a.create('Terrain', 1000,500,500,1000)

    





