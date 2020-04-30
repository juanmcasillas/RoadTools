1) open raster/map.html and add raster/google.key to open the maps. Get the bounding box.
2) save gpx/AC_XXXXXX.bounds the data from the bounding box in JSON format.
3) extract the subsets (in raster folder):
    *if MNT02, check the mapdbmanager.py to HACK the sheets
    *if sheets>4, use gdal manager to generate the jpg.
    
    $PYQGIS37 mapdbmanager.py -v ../gpx/AC_mijares.bounds /Volumes/Shared/temp/subida_mijares/AC_mijares_mdt02.asc MDT02 asc
    $PYQGIS37 mapdbmanager.py -v ../gpx/AC_mijares.bounds /Volumes/Shared/temp/subida_mijares/AC_mijares_mdt05.asc MDT05 asc
    $PYQGIS37 mapdbmanager.py -v ../gpx/AC_mijares.bounds /Volumes/Shared/temp/subida_mijares/AC_mijares_pnoa.jpg PNOA jpg
4) run the nodata function to create the road in the elevation (in roadtools/core folder):
    
    $PYQGIS37 modify_asc_nodata.py  -v -mxy -5 -w 10  -j ../../gpx/AC_mijares.bounds ../../gpx/AC_mijares.gpx /Volumes/Shared/temp/subida_mijares/AC_mijares_mdt02.asc /Volumes/Shared/temp/subida_mijares/AC_02.asc
    point the elevation offset (move to: -23.856595953363723)

5) load everything with the special plugins in blender
    - GPX with my gpxloaded, don't use ortometric altitude, don't use the optmizer. Enter the vertical offset (move_to) and -5 to xy (-mxy in modify_asc_nodata)
    - Load the ASC (AC_02.asc in the example) with the plugin fixed to delete NODATA values
    

