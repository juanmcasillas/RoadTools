 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ///////////////////////////////////////////////////////////////////////////
#
# Read a GPX file, smooth it, ready to build a road in blender, or whatever
#
# ///////////////////////////////////////////////////////////////////////////

import os
import math
import sys
import gpxpy
import gpxpy.gpx
import gpxpy.geo
from gpxtoolbox import GPXItem

class GPX_BB_bounds:
    def __init__(self, max_latitude, min_longitude, max_longitude, min_latitude):
        self.max_latitude = max_latitude
        self.min_longitude = min_longitude
        self.max_longitude = max_longitude
        self.min_latitude = min_latitude
        
class GPX_BB():
    def __init__(self, bounds):
        self.bounds = bounds
        self.calculate()

    def calculate(self):
        self.NW = gpxpy.geo.Location(self.bounds.max_latitude, self.bounds.min_longitude)
        self.NE = gpxpy.geo.Location(self.bounds.max_latitude, self.bounds.max_longitude)
        self.SE = gpxpy.geo.Location(self.bounds.min_latitude, self.bounds.max_longitude)
        self.SW = gpxpy.geo.Location(self.bounds.min_latitude, self.bounds.min_longitude)

        self.width  = self.NW.distance_3d(self.NE)
        self.height = self.NW.distance_3d(self.SW) 

        self.top = self.bounds.max_latitude
        self.left = self.bounds.min_longitude
        self.right = self.bounds.max_longitude
        self.bottom = self.bounds.min_latitude

    def meters_per_deg(self, lat, lon, pad_lat=0.0, pad_lon=0.0):
        "calculates the meters per degree at current lat, lon and if pad is given (in m) the degrees are returned"

        # formulae from here: http://en.wikipedia.org/wiki/Lat-lon

        latr = math.radians(lat)
        lonr = math.radians(lon)

        m_per_deg_lat = 111132.954 -                     \
                        559.822 * math.cos( 2 * latr ) + \
                        1.175 * math.cos(4* latr) -      \
                        0.0023 * math.cos(6 * latr)

        m_per_deg_lon = 111412.84 * math.cos (lonr) - \
                        93.5 * math.cos (3* lonr) +   \
                        0.118 * math.cos (5*lonr)

        # meters per degree in lat, long
        padding_lat = padding_lon = 0.0

        padding_lat = pad_lat if pad_lat == 0.0 else (pad_lat/m_per_deg_lat)
        padding_lon = pad_lon if pad_lon == 0.0 else (pad_lon/m_per_deg_lon)
        

        return( m_per_deg_lat, m_per_deg_lon, padding_lat, padding_lon)

    def incr_value(self, value, delta):

        sign = 1.0 if value > 0 else -1.0
        v = sign * ( math.fabs(value) + delta )
        return(v)

    def expand(self, top=0.0, left=0.0, right=0.0, bottom=0.0):
        "add to the given coords, the space in meters. + adds (grows) - removes (shrinks)"

        # download_terrain_osm(40.324347,-4.588443,-4.566994,40.297759)

        # top left maxlat, minlon
        _, _, mlat, mlon = self.meters_per_deg(self.NW.latitude, self.NW.longitude, math.fabs(top), math.fabs(left))
        self.bounds.max_latitude = self.incr_value( self.NW.latitude, mlat if top > 0 else -mlat )
        self.bounds.min_longitude = self.incr_value( self.NW.longitude, mlon if left > 0 else -mlon )

        # bottom right minlat, maxlon
        # decrease the value (invert the sign)
        _, _, mlat, mlon = self.meters_per_deg(self.SE.latitude, self.SE.longitude, math.fabs(bottom), math.fabs(right))
        self.bounds.min_latitude = self.incr_value( self.SE.latitude, -mlat if bottom > 0 else mlat )
        self.bounds.max_longitude = self.incr_value( self.SE.longitude, -mlon if right > 0 else mlon )

        self.calculate()

    def __repr__(self):
        s =  [ "           %f       " % self.top                               ]
        s += [ " %f          %f" % (self.left, self.right)                     ]
        s += [ "           %f       " % self.bottom                            ]
        s += [ "width (x): %f m" % self.width                                  ]
        s += [ "height (y): %f m" % self.height                                ]
        s += [ "download_terrain_osm(%f,%f,%f,%f)" % (self.top, self.left, self.right, self.bottom) ]
        
        return(os.linesep.join(s))