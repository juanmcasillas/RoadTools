#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# modify_asc.py
# 04/17/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# try to plot some points in the ASC grid file
#
#
# $PYQGIS37 modify_asc.py -v -j '{"top":40.41125364200409,"left":-4.320936889648445,"bottom":40.36328982190341,"right":-4.238021545410162}' ../../gpx/AC_navas_bajada_puerto.GPX  ../../raster/subset.asc ../../raster/subset_edit.asc
#
# ############################################################################

import rasterio
import argparse
from raster import Bounds, RasterManager
import json
from smooth import smooth_gpx
import numpy
from pyproj import Transformer, transform
import math

def surround_point(x, y, hop =1):
    r = []
    for j in range(y-hop,y+1+hop):
        for i in range(x-hop, x+1+hop):
            dx = abs(x-i)
            dy = abs(y-j)
            r.append((i, j, dx, dy))
    return r


class Point:
    def __init__(self, lon, lat, elev):
        self.latitude = lat
        self.longitude = lon
        self.elevation = elev

    def __eq__(self, other):
        return self.latitude == other.latitude and \
            self.longitude == other.longitude and \
            self.elevation == other.elevation
    
    def __repr__(self):
        s = "<Point: latitude=%f, longitude=%f, elevation=%f>" % (self.latitude, self.longitude, self.elevation)
        return s


def calculate_perp(a, b, meters, gpx_bounds):
    move_offset =abs(meters) #(5 meters)


    if a == b:
        return (None, None)
        
    v = (b.longitude-a.longitude, b.latitude - a.latitude)
    # cross product
    vt = (-v[1], v[0]) 
    vmod = math.sqrt( vt[0]*vt[0] + vt[1]*vt[1])
    

    left = ( vt[0] / vmod, vt[1] / vmod)
    # the vector is opposite to the standard rotation (CCW)
    # if you want to move to the right (CW)
    right = (-left[0], -left[1])

    offset_lat, offset_lon, _, _  = gpx_bounds.meters_per_deg(a.latitude, a.longitude)
    
    left_lon = a.longitude + left[0]* (move_offset / offset_lon)
    left_lat = a.latitude  + left[1]* (move_offset / offset_lat)
    
    right_lon = a.longitude + right[0]* (move_offset / offset_lon)
    right_lat = a.latitude  + right[1]* (move_offset / offset_lat) 

    return Point(left_lon, left_lat, a.elevation), Point(right_lon, right_lat, a.elevation)


class RasterEdit(RasterManager):
    def __init__(self):
        RasterManager.__init__(self)

    def rect(self, fin, fout, bounds, points, mode='asc', hop=2, carve=-1, gpx_bounds=None):


        pd = []
        for p in points:
            pd.append((p.longitude, p.latitude, p.elevation))
        pd = self.bulk_reproj(pd)
        nodata_value = -10.0

        with rasterio.open(fin, mode='r') as dataset:
            print(dataset.crs)
            print(dataset.bounds)
            print(dataset.width, dataset.height)
            data = dataset.read()
            print(data.shape)

            empty = numpy.full_like(data,nodata_value )
            print(empty.shape)

            for count in range(len(pd)):
                i = pd[count]

                work_points = [i]
                if count+1 < len(pd)-1:
                    j = pd[count+1]
                    a = Point(i[0],i[1],i[4])
                    b = Point(j[0],j[1],j[4])
                    left, right = calculate_perp(a, b, 5, gpx_bounds)
                    if left and right and False: 
                        # do a kludge here for test
                        # wgs84_to_utm(bounds.left, bounds.top)
                        lx, ly = self.wgs84_to_utm(left.longitude,left.latitude )
                        rx, ry = self.wgs84_to_utm(right.longitude,right.latitude )
                        lt = (0,0, lx, ly, left.elevation)
                        rt = (0,0, rx, ry, right.elevation)

                        #work_points += [ lt, rt ]
                    
      
                for wp in work_points:
                    lon, lat, elev = wp[2], wp[3], wp[4] # utm_x, utm_y

                    # this return in row, col (Y,X)
                    py,px = dataset.index( lon, lat )
                    #print("P:",lon, lat,":", px, py, hop, carve)

                    for x, y, dx, dy in surround_point(px,py,hop=hop):
                        #print(x,y, dx, dy,carve)
                        if dx < carve or dy < carve:
                            continue
                        # if we're inside the track ,then add the point.
                        if y >=0 and y < empty.shape[1] and x >=0 and x < empty.shape[2]:
 
                            far_value = data[0][y,x]
                            near_value = elev
                            
                            value = numpy.interp(max(dx,dy),[0,hop],[near_value,far_value])
                            print(value)
                            empty[0][y,x] = value if empty[0][y,x] == nodata_value else empty[0][y,x]



            with rasterio.open(fout,'w',
                driver='AAIgrid',
                height=dataset.height,
                width=dataset.width,
                count=1,
                dtype=data.dtype,
                crs=dataset.crs, # 'epsg:25830'
                nodata=nodata_value,
                transform=dataset.transform,
                cellsize=1
            ) as dst:
                dst.write(empty)
            self.add_prj(fout, dataset.crs)

        return True


    def calculate_avg_height(self, fin, points):

        pd = []
        for p in points:
            pd.append((p.longitude, p.latitude, p.elevation))
        pd = self.bulk_reproj(pd)
        nodata_value = -10.0

        with rasterio.open(fin, mode='r') as dataset:
            data = dataset.read()
            empty = numpy.full_like(data, nodata_value )
            avg_height = 0.0
            j = 0
            for count in range(len(pd)):
                i = pd[count]

                lon, lat, elev = i[2], i[3], i[4] # utm_x, utm_y

                y,x = dataset.index( lon, lat )
                if y >=0 and y < empty.shape[1] and x >=0 and x < empty.shape[2]:
                    avg_height += (data[0][y,x] - elev)
                    j += 1
                else:
                    pass
            return avg_height / j

if __name__ == "__main__":

    parser = argparse.ArgumentParser(usage=None,description="Raster Manager. Extract Bounds from big files")

    maingroup = parser.add_argument_group()
    maingroup.add_argument("-v", "--verbose", help="Show data about file and processing", action="count")
    parser.add_argument("-o", "--optimize", help="Optimize GPX input(filter)", action="store_true")
    parser.add_argument("-mxy", "--movexy", help="Offset to the left <0 or right >0 in the XY plane", type=float, default=0.0)
    parser.add_argument("-melev", "--moveelev", help="Offset Height", type=float, default=0.0)
    parser.add_argument("-g", "--geoid", help="Calculate the geoid N value and fix altitude", action="store_true")
    parser.add_argument("-w", "--width", help="explore from bounds", type=int, default=2)
    parser.add_argument("-p", "--carve", help="carve inside", type=int, default=-1)
    maingroup.add_argument("gpxfile", help="GPX file")
    maingroup.add_argument("infile", help="Input File")
    maingroup.add_argument("outfile", help="Output File")


    exgroup = parser.add_argument_group(title='Json or Coords')
    group = exgroup.add_mutually_exclusive_group(required=True)
    group.add_argument('-j','--json',nargs=1,help='''{"top":40.4,"left":-4.32,"bottom":40.36,"right":-4.2}''')
    group.add_argument('-c','--coords',nargs=4, metavar=('top','left','bottom','right'), type=float)
    args = parser.parse_args()

    if args.coords:
        bounds = Bounds(top=args.coords[0],left=args.coords[1],bottom=args.coords[2],right=args.coords[3])
    else:
        bounds = Bounds()
        bounds.from_file(args.json[0])

    if args.verbose:
        print(bounds)

    # read the gpx
    rasteredit = RasterEdit()

    points,gpx_bounds,distance = smooth_gpx(args.gpxfile,
                optimize=args.optimize,
                height_offset=args.moveelev,
                xy_offset=args.movexy,
                zero=False,
                geoid=args.geoid,
                output=None)

    # calculate the average difference between "terrain" and gpx
    avg_height = rasteredit.calculate_avg_height( args.infile, points)
    print("move to:", avg_height)
    # and move all the points on the gpx track that distance to the "terrain"
    for i in range(len(points)):
        points[i].elevation += avg_height

    # move the terrain to the gpx
    rasteredit.rect(args.infile, args.outfile, bounds, points, hop=args.width, carve=args.carve, gpx_bounds=gpx_bounds)
