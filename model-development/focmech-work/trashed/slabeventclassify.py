import csv
from shapely.geometry import Polygon, Point
import numpy as np
import mat

def within_interfacezone(evlon, evlat):
    # test the interpolatiors
    hik_finterp = np.load('../1SubductionModel/finterp/hik_finterp.npy', allow_pickle=True)[()]

    pbounds = hik_finterp['xbounds']
    
    if pbounds.contains(Point(evlon, evlat)):
        return 'hik'
    
    puy_finterp = np.load('../1SubductionModel/finterp/puy_finterp.npy', allow_pickle=True)[()]
    pbounds = puy_finterp['xbounds']
    
    if pbounds.contains(Point(evlon, evlat)):
        return 'puy'
    
    return None
    
def is_slabevent(evlon, evlat, evdep, fixed_parameters = None):
    # Note that evdep is positive
    # for each event:
    #  if dep <= CRUST_THICKNESS && dep > interface_depth
    #       'NOT SLAB'
    #  if dep > 60 km
    #        'SLAB'
    #  if dep < 60 km & dep > interface_depth+buffer
    #     
    # (2) shallow_events, dep <= CRUST_THICKNESS
    # (3) define filter for interface buffer
    #     for events with dep <60 km, 
    # 
    
    evdep = abs(evdep)
    if fixed_parameters is None:
        fixed_parameters = {
                     'Hmax_interface': 80, # maximum depth
                     'interface_buffer': [10, 10],
                     'Hmax_crust': 40,
                     'min_depth': 0,
                     'max_depth': 500, # tentative
                 }
    #
    if evdep>fixed_parameters['Hmax_interface']:
        return True
    
    szone = within_interfacezone(evlon, evlat)
    if szone is None:
        return False
    else:
        if szone =='hik':
            dep_finterp = np.load('../1SubductionModel/finterp/hik_finterp_lowerbounds.npy', allow_pickle=True)[()]
        else:
            dep_finterp = np.load('../1SubductionModel/finterp/puy_finterp_lowerbounds.npy', allow_pickle=True)[()]
        lower_interface_depth = dep_finterp(np.transpose([[evlon], [evlat]]))
        if evdep<=lower_interface_depth:
            return False
        else:
            return True
