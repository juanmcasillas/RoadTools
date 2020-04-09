import bpy, bmesh

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

LIMIT = None
pc = 0
idx = 0
GEOM_TO_DO = []
MESH_VERTEX_LEN = int(len(mesh_vertex)/2)-1

geom_edges = []
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

    #for e in edges:
    #    BL_DEBUG.set_mark( obj_t.matrix_world @ e[0].co.xyz, kind='CUBE', scale=0.2 )
    #    BL_DEBUG.set_mark( obj_t.matrix_world @ e[1].co.xyz, kind='SPHERE', scale=0.2 )

    # calculate the nearest vertex for each point, get the minimum,
    # and build a face using it
    
    
    ret = bmesh.ops.contextual_create(bm, geom=e_1)
    bm.edges.index_update()
    for e in ret['edges']: geom_edges.append(e)

    ret = bmesh.ops.contextual_create(bm, geom=e_2)
    bm.edges.index_update()
    for e in ret['edges']: geom_edges.append(e)
    
    if pc == 0 or pc == (MESH_VERTEX_LEN-1):
        
        if pc == 0:
            # use first
            edge_cap= [  edges[0][0], edges[1][0] ] # edge from right to left
        else:
            # use last
            edge_cap= [  edges[0][1], edges[1][1] ] # edge from right to left
        ret = bmesh.ops.contextual_create(bm, geom= edge_cap)
        bm.edges.index_update()
        for e in ret['edges']: geom_edges.append(e)
        
    #if idx >= 8: break
    if LIMIT and pc >= LIMIT:
        break    
#
#bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=geom_edges)
#geom = bmesh.ops.bisect_edges(bm, edges=bm.edges,cuts = 1)
#for g in geom['geom_split']:
#    print(g)
#    if isinstance(g, bmesh.types.BMVert):
#        pass
#        #working or vertex
        


##############################################################
#
# End
# update the meshes
# free the bmesh
# 
##############################################################  

bm.calc_loop_triangles()
bm.to_mesh(obj_t.data)
obj_t.data.update()  
bm.free()
  
