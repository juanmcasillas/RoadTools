import numpy
cols = 5
rows = 4
a = range(cols*rows)
arr = numpy.array(a)
arr = numpy.reshape(arr,(rows,cols))
arr = numpy.insert(arr, cols, values=arr[:,cols-1],axis=1)
arr = numpy.insert(arr, rows-1, values=arr[rows-1,:],axis=0)
arr = numpy.reshape(arr,((cols+1)*(rows+1)))


Formato del fichero ASCII grid de ARC/INFO
NCOLS ncols
NROWS nrows
XLLCENTER xmin
YLLCENTER ymin
CELLSIZE size
NODATA_VALUE nodata
z11 z12 z13 z14...............z1ncols ...
...
...
znrows1 znrows2 znrows3...znrowsncols
Donde:
- NCOLS es el número de nodos por fila
- NROWS es el número total de filas,
- XLLCENTER y YLLCENTER son las coordenadas suroeste de la malla (*)
- CELLSIZE es el paso de malla
- NODATA VALUE es el valor asignado a los nodos para los que no se dispone de cota conocida
Las cotas de la malla están expresadas en metros, con un espacio en blanco entre valor y valor, y describen el terreno de norte a sur y de oeste a este.
(*)Nota: El sufijo CENTER indica que las coordenadas describen la posición del centro del píxel. Cuando el sufijo es CORNER indica la posición de la esquina inferior izquierda del mismo.


# MDT05 557
NCOLS 5735
NROWS 3809
XLLCENTER 370760 esquina inferior izquierda
YLLCENTER 4465380
CELLSIZE 5
NODATA_VALUE -999

370760+(5735*5) = 399435 esquina superior derecha
4465380+(3809*5) =  4484425


# 557 25
PNOA_MDT25_ETRS89_HU30_0557_LID.asc 
NCOLS 1149
NROWS 763
XLLCENTER 370750
YLLCENTER 4465375
CELLSIZE 25
NODATA_VALUE -999

370750+(1149*25)=399475
4465375+(763*25)=4484450

# 578 05
NCOLS 5777
NROWS 3853
XLLCENTER 313670
YLLCENTER 4447850
CELLSIZE 5
NODATA_VALUE -999

313670+(5777*5)=342555
4447850+(3853*5)=4467115



# navas del rey sheet
ncols        161
nrows        184
xllcorner    314730.619071083551
yllcorner    4458361.610961413942
cellsize     4.998588763842
NODATA_value  -99999


def dd_to_dms(deg, mode='lat'):
    sign = 1 if deg > 0 else -1
    d = int(deg)
    md = abs(deg - d) * 60
    m = int(md)
    sd = (md - m) * 60

    if mode.lower() == 'lat':
        direction = 'N' if sign > 0 else 'S'
    else:
        direction = 'E' if sign > 0 else 'W'

    return (abs(d), m, sd, direction)

import numpy
cols = 1149
rows = 763
data = range(cols*rows)
arr = numpy.array(data)
arr = numpy.reshape(arr,(rows,cols))
arr = numpy.insert(arr, cols, values=arr[:,cols-1],axis=1)
arr = numpy.insert(arr, rows, values=arr[rows-1,:],axis=0)

new_len = (cols*rows) + rows + cols + 1
arr = numpy.reshape(arr,new_len)

import pyproj
cellsize=25
utmx = 342555
utmy = 4467115
dest_utm30N =  pyproj.Proj('+init=epsg:25830') # UTM30N  
target_wgs84 = pyproj.Proj('+init=epsg:4326')  # WGS84/Geographic
point = (utmx, utmy)
lon, lat = pyproj.transform(dest_utm30N, target_wgs84, *point)
print(lat,lon)
