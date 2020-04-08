import sys
import os

# modify the enviroment so we can use the internal packages as is
# mainly to work from inside blender.
sys.path.append(os.path.dirname(__file__))