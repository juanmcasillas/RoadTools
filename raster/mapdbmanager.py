#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# mapdbmanager.py
# 04/25/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# manage the directory database map, and create mosaics and so on using
# raster. Useful to stich the sheets together
#
# ############################################################################


import json
import argparse
import sys
import os
import glob
import raster
from mtn import MTN


class MapDbManager:
    def __init__(self,base="/Volumes/Shared/Cartography"):
        self.basedir = base
        self.products = { 'MDT02': 'MDT02',     #  2 meters MDT25
                          'MDT05': 'MDT05',     #  5 meters MDT50
                          'MDT25': 'MDT25',     # 10 meters MDT50
                          'PNOA': 'PNOA'        # orto      MDT50
                        }
        self.valid_ext = [ '.asc', '.ecw' ]



    def get_files(self, product, sheets, zone='30'):

        r = []
        tgt_dir = [ self.basedir , self.products[product] , "*" ]
        for file in glob.glob(os.path.sep.join(tgt_dir)):
            _,file_ext = os.path.splitext(file)
            if not file_ext in self.valid_ext:
                continue

            for sheet in sheets:
                if file.find(str(sheet)) != -1 and file.find('HU' + zone) != -1:
                    r.append(file)

        return r

        #PNOA_MDT05_ETRS89_HU30_0531_LID.asc


if __name__ == "__main__":


    parser = argparse.ArgumentParser(usage=None,description="Map Manager. Process the database map to extract subsets")

    maingroup = parser.add_argument_group()
    maingroup.add_argument("-v", "--verbose", help="Show data about file and processing", action="count")
    maingroup.add_argument("boundfile", help="Input File with the bound coords in json format")
    maingroup.add_argument("outfile", help="Output File")
    maingroup.add_argument("origin", help="MDT02, MDT05, MDT25, PNOA", default="MDT25")
    maingroup.add_argument("product", help="Asc, GeoTiff, JPEG (default=Asc)", default="asc")
    args = parser.parse_args()

    bounds = raster.Bounds().from_file(args.boundfile)
    sheets = MTN.to_MTN(bounds=bounds)['MTN50']
    mtn50_sheets = [sheet[1] for sheet in sheets]
   
    mapdb = MapDbManager()
    source_files = mapdb.get_files(args.origin, mtn50_sheets)
    
    print(mtn50_sheets)
    rasterman = raster.RasterManager()
    rasterman.rect_m(source_files, args.outfile, bounds, mode=args.product)

