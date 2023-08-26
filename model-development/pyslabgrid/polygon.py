from scipy.spatial import Delaunay
import numpy as np
import random
from shapely.geometry import Polygon, Point



def boundary(x, y, alpha =0.25, only_outer = True):
    # https://stackoverflow.com/questions/50549128/boundary-enclosing-a-given-set-of-points
    points = np.vstack([x, y]).T
    # Computing the alpha shape
    edges = alpha_shape(points, alpha=alpha, only_outer=only_outer)
    bounds = stitch_boundaries(edges)
    
    klon = []
    klat = []
    for i, j in bounds[0]:
       klon.append(x[i])
       klat.append(y[i])
    return (klon, klat)


def alpha_shape(points, alpha, only_outer=True):
    """
    Compute the alpha shape (concave hull) of a set of points.
    :param points: np.array of shape (n,2) points.
    :param alpha: alpha value.
    :param only_outer: boolean value to specify if we keep only the outer border
    or also inner edges.
    :return: set of (i,j) pairs representing edges of the alpha-shape. (i,j) are
    the indices in the points array.
    """
    assert points.shape[0] > 3, "Need at least four points"

    def add_edge(edges, i, j):
        """
        Add an edge between the i-th and j-th points,
        if not in the list already
        """
        if (i, j) in edges or (j, i) in edges:
            # already added
            assert (j, i) in edges, "Can't go twice over same directed edge right?"
            if only_outer:
                # if both neighboring triangles are in shape, it's not a boundary edge
                edges.remove((j, i))
            return
        edges.add((i, j))

    tri = Delaunay(points)
    edges = set()
    # Loop over triangles:
    # ia, ib, ic = indices of corner points of the triangle
    for ia, ib, ic in tri.vertices:
        pa = points[ia]
        pb = points[ib]
        pc = points[ic]
        # Computing radius of triangle circumcircle
        # www.mathalino.com/reviewer/derivation-of-formulas/derivation-of-formula-for-radius-of-circumcircle
        a = np.sqrt((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2)
        b = np.sqrt((pb[0] - pc[0]) ** 2 + (pb[1] - pc[1]) ** 2)
        c = np.sqrt((pc[0] - pa[0]) ** 2 + (pc[1] - pa[1]) ** 2)
        s = (a + b + c) / 2.0
        temp = s * (s - a) * (s - b) * (s - c)
        if temp > 0:
            area = np.sqrt(temp)
        else:
            area = -1
        if area>0:
            circum_r = a * b * c / (4.0 * area)
        else:
            circum_r = float('nan')
        if circum_r < alpha:
            add_edge(edges, ia, ib)
            add_edge(edges, ib, ic)
            add_edge(edges, ic, ia)
    
    return edges


def find_edges_with(i, edge_set):
    i_first = [j for (x,j) in edge_set if x==i]
    i_second = [j for (j,x) in edge_set if x==i]
    return i_first,i_second


def stitch_boundaries(edges):
    edge_set = edges.copy()
    boundary_lst = []
    while len(edge_set) > 0:
        boundary = []
        edge0 = edge_set.pop()
        boundary.append(edge0)
        last_edge = edge0
        while len(edge_set) > 0:
            i,j = last_edge
            j_first, j_second = find_edges_with(j, edge_set)
            if j_first:
                edge_set.remove((j, j_first[0]))
                edge_with_j = (j, j_first[0])
                boundary.append(edge_with_j)
                last_edge = edge_with_j
            elif j_second:
                edge_set.remove((j_second[0], j))
                edge_with_j = (j, j_second[0])  # flip edge rep
                boundary.append(edge_with_j)
                last_edge = edge_with_j

            if edge0[0] == last_edge[1]:
                break

        boundary_lst.append(boundary)
    return boundary_lst
    

def get_polygon(lon, lat):
    xy =[]
    for i in range(len(lon)):
        xy.append((lon[i], lat[i]))
    return Polygon(xy)

#Defining the randomization generator
def polygon_random_points(poly, num_points):
    min_x, min_y, max_x, max_y = poly.bounds
    points = []
    while len(points) < num_points:
        random_point = Point([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
        if (random_point.within(poly)):
            points.append(random_point)
    return points

def points2xy(points):
    x = []
    y = []
    for p in points:
        try:
            x.append(p.x)
            y.append(p.y)
        except:
            x.append(p[0])
            y.append(p[1])
    return x,y
    
def xyinpolygon(x,y, poly):
    inx = []
    iny = []
    points = []
    for i in range(len(x)):
        xypoint = Point(x[i], y[i])
        if (xypoint.within(poly)):
            points.append(xypoint)
    rx, ry = points2xy(points)
    return (rx, ry)

