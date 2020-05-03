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


def surround_band(x, y, hop =1, left=True):
    "do a left or right band"
    r = []
    x_low = x-hop
    x_high = x
    if not left:
        x_low = x
        x_high = x+1+hop

    for j in range(y-hop,y+1+hop):
        for i in range(x_low, x_high):
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


from itertools import islice

def chunck(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())

def build_rectangles(points, gpx_bounds, distance=5):

    rects = []
    for i in range(len(points)-2):
        a = points[i]
        b = points[i+1]
        if a == b:
            continue

        left, right = calculate_perp(a, b, distance, gpx_bounds)
        rects.append( (left, a, right ) )

        if i == len(points)-2:
            right, left = calculate_perp(b, a, distance, gpx_bounds)
            rects.append((left, a, right ))

    return rects


def draw_line(start, end):
    """Bresenham's Line Algorithm
    Produces a list of tuples from start and end

    >>> points1 = get_line((0, 0), (3, 4))
    >>> points2 = get_line((3, 4), (0, 0))
    >>> assert(set(points1) == set(points2))
    >>> print points1
    [(0, 0), (1, 1), (1, 2), (2, 3), (3, 4)]
    >>> print points2
    [(3, 4), (2, 3), (1, 2), (1, 1), (0, 0)]
    """
    # Setup initial conditions
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1

    # Determine how steep the line is
    is_steep = abs(dy) > abs(dx)

    # Rotate line
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2

    # Swap start and end points if necessary and store swap state
    swapped = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        swapped = True

    # Recalculate differentials
    dx = x2 - x1
    dy = y2 - y1

    # Calculate error
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1

    # Iterate over bounding box generating points between start and end
    y = y1
    points = []
    for x in range(x1, x2 + 1):
        coord = (y, x) if is_steep else (x, y)
        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx

    # Reverse the list if the coordinates were swapped
    if swapped:
        points.reverse()
    return points


def fill(x,y, empty, data, nodata_value, val=None):

    if y <0 or y >= empty.shape[1] or x <0 or x >= empty.shape[2]:
        return

    if empty[0][y,x] != val:
        empty[0][y,x] = val
        fill(x + 1, y , empty, data, nodata_value, val=val)
        fill(x , y + 1, empty, data, nodata_value, val=val)
        fill(x-1 , y , empty, data, nodata_value, val=val)
        fill(x , y-1 , empty, data, nodata_value, val=val)
        fill(x-1 , y-1 , empty, data, nodata_value, val=val)
        fill(x-1 , y+1 , empty, data, nodata_value, val=val)
        fill(x+1 , y-1 , empty, data, nodata_value, val=val)
        fill(x+1 , y+1 , empty, data, nodata_value, val=val)

class RasterEdit(RasterManager):
    def __init__(self):
        RasterManager.__init__(self)




    def rect(self, fin, fout, fmd25, bounds, points, mode='asc', hop=2, carve=-1, gpx_bounds=None, dontmove=False):

        rects = build_rectangles(points, gpx_bounds, distance=hop/2)

        pd = []
        for r in rects:
            for p in r:
                pd.append((p.longitude, p.latitude, p.elevation)) # left, center, right

        pd = self.bulk_reproj(pd)
        # each three points in pd, represent, in order, the edge of the polygon

        rects = chunck(pd, 3)
        nodata_value = -10.0
        lon_idx = 2
        lat_idx = 3
        elev_idx = 4

        lowres_dataset = rasterio.open(fmd25, mode='r')
        lowres_data = lowres_dataset.read()

        with rasterio.open(fin, mode='r') as dataset:
            print(dataset.crs)
            print(dataset.bounds)
            print(dataset.width, dataset.height)
            data = dataset.read()
            empty = numpy.full_like(data,nodata_value )


            chuncks = list(chunck(pd, 3))
            for i in range(len(chuncks)-2):
                low = chuncks[i]
                high = chuncks[i+1]

                bl,_,br = low
                tl,_,tr = high

                bl_y,bl_x = dataset.index(bl[lon_idx],bl[lat_idx])
                br_y,br_x = dataset.index(br[lon_idx],br[lat_idx])


                tl_y,tl_x = dataset.index(tl[lon_idx],tl[lat_idx])
                tr_y,tr_x = dataset.index(tr[lon_idx],tr[lat_idx])

                br_z = br[elev_idx]
                bl_z = bl[elev_idx]
                tr_z = tr[elev_idx]
                tl_z = tl[elev_idx]

                c_z = (br_z+bl_z+tr_z+tl_z) / 4
                c_x, c_y  = bl[lon_idx] + (tr[lon_idx]-bl[lon_idx])/2, bl[lat_idx] + (tr[lat_idx]-bl[lat_idx])/2,
                c_y, c_x = dataset.index(c_x, c_y)



                draw_points = []
                draw_points += draw_line((bl_x,bl_y),(br_x,br_y)) # bottom
                #draw_points += draw_line((tl_x,tl_y),(tr_x,tr_y)) # top
                #draw_points += draw_line((bl_x,bl_y),(tl_x,tl_y)) # left
                #draw_points += draw_line((br_x,br_y),(tr_x,tr_y)) # right

                # copy terrain
                for x, y, dx, dy in surround_point(c_x, c_y ,hop=hop):

                    # translate reversal and map again
                    utm_x, utm_y = dataset.xy(y, x)
                    ##print(x,y, utm_x, utm_y)
                    yl, xl = lowres_dataset.index(utm_x, utm_y)

                    if y <0 or y >= empty.shape[1] or x <0 or x >= empty.shape[2]:
                        continue
                    #if y <0 or y >= lowres_data.shape[1] or x <0 or x >= lowres_data.shape[2]:
                    #    continue
                    empty[0][y,x] = data[0][y,x]  if empty[0][y,x] == nodata_value else empty[0][y,x]

                # flatten the bottom line (move to the track)
                dontmove = False
                if not dontmove:
                    for p in draw_points:
                        ax,ay = p
                        for x, y, dx, dy in surround_point(ax, ay ,hop=1):
                            #far_value = data[0][y,x]
                            #near_value = c_z
                            #value = numpy.interp(dx,[0,hop],[near_value,far_value])
                            if y <0 or y >= empty.shape[1] or x <0 or x >= empty.shape[2]:
                                continue
                            empty[0][y,x] = c_z-0.5


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
    parser.add_argument("-X", "--dontmove", help="Don't move, only copy", action="store_true")
    parser.add_argument("-w", "--width", help="explore from bounds", type=int, default=2)
    parser.add_argument("-p", "--carve", help="carve inside", type=int, default=-1)
    maingroup.add_argument("gpxfile", help="GPX file")
    maingroup.add_argument("infile", help="Input File")
    maingroup.add_argument("md25file", help="Input File Low res")
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
                #optimize=args.optimize,
                optimize=False, ## use all the available points
                height_offset=args.moveelev,
                xy_offset=args.movexy,
                zero=False,
                geoid=args.geoid,
                output=None)

    # calculate the average difference between "terrain" and gpx
    avg_height = rasteredit.calculate_avg_height( args.infile, points)
    print("move to:", avg_height)
    # and move all the points on the gpx track that distance to the "terrain"
    if not args.geoid:
        for i in range(len(points)):
            points[i].elevation += avg_height

    # move the terrain to the gpx
    rasteredit.rect(args.infile, args.outfile, args.md25file, bounds, points, hop=args.width, carve=args.carve, gpx_bounds=gpx_bounds, dontmove=args.dontmove)
