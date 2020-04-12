 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ///////////////////////////////////////////////////////////////////////////
#
# Read a GPX file, smooth it, ready to build a road in blender, or whatever
#
# ///////////////////////////////////////////////////////////////////////////

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


# ///////////////////////////////////////////////////////////////////////////
#
#
#
# ///////////////////////////////////////////////////////////////////////////

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



def smooth_gpx( gpx_file, optimize=True, ground=False, output="output.gpx",title="output"):
    "if output is none, no file is created :D"

    gpx_loader = GPXLoader(optimize=optimize)
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
    for p in points:
        pn = gpxpy.gpx.GPXTrackPoint(latitude=p[0],longitude=p[1],time=p[2],elevation=p[3])
        if pn.elevation < min_elev:
            min_elev = pn.elevation
        pd.append(pn)

    print("running point optimizer")
    gpx_optimizer = GPXOptimizer()
    opt_points = gpx_optimizer.Optimize(pd)
    gpx_optimizer.Print_stats()
    pd = opt_points

    if len(pd) == 0:
        print("Can't get any points. bailing out")
        return False

    if ground:
        # move all the points to the minimum elevation = 0:
        print("Mininum elevation: %3.2f m" % min_elev)
        for i in range(len(pd)):
            pd[i].elevation -= min_elev

    if output:
        gpx_out = GPXItem()
        data = gpx_out.CreateGPX11(pd, trk_name=title)
        fd = open(output,"w+")
        fd.write(data)
        fd.close()
    
    return (pd, GPX_BB(gpx_loader.bounds) )

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Show data about file and processing", action="count")
    parser.add_argument("-o", "--optimize", help="Optimize GPX input(filter)", action="store_true")
    parser.add_argument("-d", "--distance", help="split the track in distance chunks", action="store", default=10.0)
    parser.add_argument("-g", "--ground", help="Set the mininum altitude as 0 reference", action="store_true")
    parser.add_argument("gpx_file", help="GPX file to load")
    args = parser.parse_args()

    smooth_gpx( args.gpx_file, optimize=args.optimize, ground=args.ground, output="output.gpx",title="output")


