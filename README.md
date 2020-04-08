# RoadTools
A Blender plugin to create roads with real terrain and smooth road profiles

All the document is WIP/TBD

https://github.com/vvoovv/blender-gpx/wiki/Documentation
https://blender.stackexchange.com/questions/132120/how-to-create-a-curved-road-in-blender
https://cgbookcase.com/textures/how-to-use-pbr-textures-in-blender?texture=two-lane-solid-line-road-patches-01

DDS mac plugin to read DDS files
https://fnordware.blogspot.com/2014/09/dds-plug-in-for-after-effects-and.html
https://www.racedepartment.com/threads/proper-technique-in-track-making-plus-tips.122794/
# A-B


# how to texture things propertly
https://assettocorsamods.net/threads/blender-2-8-uv-unwrap.1779/

1ROAD

finish
AC_AB_FINISH_L
AC_AB_FINISH_R

start
AC_AB_START_R
AC_AB_START_L
AC_HOTLAP_START_0
AC_PIT_0

Place them 1 or 2 meters above track surface. Three conditions to make sure everything will work as expected:
1. respect the naming scheme
2. make then invisible
3. make sure to respect the axis orientation (pivot point Y up, Z forward) (rotate axis X 90)

# Road modelling

1) set the origin of the track to the origin of the world (0,0,0)
2) convert the curve to bezier, change the control points, then recalculate normals
3) apply the transforms before texturing it. In object mode, press Control-A Scale


https://blender.stackexchange.com/questions/8808/what-is-the-fastest-way-to-add-vertices-to-a-curve-at-a-specific-point


1) set the origin to the bezier
    - bezier res: 24
    - bezier Twist method: zUp

2) create plane
    add array modifier
        - set uv
        - set merge
        - set merge distance to 0
    add curve modifier
        - get the curve
        - calculate the length

    Apply the Array, delete the Curve.
    Control-A apply all the transformation
    Map the UV
    First 2 using smart
    Rest Follow quad

    Add a new curve modifier
        - Select the bezier

https://blender.stackexchange.com/questions/57306/how-to-create-a-custom-ui


## fix for GPX-Import in Blender 2.8.2


/Users/assman/Library/Application Support/Blender/2.82/scripts/addons/blender-gpx-master/__init__.py:227

```
        projection = None
        if "bpyproj" in self.__dict__ and self.bpyproj:
            projection = self.bpyproj.getProjection(lat, lon)
        if not projection:
            from .transverse_mercator import TransverseMercator
            # fall back to the Transverse Mercator
            projection = TransverseMercator(lat=lat, lon=lon)
        return projection
```



# how to fix the pyproj problem (install binary dependencies on Blender)

In order to get https://github.com/vvoovv/blender-gpx/wiki/Documentation this work, we need https://github.com/JeremyBYU/bpyproj dependency
and proj installed. But the build requires some tunning in the @rpath so this is how to fix the plugin

SRID PROJ 4326 (WS84)
EPSG:4326

N:40.3319
W:-4.59881
E:-4.51401
S:40.2837



 otool -l "/Users/assman/Library/Application Support/Blender/2.82/scripts/addons/bpyproj/dependencies/binaries/osx_64_37/site-packages/pyproj/_proj.cpython-37m-darwin.so"
 see
 ```
 Load command 17
          cmd LC_RPATH
      cmdsize 40
         path @loader_path/../../../ (offset 12)
```

```
brew install proj #(latest version 7)
```

go to `/Users/assman/Library/Application Support/Blender/2.82/scripts/addons/bpyproj/dependencies/binaries/osx_64_37/site-packages/pyproj/../../../`
#ln -s libproj.13.dylib -> osx_64_37/site-packages/pyproj/libproj.13.dylib
ln -s /usr/local/lib/libproj.dylib libproj.13.dylib
```
/Users/assman/Library/Application Support/Blender/2.82/scripts/addons/bpyproj/dependencies/binaries
mephisto:binaries assman$ ls -lart
total 0
drwxr-xr-x   3 assman  staff   96  2 abr 17:47 linux_64_35
drwxr-xr-x   3 assman  staff   96  2 abr 17:47 linux_64_36
drwxr-xr-x   3 assman  staff   96  2 abr 17:47 linux_64_37
drwxr-xr-x   3 assman  staff   96  2 abr 17:47 osx_64_35
drwxr-xr-x   3 assman  staff   96  2 abr 17:47 osx_64_37
drwxr-xr-x   3 assman  staff   96  2 abr 17:47 windows_32_35
drwxr-xr-x   3 assman  staff   96  2 abr 17:47 windows_64_35
drwxr-xr-x   3 assman  staff   96  2 abr 17:47 windows_64_37
drwxr-xr-x   5 assman  staff  160  2 abr 17:47 ..
lrwxr-xr-x   1 assman  staff   47  3 abr 10:47 libproj.13.dylib -> osx_64_37/site-packages/pyproj/libproj.13.dylib
drwxr-xr-x  11 assman  staff  352  3 abr 10:47 .
```

## OSM

works awesome

https://gumroad.com/d/bcca0fa5c2eaa11bf49eea7030464879
https://github.com/vvoovv/blender-osm/wiki/Documentation#terrain-import


how to fix elevation GPX problem

0) set the Z (top) orto view
1) go to first point of GPX
2) 3d cursor, get the Z value
3) select in the terrain the face. Set the origin to THAT face
4) Move the terrain Z to the Z value recorded in step (2) from GPX.

# blender icons
https://blenderartists.org/t/icon-enumeration-script-blender-2-5/491147/3

# blender distance

## distances should be calculated in this way:

#vp = bpy.data.objects['Plane'].data.vertices[37]
#vt = bpy.data.meshes['Terrain'].vertices[24449]
#vp = Vector((-33.21149826049805, -8.433300971984863, 6.760486125946045))
#vt = Vector((-129.67138671875, -46.43072509765625, 3.25))
# goal distance (marked by measure tool: 6.307367787950501)

#vpw = bpy.data.objects['Plane'].matrix_world @ vp.co
#vtw = bpy.data.objects['Terrain'].matrix_world @ vt.co

#d1 = (vp.co.xyz - vt.co.xyz).length
#d2 = (vpw.xyz - vtw.xyz).length ## this one!
#d3 = (vpw.xy - vtw.xy).length # 2d

#print("distance 1: ", d1)
#print("distance 2: ", d2)
#print("distance 3: ", d3)

## call OSM
>>> bpy.context.scene.blender_osm.dataType = 'osm'
>>> bpy.ops.blender_osm.import_data()

>>> print(bpy.context.scene.blender_osm.maxLat) # top
40.33190155029297

>>> print(bpy.context.scene.blender_osm.minLon) # left
-4.598810195922852

>>> print(bpy.context.scene.blender_osm.maxLon) # right
-4.514009952545166

>>> print(bpy.context.scene.blender_osm.minLat) # bottom
40.28369903564453


import bpy

def download_terrain_osm( top, left, right, bottom, kind='terrain'):
    bpy.context.scene.blender_osm.dataType = kind
    bpy.context.scene.blender_osm.maxLat = top
    bpy.context.scene.blender_osm.minLon = left
    bpy.context.scene.blender_osm.maxLon = right
    bpy.context.scene.blender_osm.minLat = bottom
    bpy.ops.blender_osm.import_data()

#download_terrain_osm(40.324347,-4.588443,-4.566994,40.297759)
#download_terrain_osm(40.335921, -4.849929,-4.805058,40.253744)
## extender
download_terrain_osm(40.344927,-4.854437,-4.800551,40.244738)