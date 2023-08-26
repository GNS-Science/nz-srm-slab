import csv
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path
from shapely.geometry import Polygon, Point
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

def read_grid(gridfile):
    x,y = [],[]
    with open(gridfile, 'r') as f:
        csvreader = csv.reader(f)
        header = next(csvreader)
        for row in csvreader:
            x.append(float(row[0]))
            y.append(float(row[1])) 
    return x,y

def get_inpolgyon(dataxy, polygonxy):
    x,y = dataxy
    blon, blat = polygonxy
    points = np.vstack((x,y)).T 
   # blon, blat = polygon
    tupVerts = []
    for tx,ty in zip(blon, blat):
        tupVerts.append((tx,ty))
    pbounds = Path(tupVerts) # make a polygon
    indx = pbounds.contains_points(points)
    return indx

def read_projectedslabcatalog(input_file, min_year=99999, min_mag=99, remove_depths=[]):
    #  lon,lat, dep, mag, year, slat, slon, sdep, dproj
    eqcat = {}
    with open(input_file, "r") as f:
        datareader=csv.reader(f)
        header = next(datareader)
        nrow = 0
        year, lon, lat, dep, mag, = [], [],[],[],[]
        slat, slon, sdep = [],[],[]
        for row in datareader:  
            if  float(row[4])< min_year:
                continue
            if  float(row[3])< min_mag:
                continue
            do_continue = False
            for rdep in remove_depths:
                if float(row[2])== rdep:
                    do_continue = True
                    break
            if do_continue:
                continue
            
            lon.append(float(row[0]))
            lat.append(float(row[1]))
            dep.append(float(row[2]))
            mag.append(float(row[3]))
            year.append(float(row[4]))
            slon.append(float(row[5]))
            slat.append(float(row[6]))
            sdep.append(float(row[7]))
            
    eqcat.update({'year': year, 'lon':lon, 'lat': lat, 'dep': dep,
                      'slon': slon,'slat':slat, 'sdep':sdep,
                      'mag':mag})
    return eqcat

def get_zonepolygon(slabzone):
    zone_polygon_file = {
        'hik-whole': '../03uniform-area-zones/zone_polygons/hik_midslab-zone-whole.csv',
        'puy-whole': '../03uniform-area-zones/zone_polygons/puy_midslab-zone-whole.csv',
        'hik-steep': '../03uniform-area-zones/zone_polygons/hik_midslab-zone-steep.csv',
        'hik-flat': '../03uniform-area-zones/zone_polygons/hik_midslab-zone-flat.csv',
        'puy-steep': '../03uniform-area-zones/zone_polygons/puy_midslab-zone-steep.csv',
        'puy-flat': '../03uniform-area-zones/zone_polygons/puy_midslab-zone-flat.csv',
    }
    
    wx,wy = read_grid(zone_polygon_file[slabzone])
    return wx,wy


def scatter_magdensity(years, mags, ax, fig):
    mags = np.array([round(m,1) for m in mags.tolist()])
    uyear, umags, counts = [],[],[]
    set_year = [x for x in set(years.tolist())]
    set_mag = [m for m in set(mags.tolist())]
    
    for m in set_mag:
        for y in set_year:
            kount = sum((years==y) & (mags==m))
            if kount>0:
                uyear.append(y)
                umags.append(m)
                counts.append(kount)
            
    sc = ax.scatter(uyear, umags, c=counts, s=20, cmap='plasma')
    cbaxes = inset_axes(ax, width="100%", height="100%", \
                        bbox_to_anchor=(0.03,1-0.7,.01,.6), loc=2, bbox_transform=ax.transAxes) 
    cbar = fig.colorbar(sc, cax=cbaxes, shrink=0.5)
    
    cbar.ax.get_yaxis().labelpad = -52
    cbar.ax.set_ylabel('count', fontsize=12)
    cbar.ax.tick_params(labelsize=12)
    ax.set_xlabel('year')
    ax.set_ylabel('magnitude (Mw)')

def plot_yearlycounts(year, mag, ax):
    set_year = [x for x in set(year.tolist())]
    set_mag = [m for m in np.arange(3.0, 6, 0.5)]
    set_plotsym = ['o-', 's-', 'd-','^-', 'v-', '-']
    for umag, plotsym in zip(set_mag, set_plotsym):
        nyearly = []
        for uyear in set_year:
            cumcount = sum((year==uyear) & (mag>=umag))
            nyearly.append(cumcount)
        tstr = r'$Mw\leq$'+str(umag)
        ax.semilogy(set_year, nyearly, plotsym, markersize=6, label=tstr);
        #ax.set_xlabel('year')
    ax.set_ylabel('count')
    
