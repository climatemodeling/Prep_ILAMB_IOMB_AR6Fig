#!/usr/bin/env python
  
from pathlib import Path
from bs4 import BeautifulSoup
import sys, re, os
import numpy as np
import json, collections
import math


"""
   Harvest the absolute scores in tables of various HTML files under the ILAMB result directory.

   Aggregate the scores to upper level metrics using the weights in the ILAMB configure file.

   The absolute scores are the weighted averages of variables in the category that have non-missing 
   scores when the total number of non-missing scores are larger than three.                                 
"""


Delim = ["", "::", "!!", "||"]


def FlattenTreeOfTabJson(TabDict, ParentMetric, TreeLevel):

    """
       Remove the nested structures of a dictionary in the tabultor format
    """

    NewTabDict=[]
    for item in TabDict:
        Fdict={}
        Fdict["metric"] = ParentMetric + Delim[TreeLevel] + item["metric"]

        for key in item.keys():
            if key != "metric" and key != "_children":
               Fdict[key] = item[key]
        NewTabDict.append(Fdict)

        if "_children" in item.keys():
            NextTreeLevel = TreeLevel + 1
            ChdDict = FlattenTreeOfTabJson(item["_children"], Fdict["metric"], NextTreeLevel)
            NewTabDict = NewTabDict + ChdDict

    return NewTabDict


import argparse

parser = argparse.ArgumentParser(description = "Merge the JSON files from ILAMB and IOMB benchmarking results")

parser.add_argument("-c", "--CfgFile", type=str, help="Input: the ILAMB configure file")
parser.add_argument("-r", "--RltsDir", type=str, help="Input: the ILAMB result diretory")
parser.add_argument("-o", "--OutJSON", type=str, help="Output: the absolute scores in the CMEC JSON schema")

args = parser.parse_args() 

if args.CfgFile:
   CfgFile = args.CfgFile
else:
   print ("Please give the ILAMB configure file using -c or --CfgFile")
   sys.exit()

if args.RltsDir:
   RltsDir = args.RltsDir
else:
   print ("Please give the ILAMB result directory using -r or --RltsDir")
   sys.exit()


if args.OutJSON:
   OutJSON = args.OutJSON
else:
   print ("Please give the full path of the output JSON file using -o or --OutJSON")
   sys.exit()

print (CfgFile, RltsDir, OutJSON, len(sys.argv))


sndwgt = collections.OrderedDict({})
thdwgt = collections.OrderedDict({})

sndnew = 0
varnew = 0
relnew = 0

topmet = 'xxx'
sndmet = 'yyy'
varnam = 'zzz'

ListTopMet = []
with open(CfgFile, "r") as fc:
     for ln in fc:

         line = ln.strip()

         if line[0:1] == "#":
            continue

         if line[0:4] == '[h1:':
            topmet= ''.join(line[4:-1].split(' '))
            ListTopMet.append(topmet)

         if line[0:13] == "relationships":
            temp = line.rstrip()
            ix = temp.index('=') + 1

            relmet=temp[ix+1:-1].strip()

            relnew=1

         if line[0:4] == '[h2:':
            sndmet = ''.join(line[4:-1].split(' '))
            sndwgt[sndmet] = 10.
            sndnew = 1



         if line[0:1] == '[' and not ':' in line:
            varnam = ''.join(line[1:-1].split(' '))
            thdwgt[sndmet+'/'+varnam] = 10.
            varnew = 1


         if sndnew == 1 and relnew == 1:
  
            sndwgt['REL_'+sndmet+'/'+relmet.split('/')[1]] = 10
            thdwgt['REL_'+sndmet+'/'+relmet.split('/')[1]+'/'+relmet] =10
            relnew =0


         if line[0:6] == 'weight':
            temp = line.rstrip()
            ix = temp.index('=') + 1

            if sndnew == 1 and varnew == 1:
               print ("error")
            if sndnew == 1:
               sndwgt[sndmet] = float(temp[ix:])
               print ('second', sndmet, float(temp[ix:]))
               sndnew = 0
            if varnew == 1:
               print ('third', sndmet+'/'+varnam, float(temp[ix:]))
               thdwgt[sndmet+'/'+varnam] = float(temp[ix:])
               varnew = 0


ListTopMet.append("Relationships") 

ilambexp = []
ilambexp.append(RltsDir)

exp_modscore = []
exp_relscore = []
exp_modnames = []
exp_scrnames = []
exp_regnames = []

for ik, ilexp in enumerate(ilambexp):

    modscore={}
    relscore={}

    # loop over all html under the ilexp
    for fhtm in Path(ilexp).rglob('*.html'):
        if 'index' in str(fhtm) or 'dashboard' in str(fhtm):
           if 'index' in str(fhtm):
              # get the full set of names
               modnms = []
               scrnms = []
               regnms = []
               with open(fhtm) as fp:
                  soup = BeautifulSoup(fp, features="html.parser")
                  for tb in soup.find_all('table', id=re.compile('scoresTable')):
                      for th in tb.find_all('th'):
                          if th.text.strip():
                             modnms.append(th.text.strip())
                  for se in soup.find_all('select', id=re.compile('ScalarOption')):
                      for op in se.find_all('option'):
                          scrnms.append(op.text.strip())
                  for se in soup.find_all('select', id=re.compile('RegionOption')):
                      for op in se.find_all('option'):
                          regnms.append(op.text.strip())
               exp_modnames.append(modnms)
               exp_scrnames.append(scrnms)
               exp_regnames.append(regnms)

           continue
    
        print('mining in: ', fhtm)

        with open(fhtm) as fp:
             soup = BeautifulSoup(fp, features="html.parser")
    
             tmpdir = str(fhtm).split('/')


             topmet = tmpdir[-4]
             relvar = tmpdir[-3] + '/' + tmpdir[-2]

             # relationship and region loop
             # mx: what is oscore_reg

             oscore_reg={}
             for tb in soup.find_all('table', id=re.compile('Relationships_table')):

                 region = tb["id"][20:]

                 xtopmet = 'Relationships'

                 for h1 in soup.find_all('h1'):
                     if tmpdir[-2] in h1.text:
                        print (h1.text)
                        xrelvar = relvar + '/' + h1.text.strip()
    
                 if xtopmet not in relscore.keys():
                    relscore[xtopmet]={}

                 # model loop
                 oscore = {}
                 for tr in tb.find_all('tr'):
                     if len(tr.find_all('th')) > 0: 
                        tils = tr.find_all('th')
                        tils = [til.text.strip() for til in tils]
                        continue
    
                     # columns in table
                     cols = tr.find_all('td')
                     cols = [ele.text.strip() for ele in cols]

                     if 'Overall Score [1]' in tils or 'Overall Score  [1]' in tils:
                        if 'Overall Score [1]' in tils:
                           ix = tils.index("Overall Score [1]")
                        if 'Overall Score  [1]' in tils:
                           ix = tils.index("Overall Score  [1]")
    
                        mdname = cols[0]
                        if cols[ix].strip() == '':                                          
                           oscore[mdname] =  -999.0                                         
                        else:                                                               
                           oscore[mdname] = float(cols[ix])  

                     else:
                        print (tils, 'Overall Score  [1]' in tils)
                        print ('relationship-there is no overall score for ' + fhtm)
                        mdname = cols[0]
                        oscore[mdname] = -999.0
                        sys.exit()
    
                 oscore_reg[region] = oscore
    
             # put it back to the relscore , relative score, top metric is key and value is a dictionary with second/third metric
             if oscore_reg != {}:
                 dict1={}
                 dict1[xrelvar] = oscore_reg
                 relscore[xtopmet].update(dict1)
    
    
             # metric score MeanState
             mscore_reg = {}
             for tb in soup.find_all('table', id=re.compile("MeanState_table")):
                 region = tb["id"][16:]


                 if topmet not in modscore.keys():
                    modscore[topmet]={}
    
                 mscore = {}
                 # table row loop (model)
                 for tr in tb.find_all('tr'):

                     # get the th 
                     if len(tr.find_all('th')) > 0: 
                        tils = tr.find_all('th')
                        tils = [til.text.strip() for til in tils]

                     # table columns
                     cols = tr.find_all('td')
                     cols = [ele.text.strip() for ele in cols]

                     if len(cols) > 0:
                        if 'Overall Score [1]' in tils or 'Overall Score  [1]' in tils:
                           if 'Overall Score [1]' in tils:
                              ix = tils.index("Overall Score [1]")
                           if 'Overall Score  [1]' in tils:
                              ix = tils.index("Overall Score  [1]")

                           mdname = cols[0]
                           if mdname == 'Benchmark':
                              continue
                           if cols[ix] == '':
                              mscore[mdname] = -999.
                           else:
                              mscore[mdname] = float(cols[ix])
                        else:
                           print (tils)
                           print ('mean-state-there is no overall score for ', fhtm)
                           sys.exit()
                 mscore_reg[region] = mscore
             if mscore_reg != {}:
                 dict1={}
                 dict1[relvar] = mscore_reg
                 modscore[topmet].update(dict1)
    
    exp_modscore.append(modscore)
    exp_relscore.append(relscore)
    exp_modscore[0].update(exp_relscore[0])


# merge
# [{topmet1:{submet1:{'reg1':{}, 'reg2':{}}, submet2:{reg1:{}, reg2{}...}, {topmet2:{}}
#[{'HydrologyCycle': {'LatentHeat/FLUXCOM': {'global': {'bcc-csm1-1': 0.648, 'BCC-CSM2-MR': 0.689, 'CanESM2': 0.64, 'CanESM5': 0.626, 'CESM1-BGC': 0.666, 'CESM2': 0.703, 'GFDL-ESM2G': 0.635, 'GFDL-ESM4': 0.678, 'IPSL-CM5A-LR': 0.662, 'IPSL-CM6A-LR': 0.698, 'MeanCMIP5': 0.712, 'MeanCMIP6': 0.739, 'MIROC-ES2L': 0.617, 'MIROC-ESM': 0.634, 'MPI-ESM-LR': 0.64, 'MPI-ESM1.2-LR': 0.631, 'NorESM1-ME': 0.649, 'NorESM2-LM': 0.691, 'UK-HadGEM2-ES': 0.679, 'UKESM1-0-LL': 0.683}}, 'LatentHeat/DOLCE': {'global': {'bcc-csm1-1': 0.608, 'BCC-CSM2-MR': 0.622, 'CanESM2': 0.587, 'CanESM5': 0.556, 'CESM1-BGC': 0.574, 'CESM2': 0.659, 'GFDL-ESM2G': 0.561, 'GFDL-ESM4': 0.598, 'IPSL-CM5A-LR': 0.607, 'IPSL-CM6A-LR': 0.6, 'MeanCMIP5': 0.649, 'MeanCMIP6': 0.662, 'MIROC-ES2L': 0.541, 'MIROC-ESM': 0.559, 'MPI-ESM-LR': 0.577, 'MPI-ESM1.2-LR': 0.556, 'NorESM1-ME': 0.566, 'NorESM2-LM': 0.656, 'UK-HadGEM2-ES': 0.582, 'UKESM1-0-LL': 0.608}}, 'LatentHeat/FLUXNET2015': {'global': {'bcc-csm1-1': 0.55, 'BCC-CSM2-MR': 0.559, 'CanESM2': 0.57, 'CanESM5': 0.531, 'CESM1-BGC': 0.559, 'CESM2': 0.606, 'GFDL-ESM2G': 0.56, 'GFDL-ESM4': 0.552, 'IPSL-CM5A-LR': 0.588,

reg = "global"

# mod metrics
topmets=[]
varnams={}
regnams={}

for scr in exp_modscore:
    topmets+=list(scr.keys())

    for key in scr.keys():
        if key not in varnams.keys():
           varnams[key] = []
           varnams[key].append(list(scr[key].keys()))
        else:
           varnams[key].append(list(scr[key].keys()))

# remove the duplicated
topmets=list(set(topmets))


TabJson = []
#for met in topmets:
for met in ListTopMet:

    if met not in topmets:
        continue

    xdict = {}
    xdict['metric'] = met
    xdict['_children'] = []


    # initialization
    xdict.update({m: 0.0 for m in exp_modnames[0]})
    sdict = {}
    #for k, vnms in enumerate(varnams[met][0]):
    for k, xvnms in enumerate(thdwgt.keys()):

        if 'REL_' in xvnms:
            vnms = xvnms[4:]
        else:
            vnms = xvnms


        if vnms not in varnams[met][0]:
            continue


        if len(vnms.split('/')) > 2:
           metric_next = vnms.split('/')[0] + '/' + vnms.split('/')[1]
           metric_thrd = vnms.split('/')[2] + '/' + vnms.split('/')[3]
        else:
           metric_next = vnms.split('/')[0] 
           metric_thrd = vnms.split('/')[1]


        if metric_next not in [xt['metric'] for xt in xdict['_children']]:
            sdict = {}
            sdict['metric'] = metric_next
            sdict['_children'] = []
            sdict.update({m: 0.0 for m in exp_modnames[0]})
        else:
            for x in xdict['_children']:
                if metric_next == x['metric']:
                   sdict = x
        tdict = {}
        if metric_thrd not in [xs['metric'] for xs in sdict['_children']]:
            tdict['metric'] = metric_thrd
            for m in exp_modnames[0]:
                if m in exp_modscore[0][met][vnms][reg].keys():
                      tdict[m] = exp_modscore[0][met][vnms][reg][m]
                else:
                      tdict[m] = -999.

        sdict['_children'].append(tdict)
        if metric_next not in [xt['metric'] for xt in xdict['_children']]:
            xdict['_children'].append(sdict)
    
    ndict = {}
    xndict = {}
    tndict = {}
    for m in exp_modnames[0]:
        ndict[m] = 0.0
        xndict[m] = 0.0
        tndict[m] = 0.0


    for sdict in xdict['_children']:
        metric_next = sdict['metric']


        cdict = {}
        xcdict = {}
        tcdict = {}
        for m in exp_modnames[0]:
            cdict[m]  = 0.0
            xcdict[m] = 0.0
            tcdict[m] = 0.0


        for tdict in sdict['_children']:
            metric_thrd = tdict['metric']

            if met == 'Relationships':
               var = 'REL_' + metric_next+'/'+metric_thrd
            else:
               var = metric_next+'/'+metric_thrd

            if var in thdwgt.keys():
               w = thdwgt[var]
               for m in exp_modnames[0]:
                   tcdict[m] = tcdict[m] + 1
                   if tdict[m] != -999:

                      sdict[m] = sdict[m] + w * tdict[m]
                      cdict[m] = cdict[m] + w
                      xcdict[m] = xcdict[m] + 1
            else:
               print (var + '  -----> no')
               print (thdwgt.keys())
        for m in exp_modnames[0]:
            tndict[m] = tndict[m] + 1

            if cdict[m] > 0.0:
               sdict[m] = sdict[m] / cdict[m]

               if met == "Relationships":
                   w = sndwgt['REL_'+metric_next]                                            
               else:                                                                        
                   w = sndwgt[metric_next]    
               xdict[m] += w * sdict[m]
               ndict[m] += w
               xndict[m] = xndict[m] + 1
            else:
               sdict[m] = -999.

    for m in exp_modnames[0]:
        if ndict[m] > 0.0 and (xndict[m] >=3 or tndict[m] == xndict[m]):
           xdict[m] = xdict[m] / ndict[m]
        else:
           xdict[m] = -999.
 
    TabJson.append(xdict)

 
# rewrite to cmec json
# the following code is to write the JSON file in the CMEC json schema
# this one could be a __init__ for CMEC json schema
metric_template={"MetricName":{"Name":"", "Abstract":"", "URI":"", "Contact":"forrest AT climatemodeling.org"}, "MetricTree":{}}
region_template={"RegionName":{"LongName":"", "Description":"", "Generator":""}}
model_template={"ModelName":{"Description":"", "Source":"CMIP6 ESGF"}}

DimKws = ["region", "model", "metric", "statistic"]
RltKws = []


DimensionsDict = {}
ResultsDict = {}

DimensionsDict["json_structure"] = DimKws
DimensionsDict["dimensions"] = {}

for dkey in  DimKws:
    DimensionsDict["dimensions"][dkey] = {}

DimensionsDict["dimensions"]["statistic"]["indices"]=[]
DimensionsDict["dimensions"]["statistic"]["short_names"]={}    # shortname : indices


CMECSchemaDict = {"name": "CMEC", "version": "v1", "package": "ILAMB"}


OutputDict = {"SCHEMA":CMECSchemaDict, "DIMENSIONS":DimensionsDict, "RESULTS":ResultsDict}

# now realize the class
FlattenList =  FlattenTreeOfTabJson(TabJson, "", 0)


DimDict=OutputDict["DIMENSIONS"]["dimensions"]
RltDict=OutputDict["RESULTS"]

# models 
for m in exp_modnames[0]:
    modict = model_template.copy()
    modval = modict.pop("ModelName").copy()
    DimDict["model"][m] = modval

# metrics


# metrics
metrics = []

# get metrics names from overall score as it includes the complete list 

regions = []
scores = []

for m in FlattenList:
    regname = 'global'
    scrname = 'Overall Score'
    if regname not in RltDict.keys():
       RltDict[regname] = {}

    # now for metric and RltDict
    metdct = metric_template.copy()
    metval = metdct.pop("MetricName").copy()

    metval["Name"] = m["metric"]


    if "!!" not in m["metric"]:
       metval["Abstract"] = "composite score"
    else:
       metval["Abstract"] = "benchmark score"

    metval["URI"] = ["https://www.osti.gov/biblio/1330803", "https://doi.org/10.1029/2018MS001354"]

    DimDict["metric"][m["metric"].strip()] = metval

    for key in m.keys():

        if key != "metric" and key != "scoreboard":
           if key not in RltDict[regname].keys():
              RltDict[regname][key] = {}

           if m["metric"].strip() not in RltDict[regname][key].keys():
              RltDict[regname][key][m["metric"].strip()] = {}
              RltDict[regname][key][m["metric"].strip()][scrname] = m[key]
           else:
              RltDict[regname][key][m["metric"].strip()][scrname] = m[key]

regions = ['global']
scores = ['Overall Score']

#regions
for reg in regions:
    regdct = region_template.copy()
    regval = regdct.pop("RegionName").copy()

    if reg == "global":
       regval["LongName"] = "Global"
       regval["Description"] = "Global"
       print (reg, regval, regdct)

    else:
       regval["LongName"] = "South American Amazon"
       regval["Description"] = "South American Amazon"
       print (reg, regval, regdct)
    regval["Generator"] = "From GEED4S definition"
    DimDict["region"][reg]=regval


#indices/scores/
DimDict["statistic"]["indices"] = scores
DimDict["statistic"]["short_names"] = [scr.replace(' ', '') for scr in scores]


with open (OutJSON, "w") as fw:
     json.dump(OutputDict, fw)

