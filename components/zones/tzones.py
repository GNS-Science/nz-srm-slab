from shapely.geometry import Polygon, Point
import json
from scipy.interpolate import interp2d
import numpy as np
import sys
import components.kpolygon.polygon as poly
import csv
import re
# regumes: curst =0, crust above interface = 1, interfce = 2, slab = 3




def interface_depth_function(interface_model=None):
    if interface_model is None:
        interface_model = 'subduction/hikinterfacegrid.csv'

    depth_cutoff = 40
    
    slon, slat, sdep = ([],[],[])
    with open(interface_model, 'r') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        header = next(csvreader)
        for row in csvreader:
            if (float(row[2])< depth_cutoff):
                slon.append(float(row[0]))
                slat.append(float(row[1]))
                sdep.append(float(row[2]))
            
    fintp = interp2d(np.array(slon), np.array(slat), np.array(sdep), kind='linear')
    blon, blat = poly.boundary(slon, slat)
    return(fintp, (blon, blat))

def interface_config(subduction='hik'):
    # retrun depth function (interpolation) and polygon bounds
    if subduction=='hik':
        ifmodel = 'subduction/hikinterfacegrid.csv'
    elif subduction=='puy':
        ifmodel = 'subduction/puyinterfacegrid.csv'
    else:
        print("subduction not found!")
        return None, None
    
    fintp, ifbounds = interface_depth_function(interface_model=ifmodel)
    blon, blat = ifbounds
    pbounds = get_boundpolygon(blon, blat)
    
    return fintp, pbounds

def load_interface_configs(file = None):
    if file is None:
    	file = 'interface_configs.npy'
    interface_configs = np.load(file, allow_pickle=True)[()]
    return interface_configs
#
def get_interface_configs():
    interface_configs = {}
    fintp, pbounds =  interface_config('hik')
    interface_configs.update({'hik': {'fintp': fintp, 'pbounds': pbounds}})
    fintp, pbounds =  interface_config('puy')
    interface_configs.update({'puy': {'fintp': fintp, 'pbounds': pbounds}})
    return interface_configs

#
def get_regime(lon, lat, dep, fintp, pbounds, interface_buffer):
    if not is_within_zone(lon, lat, pbounds):
        regime = 0
    else:
        pdep = fintp(lon, lat)
        # check whether interface
        if (dep<(pdep-interface_buffer[0])):
            regime = 1
        elif (dep<=(pdep+interface_buffer[1])):
            regime = 2
        else:
            regime = 3
            
    return regime

#
def get_nzregime(lon, lat, dep, interface_configs = None, interface_buffer = [5,5]):
    # interface_configs is a dictionary of 
    # depth function (interpolation) and polygon bounds
    # regime = 0 for shallow crust (outside subduction), 1 for crust above subduction
    # 2 for interface and 3 for slab
    # first check is within bounds
    
    if interface_configs is None:
         interface_configs = load_interface_configs()
    
    regime_code = 0
    interface = [k for k in interface_configs.keys()]
    # check hik
    fintp = interface_configs[interface[0]]['fintp']
    pbounds = interface_configs[interface[0]]['pbounds']
    regime_code = get_regime(lon, lat, dep, fintp, pbounds, interface_buffer)
    
    # if outside, check Puy
    if regime_code == 0:
        fintp = interface_configs[interface[1]]['fintp']
        pbounds = interface_configs[interface[1]]['pbounds']
        regime_code = get_regime(lon, lat, dep, fintp, pbounds, interface_buffer)
   
    # one can map
    
    if regime_code==2:
       regime = 'interface'
    elif regime_code==3:
       regime = 'slab'
    else:
       regime = 'crust'
    
    return regime
  
#------------------------------------------------------------------

# given a lon, lat, check whether it is in TVZ or not
def iswithinTVZ(lon, lat, tvzbounds=None):
    bounds_provided = True
    if tvzbounds is None:
        bounds_provided = False
        
        dlon =  [176.8, 178.402, 177.853, 177.395, 177.304, 177.25, 
        177.195, 177.054, 177.002, 176.966, 176.945, 176.876, 176.853, 
        176.837, 176.795, 176.768, 176.724, 176.637, 176.529, 176.243, 176.067, 175.926, 175.895, 175.463, 
        175.068, 175.025, 174.988, 175.477, 175.477, 175.562, 175.649, 175.978, 176.037, 176.054, 
        176.085, 176.184, 176.252, 176.428, 176.592, 176.8]
        
        dlat = [-36.08, -36.104, -36.816, -37.586, -37.66, -37.708, -37.741, -37.929, -37.938, -37.938, 
        -37.95, -37.965, -38.016, -38.031, -38.043, -38.149, -38.284, -38.489, -38.695, -39.069, -39.291, 
        -39.476, -39.572, -39.684, -39.594, -39.585, -39.576, -38.797, -38.795, -38.683, 
        -38.567, -38.125, -37.896, -37.593, -37.29, -36.953, -36.87, 
        -36.592, -36.36, -36.08]
        
        dpoints = []
        for a,b in zip(dlon, dlat):
            dpoints.append((a, b))
            
        tvzbounds = Polygon(dpoints)
    if (lon==0) & (lon==0):
        return tvzbounds
    point = Point(lon, lat)
    if tvzbounds.contains(point):
        if bounds_provided:
            return True
        else:
            return True, tvzbounds
    else:
        if bounds_provided:
            return False
        else:
            return False, tvzbounds

def get_boundpolygon(blon, blat):
    #
    dpoints = []
    for a,b in zip(blon, blat):
       dpoints.append((a, b))
    return Polygon(dpoints)
    
# given a lon, lat, check whether it is in TVZ or not
def is_within_zone(lon, lat, boundpolygon):
    point = Point(lon, lat)
    if boundpolygon.contains(point):
       return True
    else:
       return False
       
       
def get_region(lon, lat, regionbounds):
    if is_within_zone(lon,lat,regionbounds['tvz']):
        region = 'tvz'
    elif is_within_zone(lon,lat,regionbounds['hik']):
        region = 'hik'
    elif is_within_zone(lon,lat,regionbounds['puy']):
        region = 'puy'
    else:
        region = 'crust'
    return (region)

