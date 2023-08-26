import scipy.stats as stats
import matplotlib.pyplot as plt
import numpy as np

"""

Thingbaijam@gmail.com, Jan 2022
"""


def cbound(x, high=180, low=0):
    if x<low:
        x = high+x
    elif x>high:
        x = x-high
    return x

def meanstats(xx, high =180, low = 0, bound=True, stdev=False):
    # returns mean, mean+std, mean-std
    cmean = stats.circmean(xx, high=high, low=low)
    cstd = stats.circstd(xx, high=high, low=low)
    if stdev:
    	return cmean, cstd
    	
    if bound:
         minus_std = cbound(cmean-cstd, high=high)
         plus_std = cbound(cmean+cstd, high=high)
    else:
         minus_std = cmean-cstd
         plus_std = cmean+cstd
    return (minus_std, cmean, plus_std)


def histogram(theta, freq, bs = None, units="degrees", \
                bars = True, normalized = False, lcolor="b", rlabel_position=345, \
                lwidth = 2, facecolor = None, hlabel = None, axe = None, theta_zero_location='N'):
    if normalized:
        freq = [fr/sum(freq) for fr in freq] 
    if axe is None:
        fig = plt.figure(1)
        axe = fig.add_subplot(111, projection='polar')
    if not bars:
        theta.append(theta[0])
        if units=="degrees":
            theta = np.deg2rad(theta).tolist()
        freq.append(freq[0])
        axe.plot(theta, freq,'o-', color=lcolor, linewidth=lwidth, label = hlabel)
    else:
        if bs is None:
            bs = (theta[1]-theta[0])/2
        labeled = False
        for k in range(len(theta)):
            th =[]
            pr = []
            th.append(theta[k]-bs)
            th.append(theta[k]-bs)
            th.append(theta[k]+bs)
            th.append(theta[k]+bs)
            if units=="degrees":
                th = np.deg2rad(th).tolist()
            pr.append(0)
            pr.append(freq[k])
            pr.append(freq[k])
            pr.append(0)
            
            if not labeled:
               if facecolor is not None:
                   axe.fill(th, pr, facecolor) 
               axe.plot(th, pr,'-', color=lcolor, linewidth=lwidth, label = hlabel)
               labeled = True
            else:
               if facecolor is not None:
                   axe.fill(th, pr, facecolor)
               axe.plot(th, pr,'-', color=lcolor, linewidth=lwidth)
   

    #------------------
    
    #r_ticks.pop()
#   #r_ticks.pop()
    #r_ticklabels.pop()
    
    # axe.set_yticklabels(r_ticklabels)    
    #axe.set_rticks(r_ticks)
    #axe.yaxis.get_major_locator().base.set_params(nbins=6)
    axe.set_rlabel_position(rlabel_position)  # angle 
	
    #write the ticks using the text command
    # for rtick, rtick_pos, rtick_ha, rtick_va in zip(r_ticks, r_ticks_pos, r_ticks_h_align, r_ticks_v_align):
    #    plt.text(np.radians(r_label_angle), rtick_pos, r'$'+str(rtick)+'$', ha=rtick_ha, va=rtick_va, transform=ax.transData, rotation=-45, fontsize=8)
    #axe.set_yticklabels([])
    axe.set_theta_zero_location(theta_zero_location)
    axe.set_theta_direction(-1)
    axe.set_xticks(np.pi/180. * np.linspace(0, 360, 18, endpoint = False))

