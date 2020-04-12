import bpy
import bmesh


# >>> e = bm.edges[476]
# >>> e
# <BMEdge(0x1311cd4d0), index=476, verts=(0x7fce98d2a6e0/214, 0x7fce98d2bba8/309)>

# >>> for v in e.verts:
# ...     print(v)
# ...     
# <BMVert(0x7fce98d2a6e0), index=214>
# <BMVert(0x7fce98d2bba8), index=309>

# >>> v = bm.verts[214]
# >>> for l in v.link_edges: print(l)
# ... 
# <BMEdge(0x1311c6310), index=112, verts=(0x7fce98d2a6e0/214, 0x7fce98d28680/66)>     no_bound
# <BMEdge(0x1311c9a60), index=289, verts=(0x7fce98d28450/56, 0x7fce98d2a6e0/214)>       
# <BMEdge(0x1311cd390), index=472, verts=(0x7fce98d2bb70/308, 0x7fce98d2a6e0/214)>    no_bound
# <BMEdge(0x1311cd4d0), index=476, verts=(0x7fce98d2a6e0/214, 0x7fce98d2bba8/309)>    my_self

# >>> 



def navigate_edge(bm,edge_idx, edges=[], vertex=[], distance=0, maxdistance=100):
    v0 = bm.edges[edge_idx].verts[0]
    v1 = bm.edges[edge_idx].verts[1]

    if distance >= maxdistance:
        return([],[],0)
    
    if edge_idx in edges:
        #print("found myself")
        return(edges, vertex, distance)
    
    #print(edge_idx, edges, vertex, distance,maxdistance)

    if v0.index not in vertex:
        for l in v0.link_edges:
            if not l.is_boundary: continue
            if l.index == edge_idx: continue
            edges,vertex, distance = navigate_edge(bm, l.index, 
                        edges = edges+[edge_idx], 
                        vertex= vertex+[v0.index], 
                        distance=distance+1)

    if v1.index not in vertex:
        for l in v1.link_edges:
            if not l.is_boundary: continue
            if l.index == edge_idx: continue
            edges,vertex, distance = navigate_edge(bm, l.index, 
                        edges = edges+[edge_idx], 
                        vertex= vertex+[v1.index], 
                        distance=distance+1)
    
    return(edges,vertex,distance)


def close_hole(bm, edge):
    edges,vertex,distance = navigate_edge(bm, edge)
    if len(edges)>0:
        geom_edges = [edge for edge in bm.edges if edge.index in edges]
        new_faces = bmesh.ops.contextual_create(bm, geom= geom_edges)
        bm.edges.index_update()
    

obj_t  =  bpy.data.objects['Grid']
bm = bmesh.new()
bm.from_mesh(obj_t.data)
bm.verts.ensure_lookup_table()
bm.edges.ensure_lookup_table()
bm.faces.ensure_lookup_table()


boundary_selected_edges = [edge for edge in bm.edges if edge.is_boundary and edge.select]
print("Found %d boundary edges" % len(boundary_selected_edges))

while len(boundary_selected_edges) > 0:
    edge = boundary_selected_edges[0]
    print("----")
    close_hole(bm, edge.index)
    boundary_selected_edges = [edge for edge in bm.edges if edge.is_boundary and edge.select]
    print("Found %d boundary edges" % len(boundary_selected_edges))

bpy.context.view_layer.update()
bm.calc_loop_triangles()
bm.to_mesh(obj_t.data)
obj_t.data.update()  
bm.free()