import numpy as np
import math

# lets shift the 3D points orthogonally
def reckon(x,y, d, bearing):
    # d is distance in km
    # x, y are corordinates in degrees
    # bearing or azimiuth in degrees
    
    R = 6378.1 #Radius of the Earth
    brng = np.deg2rad(bearing)
    lon1 = np.deg2rad(x)
    lat1 = np.deg2rad(y)
    
    lat2 = math.asin( math.sin(lat1)*math.cos(d/R) + math.cos(lat1)*math.sin(d/R)*math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng)*math.sin(d/R)*math.cos(lat1),
             math.cos(d/R)-math.sin(lat1)*math.sin(lat2))
    
    return np.rad2deg(lon2), np.rad2deg(lat2)

def reckon_depth(point_geom, H, method ='orthogonal'):
    lon, lat = point_geom['cordinate']
    h1 = point_geom['depth']
    theta1 = point_geom['dip'] # dip of the interface/slab
    strike = point_geom['strike']
    #
    theta2 = 180 - (theta1+90) # dip of the normal line/plane
    h2 = H*np.sin(np.deg2rad(theta2)) #  depth from h1 to the end of H
    
    rkdep = h1+h2
    #if rkdep<5:
     #   print(lon, lat, strike,theta1)
        
    # shifted length
    shift_h = H*np.cos(np.deg2rad(theta2));
    rklon, rklat = reckon(lon, lat, shift_h, strike-90)
    new_point_geom = {'cordinate': (rklon, rklat),
                     'depth': rkdep,
                     'strike': strike,
                     'dip': theta1}
    
    return new_point_geom
    
def shiftsheet(szone, H, sheet, finterp =None):
    X,Y,D = sheet
    if finterp is None:
        if szone=='hik':
            finterp = np.load('../1SubductionModel/finterp/hik_finterp.npy', allow_pickle=True)[()]
        else:
            finterp = np.load('../1SubductionModel/finterp/puy_finterp.npy', allow_pickle=True)[()]

    # test the interpolatiors
    fintp_strike = finterp['strikeAn'] 
    fintp_dip = finterp['dipAn'] 
    fintp_depth = finterp['depth'] 
    newX,newY, newZ = [],[],[]
    for x,y,d in zip(X,Y,D):
        if np.isnan(d):
            continue
    
        strike = fintp_strike(np.transpose([[x],[y]]))
        dip = fintp_dip(np.transpose([[x],[y]]))
        z = fintp_depth(np.transpose([[x],[y]]))
    
        point_geom = { 'cordinate': (x, y),
                       'depth': z[0],
                       'strike': strike[0],
                       'dip': dip[0]}
    
        newpointgeom = reckon_depth(point_geom, H)
        tx, ty = newpointgeom['cordinate']
        #if newpointgeom['depth']<=60:
        newX.append(tx)
        newY.append(ty)
        newZ.append(newpointgeom['depth'])
    
    return (newX,newY, newZ)
