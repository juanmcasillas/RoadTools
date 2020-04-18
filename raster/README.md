# How to install ECW support on Windows 10 and Mac OS 10.13.6

Motivation: I want to run a python code based on `rasterio` to export bounding
box for some ECW georeferenciated files. ECW is not supported "at first sight"
due "problems" with the license. Here I explain how to get it working on the 
two platforms.

# Windows 10

What you have to do:

* GDAL and ECW in windows (64 bit support, win10)
* MUST put the variables in the System Variables
* exporting on console doesn't work
* see [here](https://gis.stackexchange.com/questions/44958/gdal-importerror-in-python-on-windows) for more info


Install this packages (windows installers in order), python3.7, then `rasterio` packages
see their  [documentation](https://rasterio.readthedocs.io/en/latest/installation.html) on
how to install it. You can get GDAL PACKAGES from [here](http://www.gisinternals.com/stable.php) and
binary rasterio packages from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#rasterio)


```
gdal-300-1911-x64-core.msi
GDAL-3.0.4.win-amd64-py3.7.msi
gdal-300-1911-x64-ecw-33.msi
python-3.7.7-amd64.exe
rasterio-1.1.3-cp37-cp37m-win_amd64.whl
```

Put the following **SYSTEM** variables (no user variables)

* `PATH=C:\Program Files\GDAL` (put it at the top, first one)
* `GDAL_DATA=C:\Program Files\GDAL\gdal-data`
* `GDAL_DRIVER_PATH=C:\Program Files\GDAL\gdalplugins`

everything works fine.

# Mac OS 10.13.6 (High Sierra)

Yes, I have High sierra. I can't compile `gdal` from brew due the X-Code version (9.02)
and expects (10.21). Some big problems to update X-Code, so I try this version. I need
this *only* to do the bounding box crop, so it fits my needs.

* Get the QGIS installer for mac (3.12), all in one from [here](https://qgis.org/downloads/macos/qgis-macos-pr.dmg)
* install python3.7 from brew in `/usr/local` (`brew install python3`) see [here](https://gist.github.com/alyssaq/f60393545173379e0f3f) for more info if you want
* install your required modules with that interpreter. Mine is here:

```
lrwxr-xr-x  1 root  admin  43 17 abr 21:53 /usr/local/bin/python37 -> /usr/local/Cellar/python3/3.7.7/bin/python3
```

* So I install my deps (I need pyproj and rasterio)

```
/usr/local/Cellar/python3/3.7.7/bin/pip3 install pyproj
/usr/local/Cellar/python3/3.7.7/bin/pip3 install rasterio
```

Lets break some things now. The idea is to use the boundled python3.7 with QGIS with their `gdal` and other running
dependencies, to do the ECW work. I have to tune it first, due I can't install anything in the QGIS python enviroment.

```
QGIS=/Applications/QGIS3.12.app/Contents
SITE_PACKAGES=$QGIS/Frameworks/Python.framework/Versions/Current/lib/python3.7/site-packages
PYTHON_PACKAGES=/usr/local/lib/python3.7/site-packages
```

## Copy rasterio and change libgdal library

```
cd $SITE_PACKAGES
rsync -av $PYTHON_PACKAGES/rasterio-1.1.3.dist-info .
rsync -av $PYTHON_PACKAGES/rasterio .
cd rasterio
cd .dylibs/
mv libgdal.20.dylib  libgdal.20.dylib.old
cp $QGIS/MacOS/lib/libgdal.20.dylib .
```

## Copy affine (a required dependency of rasterio for my work)

```
cd $SITE_PACKAGES
rsync -av $PYTHON_PACKAGES/affine .
rsync -av $PYTHON_PACKAGES/affine-2.3.0.dist-info .
```

## Replace the pyproj version 

**CAUTION** QGIS scripts may stop working after that.

```
cd $SITE_PACKAGES
mv pyproj pyproj-old
rsync -av $PYTHON_PACKAGES/pyproj-2.6.0-py3.7-macosx-10.13-x86_64.egg/pyproj .
```

## set the enviroment variables, and do the magic

You NEED to export this variables, or `gdal` doesn't read the plugins. So do IT before call your python script.

```
export GDAL_DRIVER_PATH=$QGIS/Resources/gdal/gdalplugins
export GDAL_DATA=$QGIS/Contents/Resources/gdal

cd $QGIS/MacOS/bin/
./gdalinfo --formats
./gdalinfo --formats | grep -i ecw
```

## Bonus: script with all the variables

Remember: that are my paths, and my installation, maybe you need to tune some paths (specially your python's dirs).
You have to call your scripts with the python interpreter provided with QGIS (see `PYQGIS37` variable below)

```
export QGIS=/Applications/QGIS3.12.app/Contents
SITE_PACKAGES=$QGIS/Frameworks/Python.framework/Versions/Current/lib/python3.7/site-packages
PYTHON_PACKAGES=/usr/local/lib/python3.7/site-packages
export GDAL_DRIVER_PATH=$QGIS/Resources/gdal/gdalplugins
export GDAL_DATA=$QGIS/Contents/Resources/gdal
export PYQGIS37=$QGIS/Frameworks/Python.framework/Versions/Current/bin/python3.7
export PATH=$PATH:$QGIS/MacOS/bin
```

IMPORTANT NOTE: you can't call `gdal` commands from outside its path (`@executable_path`) to invoke it, you 
have to use the **full path to the binary**. See the example:

```
cd /Archive/Src/RoadTools/raster
gdalinfo subset.tif
ERROR 1: dlopen(/Applications/QGIS3.12.app/Contents/Resources/gdal/gdalplugins/2.4/gdal_MrSID.dylib, 1): Library not loaded: @executable_path/lib/libltidsdk.dylib
  Referenced from: /Applications/QGIS3.12.app/Contents/Resources/gdal/gdalplugins/2.4/gdal_MrSID.dylib
  Reason: image not found
ERROR 1: dlopen(/Applications/QGIS3.12.app/Contents/Resources/gdal/gdalplugins/2.4/gdal_MrSID.dylib, 1): Library not loaded: @executable_path/lib/libltidsdk.dylib
  Referenced from: /Applications/QGIS3.12.app/Contents/Resources/gdal/gdalplugins/2.4/gdal_MrSID.dylib
  Reason: image not found
ERROR 1: dlopen(/Applications/QGIS3.12.app/Contents/Resources/gdal/gdalplugins/2.4/gdal_ECW_JP2ECW.dylib, 1): Library not loaded: @executable_path/lib/libNCSEcw.dylib
  Referenced from: /Applications/QGIS3.12.app/Contents/Resources/gdal/gdalplugins/2.4/gdal_ECW_JP2ECW.dylib
  Reason: image not found
ERROR 1: dlopen(/Applications/QGIS3.12.app/Contents/Resources/gdal/gdalplugins/2.4/gdal_ECW_JP2ECW.dylib, 1): Library not loaded: @executable_path/lib/libNCSEcw.dylib
  Referenced from: /Applications/QGIS3.12.app/Contents/Resources/gdal/gdalplugins/2.4/gdal_ECW_JP2ECW.dylib
  Reason: image not found
ERROR 1: dlopen(/Applications/QGIS3.12.app/Contents/Resources/gdal/gdalplugins/2.4/gdal_MG4Lidar.dylib, 1): Library not loaded: @executable_path/lib/liblti_lidar_dsdk.1.dylib
  Referenced from: /Applications/QGIS3.12.app/Contents/Resources/gdal/gdalplugins/2.4/gdal_MG4Lidar.dylib
  Reason: image not found
ERROR 1: dlopen(/Applications/QGIS3.12.app/Contents/Resources/gdal/gdalplugins/2.4/gdal_MG4Lidar.dylib, 1): Library not loaded: @executable_path/lib/liblti_lidar_dsdk.1.dylib
  Referenced from: /Applications/QGIS3.12.app/Contents/Resources/gdal/gdalplugins/2.4/gdal_MG4Lidar.dylib
  Reason: image not found
Driver: GTiff/GeoTIFF
Files: subset.tif
Size is 3219, 3692
Coordinate System is `'
Origin = (314725.870489399880171,4459286.118043545633554)
Pixel Size = (0.250007080142450,0.250007080142450)
Image Structure Metadata:
  COMPRESSION=LZW
  INTERLEAVE=BAND
Corner Coordinates:
Upper Left  (  314725.870, 4459286.118)
Lower Left  (  314725.870, 4460209.144)
Upper Right (  315530.643, 4459286.118)
Lower Right (  315530.643, 4460209.144)
Center      (  315128.257, 4459747.631)
Band 1 Block=256x256 Type=Byte, ColorInterp=Red
  NoData Value=0
Band 2 Block=256x256 Type=Byte, ColorInterp=Green
  NoData Value=0
Band 3 Block=256x256 Type=Byte, ColorInterp=Blue
  NoData Value=0
```

If you don't want to get error, call the command with the full path:

```
cd /Archive/Src/RoadTools/raster
/Applications/QGIS3.12.app/Contents/MacOS/bin/gdalinfo subset.tif
Driver: GTiff/GeoTIFF
Files: subset.tif
Size is 3219, 3692
Coordinate System is `'
Origin = (314725.870489399880171,4459286.118043545633554)
Pixel Size = (0.250007080142450,0.250007080142450)
Image Structure Metadata:
  COMPRESSION=LZW
  INTERLEAVE=BAND
Corner Coordinates:
Upper Left  (  314725.870, 4459286.118)
Lower Left  (  314725.870, 4460209.144)
Upper Right (  315530.643, 4459286.118)
Lower Right (  315530.643, 4460209.144)
Center      (  315128.257, 4459747.631)
Band 1 Block=256x256 Type=Byte, ColorInterp=Red
  NoData Value=0
Band 2 Block=256x256 Type=Byte, ColorInterp=Green
  NoData Value=0
Band 3 Block=256x256 Type=Byte, ColorInterp=Blue
  NoData Value=0
```