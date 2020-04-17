#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# gpx2csv.py
# 04/17/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# read a gpx, generate a CSV list, and do some funky works on this
#
# ############################################################################

import sys
import argparse
import csv
import os
import pyproj
import numpy as np


from smooth import  smooth_gpx
from geoid import GeoidHeight
from raster import RasterManager
from mtn import MTN


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="Show data about file and processing", action="count")
    parser.add_argument("-o", "--optimize", help="Optimize GPX input(filter)", action="store_true")
    parser.add_argument("gpx_file", help="GPX file to load")
    parser.add_argument("csv_out", help="Output CSV file")
    args = parser.parse_args()

    points, bounds, length = smooth_gpx(args.gpx_file, optimize=args.optimize, output=None)

    geoid = GeoidHeight()
    rasman = RasterManager()

    pd = []
    i = 1
    mtn = [] 
    for p in points:
        N = geoid.get(p.latitude, p.longitude)
        pd.append((p.longitude,p.latitude,p.elevation, p.elevation-N, N, i))

        r = MTN.where(p.longitude,p.latitude)
        
        if r['MTN50'][0][1] not in mtn:
            mtn.append(r['MTN50'][0][1])

        i+=1
    pd = rasman.bulk_reproj(pd)


    # stdout
    # writer = csv.writer(sys.stdout, lineterminator=os.linesep)
  
    #    writer = csv.writer(f)

    print("MTN Sheets: ", list(mtn))

    header = [ 'lon', 'lat', 'x', 'y', 'elev_ellip', 'elev_orto', 'N', 'index' ]

    with open(args.csv_out, 'w', newline='') as f:
        writer = csv.writer(f, lineterminator=os.linesep)
        writer.writerow(i for i in header)
        writer.writerows(pd)

