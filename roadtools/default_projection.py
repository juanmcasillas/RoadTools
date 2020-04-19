#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# default_projection.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# implements the default (mercator) projection for project elements in 
# blender using lat/lon
# 
# ############################################################################

import sys
import bpy
import math
import pyproj

_isBlender280 = bpy.app.version[1] >= 80

class DefaultProjection:
    def __init__(self, ignoreGeoreferencing=False):
        self.ignoreGeoreferencing = ignoreGeoreferencing
        self.bpyproj = "bpyproj" in (bpy.context.preferences.addons if _isBlender280 else bpy.context.user_preferences.addons) and sys.modules.get("bpyproj")

    #self.getProjection(context, lat = (minLat + maxLat)/2, lon = (minLon + maxLon)/2)
    def getProjection(self, context, lat, lon):
        # get the coordinates of the center of the Blender system of reference
        scene = context.scene
        if "lat" in scene and "lon" in scene and not self.ignoreGeoreferencing:
            lat = scene["lat"]
            lon = scene["lon"]
        else:
            scene["lat"] = lat
            scene["lon"] = lon
        
        projection = None
        if self.bpyproj:
            projection = self.bpyproj.getProjection(lat, lon)
        if not projection:
            # fall back to the Transverse Mercator
            projection = TransverseMercator(lat=lat, lon=lon)
        return projection

class TransverseMercator:


    def __init__(self, **kwargs):
        # setting default values
        self.lat = 0 # in degrees
        self.lon = 0 # in degrees
        self.utm30N = pyproj.Proj('+init=epsg:25830')   # UTM30N
        self.wgs84 =  pyproj.Proj('+init=epsg:4326')    # WGS84/Geographic

        for attr in kwargs:
            setattr(self, attr, kwargs[attr])
        self.latInRadians = math.radians(self.lat)
        
        # generate the x,y point of the "center" of projection
        self.utmx, self.utmy = pyproj.transform(self.wgs84, self.utm30N, self.lon, self.lat)
        print("Offset UTM", self.utmx, self.utmy)

    def fromGeographic(self, lat, lon):
        # from WGS84 to utm
        print("current values (lon,lat)", self.lon, self.lat)
        point = (lon,lat)
        print("from",point)
        point_r = pyproj.transform(self.wgs84, self.utm30N, *point)
        print(point_r)
        point_r = ( point_r[0]-self.utmx, point_r[1]-self.utmy )
        print("to",point_r)
        return(point_r)

    def toGeographic(self, x, y):
        # from UTM to WGS84
        # don't know if works
        point = (x,y)
        point_r = pyproj.transform(self.utm30N, self.wgs84, *point)
        return (point_r[0]+self.lon, point_r[0].self.lat)


