#!/usr/bin/env python

import json, collections
from bs4 import BeautifulSoup
import sys, re
import numpy as np

import argparse

gfed4s_regions = {
 "BONA": "Boreal North America",
 "TENA": "Temperate North America",
 "CEAM": "Central America",
 "NHSA": "Northern Hemisphere South America",
 "SHSA": "Southern Hemisphere South America",
 "EURO": "Europe",
 "MIDE": "Middle East",
 "NHAF": "Northern Hemisphere Africa",
 "SHAF": "Southern Hemisphere Africa",
 "BOAS": "Boreal Asia",
 "CEAS": "Central Asia",
 "SEAS": "Southeast Asia",
 "EQAS": "Equatorial Asia",
 "AUST": "Australia and New Zealand"
}

Delim = ["", "::", "!!", "||"]

def read_jsontree(models, parentObj, parentScore):
    """
       This json structure is from ILAMB outputs v2.5. The structure looks like as follows:
       {top_metric1:{statistic1+region1(scoreboard1):[score_model1, score_model2, score_model3...], "children":[submetric11:{}, submetric12:{},...]}, 
        top_metric2:{statistic1+region1(scoreboard2):[score_model1, score_model2, score_model3...], "children":[submetric21:{}, submetric22:{},...]},
       ....
       }
       Return the Python dictionary in the JSON structure for direct use by the tabulator.js
    """
    parentList = []
    parentDict = {}
    for m in parentObj.keys():

        if "Score" not in m and m != "children":
           parentDict['metric'] = m

        childObj = parentObj[m]

        for key in childObj.keys():
            if parentScore != "None" and key == parentScore:
               parentDict['scoreboard'] = key
               for n, mod in enumerate(models):
                   parentDict[str(mod)] = childObj[key][n]

               if "children" in childObj.keys() and childObj["children"] != {}:
                  parentDict["_children"] = []
                  parentDict["_children"] = read_jsontree(models, childObj["children"], key)
               parentList.append(parentDict.copy())

            if parentScore == "None" and key != "children":
               parentDict['scoreboard'] = key

               for n, mod in enumerate(models):
                   parentDict[str(mod)] = childObj[key][n]

               if "children" in childObj.keys() and childObj["children"] != {}:
                  parentDict["_children"] = []
                  parentDict["_children"] = read_jsontree(models, childObj["children"], key)

               parentList.append(parentDict.copy())

    return parentList
        

def FlattenTreeOfTabJson(TabDict, ParentMetric, TreeLevel):

    """
       Flatten a dictionary in which there are "_children" keywords and move the children dictionaries
       to the topmost level by creating new values of the "metric" keyword for the children 
       dictionaries. The new values of "metric" are the strings joining all its parent metric values 
       with delimiters.
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
            ChdDict = FlattenTreeOfTabJson(item[key], Fdict["metric"], NextTreeLevel)
            NewTabDict = NewTabDict + ChdDict

    return NewTabDict
                   


if __name__ == "__main__":

   # default file names
   ilmab_index = "ilamb_index.html"
   ilamb_json = "scalars.json"
   cmec_json = "output.json"

   import argparse

   parser = argparse.ArgumentParser(description = "Convert a JSON file from a ILAMB result to a CMEC compatible JSON")

   parser.add_argument("-i", "--ilamb_index", type=str, help="Input: the index.html from a ILAMB result")
   parser.add_argument("-j", "--ilamb_json", type=str, help="Input: the JSON file from a ILAMB result")
   parser.add_argument("-c", "--cmec_json", type=str, help="Output: the JSON file in the CMEC format")

   args = parser.parse_args()
   if args.ilamb_index:
      ilamb_index = args.ilamb_index

   if args.ilamb_json:
      ilamb_json = args.ilamb_json

   if args.cmec_json:
      cmec_json = args.cmec_json

   with open(ilamb_index, "r") as fp:
       soup = BeautifulSoup(fp, features="lxml")
   
   for se in soup.find_all('select'):
       if se.get_attribute_list("id")[0] == "RegionOption":
          regStrs = se.get_text()
       if se.get_attribute_list("id")[0] == "ScalarOption":
          scaStrs = se.get_text()
   
   modList=[]
   for hd in soup.find_all("th"):
   
      if hd.get_text() != '':
         modList.append(hd.get_text())
   
   regList = regStrs.strip().split("\n")
   scaList = scaStrs.strip().split("\n")
   
   
   metricList=[]
   with open(ilamb_json, "r") as jn:
       vars=json.load(jn, object_pairs_hook=collections.OrderedDict) 
       metricList = read_jsontree(modList, vars, "None")
   
   # the following code is to write a JSON file in the CMEC json schema
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
   FlattenList =  FlattenTreeOfTabJson(metricList, "", 0)
   
   DimDict=OutputDict["DIMENSIONS"]["dimensions"]
   RltDict=OutputDict["RESULTS"]
   
   # models 
   for m in modList:
       modict = model_template.copy()
       modval = modict.pop("ModelName").copy()
       DimDict["model"][m] = modval
   
   # metrics
   metrics = []
   
   # get metrics names from the overall score as it shall include 
   # the complete list of metrics
   for m in FlattenList:
       if 'Overall Score' in m["scoreboard"]:
           metrics.append(m['metric'].strip())
   
   regions = []
   scores = []
   
   for m in FlattenList:
       # region
       temp = m["scoreboard"].split(' ')
       regname = temp[-1].strip()
       scrname = ' '.join(temp[:-1]).strip()
   
       if regname not in RltDict.keys():
          RltDict[regname] = {}
   
   
       regions.append(regname)
       scores.append(scrname)
   
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
                 for mk in metrics:
                     RltDict[regname][key][mk] = {}
   
              RltDict[regname][key][m["metric"].strip()][scrname] = m[key]
   
   regions = list(set(regions))
   scores  = list(set(scores))
   
   # regions
   for reg in regions:
       regdct = region_template.copy()
       regval = regdct.pop("RegionName").copy()
   
       if reg == "global":
          regval["LongName"] = "Global"
          regval["Description"] = "Global"
   
       else:
          regval["LongName"] = "South American Amazon"
          regval["Description"] = "South American Amazon"
       regval["Generator"] = "From GEED4S definition"
       DimDict["region"][reg]=regval
   
   # indices/scores/
   DimDict["statistic"]["indices"] = scores
   DimDict["statistic"]["short_names"] = [scr.replace(' ', '') for scr in scores]
       
   # write the JSON file in the CMEC schema
   with open (cmec_json, "w") as fw:
        json.dump(OutputDict, fw)
