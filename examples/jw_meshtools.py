"""
Toolbox for generating a mesh

"""
import numpy as np
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt
import meshpy.triangle as triangle


# Extract the edges
# ouput, edges and boundary edges
def find_edges(t):
    # pdb.set_trace();
    ne = t.shape[0]
    # generate an array of all edges
    tt = np.array([t[:, 0], t[:, 1], t[:, 1], t[:, 2], t[:, 2], t[:, 0]]).T.reshape(
        3 * ne, 2
    )
    ttt = np.sort(tt, 1)

    # find all boundary edges
    all_edges = [tuple(x) for x in ttt]
    boundary_edges = [x for x in all_edges if all_edges.count(x) == 1]

    # find all unique edges
    all_edges = list(set(all_edges))
    return all_edges, boundary_edges


##################
#
#  Boundary Tools
#
##################

# given one segment
# e.g.  (X,2) find segment (2,Y) and delete (2,Y) from list
def find_next_segment(all_segments, node):
    # find next connecting segment
    help = [x for x in all_segments if x[0] == node]

    new_bound = False
    if len(help) == 0:  # if connecting segment does not exist (=>new boundary)
        ret = all_segments[0]
        new_bound = True
    else:
        ret = help[0]

    del all_segments[all_segments.index(ret)]
    return ret, new_bound


# sort segments:  (3,6),(6,1),(1,12),(12,5),...
# on output: sorted segments and indices of the different boundaries
def sort_segments(all_segments):
    count = len(all_segments)

    node = -1
    sorted_segments = []
    boundaries = []
    for j in range(len(all_segments)):
        seg, new_bound = find_next_segment(all_segments, node)
        node = seg[1]
        sorted_segments.append(seg)
        if new_bound:
            boundaries.append(j)

    if len(sorted_segments) != count:
        print("Something is wrong, number of segments not the same")
    return sorted_segments, boundaries


# connect segments in a defined way
# (see sort_segments), but start sorting with a defined point p
# multiple p'2 for different closed boundaries are possible
def connect_boundary(boundary_segments, pall, p=[]):

    # sort the boundary segments
    allseg = boundary_segments[:]
    allseg, boundaries = sort_segments(allseg)
    if p == []:
        return allseg, boundaries

    max_boundaries = len(boundaries)

    # find all nodes on the given boundary
    nodes = [x[0] for x in allseg]
    # find closest nodes to desired point list p
    indices, distances = find_closest_node(nodes, pall, p)

    # change order within each closed boundary
    flag_sorted = []
    for j in range(len(boundaries)):
        flag_sorted.append(False)

    for j in range(len(indices)):
        # find position of node in the boundary list
        # indj gives the position of the segment in allseg
        indj = nodes.index(indices[j])
        # find the number of boundary the node belongs to
        this_boundary = (np.where(np.array(boundaries) <= indj)[0])[-1]

        if not flag_sorted[this_boundary]:
            # define the indices for slicing
            ind_1 = boundaries[this_boundary]
            if this_boundary + 1 == max_boundaries:
                ind_2 = len(allseg)
            else:
                ind_2 = boundaries[this_boundary + 1]

            # rearange the segments in the corresponding boundary
            allseg = (
                allseg[:ind_1]
                + allseg[indj:ind_2]
                + allseg[ind_1:indj]
                + allseg[ind_2:]
            )
            # resort only once
            flag_sorted[this_boundary] = True

    return allseg, boundaries


#
# find closest node to point p0 in a list of N nodes
# Pall coordinates of M nodes  M>=N
# constraint defines constraints on distance
def find_closest_node(nodes, pall, p0, constraint=-1, tree=None):
    # take those points of the node list

    if tree is None:
        p_nodes = np.array(pall)
        p_nodes = p_nodes[nodes]
        # look for minimum distance, define dist function
        mytree = cKDTree(p_nodes)
    else:
        mytree = tree

    dist, index = mytree.query(np.array(p0))

    node_closest = [nodes[j] for j in index]

    # check constraints
    num_p = len(p0)
    if constraint < 0:
        return node_closest, dist
    elif np.isscalar(constraint):
        constraint = constraint * np.ones(num_p)
    elif len(p0) != len(constraint):
        print("Error in constraint definition")
        return [], []

    # check constraint for each node
    flags = [((dist[j] <= constraint[j]) | (constraint[j] < 0))
            for j in range(num_p)]
    for j in range(num_p):
        if not flags[j]:
            node_closest[j] = -1
    return node_closest, dist


# check relative position of two points
def same_point(p1, p2, delta):
    dp = np.array(p1) - np.array(p2)
    d = np.sqrt(dp[0] ** 2 + dp[1] ** 2)
    ret = False
    if d < delta:
        ret = True
    return ret


#####################
#
# Make simple curves
#
#####################
#
#
#
# make a circle or part of it
#
def circle_segments(
    middle, radius, num_points=10, a_min=0.0, a_max=2.0 * np.pi, edge_length=-1
):
    # check for closed loop
    number_points = num_points
    if edge_length > 0:
        number_points = np.floor(abs(radius / edge_length * (a_max - a_min))) + 1

    delta = (a_max - a_min) / number_points
    closed = False
    if abs(a_max - a_min - 2 * np.pi) < 0.1 * delta:
        closed = True

    t = np.linspace(a_min, a_max, number_points, not closed)
    # define points
    points = [
        (middle[0] + radius * np.cos(angle), middle[1] + radius * np.sin(angle))
        for angle in t
    ]

    # define vertices
    vertices = [(j, j + 1) for j in range(0, len(points) - 1, 1)]
    if closed:
        vertices += [(len(points) - 1, 0)]
    return points, vertices


# Straight line
def line_segments(p1, p2, num_points=10, edge_length=-1):

    number_points = num_points
    if edge_length > 0:
        p1 = np.array(p1)
        p2 = np.array(p2)
        number_points = np.floor(np.sqrt(np.sum((p2 - p1) ** 2)) / edge_length) + 1

    t = np.linspace(0, 1, number_points)
    points = [
        (p1[0] + param * (p2[0] - p1[0]), p1[1] + param * (p2[1] - p1[1]))
        for param in t
    ]
    vertices = [(j, j + 1) for j in range(0, len(points) - 1, 1)]
    return points, vertices


# Rectangle
def rectangle_segments(p1, p2, num_points=60, edge_length=-1):
    p11 = [p2[0], p1[1]]
    p22 = [p1[0], p2[1]]
    npoints = np.floor(num_points / 4)
    p_1, v_1 = line_segments(p1, p11, npoints, edge_length)
    p_2, v_2 = line_segments(p11, p2, npoints, edge_length)
    p_3, v_3 = line_segments(p2, p22, npoints, edge_length)
    p_4, v_4 = line_segments(p22, p1, npoints, edge_length)
    p, v = add_segments(p_1, p_2)
    p, v = add_segments(p, p_3)
    p, v = add_segments(p, p_4)
    return p, v


# List of points
def point_segments(p):
    p1 = np.array(p)
    delta = np.min(np.sqrt(np.sum((p1[1:] - p1[:-1]) ** 2, axis=1)))
    pall = [(x[0], x[1]) for x in p]
    closed = False
    if same_point(p1[0], p1[-1], delta):
        pall = pall[:-1]
        closed = True

    vertices = [(j, j + 1) for j in range(0, len(pall) - 1, 1)]
    if closed:
        vertices += [(len(pall) - 1, 0)]

    return pall, vertices


# Connect two different polygons
def add_segments(p1, p2, closed=False):
    p1 = np.array(p1)
    p2 = np.array(p2)
    # find smallest distance within points p1 and p2
    min1 = np.min(np.sqrt(np.sum((p1[1:] - p1[:-1]) ** 2, axis=1)))
    min2 = np.min(np.sqrt(np.sum((p2[1:] - p2[:-1]) ** 2, axis=1)))
    delta = np.min([min1, min2])

    # Add second curve to first curve
    del_first = same_point(p1[-1], p2[0], delta)
    pall = p1[:]
    if del_first:
        pall += p2[1:]
    else:
        pall += p2

    # check if pall is closed
    del_last = same_point(pall[-1], p1[0], delta)
    if del_last:
        pall = pall[:-1]

    vertices = [(j, j + 1) for j in range(0, len(pall) - 1, 1)]
    if del_last or closed:
        vertices += [(len(pall) - 1, 0)]

    return pall, vertices


# Append Curves
def add_curves(p1, v1, p2, v2):
    # make one list
    p = p1 + p2
    v2n = [(v2[j][0] + len(p1), v2[j][1] + len(p1)) for j in range(len(v2))]
    v = v1 + v2n
    return p, v


# Generate mesh
def do_tri_mesh(points, vertices, edge_length=-1, holes=[], tri_refine=None):
    info = triangle.MeshInfo()
    info.set_points(points)
    if len(holes) > 0:
        info.set_holes(holes)
    info.set_facets(vertices)

    if tri_refine is not None:
        mesh = triangle.build(info, refinement_func=tri_refine)
    elif edge_length <= 0:
        mesh = triangle.build(info)
    else:
        mesh = triangle.build(info, max_volume=0.5 * edge_length ** 2)

    mesh_points = np.array(mesh.points)
    mesh_elements = np.array(mesh.elements)

    plt.triplot(
        mesh_points[:, 0],
        mesh_points[:, 1],
        mesh_elements,
    )
    plt.show()
    return mesh_points, mesh_elements
