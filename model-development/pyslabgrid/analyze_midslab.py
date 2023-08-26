import csv
from shapely.geometry import Polygon, Point
import numpy as np
import eqcat as eqc
import scipy.spatial.distance


def is_within_interfacezone(evlon, evlat, szone):
    # test the interpolatiors
    if szone=='hik':
        finterp = np.load('../1SubductionModel/hik_finterp.npy', allow_pickle=True)[()]
    elif szone=='puy':
        finterp = np.load('../1SubductionModel/puy_finterp.npy', allow_pickle=True)[()]
        
    pbounds = finterp['pbounds']
    if pbounds.contains(Point(evlon, evlat)):
        return True
    return False

def writeout_deps(lon, lat,dep, mag, year, szone, fout):
   # get the earthquake catalogue for hikurangi
   qlat, qlon, qdep, qmag, qyear = [],[],[], [], []
   for x,y,z, m, yr in zip(lon, lat,dep, mag, year):
      if is_within_interfacezone(x, y, szone):
          qlon.append(x)
          qlat.append(y)
          qdep.append(z)
          qmag.append(m)
          qyear.append(yr)

   if szone =='hik':
      imod_highres = '../1SubductionModel/hikmod_highres1.csv'
   else:
      imod_highres = '../1SubductionModel/puymod_highres1.csv'

   interf_rows = []
   with open(imod_highres, mode='r') as csv_file:
      csv_reader = csv.reader(csv_file, delimiter=',')
      next(csv_reader)
      for row in csv_reader:
         interf_rows.append([float(row[0]), float(row[1]), float(row[2])])
   interf_rows = np.array(interf_rows)


   for x, y, z, m, yr in zip(qlon, qlat, qdep, qmag, qyear):
       # Distance between all pairs of points
       d = scipy.spatial.distance.cdist(interf_rows, np.transpose([[x],[y],[z]]))
       dmin = min(d)[0]
       mindx = np.where(d==dmin)[0]
       fout.write('\n%.4f, %.4f, %.4f, %.4f, %d, %.4f, %.4f, %.4f,' \
               %(x,y, z, m, yr, \
               interf_rows[mindx,0], interf_rows[mindx,1], interf_rows[mindx,2]))
       if z < interf_rows[mindx,2]:
          fout.write('%.4f'%(-dmin))
       else:
          fout.write('%.4f'%(dmin))


def compute_midslabdepths():
   catalogues = ['NZeqcat_Rollins13042020-subd-slab.csv',
             'Grue_NZeqcat_Rollins13042020SepiShallow_subd-slab.csv',
             'Grue_NZeqcat_Rollins13042020SepiDeep-subd.csv',]
   catalogue_folder = '../2EventClassifcation/'
   print('loading earthquake catalogue ..')
   
   ecat = eqc.read_slabcatalogue(catalogue_folder+catalogues[0], onlyslab=True)
   lon, lat, mag, dep = ecat['lon'], ecat['lat'], ecat['mag'], ecat['dep']
   year =  ecat['year']
   print('earthquake catalogue loaded ..')
   fout= open('NZeqcat_Rollins13042020-subd-slab-projected.csv','w')
   fout.write('lon,lat, dep, mag, year, slat, slon, sdep, dproj')
   print('Working on Hikurangi..')
   writeout_deps(lon, lat,dep, mag, year, 'hik', fout)
   print('Working on Puysegur..')
   writeout_deps(lon, lat,dep, mag, year, 'puy', fout)
       
   fout.close()


def main():
    compute_midslabdepths()
    
if __name__ == "__main__":
    main()

