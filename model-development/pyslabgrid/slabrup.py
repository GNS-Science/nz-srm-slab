import csv
import numpy as np
import pyslabgrid.circ as circ
import pyslabgrid.slabeventclassify as evc
import matplotlib.pyplot as plt

def review_strikediprake(xslabevents, procslabevents, szone):
    #
    stitle = {'hik': 'Hikurangi slab', 'puy': 'Puysegur slab'}
    fig = plt.figure(1, figsize=(12,8))
    ax1 = fig.add_subplot(231, projection='polar')
    plot_hist(xslabevents[szone]['strike'], ax=ax1, stitle ='unconstrained strike', facecolor='c')
    ax2 = fig.add_subplot(232, projection='polar')
    plot_hist(xslabevents[szone]['dip'], ax=ax2, stitle ='unconstrained dip', facecolor='c')
    ax3 = fig.add_subplot(233, projection='polar')
    trakes = xslabevents[szone]['rake']
    krakes = rakeTo360(trakes);
    plot_hist(krakes, ax=ax3, stitle ='unconstrained rake', facecolor='c')

    ax4 = fig.add_subplot(234, projection='polar')
    plot_hist(procslabevents[szone]['strike'], ax=ax4, stitle ='constrained strike', facecolor='m')
    ax5 = fig.add_subplot(235, projection='polar')
    plot_hist(procslabevents[szone]['dip'], ax=ax5, stitle ='constrained dip', facecolor='m')
    ax6 = fig.add_subplot(236, projection='polar')
    trakes = procslabevents[szone]['rake']
    krakes = rakeTo360(trakes);
    plot_hist(krakes, ax=ax6, stitle ='constrained rake', facecolor='m')
    fig.suptitle(stitle[szone], fontsize=18, y=0.95)  
    fig.tight_layout();
    return ax1 

def rakeTo360(trakes):
    krakes = []
    for x in trakes:
        if x <0:
            krakes.append(360+x)
        else:
            krakes.append(x)
    return krakes
    
def get_allstrikediprakes(slabevents, szone):
    mystrike = slabevents[szone]['strike1'] + slabevents[szone]['strike2']
    mydip = slabevents[szone]['dip1'] + slabevents[szone]['dip2']
    myrake = slabevents[szone]['rake1'] + slabevents[szone]['rake2']
    mydep = slabevents[szone]['dep'] + slabevents[szone]['dep'] 
    return {'strike': mystrike, 'dip': mydip, 'rake': myrake, 'dep': mydep} 
    
    
# we make choice
def process_strikediprake(slabevents, szone, critical_dip=None):
    finterp_file = {'hik': '../subduction-model/finterp/hik_finterp.npy', 
                    'puy': '../subduction-model/finterp/puy_finterp.npy',}
    
    finterp = np.load(finterp_file[szone], allow_pickle=True)[()]
    strike_finterp = finterp['strikeAn']
    dip_finterp = finterp['dipAn']
    Mw = slabevents[szone]['Mw']
    lon, lat = slabevents[szone]['lon'], slabevents[szone]['lat']
    strike1, strike2 = slabevents[szone]['strike1'], slabevents[szone]['strike2']
    dip1, dip2  = slabevents[szone]['dip1'], slabevents[szone]['dip2'] 
    rake1, rake2  = slabevents[szone]['rake1'], slabevents[szone]['rake2'] 
    
    deps = slabevents[szone]['dep']
    mystrike, slabstrike = [], []
    myrake = []
    mydip, slabdip, mydep = [],[],[]
    
    if not critical_dip:
    	critical_dip = {'hik': 30, 'puy': 60}
    kkiss = []
    cdep = {'hik': 80, 'puy': 0}    
    for x,y,s1,s2,d1,d2,r1,r2,dep in zip(lon,lat,strike1,strike2,dip1,dip2,rake1,rake2,deps):
        #
        kslabstrike = strike_finterp(np.transpose([[x],[y]]))[0]
        kslabdip = dip_finterp(np.transpose([[x],[y]]))[0]
        
        if kslabdip>critical_dip[szone]:
            # if szone=='hik':
            kstrike = (kslabstrike-180)%360
            #else:
            #    kstrike = kslabstrike-180
        else:
            kstrike = kslabstrike
         
        #lowstrike, highstrike = (kstrike-90)%360, (kstrike+90)%360
        abs_cric_diff = abs(((s1-kstrike)+180)%360-180)
        abs_cric_diff2 = abs(((s2-kstrike)+180)%360-180)
        
        #abs_cric_diff = abs((s1-kstrike)%360)
        #abs_cric_diff2 = abs((s2-kstrike)%360)
        
        if abs_cric_diff< 45:
            mystrike.append(s1)
            mydip.append(d1)
            myrake.append(r1)
            mydep.append(dep)
        elif abs_cric_diff2<45:
            mystrike.append(s2)
            mydip.append(d2)
            myrake.append(r2)
            mydep.append(dep)
        
        slabstrike.append(kslabstrike)
        slabdip.append(kslabdip)
        
    
    return {'strike': mystrike, 'dip': mydip, 'rake': myrake, 'dep': mydep,
            'slabstrike': slabstrike, 'slabdip': slabdip,'Mw': Mw} 

def get_GeoNetevents(szone):
    with open('../focmech-work/GeoNet_slabevents.csv', 'r') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        slat,slon,sdep,sMw,s1,d1,r1,s2,d2,r2 = [],[],[],[],[],[],[],[],[],[]
        hik_count, puy_count = 0,0
        # 'lon,lat,dep,Mw,strike1,dip1,rake1,strike2,dip2,rake2'
        for row in csvreader:
            if float(row[2])>300:
                continue
            if float(row[2])<=10:
                continue
            if evc.within_interfacezone(float(row[0]), float(row[1]))==szone:
                slat.append(float(row[1]))
                slon.append(float(row[0]))
                sdep.append(float(row[2]))
                sMw.append(float(row[3]))
                s1.append(float(row[4]))
                d1.append(float(row[5]))
                r1.append(float(row[6]))
                s2.append(float(row[7]))
                d2.append(float(row[8]))
                r2.append(float(row[9]))
    dump = {'lon': slon,'lat': slat, 'dep': sdep, 
            'Mw':sMw, 'strike1': s1, 'dip1': d1,'rake1':r1,
            'strike2':s2, 'dip2':d2, 'rake2': r2,}
    return dump


def cbinning(data_angles,binsize = 10, maxangle = 360):
    # circular count is needed. 
    # binsize must be an integer
    halfbinw = int(binsize/2)
    cbins = [x for x in range(halfbinw,maxangle,halfbinw)]
    bin_count = [0]*len(cbins)
    for cb, i in zip(cbins, range(len(bin_count))):
        lowangle = cb-halfbinw 
        highangle = cb+halfbinw
        for sang in data_angles:
            if sang== highangle:
                sang = lowangle
            if (sang>= lowangle) & (sang<highangle):
                bin_count[i]=bin_count[i]+1

    return cbins, bin_count

def plot_hist(data_angles, ax, stitle ='', facecolor='c'):
    theta, freq = cbinning(data_angles)
    
    circ.histogram(theta, freq, bs = 2, units="degrees", \
               bars = True, normalized = False, lcolor="k", \
               lwidth = 0.5, facecolor = facecolor, axe = ax)
               
    ax.set_title(stitle, y=1.1, fontsize=15)

    r_ticks = ax.get_yticks()
    r_ticks.pop()
    if r_ticks[-1]>=55:
       r_ticks.pop()
    ax.set_yticks(r_ticks)

    
def binned_boxes(x, y, fbs =10, min_x = 20, max_x = 300, doplot=True,
                       strtitle='', xlabel='depth (km)', ylabel = '', ax = None):
    # plot y according to binnned x
    x_bin = [d for d in range(min_x, max_x, fbs)]
    xbox  ={}
    x_means = []
    for xb in x_bin:
        kx =[]
        for xx, yy in zip(x, y):
            if (xx>=(xb-fbs)) & (xx<(xb+fbs)):
                kx.append(yy)
        if len(kx)<5:
            x_means.append(float("nan"))
            xbox.update({xb:[]})
        else:
            x_means.append(np.mean(kx))
            xbox.update({xb:kx})
        
    data = []
    for b in xbox.keys():
        data.append(xbox[b])
    if doplot:
        if ax is None:
            if max_x==300:
                fig, ax = plt.subplots(figsize=(17,2))
            else:
                fig, ax = plt.subplots(figsize=(17,1.2))
          
        X = range(1, len(x_bin)+1)
        ax.boxplot(data)
        ax.plot(X, x_means, 'x')
        #for dat,x in zip(data,X):
        #  plt.text(x,70, str(len(dat)))
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        
        #ax.set_xticks([x for x in X])
        #ax.set_xticklabels([str(xx) for xx in x_bin])
        #ax.set_title(strtitle, fontsize=13)
       
        ax.set_xticks([x for x in X])
        ax.set_xticklabels([str(xx) for xx in x_bin])
        ax.set_title(strtitle, fontsize=13)
        #ax.set_xlim([0.5, 28+0.5])
    return xbox

# set aside for time being
def circ_boxplot(data, high=360):
    rdata = []
    for dat in data:
        dat = np.array(dat)
        qr = np.percentile(dat, [25, 50, 75])
        iqr = qr[2]-qr[0]
        ub = qr[2]+(1.5*iqr)
        lb = qr[0]-(1.5*iqr)
        
        upper_bound = ub + 3*(ub-qr[2])
        lower_bound = lb - 3*(qr[0]-lb)
        outs = dat[(dat <= lower_bound) | (dat >= upper_bound)]
        nouts = dat[(dat > lower_bound) & (dat < upper_bound)]
        nouts = nouts.tolist()
        for x in outs:
            if x>=upper_bound:
                nouts.append(x-high)
            else:
                nouts.append(x+high)
        
        rdata.append(nouts)
        
    plt.boxplot(rdata)
