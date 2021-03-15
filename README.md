For the version of the AR6 figure,  the ILAMBv2.5 and v2.4 were used for land and ocean model benchmarking, respectively. 

The web portals for these two results are hosted by [www.ilamb.org](https://www.ilamb.org/results/) for ([Land](https://www.ilamb.org/CMIP5v6/ILAMB_AR6) and [Ocean](https://www.ilamb.org/CMIP5v6/IOMB_AR6)), respectively.

The DOI and tarball of the above two results can be obtained from the [figshare] ()


There are several steps to get the final result. They are described as follows:

1. Convert the two benchmarking results in the ILAMB JSON format to the CMEC format. After conversions, they can be used by the LMT Unified Dashboard directly. (the "dashboard.html" is in the same directory of the ILAMB index.html that will provide the UD interactive experiences to users). The conversion python script is Cvt_ILAMB2CMECJson.py. 

```
./Cvt_ILAMB2CMECJson.py -i ./data/ILAMB/ilamb_index.html -j ./data/ILAMB/scalars.json -c ./data/ILAMB/ar6_ilamb_cmec.json 

```
```
./Cvt_ILAMB2CMECJson.py -i ./data/IOMB/iomb_index.html -j ./data/IOMB/scalars.json -c ./data/IOMB/ar6_iomb_cmec.json
```

2. Fill in the missing values in the categorical metrics. A python script is used to crawl various tables in the HTML files in the ILAMB result directory (\_build) to harvest absolute scores.  The script also reads the ILAMB configuration file to get the weights to aggregate the scores from variable to categorical metrics. As suggested by Forrest, aggregation is only applied when there are more than three valid sub-metrics or all sub-metrics (the total number of sub-metrics is less than 3) are valid. The computed categorical scores will be normalized to get the relative scores and replace the values in the ILAMB and IOMB CMEC JSON files that we get in Step 1. 

The code is DmILAMB.py.

```
./DmILAMB.py -c ./data/IOMB/ar6_iomb.cfg -r ../../ipcc_fig/dmilamb_iomb/IOMB/ -o ./data/IOMB/ar6_iomb_cmec_cal.json
```

3. Merge the ILAMB and IOMB CMEC JSON files after filling the missing values in step 2. A python script is used to merge the two CMEC JSON files. It will do the followings:
    - change model names to make them consistent across two results
    - filter out the models in IOMB results that are not in ILAMB results
    - change model names by adding a blank space
    - MPI and bcc
    - Add the  "Land" and "Ocean" prefix to the categorical metrics for land and ocean results.
    - Remove the "Ecosystem" in the "Global Net Ecosystem Carbon Balance"
    - Dump the merged CMEC JSON file

The code is MergeCmecJson.py.

```
./MergeCmecJson.py -lo ./data/ILAMB/ar6_ilamb_cmec.json -lc ./data/ILAMB/ar6_ilamb_cmec_cal.json -oo ./data/IOMB/ar6_iomb_cmec.json -oc ./data/IOMB/ar6_iomb_cmec_cal.json 
```

4. The CMEC JSON file will be used by the LMT Unified Dashboard (UD) to show results interactively. The UD provides a function to save the dashboard to a pure HTML file. The saving function will do:
    - make the names of categorical metrics bold and apply the background colors (4 colors are used repeatedly)
    - put the legend to the top-left corner
    - adjust the font size (11.5px for numbers in the square cells, 20px for the model and metric names.)
    - adjust the locations of the model and metric names in the table
    - apply the IPCC colors to the model names

The LMT UD version used above (***hashtag: eb4d53186c50215d462a293cb4f00f850fe8d618***) can be found on the UD GitHub repository [here](https://github.com/climatemodeling/unified-dashboard/tree/eb4d53186c50215d462a293cb4f00f850fe8d618).

5. Finally, we get the HTML file, we have to manually edit it to insert two black rows with (a) and (b) captions. This is the only manual operation for the whole process.


* * *

___An online conversion tool like [this](https://cloudconvert.com/) could convert the HTML page to a pdf file in a vector format. I am trying to find a reliable and free PDF conversion tool to include in UD to save pdf files directly.___



The final figure is:

![]()



