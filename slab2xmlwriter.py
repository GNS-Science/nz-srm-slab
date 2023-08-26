import toml 
import json
import csv
import numpy as np
from datetime import datetime
from lxml import etree 

#  
#----------------------------------------------------------------------------------------------------------
def load_slabmodules(modules=None, echo=False, fpath=''):
    if modules is None:
        # load a default config
        modules = toml.load(fpath+'default.ini')     
    config = {}
    for key in modules:
        file = modules[key]
        if echo:
            print('reading '+ key + '.....')
        if file[-4:]=='.ini':
            config.update({
                key: toml.load(fpath+modules[key]),
            })
        else:
            config.update({
                key: modules[key],
            })        
    return(config)

#----------------------------------------------------------------------------------------------------------
def load_slabconfig(config):
    # rates model
    rates_model = config['rates_model']
    faulting_model = config['faulting_model']
    seismicity_model = config['seismicity_model']
    rupture_model = config['rupture_model']
    
    # slab_model is not used, as it has been recorded in the rates model
    # rate model also has depth distrbution
    return (rates_model, faulting_model, seismicity_model, rupture_model)
#----------------------------------------------------------------------------------------------------------
def get_xmlroot():
    # set initial XML definitions
    today = datetime.today()
    datem = datetime(today.year, today.month, today.day)
    NAMESPACE = 'http://openquake.org/xmlns/nrml/0.4'
    GML_NAMESPACE = 'http://www.opengis.net/gml'
    SERIALIZE_NS_MAP = {None: NAMESPACE, 'gml': GML_NAMESPACE}   
    gml_ns = SERIALIZE_NS_MAP['gml']
    
    root = etree.Element(_tag='nrml', nsmap={'gml': GML_NAMESPACE})
    root.set('xmlns', NAMESPACE)
    comment = '2022 NZ Seismic Hazard Model 1y (GNS Science; '\
                        + datem.strftime('%d%m%Y') + ')'
    root.append(etree.Comment('%s' % comment))
    return root

#----------------------------------------------------------------------------------------------------------

def set_source_model(root, source_identifer):
    source_name = 'New Zealand Distributed Seismicity Model - '+source_identifer+' (1y) '
    source_model = etree.SubElement(root, "sourceModel")
    source_model.set('name', source_name)
    return source_model

#----------------------------------------------------------------------------------------------------------
def read_ratefile(infile):
    x,y,z,r = [],[],[],[]
    with open(infile, 'r') as f:
        csvreader = csv.reader(f)
        header = next(csvreader)
        for row in csvreader:
            x.append(float(row[0]))
            y.append(float(row[1]))
            z.append(float(row[2]))  
            r.append(float(row[3]))
    return x,y,z,r 

# -----------------------------------------------------------------------------------------------
def set_slabpointsource(pointsource, source_model):
    # pointsource is a dictionary with the following keys and values:
    #   source_id = #
    #   location = (lon, lat)
    #   depths = (dep, prob)
    #   seismogenic_bounds = (upper, lower)
    #   rupture_model = {'scaling':{'point': , 'crust': , 'interface': , 'slab':  }
    #   seismicity_model = {bvalue, magnitude_range = mmax, mmin}
    #   nodalplane_distr = (probs, strikes, dips, rakes)
    #   activity_rate = (mag, rate)
    
    # XML definition hard-coded.. not good. we can use oqxml.cfg file
    NAMESPACE = 'http://openquake.org/xmlns/nrml/0.4'
    GML_NAMESPACE = 'http://www.opengis.net/gml'
    SERIALIZE_NS_MAP = {None: NAMESPACE, 'gml': GML_NAMESPACE}   
    gml_ns = SERIALIZE_NS_MAP['gml']
    
    # extract the data --------------------------------------------------------------
    pointsource_id  = pointsource['source_id']
    lon, lat  = pointsource['location']
    hdep, hdep_prob = pointsource['depths']
    sdep_upper, sdep_lower = pointsource['seismogenic_bounds']
    
    rupture_model = pointsource['rupture_model']
    nodalplane_distr = pointsource['nodalplane_distr']
    seismicity = pointsource['seismicity']
    tectonic_region = pointsource['tectonic_region']
    
    # set the source -----------------------------------------------------------------
    psource = etree.SubElement(source_model, "pointSource")
    psource.set('id', pointsource_id)
    psource.set('name', 'pt'+ pointsource_id)
    psource.set('tectonicRegion', tectonic_region)
    
    # point geometry  ------------------------------------------------------------------
    pgeom = etree.SubElement(psource, 'pointGeometry')
        
    # point geometry -> grid position
    gml_point = etree.SubElement(pgeom, '{%s}Point' % gml_ns)
    gmlPos = etree.SubElement(gml_point, '{%s}pos' % gml_ns)
    
    gmlPos.text = '%s %s' % (lon, lat)

    # point geometry -> Seimogeic depths ------------------------------------------------
    upperSeis = etree.SubElement(pgeom, 'upperSeismoDepth')
    upperSeis.text = str(sdep_upper)
    lowerSeis = etree.SubElement(pgeom, 'lowerSeismoDepth')
    lowerSeis.text = str(sdep_lower)
    
    # source -> hypocentral depths -------------------------------------------------------
    # Set hypocentral depth distribution
    hypodepth_distr = etree.SubElement(psource, 'hypoDepthDist')
    
    for d,p in zip(hdep, hdep_prob):
        hypo_depth = etree.SubElement(hypodepth_distr, 'hypoDepth')
        hypo_depth.set('probability', '%s' % p)
        hypo_depth.set('depth', '%s' % d)
        
    if round(sum(hdep_prob), 2)!=1.0:
        print(hdep, hdep_prob, tectonic_region)
        raise Exception('Depth Probabilties not adding up to One!')
    
    # source: -> SRC Scaling relation -----------------------------------------------------
    #         -> rupture aspect ratio
    # CAVEAT1.0: 
    # If magnitude-range bounds both point source and finite ruptures, the following code may not work
    # e.g., if Mmax for point source definition is 6.5, then the range should be such that 
    # either Mw 6.5 is Mmax or Mw 6.6. is Mmin. 
    
    # To deal the difference in our namming convention and that of OQ
    tectonic_regime_key = { 'active shallow crust': 'crust',
                            'subduction interface':'interface',
                            'subduction intraslab': 'slab', }

    magscalerel = etree.SubElement(psource, 'magScaleRel')
    
    Mmin, Mmax = seismicity['magnitude_range']
    tregion = tectonic_regime_key[tectonic_region.lower()]
    
    if Mmax <= rupture_model['Mmax_ptsrc'][tregion]:
        magscalerel.text = 'PointMSR'
        #  rupture aspect ratio (for finite ruptures)
        aspect_ratio = etree.SubElement(psource, 'ruptAspectRatio')
        aspect_ratio.text = '%s' % (rupture_model['aspect_ratio']['small'])
    else:
        # check the CAVEAT1.0 out!
        if Mmin<=rupture_model['Mmax_ptsrc'][tregion]:
            print('magnitude-range:', Mmin, Mmax, ', point source Mmax:', rupture_model['Mmax_ptsrc'])
            raise Exception('Magnitude range must NOT BOUND both point sources and finite sources!')
            
        magscalerel.text =  rupture_model['MSR'][tregion]
        #  rupture aspect ratio (for finite ruptures)
        aspect_ratio = etree.SubElement(psource, 'ruptAspectRatio')
        aspect_ratio.text = '%s' % (rupture_model['aspect_ratio']['large'])

    #  Magnitude Frequency Distrbution -----------------------------------------------------------
    # "weights" on the activity_rate, if any, should be taken a prior (and not here)
    rates = seismicity['rate']
    bvalue = seismicity['bvalue']
    grmag =  seismicity['mag']
    if type(rates) is float:
        #print('magnitude for the rate input= Mw ', mag)
        avalue = np.log10(rates) + bvalue*grmag
        avalue = round(avalue, 10)
        mfd = etree.SubElement(psource, 'truncGutenbergRichterMFD')
        mfd.set('aValue', '%s' % avalue)
        mfd.set('bValue','%s' % bvalue)
        mfd.set('minMag','%s' % Mmin)
        mfd.set('maxMag','%s' % Mmax)
    else:
        mfd = etree.SubElement(psource, 'incrementalMFD')
        mfd.set('minMag', '%s' % mag[0])
        mfd.set('binWidth', '%s' % mag[2])
        occurRates = etree.SubElement(mfd, 'occurRates')
        rate_txt = ''
        for rate in rates:
            rate_txt = rate_txt + "%s " % (rate)
        occurRates.text = rate_txt
    
    # Nodal Plane Distribution --------------------------------------------------------------------
    strikes, dips, rakes, np_probs =  [], [], [], []
    for sdrp in nodalplane_distr: 
        strikes.append(sdrp[0])
        dips.append(sdrp[1])
        rakes.append(sdrp[2]) 
        np_probs.append(sdrp[3])
    
    if round(sum(np_probs),2) !=1.0:
        print('probabilities:', np_probs, 'sum:', sum(np_probs))
        raise Exception('***** probabilities of nodal plane distribution do not add up to 1.0')
    
    nodalplanedist = etree.SubElement(psource, 'nodalPlaneDist')
    
    for p, strike, dip, rake in zip(np_probs, strikes, dips, rakes):
        strike360 = strike%360
        nodalplane = etree.SubElement(nodalplanedist, 'nodalPlane')
        nodalplane.set('probability', '%s' % p)
        nodalplane.set('strike','%s' % strike360)
        nodalplane.set('dip', '%s' % dip)
        nodalplane.set('rake', '%s' % rake) 
    
    return source_model

#--------------------------------------------------------------------------------------------------------

def set_slabsource(klon, klat, src_count, source_model, seismicity = None, \
                     StrikeDipRakeProb = None, depths = None,\
                   seismogenic_bounds =None, config=None): 
    
    #rates_model = config['rates_model']                                     
    magbins = config['faulting_model']['slab']['magbins']
   # seismicity_slab = config['seismicity_model']['whole']
    
    for mbin in magbins:
       # seismicity_slab.update({'magnitude_range': mbin})
        src_count +=1
        seismicity.update({'magnitude_range': mbin})
        pointsource = {}
        pointsource.update({
                'source_id': 'sla'+ str(src_count).zfill(6),
                'location': (klon, klat),
                'tectonic_region': "Subduction Intraslab",
                'seismogenic_bounds': seismogenic_bounds,
                'depths': depths,
                'rupture_model': config['rupture_model'],
                'seismicity': seismicity,
                'nodalplane_distr': StrikeDipRakeProb,
           })
                
        source_model = set_slabpointsource(pointsource,  source_model)
                    
    return source_model, src_count
#----------------------------------------------------------------------------------------------------------

def get_depbincenter(kdep):
    fbs, min_x,max_x  =10, 20, 300
    x_bin = [d for d in range(min_x, max_x, fbs)]
    for db in x_bin:
        if (kdep>=(db-fbs)) & (kdep<(db+fbs)):
            return(str(db))
    return None

def process_szone(szone, src_count, source_model, config=None, fpath=''):
     # load key configs 
    with open(fpath + config['faulting_model']['slab']['file'], 'r') as f:
        focmec_model = json.load(f)
    interface_modules = np.load(fpath + config['depth_model']['interface']['file'], \
                                       allow_pickle=True)[()]
    Hseis = 60
    
    #--
    rate_files = config['rates_model'][szone]['files']
    seismicity_model = config['seismicity_model']
    pref_model =  seismicity_model[szone]['pref_candidate']
    fintp_interface = interface_modules[szone[:3]]['fintp']
    bvalue, gr_mag, Ncum, Ninc = seismicity_model[szone][pref_model]
 
    for file in rate_files:
        print('--- Working on %s ----' %file)
        lon,lat, dep, prate = read_ratefile(fpath+file)
        fmdict  = focmec_model[szone[:3]]
        rates = [p*Ncum for p in prate]
        
        for klon, klat, kdep, rate in zip(lon, lat, dep, rates):
            if klon>180:
                klon = klon-360
            #
            StrikeDipRakeProb = fmdict[get_depbincenter(kdep)]
            #
            interface_depth = fintp_interface(klon, klat)[0]
            diper = StrikeDipRakeProb[1][1]
            W_sei = Hseis/np.sin(np.deg2rad(diper))
            xh = W_sei*np.sin(np.deg2rad(diper))
            sup = round(kdep-(xh/2), 1)
            if sup<20:
                sup = 20           
            if kdep<sup:
                kdep = sup+3
                # print('asdsadsadas', kdep, sup)
                
            slo = sup+Hseis
            
            if (kdep>slo) |(kdep<sup):
                raise Exception('**** hypocenter is not within seismogenic bounds')
            depths = [[kdep], [1.0]]
            
            seismogenic_bounds =[sup, slo]
            #--------------
            seismicity =  {'mag': gr_mag, 'bvalue': bvalue, 'rate': rate,}
            source_model, src_count =  set_slabsource(klon, klat, src_count, source_model,\
                            seismicity = seismicity, StrikeDipRakeProb = StrikeDipRakeProb, \
                            depths = depths,seismogenic_bounds=seismogenic_bounds,\
                            config=config)
        #print('--- Done!')
    return source_model, src_count

def writexml(outfile,output_folder, config = None, config_file=None, fpath=''):
    #
    print('\ngenerating SLAB xmls ')
    if config is None:
        raise ValueError('Config must be provide as of now.')

    root = get_xmlroot()
    source_model = set_source_model(root, 'SLAB')

    src_count = 0
    # first hikurnagi -------------------------
    szone = 'hikurangi'
    source_model, src_count = process_szone(szone, src_count, source_model, config=config, fpath=fpath)
    szone = 'puysegur'
    source_model, src_count = process_szone(szone, src_count, source_model, config=config, fpath=fpath)
   
    tree = etree.ElementTree(root)
    
    tree.write(output_folder+outfile, encoding="utf-8", xml_declaration=True, pretty_print=True)
    print('>>> FILE written : ' + output_folder+outfile)

