import csv

def read_slabcatalogue(input_file, remove_depths=[12,33], onlyslab=False):
    # year, lon, lat, dep, mag, isslab
    eqcat = {}
    with open(input_file, "r") as f:
        datareader=csv.reader(f)
        header = next(datareader)
        nrow = 0
        lon, lat, dep, mag, isslab = [],[],[],[],[]
        year, month, day = [],[],[]
        for row in datareader:  
            hdepth = float(row[5])
            do_continue = False
            for rdep in remove_depths:
                if hdepth== rdep:
                    do_continue = True
                    break
            if do_continue:
                continue
            is_slab = int(row[7])
            if onlyslab:
               if is_slab!=1:
            	   continue
            year.append(int(row[0]))
            month.append(int(row[1]))
            day.append(int(row[2]))
            lon.append(float(row[3]))
            lat.append(float(row[4]))
            dep.append(float(hdepth))
            mag.append(float(row[6]))
            isslab.append(is_slab)
            
    eqcat.update({'year': year, 'month':month, 'day': day, 
                      'lon': lon,'lat':lat, 'dep':dep,
                      'mag':mag, 'isslab': isslab})
    return eqcat
