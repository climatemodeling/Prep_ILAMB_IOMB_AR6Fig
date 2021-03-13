#!/usr/bin/env python

import json, collections
import numpy as np

"""
   Merge the JSON files from ILAMB and IOMB benchmarking results in the CMEC JSON schema. 

   The Merged ILAMB and IOMB results will be shown in the Land Model Testbed (LMT) 
   Unified Dashboard (UD) using the merged JSON file above. 
   
   To fill in the missing values in the categorical metrics in the benchmarking result, 
   we first normalize the absolute scores in the same categorical metrics that are calculated 
   from the absolute scores of variables from the HTML tables of the ILAMB result. 
   Then, the normalized scores are used to replace the values in the categorical metrics. 
"""

LandJsonOrg = '/lmt/www/html/test_lmtud/AR6_UD/ar6_cmec.json'
LandJsonCal = '/lmt/www/html/test_lmtud/AR6_CAL/ar6_cal.json'

IombJsonOrg = '/lmt/www/html/test_lmtud/IOMB_AR6_modeladded_UD/ar6_iomb.json'
IombJsonCal = '/lmt/www/html/test_lmtud/IOMB_CAL/ar6_iomb_cal.json'

# the *JsonCal: the absolute scores harvested from the html tables under a ILAMB
# result directory using the tool *** DataMine_ILAMB.py ***.
# the *JsonOrg: the original JSON files from the ILAMB and IOMB results in the 
# CMEC schema that are converted from the ILAMB JSON files using the tool 
# *** Cvt_ILAMB2CMECJson.py ***


import argparse

parser = argparse.ArgumentParser(description = "Merge the JSON files from ILAMB and IOMB benchmarking results")

parser.add_argument("-lo", "--LandOrg", type=str, help="Input: Original JSON file from a land benchmarking")
parser.add_argument("-lc", "--LandCal", type=str, help="Input: Calculated JSON file from a land benchmarking")
parser.add_argument("-oo", "--OceanOrg", type=str, help="Input: Original JSON file from a ocean benchmarking")
parser.add_argument("-oc", "--OceanCal", type=str, help="Input: Calculated JSON file from a land benchmarking")

args = parser.parse_args()

if args.LandOrg:
   LandJsonOrg = args.LandOrg

if args.LandCal:
   LandJsonCal = args.LandCal

if args.OceanOrg:
   IombJsonOrg = args.OceanOrg

if args.OceanCal:
   IombJsonCal = args.OceanCal

print (LandJsonOrg, LandJsonCal, IombJsonOrg, IombJsonCal)


with open(LandJsonCal, "r") as jn:
    vars_land_cal = json.load(jn, object_pairs_hook=collections.OrderedDict)

with open(IombJsonCal, "r") as jn:
    vars_iomb_cal = json.load(jn, object_pairs_hook=collections.OrderedDict)

with open(LandJsonOrg, "r") as jn:
    vars_land_org = json.load(jn, object_pairs_hook=collections.OrderedDict)

with open(IombJsonOrg, "r") as jn:
    vars_iomb_org = json.load(jn, object_pairs_hook=collections.OrderedDict)


# step 1 land:
MergedLand = vars_land_org.copy()
for m in vars_land_cal['DIMENSIONS']['dimensions']['metric'].keys():
    if '::' not in m and '||' not in m and '!!' not in m:
        arr = []
        mdict ={}
        sdict ={}

        for md in vars_land_cal['RESULTS']['global'].keys():
            if vars_land_cal['RESULTS']['global'][md][m]['Overall Score'] != -999.:
               arr.append(vars_land_cal['RESULTS']['global'][md][m]['Overall Score'])
            mdict[md] = vars_land_cal['RESULTS']['global'][md][m]['Overall Score']
            
        nparr = np.array(arr)  

        for md in vars_land_cal['RESULTS']['global'].keys():

            # normalize the absolute scores
            if mdict[md] != -999:
               sdict[md] = (mdict[md]-nparr.mean())/(nparr.std().clip(0.02) if nparr.std() > 1e-12 else 1)
            else:
               sdict[md] = -999.

            # replace the categorical metrics with the values normalized above.
            if sdict[md] != -999.:
               for key in MergedLand['RESULTS']['global'][md].keys():
                   if key.replace(' ','') == m:
                      MergedLand['RESULTS']['global'][md][key]['Overall Score'] = sdict[md]

# change UK-HadGEM2-ES to HadGEM2-ES
MergedLand['DIMENSIONS']['dimensions']['model']['HadGEM2-ES'] = MergedLand['DIMENSIONS']['dimensions']['model'].pop('UK-HadGEM2-ES')
MergedLand['RESULTS']['global']['HadGEM2-ES'] = MergedLand['RESULTS']['global'].pop('UK-HadGEM2-ES')

# step 2 ocean
MergedIomb = vars_iomb_org.copy()
for m in vars_iomb_cal['DIMENSIONS']['dimensions']['metric'].keys():
    if '::' not in m and '||' not in m and '!!' not in m:
        arr = []
        mdict ={}
        sdict ={}

        for md in vars_iomb_cal['RESULTS']['global'].keys():
            if vars_iomb_cal['RESULTS']['global'][md][m]['Overall Score'] != -999.:
               arr.append(vars_iomb_cal['RESULTS']['global'][md][m]['Overall Score'])
            mdict[md] = vars_iomb_cal['RESULTS']['global'][md][m]['Overall Score']

        nparr = np.array(arr)

        for md in vars_iomb_cal['RESULTS']['global'].keys():

            # normalize the absolute scores
            if mdict[md] != -999:
               sdict[md] = (mdict[md]-nparr.mean())/(nparr.std().clip(0.02) if nparr.std() > 1e-12 else 1)
            else:
               sdict[md] = -999.

            # replace
            if sdict[md] != -999:
               for key in MergedIomb['RESULTS']['global'][md].keys():
                   if key.replace(' ','') == m:
                      MergedIomb['RESULTS']['global'][md][key]['Overall Score'] = sdict[md]


# change bcc-cesm1-1 to bcc-csm1-1
MergedIomb['DIMENSIONS']['dimensions']['model']['bcc-csm1-1'] = MergedIomb['DIMENSIONS']['dimensions']['model'].pop('bcc-cesm1-1')
MergedIomb['RESULTS']['global']['bcc-csm1-1'] = MergedIomb['RESULTS']['global'].pop('bcc-cesm1-1')

# change MPI-ESM1-2-LR to MPI-ESM1.2-LR
MergedIomb['DIMENSIONS']['dimensions']['model']['MPI-ESM1.2-LR'] = MergedIomb['DIMENSIONS']['dimensions']['model'].pop('MPI-ESM1-2-LR')
MergedIomb['RESULTS']['global']['MPI-ESM1.2-LR'] = MergedIomb['RESULTS']['global'].pop('MPI-ESM1-2-LR')

# change meanCMIP5 to MeanCMIP5
MergedIomb['DIMENSIONS']['dimensions']['model']['MeanCMIP5'] = MergedIomb['DIMENSIONS']['dimensions']['model'].pop('meanCMIP5')
MergedIomb['RESULTS']['global']['MeanCMIP5'] = MergedIomb['RESULTS']['global'].pop('meanCMIP5')

# change meanCMIP6 to MeanCMIP6
MergedIomb['DIMENSIONS']['dimensions']['model']['MeanCMIP6'] = MergedIomb['DIMENSIONS']['dimensions']['model'].pop('meanCMIP6')
MergedIomb['RESULTS']['global']['MeanCMIP6'] = MergedIomb['RESULTS']['global'].pop('meanCMIP6')

vars_land = MergedLand
vars_iomb = MergedIomb

vars_merg = vars_land_org.copy()

metrics_land = collections.OrderedDict(vars_land['DIMENSIONS']['dimensions']['metric'])
metrics_iomb = collections.OrderedDict(vars_iomb['DIMENSIONS']['dimensions']['metric'])

# add the Land before the categorical metrics in land benchmarking
vars_merg['DIMENSIONS']['dimensions']['metric'] = \
    { k.replace('Ecosystem and Carbon Cycle', 'Land Ecosystem and Carbon Cycle'): v for k, v in metrics_land.items() }

# remove the Ecosystem in the 'Global Net Ecosystem Carbon Balance'
vars_merg['DIMENSIONS']['dimensions']['metric'] = \
    { k.replace('Global Net Ecosystem Carbon Balance', 'Global Net Carbon Balance'): v for k, v in vars_merg['DIMENSIONS']['dimensions']['metric'].items() }

# add the Land before the categorical metrics in land benchmarking
vars_merg['DIMENSIONS']['dimensions']['metric'] = \
    { k.replace('Hydrology Cycle', 'Land Hydrology Cycle'): v for k, v in vars_merg['DIMENSIONS']['dimensions']['metric'].items() }

# merge the ocean result
vars_merg['DIMENSIONS']['dimensions']['metric'].update( \
    { 'Ocean '+k: v for k, v in metrics_iomb.items() } )
    
for k in vars_merg['RESULTS']['global'].keys():

    # add the Land in the RESULT section of the CMEC schema
    vars_merg['RESULTS']['global'][k] = \
    { k.replace('Ecosystem and Carbon Cycle', 'Land Ecosystem and Carbon Cycle'): v for k, v in vars_merg['RESULTS']['global'][k].items() }

    # remove the Ecosystem in the 'Global Net Ecosystem Carbon Balance' in the RESULT section of the CMEC schema
    vars_merg['RESULTS']['global'][k] = \
    { k.replace('Global Net Ecosystem Carbon Balance', 'Global Net Carbon Balance'): v for k, v in vars_merg['RESULTS']['global'][k].items() }

    # add the Land in the RESULT section of the CMEC schema
    vars_merg['RESULTS']['global'][k] = \
    { k.replace('Hydrology Cycle', 'Land Hydrology Cycle'): v for k, v in vars_merg['RESULTS']['global'][k].items() }

    # merge the ocean result and add the Ocean in the RESULT section of the CMEC schema
    if k in vars_iomb['RESULTS']['global']:
       vars_merg['RESULTS']['global'][k].update(\
          { 'Ocean '+k: v for k, v in vars_iomb['RESULTS']['global'][k].items() } )

    # merge in the ocean UKESM result to land UKESM1-0-LL
    elif k == 'UKESM1-0-LL' and 'UKESM' in vars_iomb['RESULTS']['global']:
       vars_merg['RESULTS']['global'][k].update(\
          { 'Ocean '+k: v for k, v in vars_iomb['RESULTS']['global']['UKESM'].items() } )


vars_merg['DIMENSIONS']['dimensions']['model']['Mean CMIP5'] = vars_merg['DIMENSIONS']['dimensions']['model'].pop('MeanCMIP5')
vars_merg['RESULTS']['global']['Mean CMIP5'] = vars_merg['RESULTS']['global'].pop('MeanCMIP5')

vars_merg['DIMENSIONS']['dimensions']['model']['Mean CMIP6'] = vars_merg['DIMENSIONS']['dimensions']['model'].pop('MeanCMIP6')
vars_merg['RESULTS']['global']['Mean CMIP6'] = vars_merg['RESULTS']['global'].pop('MeanCMIP6')

with open ("Merged.json", "w") as fw:
     json.dump(vars_merg, fw)

