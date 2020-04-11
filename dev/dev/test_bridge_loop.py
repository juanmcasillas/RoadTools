import bpy, bmesh
import collections


DEBUG = False
LIMIT = None
MIN_FACE_DIST = 10

# build a table with the point and the face_idx, to speed up the thing
# store the vertex only one time. use raycast to the Z down to check the
# points, instead closest.
# use side points, and center

obj_s=  bpy.data.objects['Plane']
mesh_s = obj_s.data
obj_t=  bpy.data.objects['Grid']

bm = bmesh.new()
bm.from_mesh(obj_t.data)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# here, I can flatten or move the thing
#for f in  bm.faces:
#    if f.select:
#        for v in f.verts:
#            bm.verts[v.index].co[2] += 5

verts = []
for v in mesh_s.vertices:
    verts.append(v.index)

mesh_vertex = []
for v_idx in verts:
    world_point = obj_s.matrix_world @ obj_s.data.vertices[v_idx].co
    local_point = obj_t.matrix_world.inverted() @ world_point

    #set_mark( obj_s.matrix_world @ obj_s.data.vertices[v_idx].co, kind='PLAIN_AXES', scale=0.2 )
    #set_mark( obj_t.matrix_world @ local_point,  scale=0.2 )
    
    vnew = bm.verts.new( local_point )
    mesh_vertex.append(vnew)

# update the index of the new created verts. WTF ???
bm.verts.index_update()
bm.verts.ensure_lookup_table()

#

pc = 0
idx = 0
GEOM_TO_DO = []
MESH_VERTEX_LEN = int(len(mesh_vertex)/2)-1

geom_edges = []
geom_faces = []

for pc in range(MESH_VERTEX_LEN):
    
    # iterate about the number of quads
    
    edges = []
    if pc == 0:
        e_1 = [ mesh_vertex[0], mesh_vertex[1] ] # right
        e_2 = [ mesh_vertex[2], mesh_vertex[3] ] # left
        idx = 1
    elif pc == 1:
        e_1 = [ mesh_vertex[1], mesh_vertex[4] ]  # right     
        e_2 = [ mesh_vertex[3], mesh_vertex[5] ]  # left edge
        idx += 3
    else:
        e_1 = [ mesh_vertex[idx], mesh_vertex[idx+2] ]       # right 
        e_2 = [ mesh_vertex[idx+1], mesh_vertex[idx+3] ]     # left edge
        idx += 2

        
    # 0 is the right side
    # 1 is the left side 
    edges = [ e_1, e_2 ]  
    
    # calculate the center of the edges, so we have more points and avoid the "half split"
    # problem in the face selector

    c1 = e_1[0].co + (e_1[1].co - e_1[0].co)/2
    c2 = e_2[0].co + (e_2[1].co - e_2[0].co)/2

    points = [item.co for sublist in edges for item in sublist]
    for p in points + [c1, c2]:
        result, location, normal, face_idx = obj_t.closest_point_on_mesh(p.xyz)
        if result:
            geom_faces.append(face_idx)


    #for e in edges:
    #    BL_DEBUG.set_mark( obj_t.matrix_world @ e[0].co.xyz, kind='CUBE', scale=0.2 )
    #    BL_DEBUG.set_mark( obj_t.matrix_world @ e[1].co.xyz, kind='SPHERE', scale=0.2 )

    # calculate the nearest vertex for each point, get the minimum,
    # and build a face using it
    
    if pc == 0:
        edge_cap= [  edges[0][0], edges[1][0] ] # edge from right to left
        ret = bmesh.ops.contextual_create(bm, geom= edge_cap)
        bm.edges.index_update()
        for e in ret['edges']: geom_edges.append(e)
    
    ret = bmesh.ops.contextual_create(bm, geom=e_1)
    bm.edges.index_update()
    for e in ret['edges']: geom_edges.append(e)

    ret = bmesh.ops.contextual_create(bm, geom=e_2)
    bm.edges.index_update()
    for e in ret['edges']: geom_edges.append(e)    
    
    if pc == (MESH_VERTEX_LEN-1):
        edge_cap= [  edges[0][1], edges[1][1] ] # edge from right to left
        ret = bmesh.ops.contextual_create(bm, geom= edge_cap)
        bm.edges.index_update()
        for e in ret['edges']: geom_edges.append(e)
        
    #if idx >= 8: break
    if LIMIT and pc >= LIMIT:
        break    

# list of faces just below the curve.
# remove dupes but preserve order of aparition
geom_faces = list(collections.OrderedDict.fromkeys(geom_faces).keys())

faces_to_delete = [bm.faces[f] for f in geom_faces]

deleted_geom_edges = []
for f in faces_to_delete:
    deleted_geom_edges += [e for e in f.edges]

#test the selection
#for face_idx in geom_faces:
#    bm.faces[face_idx].select = True

r = bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES_KEEP_BOUNDARY') # FACES_ONLY
bm.verts.index_update()
bm.edges.index_update()
bm.faces.index_update()

bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()

# remove all the deleted edges, but keep the exiting ones.

keep_edges = []
for edge in deleted_geom_edges:
    if edge.is_valid:
        keep_edges.append(edge)

new_edges = []
geom_created = bmesh.ops.subdivide_edges(bm, edges=keep_edges, cuts=1, use_grid_fill=False)
  
for item in geom_created['geom_split']:
    if isinstance(item, bmesh.types.BMEdge):
        #item.select = True
        #print(item.index)
        new_edges.append(item)

for e in bm.edges: e.select = False
for e in bm.verts: e.select = False
for e in bm.faces: e.select = False

#select the first subedge, run this, generates a list of 

#bmesh.ops.bridge_loops(bm, edges = geom_edges )

if False:
    p_edges = [ 180,181,182, 183, 184 ]
    g_edges = [ 312, 311, 310, 309, 321, 322, 323, 324, 100]
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    kk = []
    pp = [bm.edges[i] for i in p_edges]
    gg = [bm.edges[i] for i in g_edges]
    bmesh.ops.bridge_loops(bm, edges = pp + gg)



new_edges = [e.index for e in new_edges]

# first element in plane to get the loop

geom_edges[0].select = True
bm.calc_loop_triangles()
bm.to_mesh(obj_t.data)
obj_t.data.update()  
bm.free()


# bpy.ops.object.mode_set(mode = 'EDIT')
# bpy.ops.mesh.loop_multi_select(ring=False)

# plane_loop = [e for e in obj_t.data.edges if e.select]

# bpy.ops.object.mode_set(mode = 'OBJECT')


# # get the loops for the faces. for each 
# for edge_idx in new_edges:
#     for e in obj_t.data.edges: e.select = False 
    
#     bpy.ops.object.mode_set(mode = 'EDIT')
#     bpy.data.meshes['Grid'].edges[edge_idx].select = True
#     bpy.ops.mesh.loop_multi_select(ring=False)
#     bpy.ops.object.mode_set(mode = 'OBJECT')
#     grid_loop = [e for e in obj_t.data.edges if e.select]
#     print(edge_idx, grid_loop)


# bpy.ops.object.mode_set(mode = 'OBJECT')




# bm = bmesh.new()
# bm.from_mesh(obj_t.data)
# bm.verts.ensure_lookup_table()
# bm.edges.ensure_lookup_table()
# bm.faces.ensure_lookup_table()



# bm.calc_loop_triangles()
# bm.to_mesh(obj_t.data)
# obj_t.data.update()  
# bm.free()


##############################################################
#
# End
# update the meshes
# free the bmesh
# 
##############################################################  
