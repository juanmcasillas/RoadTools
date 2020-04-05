#
# Use this file in Blender Editor to launch the module so we don't need to install it
#
import os
import sys
import bpy

filesDir = "/Archive/Src/RoadTools/roadtools"
initFile = "__init__.py"

if filesDir not in sys.path:
    sys.path.append(filesDir)

#import myscript
#import imp
#imp.reload(myscript)
#myscript.main()

file = os.path.join(filesDir, initFile)

if 'DEBUG_MODE' not in sys.argv:
    sys.argv.append('DEBUG_MODE')

exec(compile(open(file).read(), initFile, 'exec'))

if 'DEBUG_MODE' in sys.argv:
    sys.argv.remove('DEBUG_MODE')

# to reload: bpy.ops.script.reload()