import bpy
import os
import math

class ImportAsciiGrid():

  def load_ascii(filename, context=bpy.context):

    FILEHEADERLENGTH = 6
    SCALE = 10

import bpy
import os
import math

class ImportAsciiGrid():

  def load_ascii(filename, context=bpy.context):

    FILEHEADERLENGTH = 6
    SCALE = 10

    # Load file
    f = open(filename, "r")
    content = f.readlines()

    cols = int(content[0].split()[1])
    rows = int(content[1].split()[1])
    cellsize = float(content[4].split()[1])

    # Mesh scaling
    scale_xy = SCALE / float(cols - 1)
    scale_z = SCALE / (cellsize * float(cols - 1))
    #print(cellsize, float(cols - 1), scale_z)

    data = " ".join(content[FILEHEADERLENGTH:]).split()
    vertices = []
    faces = []

    # Create vertices
    index = 0;
    for r in range(rows - 1, -1, -1):
      for c in range(0, cols):
        zvalue = float(data[index]) 
        vertices.append((c, r, zvalue))
        index += 1

    # Construct faces
    index = 0
    for r in range(0, rows - 1):
      for c in range(0, cols - 1):
        v1 = index
        v2 = v1 + cols
        v3 = v2 + 1
        v4 = v1 + 1
        faces.append((v1, v2, v3, v4))
        index += 1
      index += 1

    # Create mesh
    name = os.path.splitext(os.path.basename(filename))[0]
    me = bpy.data.meshes.new(name)
    ob = bpy.data.objects.new(name, me)
    ob.location = (0, 0, 0)
    ob.show_name = True

    # Link object to scene and make active
    col = bpy.context.collection
    col.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)

    # Transform mesh
    bpy.ops.transform.resize(value = (scale_xy, scale_xy, scale_z))
    bpy.ops.transform.translate(value = (-scale_xy * (cols - 1) / 2.0, -scale_xy * (rows - 1) / 2.0, 0))

    # Setting data
    me.from_pydata(vertices, [], faces)

    # Update mesh with new data
    me.update()

    return {'FINISHED'}


ImportAsciiGrid.load_ascii('E:\Downloads\subset.asc')