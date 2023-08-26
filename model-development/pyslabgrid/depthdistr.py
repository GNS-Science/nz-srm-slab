import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
import numpy as np


def get_empdepdistr(file, location = None, applysmooth = False, doplot = False, weight = 1.0):
    # 
    if location is not None:
        fname = location + "/" + file
    else:
        fname = file
    dep, prob = ([], [])
    with open(fname, 'r') as f:
        for row in f:
            d, p = row.split()
            dep.append(float(d))
            prob.append(float(p))
            
    if applysmooth:
        for i in range(10):
            prob = smooth_it(prob)
    if weight!=1: 
        tprob = [p/sum(prob) for p in prob]
        prob = [p*weight for p in tprob]
    
    if doplot:
        plt.plot(dep, prob, 'o');
        plt.xlabel('depth (km)')
    return dep, prob

def get_candidates(discr_depths, dzones, zone, zonefile, \
                       subzones_map, filelocation, weights, apply_smoothdistr=False):
    xmodel = {}
    candies = ['candidate1', 'candidate2', 'candidate3']
    for subzone in dzones:
        # smoothed model
        candidate_models = {}
        dep, prob = get_empdepdistr(file=zonefile[subzone], \
                            location = filelocation,\
                            applysmooth = apply_smoothdistr, weight=weights[subzone])
        candidate_models.update({'weight': weights[subzone]})
        candidate_models.update({'empirical':(dep, prob)})
        
        for candy in candies:
            depths = discr_depths[zone][candy]
            kdep, kprob = get_dicr_depthprob((dep, prob), depths)
            
            weight=weights[subzone]
            sprob = [round(p*weight, 3) for p in kprob]
            
            totprob = sum(sprob)
            if totprob<weight:
            	indx = sprob.index(max(sprob))
            	sprob[indx] = round(sprob[indx]+(weight-totprob),2)
            kprob = sprob
            
            candidate_models.update({candy:(kdep, kprob)})
       
        xmodel.update({subzones_map[subzone]: candidate_models})
        
    return xmodel

def check_empiricaldistributions(zonefile, filelocation, weights):
    # Puysegur: (28.2% crustal, 54.5% interface, 17.3% slab) 
    # Hikurangi: 56.8% crustal, 14.8% interface, 28.5% slab.
    dzones = ['hik-crust', 'hik-interface', 'hik-slab']
    scolor = ['b', 'r', 'g']
    
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, figsize=(11,5));

    #plt.figure(figsize=(10, 10), dpi=80);

    for zone,z in zip(dzones, range(3)):
        dep, prob = get_empdepdistr(file=zonefile[zone], \
                            location = filelocation,\
                            applysmooth = False, weight=weights[zone])
        ax1.plot(prob, dep, '--', color=scolor[z]);
        dep, prob = get_empdepdistr(file=zonefile[zone], \
                            location = filelocation,\
                            applysmooth = True, weight=weights[zone])
        ax1.plot(prob, dep, '-', color=scolor[z], label=zone);

    ax1.set_ylim([0, 40])
    ax1.set_xlim([0, 0.05])
    ax1.set_xlabel('probability')
    ax1.set_ylabel('depth(km)')
    ax1.legend(loc='lower right');
    ax1.invert_yaxis();
    #
    dzones = ['puy-crust', 'puy-interface', 'puy-slab']
    scolor = ['b', 'r', 'g']

    for zone,z in zip(dzones, range(3)):
        dep, prob = get_empdepdistr(file=zonefile[zone], \
                            location = filelocation,\
                            applysmooth = False, weight=weights[zone])
        ax2.plot(prob, dep,'--', color=scolor[z]);
        dep, prob = get_empdepdistr(file=zonefile[zone], \
                            location = filelocation,\
                            applysmooth = True, weight=weights[zone])
        ax2.plot(prob,dep, '-', color=scolor[z], label=zone);

    ax2.set_ylim([0, 40]);
    ax2.set_xlim([0, 0.05]);
    ax2.set_xlabel('probability')
    ax2.set_ylabel('depth(km)')
    ax2.legend(loc='lower right');
    ax2.invert_yaxis();
    #
    dep, prob = get_empdepdistr(file=zonefile['crust'], \
                            location = filelocation,\
                            applysmooth = False)
    ax3.plot(prob, dep,'--', color='b');
    dep, prob = get_empdepdistr(file=zonefile['crust'], \
                            location = filelocation,\
                            applysmooth = True)
    ax3.plot(prob,dep, '-', color='b', label='Crust');

    ax3.set_ylim([0, 40]);
    ax3.set_xlim([0, 0.11]);
    ax3.set_xlabel('probability')
    ax3.set_ylabel('depth(km)')
    ax3.legend(loc='lower right');
    ax3.invert_yaxis();
    #
    dep, prob = get_empdepdistr(file=zonefile['tvz'], \
                            location = filelocation,\
                            applysmooth = False)
    ax4.plot(prob, dep,'--', color='b');
    dep, prob = get_empdepdistr(file=zonefile['tvz'], \
                            location = filelocation,\
                            applysmooth = True)
    ax4.plot(prob,dep, '-', color='b', label='TVZ');

    ax4.set_ylim([0, 40]);
    ax4.set_xlim([0, 0.15]);
    ax4.set_xlabel('probability')
    ax4.set_ylabel('depth(km)')
    ax4.legend(loc='lower right');
    ax4.invert_yaxis();
    fig.tight_layout()

def smooth_it(prob):
    prob[0]= 0.0
    yhat = savgol_filter(prob, 7, 2)
    
    fprob = yhat
    prob = []
    for p in fprob:
        if p<=0:
            prob.append(0)
        else:
            prob.append(p)
            
    prob = [p/sum(prob) for p in prob]

    return prob

def plot_dpbar(dep, prob, ax = None, xlabel=None, xlim= None, ylim=None, annotate=False):
    if ax is None:
        fig, ax = plt.subplots(1)
    else:
        ax.barh(dep, prob)
        if annotate:
            for a,b in zip(dep, prob):
                ax.text(b,a, ' ('+str(b)+')')
                    
        if xlim is None:
            xlim = [-1, 41]
        if ylim is None:
            ylim = [0, 1.3]
        ax.set_ylim(xlim)
        ax.set_xlim(ylim)
        ax.invert_yaxis()
        ax.set_ylabel('depth (km)')
        if xlabel is None:
            ax.set_xlabel('probability')
        else:
            ax.set_xlabel(xlabel)
            
            
def get_dicr_depthprob(empirical_depth_model, depths, method='histogram', max_depth=40):
    # 
    dep_emp, prob_emp = empirical_depth_model
    
    if method == 'histogram':
        dbin = [0]
        for i in range(len(depths)-1):
            dbin.append((depths[i]+depths[i+1])/2)
        dbin.append(max_depth)
        
        kprob = []
        for i in range(len(dbin)-1):
            pp = [ p for (d, p) in zip(dep_emp,prob_emp) if (d >= dbin[i])&(d<dbin[i+1]) ]
            kprob.append(sum(pp))
        
    elif method=='point': 
        bindx = np.digitize(depths, dep_emp) 
        kprob = [prob_emp[i] for i in bindx]
        # normalized to sum=1
        kprob = [round(p/sum(kprob),2) for p in kprob]
        
    if sum(kprob)<1.0:
        mindx = kprob.index(max(kprob))
        titbit = 1.0 - sum(kprob)
        kprob[mindx]= round(kprob[mindx]+titbit, 2)
        
    return depths, kprob
            


def read_interfacemodel(subduction):
    if subduction =='hik':
        interface_model = 'subduction/hikinterfacegrid.csv'
    elif subduction == 'puy':
        interface_model = 'subduction/puyinterfacegrid.csv'
    
    slon, slat, sdep = ([],[],[])
    with open(interface_model, 'r') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        tok= header[0].split()
        nrows, ncols = int(tok[2]), int(tok[4])
        header = next(csvreader)
        
        for items in csvreader:
          #  if (float(row[2])< depth_cutoff):
            slon.append(float(items[0]))
            slat.append(float(items[1]))
            sdep.append(float(items[2]))
            
    slon = np.array(slon)
    slat = np.array(slat)
    sdep = np.array(sdep)
    yhat = (slon.reshape(ncols, nrows), \
            slat.reshape(ncols, nrows), \
            sdep.reshape(ncols, nrows))
    return yhat
    

def get_grid(file="samplegrid.txt"):
    lon, lat = ([], [])
    with open(file, mode="r") as f:
        for line in f:
            temp = line.split()
            lon.append(float(temp[0]))
            lat.append(float(temp[1]))
    return (lon, lat)

