import pyslabgrid.mat as mat
import csv
import matplotlib.pyplot as plt
import pyslabgrid.polygon as poly
from shapely.geometry import Polygon, Point
import json
from scipy.interpolate import interp2d
from scipy.interpolate import RBFInterpolator
import numpy as np
import pyslabgrid.reckoner as reck
from matplotlib.path import Path
import math
import pyslabgrid.eqcatana as eqc

def read_catalog(catalog, min_year=1900, min_mag=3.0, slabzone = 'hik-whole', decimate=None):
    cat_folder = '../02midslab-config/projected_catalogs/'
    eqcat = eqc.read_projectedslabcatalog(cat_folder+catalog, min_year=min_year, min_mag=min_mag)
    slon = np.array(eqcat['slon'])
    slat = np.array(eqcat['slat'])
    smag = np.array(eqcat['mag'])

    in_zone = eqc.get_inpolgyon((eqcat['slon'],eqcat['slat']), eqc.get_zonepolygon(slabzone))
    mags_in_zone = smag[in_zone]
    lons_in_zone = slon[in_zone]
    lats_in_zone = slat[in_zone]
    
    if decimate is not None:
        mags_in_zone = [round(m, decimate) for m in mags_in_zone]
    return lons_in_zone, lats_in_zone, mags_in_zone
    
    
def get_3sheets(X,Y,Z, szone, depdistr = None, doplot=False):
    # orthogal shifted sheets
    if depdistr is None:
        depdistr = {'hik': [[17, 29, 40]], 'puy': [[10,15,20]], }

    deps = depdistr[szone][0]
    # example
    # a = [[1,3,4],[5,6,7]]
    # nrows, ncols = len(a), len(a[0])
    # b = mat.flatten(a)
    # print(a, b)
    # c = np.reshape(np.array(b), (nrows, ncols)).tolist()
    # print(c)
    X,Y,Z = mat.flatten(X), mat.flatten(Y), mat.flatten(Z)
    
    X1, Y1, Z1 = reck.shiftsheet(szone, deps[0], (X,Y,Z))
    X2, Y2, Z2 = reck.shiftsheet(szone, deps[1], (X,Y,Z))
    X3, Y3, Z3 = reck.shiftsheet(szone, deps[2], (X,Y,Z))
    
    sheets = {'interface': [X,Y,Z],
              'slabq1': [X1,Y1,Z1], 
              'slabq2': [X2,Y2,Z2], 
              'slabq3': [X3,Y3,Z3],}
    if doplot:
        #%matplotlib notebook
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"}, figsize=(7,7))
        ax.set_box_aspect([1,1,0.3])
        
        ax.plot3D(X, Y, Z,'.', color='r');
        ax.plot3D(X1, Y1, Z1,'.', color='c');
        ax.plot3D(X2, Y2, Z2,'.', color='b');
        ax.plot3D(X3, Y3, Z3,'.', color='k');
        ax.invert_zaxis()
        
    return sheets

def get_centroids(X,Y,Z, i,j):
    cx = round(np.mean([X[i,j], X[i+1,j], X[i,j+1], X[i+1,j+1]]),4)
    cy = round(np.mean([Y[i,j], Y[i+1,j], Y[i,j+1], Y[i+1,j+1]]),4)
    cz = round(np.mean([Z[i,j], Z[i+1,j], Z[i,j+1], Z[i+1,j+1]]),3)
    return cx,cy,cz

def generate_gridfiles(szone, DX_KM = 40, outfolder = 'grids/', doplot=False, depdistr=None):

    X,Y,Z = compute_slabgrids(szone, None, dx_km=DX_KM, doplot=False, clipzone=False)

    sheets = get_3sheets(X,Y,Z, szone, depdistr = depdistr, doplot=doplot);

    X1,Y1,Z1 = sheets['slabq1']
    X2,Y2,Z2 = sheets['slabq2']
    X3,Y3,Z3 = sheets['slabq3']

    nr, nc = len(X),len(X[0])

    X1,Y1,Z1 = np.reshape(X1,(nr,nc)), np.reshape(Y1,(nr,nc)), np.reshape(Z1,(nr,nc))
    X2,Y2,Z2 = np.reshape(X2,(nr,nc)), np.reshape(Y2,(nr,nc)), np.reshape(Z2,(nr,nc))
    X3,Y3,Z3 = np.reshape(X3,(nr,nc)), np.reshape(Y3,(nr,nc)), np.reshape(Z3,(nr,nc))

    # write-out -------------------
    outfile_grids = szone +'_' + str(DX_KM)+'km_grids.csv'
    outfile_meshgrids =  szone + '_' + str(DX_KM)+'km_meshed-midslabgrids.csv'

    f1 = open(outfolder+outfile_grids, 'w')
    f2 = open(outfolder+outfile_meshgrids, 'w')

    f1.write('clon1,clat1,cdep1,clon2,clat2,cdep2,clon3,clat3,cdep3')
    f2.write('clon,clat,cdep,lon1,lat1,dep1,lon2,lat2,dep2,lon3,lat3,dep3,lon4,lat4,dep4')

    for i in range(nr-1):
        for j in range(nc-1):
   
            
            cx2, cy2, cz2 = get_centroids(X2,Y2, Z2, i,j)
            if not is_inzone(cx2, cy2, szone):
                 continue
            cx1, cy1, cz1 = get_centroids(X1,Y1, Z1, i,j)
            cx3, cy3, cz3 = get_centroids(X3,Y3, Z3, i,j)
            f1.write('\n%.4f,%.4f,%.3f' %(cx1,cy1,cz1))
            f1.write(',%.4f,%.4f,%.3f' %(cx2,cy2,cz2))
            f1.write(',%.4f,%.4f,%.3f' %(cx3,cy3,cz3))
            
            #midslab -----------------
            f2.write('\n%.4f,%.4f,%.3f' %(cx2,cy2,cz2))
            f2.write(',%.4f,%.4f,%.3f' %(X2[i,j],Y2[i,j],Z2[i,j]))
            f2.write(',%.4f,%.4f,%.3f' %(X2[i+1,j],Y2[i+1,j],Z2[i+1,j]))
            f2.write(',%.4f,%.4f,%.3f' %(X2[i+1,j+1],Y2[i+1,j+1],Z2[i+1,j+1]))
            f2.write(',%.4f,%.4f,%.3f' %(X2[i,j+1],Y2[i,j+1],Z2[i,j+1]))
        
    f1.close()
    f2.close()
    print('\n>>> FILES written: ') 
    print(outfolder+outfile_grids)
    print(outfolder+outfile_meshgrids)
    return (outfile_grids, outfile_meshgrids)

def read_grid(gridfile):
    x1,y1,z1,x2,y2,z2,x3,y3,z3 = [],[],[], [],[],[], [],[],[]
    with open(gridfile, 'r') as f:
        csvreader = csv.reader(f)
        header = next(csvreader)
        for row in csvreader:
            x1.append(float(row[0]))
            y1.append(float(row[1]))
            z1.append(float(row[2]))  
            x2.append(float(row[3]))
            y2.append(float(row[4]))
            z2.append(float(row[5]))  
            x3.append(float(row[6]))
            y3.append(float(row[7]))
            z3.append(float(row[8]))  
    return x1,y1,z1,x2,y2,z2,x3,y3,z3

def read_meshgrid(meshgridfile, maxdepth=None):
    x,y,z =[],[],[]
    x1,y1,z1,x2,y2,z2= [],[],[], [],[],[]
    x3,y3,z3,x4,y4,z4 = [],[],[],[],[],[]
    with open(meshgridfile, 'r') as f:
        csvreader = csv.reader(f)
        header = next(csvreader)
        for row in csvreader:
            if maxdepth is not None:
                if float(row[8])>maxdepth:
                    continue
            x.append(float(row[0]))
            y.append(float(row[1]))
            z.append(float(row[2]))  
            x1.append(float(row[3]))
            y1.append(float(row[4]))
            z1.append(float(row[5]))  
            x2.append(float(row[6]))
            y2.append(float(row[7]))
            z2.append(float(row[8]))  
            x3.append(float(row[9]))
            y3.append(float(row[10]))
            z3.append(float(row[11]))  
            x4.append(float(row[12]))
            y4.append(float(row[13]))
            z4.append(float(row[14]))  
    return x,y,z,x1,y1,z1,x2,y2,z2,x3,y3,z3,x4,y4,z4

def get_pbounds(szone):
    finterp_file = {'hik': '../subduction-model/finterp/hik_finterp.npy',
                    'puy': '../subduction-model/finterp/puy_finterp.npy'}
    finterp = np.load(finterp_file[szone], allow_pickle=True)[()]
    pbounds = finterp['xbounds']
    return pbounds
    
def is_inzone(evlon, evlat, szone):
    pbounds = get_pbounds(szone)
    if pbounds.contains(Point(evlon, evlat)):
        return True
    return False

def get_points_within_bounds(points, polygon_bounds):
    path_p = Path(polygon_bounds.boundary)
    inside_points = path_p.contains_points(points)
    points_within = np.array(points)[inside_points].tolist()
    return points_within
    # Example:
    # finterp = np.load('../1SubductionModel/hik_finterp.npy', allow_pickle=True)[()]
    # pbounds = finterp['pbounds']
    # points = [(177, -41), (177, -40)]
    # points_within_p_3 = get_points_within_bounds(points, pbounds)
    # print(points_within_p_3)
    # [[177, -41], [177, -40]]
    # 475.25359439849854
    # x, y = pbounds.exterior.coords.xy
    # plt.plot(x,y, '-');
    
def compute_slabgrids(szone, fileout=None, dx_km=11, doplot=False, dep_finterp=None, clipzone = False):
    startpoint = {'hik': [182.3, -35.5, 210, 1150, 1000], 
                  'puy':[162.5, -47.9, 40, 650, 600] }
    
    finterp_file = {'hik': '../subduction-model/finterp/hik_finterp.npy',
                    'puy': '../subduction-model/finterp/puy_finterp.npy'}
                    
    finterp = np.load(finterp_file[szone], allow_pickle=True)[()]    
    pbounds = get_pbounds(szone)

    finterp_dip = finterp['dipAn'];
    bx, by = pbounds.exterior.coords.xy
    if doplot:
        plt.figure(figsize=(7,7)) 
        plt.plot(bx,by,'-');
        
    x0, y0, strike, maxl, maxw = startpoint[szone]

    xx, yy =[],[]
    tx, ty = x0,y0
    for d in np.arange(0,maxl,dx_km):
        tx,ty = reck.reckon(tx,ty, dx_km, strike)
        xx.append(tx)
        yy.append(ty)
    if dep_finterp is None:
        dep_finterp = finterp['depth']
    
    X,Y,Z = [],[],[]
    for x,y in zip(xx,yy):
        cx,cy,cz = [],[],[]
        tx,ty = x,y
        for d in np.arange(0,maxw,dx_km):  
            fdip = finterp_dip(np.transpose([[tx],[ty]]))
            dxx = dx_km*np.cos(np.deg2rad(fdip))[0]
            tx,ty = reck.reckon(tx,ty, dxx, strike+90)
            
            tz = dep_finterp(np.transpose([[tx],[ty]]))[0]
            if clipzone:
               if not is_inzone(tx, ty, szone):
                    tz = float('nan')
            cx.append(tx)
            cy.append(ty)
            cz.append(tz)
        
        X.append(cx)
        Y.append(cy)
        Z.append(cz)
    
    xx = mat.flatten(X)
    yy = mat.flatten(Y)
    zz = mat.flatten(Z)
    
    if fileout is not None:
       # write out
       with open(fileout, 'w') as f:
            if not clipzone:
               f.write('row-major:%dx%d\n' %(len(X[0]), len(X)))
               f.write('lon,lat,dep')
            if clipzone:
               for x,y,z in zip(xx, yy,zz):
                    if math.isnan(z):
                       continue
                    f.write('\n%.4f,%.4f,%.3f' %(x,y,z))
            else:
               for x,y,z in zip(XX,YY,ZZ):
                    f.write('\n%.4f,%.4f,%.3f' %(x,y,z))
    return X,Y,Z
    
    
