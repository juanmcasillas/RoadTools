#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# __init__.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# roadtools init file for blender addon. Load the modules and set the path
# right, so we can use it from blender. Does automatic registration
# 
# ############################################################################

bl_info = {
    "name": "Road Tools",
    "description": "Road Tools Helpers",
    "author": "Juan M. Casillas",
    "version": (0, 0, 3),
    "blender": (2, 80, 0),
    "location": "3D View > UI",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "",
    "tracker_url": "",
    "category": "Development"
}

modulesNames = [ 'properties', 
                'op_load_gpx',
                'op_expand_terrain', 
                'op_download_terrain', 
                'op_fake_terrain',
                'op_match_terrain',
                'op_create_road',
                'op_join_road',
                'op_flatten_terrain', 
                'ui']

import sys
import importlib


modulesFullNames = {}
for currentModuleName in modulesNames:
    #modulesFullNames[currentModuleName] = ('{}.{}'.format(__name__, currentModuleName))
    # jmc hack. Remove the __main__. python 3 doesn't need it
    modulesFullNames[currentModuleName] = ('{}'.format(currentModuleName))

for currentModuleFullName in modulesFullNames.values():
    if currentModuleFullName in sys.modules:
        importlib.reload(sys.modules[currentModuleFullName])
    else:
        print("to import ", currentModuleFullName)
        globals()[currentModuleFullName] = importlib.import_module(currentModuleFullName)
        setattr(globals()[currentModuleFullName], 'modulesNames', modulesFullNames)

def register():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'register'):
                sys.modules[currentModuleName].register()

def unregister():
    for currentModuleName in modulesFullNames.values():
        if currentModuleName in sys.modules:
            if hasattr(sys.modules[currentModuleName], 'unregister'):
                sys.modules[currentModuleName].unregister()

if __name__ == "__main__":
    register()