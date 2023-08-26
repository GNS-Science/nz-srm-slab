import csv
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point
import numpy as np
from matplotlib.path import Path

deg2km = 111.19492664455873
km2deg = 0.008993216059187306

# extract events on a profile/box
def get_abox(cx,cy, szone=None, params=None):
    if params is None:
        params= {'hL': 900,
        	  'hW': 10,
        	  'rothik': -10,
        	  'rotpuy':-10,
                 }
                 
    L = params['hL']*km2deg
    W = params['hW']*km2deg
    x = [cx-L, cx+L, cx+L,cx-L, cx-L]
    y = [cy+W, cy+W, cy-W, cy-W, cy+W]
    if szone=='hik':
        bx, by = rotate((cx,cy), (x,y), params['rothik'])
    else:
        bx, by = rotate((cx,cy), (x,y), params['rotpuy'])
    return bx, by

def get_aline(cx,cy, szone=None):
    L = 900*km2deg
    x = [xx for xx in np.arange((cx-L),(cx+L), 0.1)]
    y = [cy]*len(x)
    if szone=='hik':
        bx, by = rotate((cx,cy), (x,y), -10)
    else:
        bx, by = rotate((cx,cy), (x,y), -10)
    return bx, by
#
def get_inpolygon(X,Y, polygon):
    xs,ys = polygon
    tupVerts = []
    for x,y in zip(xs,ys):
        tupVerts.append((x,y))
    p = Path(tupVerts) # make a polygon
    points = np.vstack((X,Y)).T 
    IN = p.contains_points(points)
    return IN
import math

def rotate(origin, points, angle):
    ox, oy = origin
    qx, qy = [],[]
    pX, pY = points
    for px,py in zip(pX, pY): 
        qx.append(ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy))
        qy.append(oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy))
    return qx, qy

def is_within_interfacezone(evlon, evlat, szone, pbounds=None):
    if pbounds is None:
        finterp_file = {'hik': '../01subduction-model/finterp/hik_finterp.npy',
                    'puy': '../01subduction-model/finterp/puy_finterp.npy'}
        finterp = np.load(finterp_file[szone], allow_pickle=True)[()]
        pbounds = finterp['xbounds']
    if pbounds.contains(Point(evlon, evlat)):
        return True
    return False

# scaling relation
def mag2Area(mag):
    return 10**(mag-4.15)

def get_lonlat(fname, isheader = False):
    lon, lat = [],[]
    with open(fname, 'r') as f:
        csvreader = csv.reader(f)
        if isheader:
            next(csvreader)
        for row in csvreader:
            lon.append(float(row[0]))
            lat.append(float(row[1]))
    return lon,lat

def get_grid(szone):
    maxdep = {'hik':250, 'puy': 150}
    fiterp_file = {'hik': '../01subduction-model/finterp/hik_finterp.npy', 
               'puy': '../01subduction-model/finterp/puy_finterp.npy' }
    finterp = np.load(fiterp_file[szone], allow_pickle=True)[()]
    dep_finterp = finterp['depth']

    grid_file = {'hik': '../04mid-slab/grids/hik_11km_grids.csv', 
            'puy': '../04mid-slab/grids/puy_11km_grids.csv'}

    lon, lat  = get_lonlat(grid_file[szone], isheader = True)
    xlon, xlat, xdep = [],[],[]
    for x,y in zip(lon, lat):
        z = dep_finterp(np.transpose([[x],[y]]))
        if z> maxdep[szone]:
            continue
        xdep.append(z)
        xlon.append(x)
        xlat.append(y)
    return xlon, xlat, xdep
