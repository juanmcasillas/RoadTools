#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ############################################################################
#
# __init__.py
# 04/13/2020 (c) Juan M. Casillas <juanm.casillas@gmail.com>
#
# set the path so we can call these things from outside (blender imports)
# 
# ############################################################################
import sys
import os

# modify the enviroment so we can use the internal packages as is
# mainly to work from inside blender.
sys.path.append(os.path.dirname(__file__))