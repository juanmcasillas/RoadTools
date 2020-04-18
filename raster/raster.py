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
    def __init__(self, top=0.0, left=0.0, bottom=0.0, right=0.0):
        self.top = top # north
        self.left = left # west
        self.bottom = bottom # south
        self.right = right # east

class RasterManager:
    def __init__(self):
        self.outputs = {}
        self.outputs['asc'] = self.save_to_asc
        self.outputs['geotiff'] = self.save_to_geotiff
        self.PROJCS="""PROJCS["ETRS_1989_UTM_Zone_30N",GEOGCS["GCS_ETRS_1989",DATUM["D_ETRS_1989",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-3.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]"""

        self.dest_wgs84 =  pyproj.Proj('EPSG:4326') # WGS84/Geographic
        self.target_utm30N =  pyproj.Proj(self.PROJCS) # WGS84 UTM Zone 30N EPSG:25830


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

            # this return in row, col (Y,X)
            py_a,px_a = dataset.index( lon_a, lat_a )
            py_b,px_b = dataset.index( lon_b, lat_b )

            width = px_b - px_a
            height = py_b - py_a

            print("A:",lon_a, lat_a,":", px_a, py_a)
            print("B:",lon_b, lat_b,":", px_b, py_b)
            print("width, height: ", width, height)

            bbox = from_bounds(lon_a, lat_b, lon_b, lat_a, dataset.transform) #left, bottom, right, top
            window = dataset.read(window=bbox) # 1 -> 1 channel, nothing, all
            res_x = (lon_b - lon_a) / width
            res_y = (lat_b - lat_a) / height
            # this is the point (A) scaled, so we can locate coords inside.
            # Affine.scale(res_x, res_x) should be Affine.scale(res_x, res_y) but this generates
            # non square pixels, and insert dx,dy values, that are not supported by noone.
            # tested with GlobalMapper, and it works fine.
            transform = Affine.translation(lon_a + res_x, lat_a + res_y) * Affine.scale(res_x, res_x)

            self.outputs[mode](fout, width, height, window, transform, dataset.crs)
            self.add_prj(fout, dataset.crs)

        return True

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

if __name__ == "__main__":

    rm = RasterManager()
    # asc test
    # picadas
    # bounds = Bounds(top=40.4076142700,left=-4.3395996094,bottom=40.3579254107,right=-4.2232131958)
    # f_in="K:\Cartography\MDT05\PNOA_MDT05_ETRS89_HU30_0557_LID.asc"
    # f_out="K:\Cartography\MDT05\subset.asc"
    # rm.rect(f_in, f_out, bounds ,mode='asc')
    # # geotiff test
    # f_in="K:\Cartography\PNOA\PNOA_MA_OF_ETRS89_HU30_h50_0557.ecw"
    # f_out="K:\Cartography\PNOA\subset.tif"
    # rm.rect(f_in, f_out, bounds ,mode='geotiff')

    # galayos
    #Top (N): 40.263546616792624
    #Left (W): -5.1788258082264305
    #Right (E): -5.169102583586535
    #Bottom (S): 40.25541390947118

    bounds = Bounds(top=40.263546616792624,left=-5.1788258082264305,bottom=40.25541390947118,right=-5.169102583586535)

    import platform
    if platform.system().lower() == 'darwin':
        f_in_asc="/Volumes/Shared/Cartography/MDT05/PNOA_MDT05_ETRS89_HU30_0578_LID.asc"
        f_out_asc="subset.asc"
        f_in_ecw="/Volumes/Shared/Cartography/PNOA/PNOA_MA_OF_ETRS89_HU30_h50_0578.ecw"
        f_out_ecw="subset.tif"

    else:

        f_in_asc="K:\Cartography\MDT05\PNOA_MDT05_ETRS89_HU30_0578_LID.asc"
        f_out_asc="K:\Cartography\MDT05\subset.asc"
        f_in_ecw="K:\Cartography\PNOA\PNOA_MA_OF_ETRS89_HU30_h50_0578.ecw"
        f_out_ecw="K:\Cartography\PNOA\subset.tif"


    rm.rect(f_in_asc, f_out_asc, bounds ,mode='asc')
    # geotiff test
    # if platform.system().lower() == 'darwin':
    rm.rect(f_in_ecw, f_out_ecw, bounds ,mode='geotiff')
