import matplotlib.pyplot as plt
from matplotlib import patches, collections, transforms, path as mplpath
import numpy as np


D2R = np.pi / 180
R2D = 180 / np.pi
EPSILON = 0.00001

# The code are from ObsPy (which is a neat and very useful package
# , except for the main functions: plotbb, 
# which is modified function that suits my application.
# One can also import obspy and use the axilliary functions
# without having to have have them here.

def xy2patch(x, y, res, xy):
    # check if one or two resolutions are specified (Circle or Ellipse)
    try:
        assert(len(res) == 2)
    except TypeError:
        res = (res, res)
    # transform into the Path coordinate system
    x = x * res[0] + xy[0]
    y = y * res[1] + xy[1]
    verts = list(zip(x.tolist(), y.tolist()))
    codes = [mplpath.Path.MOVETO]
    codes.extend([mplpath.Path.LINETO] * (len(x) - 2))
    codes.append(mplpath.Path.CLOSEPOLY)
    path = mplpath.Path(verts, codes)
    return patches.PathPatch(path)


def Pol2Cart(th, r):
    """
    """
    x = r * np.cos(th)
    y = r * np.sin(th)
    return (x, y)


def StrikeDip(n, e, u):
    """
    Finds strike and dip of plane given normal vector having components n, e,
    and u.

    Adapted from MATLAB script
    `bb.m <http://www.ceri.memphis.edu/people/olboyd/Software/Software.html>`_
    written by Andy Michael and Oliver Boyd.
    """
    r2d = 180 / np.pi
    if u < 0:
        n = -n
        e = -e
        u = -u

    strike = np.arctan2(e, n) * r2d
    strike = strike - 90
    while strike >= 360:
            strike = strike - 360
    while strike < 0:
            strike = strike + 360
    x = np.sqrt(np.power(n, 2) + np.power(e, 2))
    dip = np.arctan2(x, u) * r2d
    return (strike, dip)



def AuxPlane(s1, d1, r1):
    """
    Get Strike and dip of second plane.

    Adapted from MATLAB script
    `bb.m <http://www.ceri.memphis.edu/people/olboyd/Software/Software.html>`_
    written by Andy Michael and Oliver Boyd.
    """
    r2d = 180 / np.pi

    z = (s1 + 90) / r2d
    z2 = d1 / r2d
    z3 = r1 / r2d
    # slick vector in plane 1
    sl1 = -np.cos(z3) * np.cos(z) - np.sin(z3) * np.sin(z) * np.cos(z2)
    sl2 = np.cos(z3) * np.sin(z) - np.sin(z3) * np.cos(z) * np.cos(z2)
    sl3 = np.sin(z3) * np.sin(z2)
    (strike, dip) = StrikeDip(sl2, sl1, sl3)

    n1 = np.sin(z) * np.sin(z2)  # normal vector to plane 1
    n2 = np.cos(z) * np.sin(z2)
    h1 = -sl2  # strike vector of plane 2
    h2 = sl1
    # note h3=0 always so we leave it out
    # n3 = np.cos(z2)

    z = h1 * n1 + h2 * n2
    z = z / np.sqrt(h1 * h1 + h2 * h2)
    
    if (z>1.0):
    	z = 1.0
    if (z<-1.0):
    	z = -1.0
    z = np.arccos(z)
    
    rake = 0
    if sl3 > 0:
        rake = z * r2d
    if sl3 <= 0:
        rake = -z * r2d
    return (strike, dip, rake)

   
def plotbb(S1, D1, R1, size=200, xy=(0, 0), width=200, alpha=1.0):
    """
    Uses one nodal plane of a double couple to draw a beach ball plot.

    :param ax: axis object of a matplotlib figure
    :param np1: :class:`~NodalPlane`

    Adapted from MATLAB script
    `bb.m <http://www.ceri.memphis.edu/people/olboyd/Software/Software.html>`_
    written by Andy Michael and Oliver Boyd.
    """
    # check if one or two widths are specified (Circle or Ellipse)
    try:
        assert(len(width) == 2)
    except TypeError:
        width = (width, width)
    
    M = 0
    if R1 > 180:
        R1 -= 180
        M = 1
    if R1 < 0:
        R1 += 180
        M = 1

    # Get azimuth and dip of second plane
    (S2, D2, _R2) = AuxPlane(S1, D1, R1)

    D = size / 2

    if D1 >= 90:
        D1 = 89.9999
    if D2 >= 90:
        D2 = 89.9999

    # arange checked for numerical stablility, np.pi is not multiple of 0.1
    phi = np.arange(0, np.pi, .01)
    l1 = np.sqrt(
        np.power(90 - D1, 2) / (
            np.power(np.sin(phi), 2) +
            np.power(np.cos(phi), 2) * np.power(90 - D1, 2) / np.power(90, 2)))
    l2 = np.sqrt(
        np.power(90 - D2, 2) / (
            np.power(np.sin(phi), 2) + np.power(np.cos(phi), 2) *
            np.power(90 - D2, 2) / np.power(90, 2)))

    inc = 1
    (X1, Y1) = Pol2Cart(phi + S1 * D2R, l1)

    if M == 1:
        lo = S1 - 180
        hi = S2
        if lo > hi:
            inc = -1
        th1 = np.arange(S1 - 180, S2, inc)
        (Xs1, Ys1) = Pol2Cart(th1 * D2R, 90 * np.ones((1, len(th1))))
        (X2, Y2) = Pol2Cart(phi + S2 * D2R, l2)
        th2 = np.arange(S2 + 180, S1, -inc)
    else:
        hi = S1 - 180
        lo = S2 - 180
        if lo > hi:
            inc = -1
        th1 = np.arange(hi, lo, -inc)
        (Xs1, Ys1) = Pol2Cart(th1 * D2R, 90 * np.ones((1, len(th1))))
        (X2, Y2) = Pol2Cart(phi + S2 * D2R, l2)
        X2 = X2[::-1]
        Y2 = Y2[::-1]
        th2 = np.arange(S2, S1, inc)
    (Xs2, Ys2) = Pol2Cart(th2 * D2R, 90 * np.ones((1, len(th2))))
    X = np.concatenate((X1, Xs1[0], X2, Xs2[0]))
    Y = np.concatenate((Y1, Ys1[0], Y2, Ys2[0]))

    X = X * D / 90
    Y = Y * D / 90

    # calculate resolution
    res = [value / float(size) for value in width]

    # construct the patches
    p = patches.Ellipse(xy, width=width[0], height=width[1],)
    p.set_alpha(alpha)
    collect = [p,]
    collect.append(xy2patch(Y, X, res, xy))
    return ['b', 'w'], collect



def curveT1(S1, D1, R1, size=200, xy=(0, 0), width=200):
    # get -T1 curve
    M = 0
    if R1 > 180:
        R1 -= 180
        M = 1
    if R1 < 0:
        R1 += 180
        M = 1
    D = size / 2
    if D1 >= 90:
        D1 = 89.9999
    # arange checked for numerical stablility, np.pi is not multiple of 0.1
    phi = np.arange(0, np.pi, .01)
    l1 = np.sqrt(
        np.power(90 - D1, 2) / (
            np.power(np.sin(phi), 2) +
            np.power(np.cos(phi), 2) * np.power(90 - D1, 2) / np.power(90, 2)))

    (X1, Y1) = Pol2Cart(phi + S1 * D2R, l1)

    X = X1 * D / 90
    Y = Y1 * D / 90
    X = X+xy[0]
    Y = Y+xy[1]
    return Y,X

