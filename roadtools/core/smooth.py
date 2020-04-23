#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# smooth.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# Read a GPX file, smooth it, ready to build a road in blender, or whatever
#
# ############################################################################

import os
import numpy as np
import math
import argparse
import sys
import gpxpy
import gpxpy.gpx
import gpxpy.geo
import pyproj
from gpx_optimizer import GPXOptimizer, savitzky_golay
from slopes import SlopeManager
from gpxtoolbox import GPXItem
import datetime
from gpxbb import GPX_BB
from geoid import GeoidHeight

class ProjectionMapper:
    """
    project a WSG84 to UTM
    z, l, x, y = project((point.longitude, point.latitude))
    """

    def __init__(self):
        self._projections = {}

    def zone(self,coordinates):
        if 56 <= coordinates[1] < 64 and 3 <= coordinates[0] < 12:
            return 32
        if 72 <= coordinates[1] < 84 and 0 <= coordinates[0] < 42:
            if coordinates[0] < 9:
                return 31
            elif coordinates[0] < 21:
                return 33
            elif coordinates[0] < 33:
                return 35
            return 37
        return int((coordinates[0] + 180) / 6) + 1


    def letter(self,coordinates):
        return 'CDEFGHJKLMNPQRSTUVWXX'[int((coordinates[1] + 80) / 8)]

    def project(self,coordinates): # lon, lat
        z = self.zone(coordinates)
        l = self.letter(coordinates)
        if z not in self._projections:
            self._projections[z] = pyproj.Proj(proj='utm', zone=z, ellps='WGS84')
        x, y = self._projections[z](coordinates[0], coordinates[1])
        if y < 0:
            y += 10000000
        return z, l, x, y

    def project_2(self, lon, lat):

        myProj = pyproj.Proj("+proj=utm +zone=30T, +north +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
        UTMx, UTMy = myProj(lon, lat)
        #print(lat, lon, UTMx, UTMy)
        return (UTMx, UTMy)

    def unproject(self, z, l, x, y):
        if z not in self._projections:
            self._projections[z] = pyproj.Proj(proj='utm', zone=z, ellps='WGS84')
        if l < 'N':
            y -= 10000000
        lng, lat = self._projections[z](x, y, inverse=True)
        return (lng, lat)


# ///////////////////////////////////////////////////////////////////////////
#
#
#
# ///////////////////////////////////////////////////////////////////////////

class GPXLoader:
    def __init__(self, fname=None, optimize=False, reproject=False):
        self.fname = fname
        self.optimize = optimize
        self.reproject = reproject
        self.bounds = None

    def load(self,fname=None):
        f = fname or self.fname
        if f is None:
            raise ValueError("GPX file is None")
        if not os.path.exists(f):
            raise RuntimeError("GPX file %s not found" % f)

        gpx_file = open(f, 'r')
        gpx_data = gpxpy.parse(gpx_file)

        self.bounds = gpx_data.get_bounds()
        points = []
        pm = ProjectionMapper()

        # call my optimizer (remove contiguous points)
        points = []
        for track in gpx_data.tracks:
            for segment in track.segments:
                points += segment.points

        gpx_data.tracks[0].segments[0].points = points
        self.length_3d = gpx_data.tracks[0].length_3d()

        print("Loaded %d points" % len(points))
        #if self.optimize:
        #    gpx_optimizer = GPXOptimizer()
        #    opt_points = gpx_optimizer.Optimize(points)
        #    gpx_optimizer.Print_stats()
        #    points = opt_points

        elevs = []
        ret_points = []


        # don't reproject to UTM

        if self.reproject:
            for point in points:
                z, l, x, y = pm.project((point.longitude, point.latitude))
                point.x = x
                point.y = y
                ret_points += [x, y, point.time, point.elevation]
                self.optimize and elevs.append(point.elevation)
        else:
            for point in points:
                if not point.time:
                    #timezone = pytz.timezone("Zulu")
                    point.time = datetime.datetime.now()
                    #point.time = timezone.localize(point.time)
                ret_points += [point.latitude, point.longitude, point.time , point.elevation]
                self.optimize and elevs.append(point.elevation)

        if self.optimize:
            #smoothed_elevations = savitzky_golay( np.array(elevs) , 11, 5)
            print("doing savitzky_golay")
            #smoothed_elevations = savitzky_golay( np.array(elevs) , 51, 9)
            smoothed_elevations = savitzky_golay( np.array(elevs) , 51, 2)

            ret_points = np.array(ret_points).reshape( int(len(ret_points)/4), 4)
            ret_points[:,3] = smoothed_elevations[0:len(elevs)]

            print("Smoothed %d points" % len(ret_points))
            ##draw_elev(elevs,smoothed_elevations)


        return(ret_points)


# ///////////////////////////////////////////////////////////////////////////
#
#
#
# ///////////////////////////////////////////////////////////////////////////

def draw(points, reshape=False):
    import matplotlib.pyplot as plt
    if reshape:
        d = np.array(points).reshape(int(len(points)/4),4)
    else:
        d = points
    x = d[:,[0]]
    y = d[:,[1]]
    plt.plot(x,y, linestyle="",marker="o")
    plt.show()

def draw_elev(elevs,smooth):
    import matplotlib.pyplot as plt
    from scipy.interpolate import splrep, splev
    from scipy.interpolate import make_interp_spline, BSpline

    idx = np.arange(0,len(elevs))
    plt.plot(idx,elevs, color="grey")
    plt.plot(idx,smooth, color="lime")

    #some interpolation methods, but savitzky_golay with high window size, and
    #high poly order does the trick fast

    #xnew = np.linspace(idx.min(), idx.max(), 300)
    #spl = make_interp_spline(idx, smooth, k=5)  # type: BSpline
    #elev_smooth_spl = spl(xnew)
    #plt.plot(xnew,elev_smooth_spl, color="blue")

    ##bspl = splrep(idx,elevs,s=5)
    ##bspl_y = splev(idx,bspl)
    ##plt.plot(idx,bspl_y, color="blue")

    plt.show()



def smooth_gpx( gpx_file, optimize=True, zero=False, geoid=False, output="output.gpx",title="output", height_offset=0.0, xy_offset=0.0):
    "if output is none, no file is created :D"

    gpx_loader = GPXLoader(optimize=True) # allways smooth elevations
    points = gpx_loader.load(gpx_file)

    bb = GPX_BB(gpx_loader.bounds)
    print(bb)
    #print(bb.meters_per_deg(bb.NW.latitude, bb.NW.longitude, 100, 100))
    #bb.expand(1000,500,500,1000)
    #print(bb)

    #
    # build the "dict" again
    #

    pd = []
    min_elev = sys.maxsize

    geoidman = None
    if geoid:
        print("Using Geoid (N) correction elevation")
        geoidman = GeoidHeight()

    for p in points:

        # apply the height_offset in the elevation for all the points, if found
        p[3] = p[3] + height_offset

        pn = gpxpy.gpx.GPXTrackPoint(latitude=p[0],longitude=p[1],time=p[2],elevation=p[3])
        if pn.elevation < min_elev:
            min_elev = pn.elevation

        # calculate geoid elevation and apply it
        if geoid:
             N = geoidman.get(pn.latitude, pn.longitude)
             pn.elevation = pn.elevation-N


        pd.append(pn)

    if optimize:
        print("running point optimizer")
        gpx_optimizer = GPXOptimizer()
        opt_points = gpx_optimizer.Optimize(pd)
        gpx_optimizer.Print_stats()
        pd = opt_points

    if len(pd) == 0:
        print("Can't get any points. bailing out")
        return False

    if zero:
        # move all the points to the minimum elevation = 0:
        print("Mininum elevation: %3.2f m" % min_elev)
        for i in range(len(pd)):
            pd[i].elevation -= min_elev

   
    # calculate a offset in the XY plane. This is useful to move the road
    # to the left, or to the right. Note that most of GPX tracks are recorder
    # on bicycle, and I run in the most right side of the road, when the road's
    # center is about 3.5-4m left

    if xy_offset != 0.0:
        move_offset =abs(xy_offset) #(5 meters)
        to_left = True if xy_offset < 0 else False 
        for i in range(len(pd)-1):
            a = pd[i]
            b = pd[i+1]
            if a == b:
                continue
            v = (b.longitude-a.longitude, b.latitude - a.latitude)
            vt = (-v[1], v[0]) 
            
            vmod = math.sqrt( vt[0]*vt[0] + vt[1]*vt[1])
            
            vt = ( vt[0] / vmod, vt[1] / vmod)
            # the vector is opposite to the standard rotation (CCW)
            # if you want to move to the right (CW)
            if not to_left:
                vt = (-vt[0], -vt[1])

            offset_lat, offset_lon, _, _  = bb.meters_per_deg(pd[i].latitude, pd[i].longitude)
            pd[i].longitude += vt[0]* (move_offset / offset_lon)
            pd[i].latitude  += vt[1]* (move_offset / offset_lat)


    if output:
        gpx_out = GPXItem()
        data = gpx_out.CreateGPX11(pd, trk_name=title)
        fd = open(output,"w+")
        fd.write(data)
        fd.close()

    print("length:", gpx_loader.length_3d)
    return (pd, GPX_BB(gpx_loader.bounds), gpx_loader.length_3d )

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Show data about file and processing", action="count")
    parser.add_argument("-o", "--optimize", help="Optimize GPX input(filter)", action="store_true")
    parser.add_argument("-z", "--zero", help="Set the mininum altitude as 0 reference", action="store_true")
    parser.add_argument("-g", "--geoid", help="Calculate the geoid N value and fix altitude", action="store_true")
    parser.add_argument("-m", "--move", help="Offset to the left <0 or right >0 in the XY plane", type=float, default=0.0)
    parser.add_argument("gpx_file", help="GPX file to load")
    args = parser.parse_args()

    _,_,d = smooth_gpx( args.gpx_file, optimize=args.optimize, zero=args.zero, geoid=args.geoid, xy_offset=args.move, output="output.gpx",title="output")
    print(d)


