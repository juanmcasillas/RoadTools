https://gis.stackexchange.com/questions/44958/gdal-importerror-in-python-on-windows
GDAL and ECW in windows (64 bit support, win10)
MUST put the variables in the System Variables
exporting on console doesn't work

install this packages

gdal-300-1911-x64-core.msi
GDAL-3.0.4.win-amd64-py3.7.msi
gdal-300-1911-x64-ecw-33.msi
python-3.7.7-amd64.exe
rasterio-1.1.3-cp37-cp37m-win_amd64.whl

https://rasterio.readthedocs.io/en/latest/installation.html
https://www.lfd.uci.edu/~gohlke/pythonlibs/#rasterio
http://www.gisinternals.com/stable.php

rasterio works with ECW support (read only)

SYSTEM variables (no user variables)
PATH=C:\Program Files\GDAL (put it at the top, first one)
GDAL_DATA=C:\Program Files\GDAL\gdal-data
GDAL_DRIVER_PATH=C:\Program Files\GDAL\gdalplugins

everything works fine.

# mac version
brew install gdal
gdalinfo --version to see the version (2.4.4)

Doesn't work. I installed the framework, and still no luck, and I loose the PROJ version
for the 3.6 python (standard installed) so I have to revert to 3.7 (brew)

See that
https://github.com/ciaranevans/macos_ecw_qgis_support
https://download.hexagongeospatial.com/downloads/ecw/erdas-ecw-jp2-sdk-v5-4-macosx?result=true

first, download ERDAS plugin (5.4)
from https://download.hexagongeospatial.com/downloads/ecw/erdas-ecw-jp2-sdk-v5-4-macosx?result=true
Desktop Read Only and

cd /Hexagon/ERDASEcwJpeg2000SDK5.4.0/Desktop_Read-Only/lib/libc++/dynamic
sudo mkdir /Library/Application\ Support/GDAL/2.4/Libraries
sudo cp libNCSEcw.dylib /Library/Application\ Support/GDAL/2.4/Libraries/
sudo cp -R ../../../etc /Library/Application\ Support/GDAL/2.4/
tree /Library/Application\ Support/GDAL/2.4/ you should get a structure similar to:
/Library/Application\ Support/GDAL/2.4/
├── Libraries
│   └── libNCSEcw.dylib
└── etc


second, the GDAL ECW plugin
from http://www.kyngchaos.com/files/software/frameworks/GDAL-ECW_Plugin-2.4.0-1.dmg


You MUST download and install the ECW SDK yourself.  I don't have the means to enforce export restrictions.  
I'm sorry, but installation is a manual process for now, and a little more annoying than it used to be:

Go to https://download.hexagongeospatial.com.  Search for "ECW JP2 SDK" (it may be case sensitive).  
Find and click "ERDAS ECW/JP2 SDK v5.4 (MacOSX)" (do not download a newer or older version).  Fill in the form and Submit it.  
You may need to wait to confirm your email before downloading, or you should be able to download immediately if you've registered already.

Unzip and open the downloaded disk image and run the installer, select the Desktop Read-Only Redistributable license (or Read-Write if you have a full license).  
It will install into the top of your boot drive, /Hexagon.  Dig into this folder to lib/libc++/dynamic.

Copy the libNCSEcw.dylib file to (the /Library folder is likely hidden, so you need to Go->Go to Folder from your desktop and type in /Library):

	/Library/Application Support/GDAL/2.4/Libraries

and copy the contents of the etc folder here to:

	/Library/Application Support/GDAL/2.4/etc

so it looks like (there may be other files in Libraries and PlugIns for other installed plugins):

	Library
		Application Support
			GDAL
				2.4
					etc
               (files in here)
					Libraries
						libNCSEcw.dylib
					PlugIns
						gdal_ECW_JP2ECW.dylib

You can trash the installed Hexagon folder when done to save a few hundred MB of space.


Driver Loading

ECW includes JP2 read/write support, in addition to ECW of course.  My GDAL framework comes with JasPer and OpenJPEG JP2 R/W support.  Two other JP2 options are possible - MrSID JP2 and Kakadu.  Depending on the load order of drivers, any one of these could be used, though you might prefer one over another.

Drivers are loaded in this order, and drivers loaded first are first used:

1. Plugins (not sure how GDAL orders them)

2. Embedded drivers (ordered how they are in the source code)

I think gdalinfo --formats lists drivers in the order they are loaded, so check that.

To force one driver to be used over another, use the GDAL_SKIP environment variable.  In the default Mac OS X bash shell (Terminal):

export GDAL_SKIP="[driver list]"

[driver list] is a space-delimited list of the drivers you don't want to use, as named in the gdalinfo --formats listing.  ie to override JasPer:

export GDAL_SKIP="JPEG2000"


Support, Documentation, and Disclaimer

This software is provided "as is", without any warranty or guarantee of its usability or fitness for any purpose.  See the ECW license for specific licensing info for the ECWJP2 SDK.

I don't provide support on the usage of the included software.  See the documentation and help resources on their websites if you need such help.  All I can help with is the installation on Mac OS X, and problems related to its operation on Mac OS X.

Documentation shortcuts are included for just the commandline tools.  These shortcuts range from full html documentation to running the command in a terminal window to display its built-in help (which can be very brief).

I am not a C programmer and cannot help with programming involving the software.  I have enough general programming skills to deal with most build issues and some programming issues, and may be able to help with problems with this build that affect its inclusion in other software.


- William Kyngesburye
kyngchaos@kyngchaos.com
http://www.kyngchaos.com/
