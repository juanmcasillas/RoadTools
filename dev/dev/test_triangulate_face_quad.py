import bpy
import bmesh
import copy
from bl_utils import BL_UTILS

mesh_t= bpy.data.meshes[bpy.data.objects['Grid'].data.name]

bpy.ops.object.mode_set(mode = 'EDIT')
bm = bmesh.new()
bm.from_mesh(mesh_t)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# work on selected face
f = [f for f in bm.faces if f.select][0]


BL_UTILS.triangulate_face_quad(bm, f.index)

bpy.ops.object.mode_set(mode = 'OBJECT') 
bm.to_mesh(mesh_t)
mesh_t.update()
bpy.ops.object.mode_set(mode = 'EDIT')