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


def surround_point(x, y, hop =1):
    r = []
    for j in range(y-hop,y+1+hop):
        for i in range(x-hop, x+1+hop):
            dx = abs(x-i)
            dy = abs(y-j)
            r.append((i, j, dx, dy))
    return r

class RasterEdit(RasterManager):
    def __init__(self):
        RasterManager.__init__(self)


    def rect(self, fin, fout, bounds, points, mode='asc'):
        """crops a rectangle of Bounds, from a file. Returns a asc (grid) or geotiff

        Arguments:
            fin {string} -- input file
            fout {string} -- output file path
            bounds {bound class} -- a class with top,left,bottom,right attrs

        Keyword Arguments:
            mode {string} -- output file mode. can be 'asc' or 'geotiff' (default: {'asc'})

        Returns:
            [bool] -- Nothing, for now. True
        """




        with rasterio.open(fin, mode='r') as dataset:
            print(dataset.crs)
            print(dataset.bounds)
            print(dataset.width, dataset.height)
            data = dataset.read()


            avg_ahead = 10
            for count in range(len(points)):
                i = points[count]
                if count > 0 and count+avg_ahead < len(points)-1:
                    avg_elev = 0
                    for x in range(avg_ahead):
                        avg_elev += points[count+avg_ahead].elevation
                    avg_elev = avg_elev/avg_ahead
                else:
                    if count == 0:
                        avg_elev = points[count].elevation
                    else:
                        rr = len(points)-1-count
                        avg_elev = 0
                        for x in range(rr):
                            avg_elev += points[count+x].elevation
                        avg_elev = avg_elev/avg_ahead


                lon, lat = self.wgs84_to_utm(i.longitude, i.latitude) # lon, lat # TOPLEFT

                # this return in row, col (Y,X)
                py,px = dataset.index( lon, lat )
                print("P:",lon, lat,":", px, py)

                for x, y, dx, dy in surround_point(px,py,hop=2):
                    #print(x,y, dx, dy)
                    if dx == 2 or dy == 2:
                        data[0][y,x] = data[0][y,x] - (data[0][y,x]-avg_elev)/5
                    elif dx == 1 or dy == 1:
                        data[0][y,x] = data[0][y,x] - (data[0][y,x]-avg_elev)/3
                    else:
                        data[0][y,x]= avg_elev-0.11



            with rasterio.open(fout,'w',
                driver='AAIgrid',
                height=dataset.height,
                width=dataset.width,
                count=1,
                dtype=data.dtype,
                crs=dataset.crs, # 'epsg:25830'
                nodata=-99999.0,
                transform=dataset.transform,
                cellsize=1
            ) as dst:
                dst.write(data)
            self.add_prj(fout, dataset.crs)

        return True





if __name__ == "__main__":

    parser = argparse.ArgumentParser(usage=None,description="Raster Manager. Extract Bounds from big files")

    maingroup = parser.add_argument_group()
    maingroup.add_argument("-v", "--verbose", help="Show data about file and processing", action="count")
    parser.add_argument("-o", "--optimize", help="Optimize GPX input(filter)", action="store_true")
    parser.add_argument("-mxy", "--movexy", help="Offset to the left <0 or right >0 in the XY plane", type=float, default=0.0)
    parser.add_argument("-melev", "--moveelev", help="Offset Height", type=float, default=0.0)
    parser.add_argument("-g", "--geoid", help="Calculate the geoid N value and fix altitude", action="store_true")

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
        bounds = Bounds(jsonstr=args.json[0])

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
    rasteredit.rect(args.infile, args.outfile, bounds, points)
