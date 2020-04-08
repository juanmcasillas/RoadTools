import sys
import bpy
import math


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
    radius = 6378137

    def __init__(self, **kwargs):
        # setting default values
        self.lat = 0 # in degrees
        self.lon = 0 # in degrees
        self.k = 1 # scale factor
        
        for attr in kwargs:
            setattr(self, attr, kwargs[attr])
        self.latInRadians = math.radians(self.lat)

    def fromGeographic(self, lat, lon):
        lat = math.radians(lat)
        lon = math.radians(lon-self.lon)
        B = math.sin(lon) * math.cos(lat)
        x = 0.5 * self.k * self.radius * math.log((1+B)/(1-B))
        y = self.k * self.radius * ( math.atan(math.tan(lat)/math.cos(lon)) - self.latInRadians )
        return (x,y)

    def toGeographic(self, x, y):
        x = x/(self.k * self.radius)
        y = y/(self.k * self.radius)
        D = y + self.latInRadians
        lon = math.atan(math.sinh(x)/math.cos(D))
        lat = math.asin(math.sin(D)/math.cosh(x))

        lon = self.lon + math.degrees(lon)
        lat = math.degrees(lat)
        return (lat, lon)


