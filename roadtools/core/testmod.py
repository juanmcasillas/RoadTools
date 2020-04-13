#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# testmod.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# simple test to import things from the module
# TODO: remove it after all works
# 
# ############################################################################
from smooth import smooth_gpx

def do_some_bizarre_thing():
    smooth_gpx( "../gpx/casillas_sotillo.gpx", output="output_test.gpx",title="salida")
