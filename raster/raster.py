#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# raster.py
# 04/17/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# Process some raster files (ARC, ECW) and extract a bounding box,
# so we can manage the result files in blender, for example.
#
# http://centrodedescargas.cnig.es/CentroDescargas/index.jsp
# MDT02 is ETRS89 UTM (zone in the name of the file HU30 -> zone 30)
# https://epsg.io/25830 ETRS89 / UTM zone 30N EPSG:25830

# this is how it's supposed to do, but not works
# with rasterio.open(solar_path, mode='r+') as raster:
#    raster.crs = rasterio.crs.CRS({'init': 'epsg:25830'})
#    show((raster, 1))
#    print(raster.crs)
#
# this is done to reproject
# this creates a prj file (called) with the info. if you do the file, you don't
# need to reproject the data, I think
#
# https://epsg.io/25830 ETRS89 / UTM zone 30N
# PROJCS["ETRS_1989_UTM_Zone_30N",GEOGCS["GCS_ETRS_1989",DATUM["D_ETRS_1989",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-3.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]
# dataset = rasterio.open(ASC)
# print(dataset.bounds)
# reproject_raster(ASC,OUT,crs= rasterio.crs.CRS({'init': 'epsg:25830'}))
# dataset = rasterio.open(OUT)
#
# https://gis.stackexchange.com/questions/299787/finding-pixel-location-in-raster-using-coordinates
#
# ############################################################################

import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.windows import Window, from_bounds
from rasterio.transform import Affine
import pyproj
import numpy
from pyproj import Transformer, transform
import os
import argparse
import json
import rasterio.merge
import subprocess
import tempfile

def reproject_raster(in_path, out_path,crs):
    """reproject a raster image. Call this method if you don't have the .prj file
    for the asc file. But all the IGN files are in the same Proj (UTM H30) so the
    same file is valid

    Arguments:
        in_path {string} -- input file
        out_path {string} -- output file
        crs {string} -- projection string
    """
    # reproject raster to project crs
    with rasterio.open(in_path) as src:
        src_crs = src.crs
        print(src_crs)
        transform, width, height = calculate_default_transform(src_crs, crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()

        kwargs.update({
            'crs': crs,
            'transform': transform,
            'width': width,
            'height': height})

        with rasterio.open(out_path, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=crs,
                    resampling=Resampling.nearest)
    return(out_path)






class Bounds:
    def __init__(self, top=0.0, left=0.0, bottom=0.0, right=0.0, jsonstr=None):
        self.top = top # north
        self.left = left # west
        self.bottom = bottom # south
        self.right = right # east

        if jsonstr:
            self.from_string(jsonstr)

    def from_string(self, jsonstr):
        ret = json.loads(jsonstr)
        for i in ["top","left","bottom","right"]:
            setattr(self,i, ret[i])
        return self


    def from_file(self, fname):
        with open(fname,"r") as f:
            data = f.read()
            ret = json.loads(data)
            self.from_string(data)
        return self

    def __repr__(self):
        s = "<%s top=%f, left=%f, bottom=%f, right=%f>" % (
            self.__class__.__name__, self.top, self.left, self.bottom,self.right
        )
        return s
    

class RasterManager:
    def __init__(self):
        self.outputs = {}
        self.outputs['asc'] = self.save_to_asc
        self.outputs['geotiff'] = self.save_to_geotiff
        self.outputs['png'] = self.save_to_png
        self.outputs['jpg'] = self.save_to_jpg
        self.PROJCS="""PROJCS["ETRS_1989_UTM_Zone_30N",GEOGCS["GCS_ETRS_1989",DATUM["D_ETRS_1989",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-3.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]"""

        self.dest_wgs84 =  pyproj.Proj('EPSG:4326') # WGS84/Geographic
        self.target_utm30N =  pyproj.Proj(self.PROJCS) # WGS84 UTM Zone 30N EPSG:25830
        self.epsg_pnoa = "EPSG:25830"
        self.gdal_dir = '/Applications/QGIS3.12.app/Contents/MacOS/bin'

    def wgs84_to_utm(self, lon,lat):
        """convert from lat, lon in WGS84 (GPS) 'EPSG:4326' UTM zone 30N 'EPSG:25830'

        Arguments:
            lon {float} -- longitude
            lat {float} -- latitude
        """



        point = (lat, lon)
        point_r = pyproj.transform(self.dest_wgs84, self.target_utm30N, *point)
        #x,y
        return(point_r[0], point_r[1])


    def bulk_reproj(self,points):
        """do a bulk reprojection over an array of tuples [(lon, lat),(lon,lat)]
           one call to proj is slow, but
           https://github.com/pyproj4/pyproj/issues/484
           https://pyproj4.github.io/pyproj/stable/advanced_examples.html#optimize-transformations
           does the trick for speed up the projection

        Arguments:
            points {list} -- array of tuples [(lon, lat),(lon,lat)]

        """

        transformer = Transformer.from_proj(proj_from=self.dest_wgs84, proj_to=self.target_utm30N)
        np_points = numpy.array(points)

        # convert the array of points, into np arrays
        lon_coords = np_points[:,0]
        lat_coords = np_points[:,1]

        # call first lat, then lon
        # I don't know how this hell can works properly XD
        r = transformer.transform(lat_coords, lon_coords)


        np_points =numpy.insert(np_points, 2, values=r[0],axis=1)
        np_points =numpy.insert(np_points, 3, values=r[1],axis=1)

        return(np_points)

    def add_prj(self, fout, crs, overwrite=False):
        """creates the .prj file if not found

        Arguments:
            fout {string} -- output file destination

        Keyword Arguments:
            overwrite {bool} -- overwrite the file if exists (default: {False})

        """

        if crs is None:
            crs = self.PROJCS
        P = pyproj.Proj(crs)
        wkt = P.crs.to_wkt(version=pyproj.enums.WktVersion.WKT1_ESRI)

        fdir = os.path.dirname(os.path.abspath(fout))
        base = os.path.basename(fout)
        fname, fext = os.path.splitext(base)
        prj_path = fdir + os.sep + "%s.%s" % (fname, "prj")
        if not os.path.exists(prj_path) or overwrite:
            print("created %s file" % prj_path)
            with open(prj_path, 'w') as f:
                f.write(wkt)

    def rect(self, fin, fout, bounds, mode='asc'):
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

            #big
            lon_a, lat_a = self.wgs84_to_utm(bounds.left, bounds.top) # lon, lat # TOPLEFT
            lon_b, lat_b = self.wgs84_to_utm(bounds.right, bounds.bottom) # lon, lat #BOTTOMRIGHT

            print("NW:", lon_a, lat_a)
            print("SE:", lon_b, lat_b)
            # this return in row, col (Y,X)
            # py_a,px_a = dataset.index( lon_a, lat_a )
            # py_b,px_b = dataset.index( lon_b, lat_b )
            # width = px_b - px_a
            # height = py_b - py_a
            # print("A:",lon_a, lat_a,":", px_a, py_a)
            # print("B:",lon_b, lat_b,":", px_b, py_b)
            # print("width, height: ", width, height)

            bbox = from_bounds(lon_a, lat_b, lon_b, lat_a, dataset.transform) #left, bottom, right, top
            window = dataset.read(window=bbox) # 1 -> 1 channel, nothing, all
            # this is the point (A) scaled, so we can locate coords inside.
            # Affine.scale(res_x, res_x) should be Affine.scale(res_x, res_y) but this generates
            # non square pixels, and insert dx,dy values, that are not supported by noone.
            # tested with GlobalMapper, and it works fine.
            # res_x = (lon_b - lon_a) / width
            # res_y = (lat_b - lat_a) / height
            #transform = Affine.translation(lon_a + res_x, lat_a + res_y) * Affine.scale(res_x, res_x)
            transform = dataset.window_transform(bbox)

            self.outputs[mode](fout, width, height, window, transform, dataset.crs)
            self.add_prj(fout, dataset.crs)

        return True

    def rect_m(self, filenames, fout, bounds, mode='asc'):
        """TBD. Use merge to build a big map"""

        with rasterio.open(filenames[0], mode='r') as dataset:
            print(dataset.crs)
            print(dataset.bounds)

            lon_a, lat_a = self.wgs84_to_utm(bounds.left, bounds.top) # lon, lat # TOPLEFT
            lon_b, lat_b = self.wgs84_to_utm(bounds.right, bounds.bottom) # lon, lat #BOTTOMRIGHT

            print("NW:", lon_a, lat_a)
            print("SE:", lon_b, lat_b)

            utm_bounds = (lon_a, lat_b, lon_b, lat_a)
            fds = []
            for i in filenames:
                src = rasterio.open(i,mode='r')
                fds.append(src)

            #if mode in [ 'geotiff', 'png', 'jpg' ]:
            #    return self.rect_gdal( utm_bounds, filenames, fout)

            print("merging files")
            big_array, big_transform = rasterio.merge.merge(fds,bounds=utm_bounds,precision=50)
            print(big_array.shape, big_transform)

            height = big_array.shape[1]
            width = big_array.shape[2]
            self.outputs[mode](fout, width, height, big_array, big_transform, dataset.crs)
            self.add_prj(fout, dataset.crs)
        return True

    def rect_gdal(self, bounds, filenames, fout):
        
        gda_lbuildvrt = "%s/gdalbuildvrt" % (self.gdal_dir)
        gdal_translate = "%s/gdal_translate" % (self.gdal_dir)

        temp_file = os.path.sep.join( [tempfile.gettempdir(),next(tempfile._get_candidate_names())] )
        # first, create the command to build the virtual merged ECW file
        cmd_list = [ gda_lbuildvrt, temp_file ] + filenames + [ "-a_srs", self.epsg_pnoa ]
        print(cmd_list)
        r = subprocess.run(cmd_list, capture_output=True)
        print(r.stdout)

        left, bottom, right, top = map(lambda x: str(x), bounds)
        cmd_list = [ gdal_translate, "-projwin_srs", self.epsg_pnoa, 
                    "-projwin", left, top, right, bottom,
                    "-of", "PNG", temp_file, fout ]
        print(cmd_list)
        r = subprocess.run(cmd_list, capture_output=True)
        print(r.stdout)
        os.remove(temp_file)
        # $QGIS/gdalbuildvrt MergedECW ecw1 ecw2 ... -a_srs EPSG:25830
        # $QGIS/gdal_translate -projwin_srs EPSG:25830 -projwin left top right bottom -of GTiff MergedECW out.tif




    def save_to_asc(self, fout, width, height, window, transform, crs):
        """save to asc (grid) format. Internal

        Arguments:
            fout {[type]} -- [description]
            width {[type]} -- [description]
            height {[type]} -- [description]
            window {[type]} -- [description]
            transform {[type]} -- [description]
        """
        with rasterio.open(fout,'w',
                driver='AAIgrid',
                height=height,
                width=width,
                count=1,
                dtype=window.dtype,
                crs=crs, # 'epsg:25830'
                nodata=-99999.0,
                transform=transform,
                cellsize=1
        ) as dst:
            dst.write(window)


    def save_to_geotiff(self, fout, width, height, window, transform, crs):
        """save to geotiff format. Internal

        Arguments:
            fout {[type]} -- [description]
            width {[type]} -- [description]
            height {[type]} -- [description]
            window {[type]} -- [description]
            transform {[type]} -- [description]
        """
        with rasterio.open(fout,'w',
                driver='GTiff',
                height=height,
                width=width,
                count=window.shape[0],
                transform=transform,
                # specific for format
                blockxsize=256,
                blockysize=256,
                compress='lzw',
                dtype=window.dtype,
                crs=crs, # 'epsg:25830'
                interleave='band',
                nodata=0,
                tiled=True
        ) as dst:
            dst.write(window)

    def save_to_png(self, fout, width, height, window, transform, crs):
        """save to geotiff format. Internal

        Arguments:
            fout {[type]} -- [description]
            width {[type]} -- [description]
            height {[type]} -- [description]
            window {[type]} -- [description]
            transform {[type]} -- [description]
        """
        with rasterio.open(fout,'w',
                driver='PNG',
                height=height,
                width=width,
                count=window.shape[0],
                dtype=window.dtype,
                transform=transform
        ) as dst:
            dst.write(window)        

    def save_to_jpg(self, fout, width, height, window, transform, crs):
        """save to geotiff format. Internal

        Arguments:
            fout {[type]} -- [description]
            width {[type]} -- [description]
            height {[type]} -- [description]
            window {[type]} -- [description]
            transform {[type]} -- [description]
        """
        with rasterio.open(fout,'w',
                driver='JPEG',
                height=height,
                width=width,
                count=window.shape[0],
                dtype=window.dtype,
                transform=transform
        ) as dst:
            dst.write(window)            

if __name__ == "__main__":

    parser = argparse.ArgumentParser(usage=None,description="Raster Manager. Extract Bounds from big files")

    maingroup = parser.add_argument_group()
    maingroup.add_argument("-v", "--verbose", help="Show data about file and processing", action="count")
    maingroup.add_argument("infile", help="Input File")
    maingroup.add_argument("outfile", help="Output File")
    maingroup.add_argument("product", help="Asc, GeoTiff (default=Asc)", default="asc")

    exgroup = parser.add_argument_group(title='Json or Coords')
    group = exgroup.add_mutually_exclusive_group(required=True)
    group.add_argument('-j','--json',nargs=1,help='''{"top":40.4,"left":-4.32,"bottom":40.36,"right":-4.2}''')
    group.add_argument('-c','--coords',nargs=4, metavar=('top','left','bottom','right'), type=float)
    args = parser.parse_args()


    rasterman = RasterManager()
    if args.product not in rasterman.outputs.keys():
        raise TypeError("product not valid: %s" % args.product)

    if args.coords:
        bounds = Bounds(top=args.coords[0],left=args.coords[1],bottom=args.coords[2],right=args.coords[3])
    else:
        bounds = Bounds(jsonstr=args.json[0])
    
    if args.verbose:
        print(bounds)

    rasterman.rect(args.infile, args.outfile, bounds, mode=args.product)
  
