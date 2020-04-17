import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.windows import Window, from_bounds
from rasterio.transform import Affine

#import ogr, osr # gdal
import pyproj
import numpy



#http://centrodedescargas.cnig.es/CentroDescargas/index.jsp
#MDT02 is ETRS89 UTM (zone in the name of the file HU30 -> zone 30)
#https://epsg.io/25830 ETRS89 / UTM zone 30N EPSG:25830

# this is how it's supposed to do, but not works
#with rasterio.open(solar_path, mode='r+') as raster:
#    raster.crs = rasterio.crs.CRS({'init': 'epsg:25830'})
#    show((raster, 1))
#    print(raster.crs)

#
# this is done to reproject
# this creates a prj file (called) with the info. if you do the file, you don't 
# need to reproject the data, I think
#
#https://epsg.io/25830 ETRS89 / UTM zone 30N
#PROJCS["ETRS_1989_UTM_Zone_30N",GEOGCS["GCS_ETRS_1989",DATUM["D_ETRS_1989",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-3.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]
#dataset = rasterio.open(ASC)
#print(dataset.bounds)
#reproject_raster(ASC,OUT,crs= rasterio.crs.CRS({'init': 'epsg:25830'}))
#dataset = rasterio.open(OUT)

#https://gis.stackexchange.com/questions/299787/finding-pixel-location-in-raster-using-coordinates

#ASC="E:\Downloads\MDT02-ETRS89-HU30-0557-4-COB2.asc"
#OUT="E:\Downloads\MDT02-ETRS89-HU30-0557-4-COB2.rio"

ECW="K:\Cartography\PNOA\\PNOA_MA_OF_ETRS89_HU30_h50_0557.ecw"
SUBSET="K:\Cartography\PNOA\out.tif"


PROJCS="""PROJCS["ETRS_1989_UTM_Zone_30N",GEOGCS["GCS_ETRS_1989",DATUM["D_ETRS_1989",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-3.0],PARAMETER["Scale_Factor",0.9996],PARAMETER["Latitude_Of_Origin",0.0],UNIT["Meter",1.0]]"""

def wgs84_to_utm(lon,lat):

    dest =  pyproj.Proj('EPSG:4326') # WGS84/Geographic
    target =  pyproj.Proj(PROJCS) # WGS84 UTM Zone 30N

    point = (lat, lon)
    point_r = pyproj.transform(dest, target, *point)
    # return lon(x),lat(y)
    #print(point_r)
    return(point_r[0], point_r[1])

with rasterio.open(ECW, mode='r') as dataset:
    print(dataset.crs)
    print(dataset.bounds)

    #big    
    lon_a, lat_a = wgs84_to_utm(-4.325984, 40.38159014) # lon, lat # TOPLEFT
    lon_b, lat_b = wgs84_to_utm(-4.30654020, 40.37470263) # lon, lat #BOTTOMRIGHT

    #small    
    #lon_a, lat_a = wgs84_to_utm(-4.3262100220, 40.3791130379) # lon, lat # TOPLEFT
    #lon_b, lat_b = wgs84_to_utm(-4.2860412598, 40.3618495478) # lon, lat #BOTTOMRIGHT


    # this return in row, col (Y,X)
    py_a,px_a = dataset.index( lon_a, lat_a )
    py_b,px_b = dataset.index( lon_b, lat_b )
    
    width = px_b - px_a
    height = py_b - py_a

    print("A:",lon_a, lat_a,":", px_a, py_a)
    print("B:",lon_b, lat_b,":", px_b, py_b)
    print("width, height: ", width, height)

    if True:
        #bbox = Window( px_a, py_a, width, height)
        bbox = from_bounds(lon_a, lat_b, lon_b, lat_a, dataset.transform) #left, bottom, right, top
        window = dataset.read(window=bbox)
        print(window.shape)
        res_x = (lon_b - lon_a) / width
        res_y = (lat_b - lat_a) / height
        # this is the point (A) scaled, so we can locate coords inside.
        # Affine.scale(res_x, res_x) should be Affine.scale(res_x, res_y) but this generates
        # non square pixels, and insert dx,dy values, that are not supported by noone. 
        # tested with GlobalMapper, and it works fine.
        transform = Affine.translation(lon_a + res_x, lat_a + res_y) * Affine.scale(res_x, res_x)

        with rasterio.open(SUBSET,'w', 
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
                interleave='band',
                nodata=0,
                tiled=True
        ) as dst:
            dst.write(window)

# original header
# ncols         7195
# nrows         4779
# xllcenter     384916
# yllcenter     4465380
# cellsize      2
# nodata_value  -9999.0

#ncols        1960
#nrows        1131
#xllcorner    0.000000000000
#yllcorner    -1131.000000000000
#cellsize     1.000000000000
#NODATA_value  -99999


#topleft
# Datum:	ETRS89
# Latitud:	40,4076142700
# Longitud:	-4,3395996094
# Huso UTM:	30
# Coord. X:	386 333,32
# Coord. Y:	4 473 861,45
# Altura (m):	796,76

#bottomright
# Datum:	ETRS89
# Latitud:	40,3579254107
# Longitud:	-4,2232131958
# Huso UTM:	30
# Coord. X:	396 132,80
# Coord. Y:	4 468 202,70
# Altura (m):	606,38

#small

#topleft
# Datum:	ETRS89
# Latitud:	40,3791130379
# Longitud:	-4,3262100220
# Huso UTM:	30
# Coord. X:	387 422,01
# Coord. Y:	4 470 680,60
# Altura (m):	572,6



#bottomright
# Datum:	ETRS89
# Latitud:	40,3618495478
# Longitud:	-4,2860412598
# Huso UTM:	30
# Coord. X:	390 804,05
# Coord. Y:	4 468 713,95
# Altura (m):	561,53

# Galayos
#Top (N): 40.263546616792624
#Left (W): -5.1788258082264305
#Right (E): -5.169102583586535
#Bottom (S): 40.25541390947118