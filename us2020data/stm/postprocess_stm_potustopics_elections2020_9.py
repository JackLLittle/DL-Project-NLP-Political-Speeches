################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

import os
import numpy as np
import pandas as pd
import pathlib
import calendar
from datetime import datetime

if __name__ == "__main__":

    # choose model with stepwise (True) or countdown only time-covariate (False)
    timecovariate = False
    cwd = pathlib.Path.cwd()
    kwargs_cfg = dict()    
    kwargs_cfg["run_parent_folder"] = "{}/".format(cwd)        
    DIR_in = "{}us2020data/stm/postprocessed4stm/".format(kwargs_cfg["run_parent_folder"])    
    dictionary_topic = "POTUS2020"
    outputdirectory = "{}us2020data/stm/postprocessed4stm/{}/".format(kwargs_cfg["run_parent_folder"], dictionary_topic)      
    potusnames = ["Donald Trump", "Joe Biden", "Mike Pence", "Kamala Harris"]
    potuses_terms = {"Donald Trump": {"term": ["2017-2021"], "party":"Republicans"},
                     "Mike Pence": {"term": ["2017-2021"], "party":"Republicans"},
                     "Joe Biden": {"term": ["2021-Incumbent"], "party":"Democrats"},
                     "Kamala Harris": {"term": ["2021-Incumbent"], "party":"Democrats"}}
 
    if timecovariate:
        stm_out = pd.read_csv("{}/stm/selected_models_with_time_covariate.csv".format(outputdirectory))
    else:
        stm_out = pd.read_csv("{}/stm/selected_models.csv".format(outputdirectory))
    results_out = "{}/stm_analysis/timecovariate{}/".format(outputdirectory, timecovariate)
    pathlib.Path(results_out).mkdir(parents=True, exist_ok=True)
    period_folders = [f.name for f in os.scandir("{}/".format(outputdirectory)) if f.is_dir()]
    datawrapper = {"time": [], "potus": [], "period": []}
    datawrapperlong = {"time": [], "period": [], "potus": [], "median": [], "topic": [], "summary": [], "bestmatch": []}
    potusout = dict()
    for potus in potusnames:
        potusout[potus] = dict()
    corrlabels = []
    for i, row in stm_out.iterrows(): 
        period = row["times"]
        topics = row["ks"]
        results_out_period = "{}/{}/".format(results_out, period)  
        outlabelling = pd.read_csv("{}/topiclabelling.csv".format(results_out_period))
        for corrlabel in np.unique(outlabelling.LASSOTopics.values).tolist():
            corrlabels.append(corrlabel)            
            clustertopics = eval(outlabelling.loc[outlabelling.LASSOTopics==corrlabel, "STMTopics"].values.tolist()[0])
            alltopics = None
            for ct in clustertopics:
                topicdocs = pd.read_csv("{}/topic{}.csv".format(results_out_period, ct), index_col=0)
                topicdocs = topicdocs.rename(columns={"Topic{}".format(ct): "TopicCorr"})   
                if alltopics is None:
                    alltopics = topicdocs
                else:
                    alltopics = pd.concat([alltopics, topicdocs])
            alltopics = alltopics.drop_duplicates().reset_index(drop=True)
            for potus in potusnames:
                potusdocs = alltopics.loc[alltopics["speeches.POTUS"]==potus]
                topicmed = None
                topicmedsum = None
                if period not in potusout[potus].keys():
                    potusout[potus][period] = dict() 
                if len(potusdocs) > 0:
                    topicmed = np.percentile(potusdocs.TopicCorr.values, 50, method="higher")
                    topicmedsum = np.unique(outlabelling.loc[outlabelling.LASSOTopics==corrlabel, "label"].values).tolist()    
                    bestfoundtopicmatch = outlabelling.loc[outlabelling.LASSOTopics==corrlabel, "bestmatch"].values[0]
                    potusout[potus][period][corrlabel] = {"median" : topicmed, 
                                                          "summary": topicmedsum,
                                                          "bestmatch": bestfoundtopicmatch}      
    for i, row in stm_out.iterrows(): 
        period = row["times"]
        for potus in potusnames:
            datawrapper["potus"].append(potus)             
            dateperiod = datetime.strptime(period, '%b%Y')
            _, monthdays = calendar.monthrange(dateperiod.year, dateperiod.month) 
            dateperiodendmonth = datetime.strptime("{}-{}-{}".format(monthdays, dateperiod.month, dateperiod.year), '%d-%m-%Y')
            datawrapper["time"].append(dateperiodendmonth)    
            datawrapper["period"].append(period)            
            for corrlabel in np.unique(corrlabels):                         
                if "TopicCorr-{}-median".format(corrlabel) not in datawrapper.keys():
                    datawrapper["TopicCorr-{}-median".format(corrlabel)] = []
                    datawrapper["TopicCorr-{}-summary".format(corrlabel)] = []
                    datawrapper["TopicCorr-{}-bestmatch".format(corrlabel)] = []
                if corrlabel in potusout[potus][period].keys():
                    datawrapper["TopicCorr-{}-median".format(corrlabel)].append(potusout[potus][period][corrlabel]["median"])
                    datawrapper["TopicCorr-{}-summary".format(corrlabel)].append(potusout[potus][period][corrlabel]["summary"])
                    datawrapper["TopicCorr-{}-bestmatch".format(corrlabel)].append(potusout[potus][period][corrlabel]["bestmatch"])
                    datawrapperlong["median"].append(potusout[potus][period][corrlabel]["median"]) 
                    datawrapperlong["summary"].append(potusout[potus][period][corrlabel]["summary"])
                    datawrapperlong["bestmatch"].append(potusout[potus][period][corrlabel]["bestmatch"])
                    datawrapperlong["topic"].append("TopicCorr-{}".format(corrlabel))  
                    datawrapperlong["potus"].append(potus)            
                    datawrapperlong["time"].append(dateperiodendmonth)
                    datawrapperlong["period"].append(period)
                else:
                    datawrapper["TopicCorr-{}-median".format(corrlabel)].append(None)
                    datawrapper["TopicCorr-{}-summary".format(corrlabel)].append(None)
                    datawrapper["TopicCorr-{}-bestmatch".format(corrlabel)].append(None)
                   
    datawrapper_df = pd.DataFrame.from_dict(datawrapper)
    datawrapper_df = datawrapper_df.sort_values(by="time").reset_index(drop=True)
    datawrapper_df.to_csv("{}/datawrapper.csv".format(results_out))
    datawrapperlong_df = pd.DataFrame.from_dict(datawrapperlong)
    datawrapperlong_df.to_csv("{}/datawrapper_long.csv".format(results_out))
    for potus in potusnames:
        potusdf = datawrapper_df.loc[datawrapper_df["potus"]==potus]
        potusdf.to_csv("{}/datawrapper_{}.csv".format(results_out, potus))        
        potuslongdf = datawrapperlong_df.loc[datawrapperlong_df["potus"]==potus]
        
        longdf = {"time": [], "period": [], "potus": [], "bestmatch": [], "median": []}
        for name, group in potuslongdf.groupby(["period", "potus", "bestmatch"]):
            longdf["time"].append(group["time"].values[0])
            longdf["period"].append(name[0])
            longdf["potus"].append(name[1])
            longdf["bestmatch"].append(name[2])
            longdf["median"].append(group["median"].sum())

        longdf = pd.DataFrame.from_dict(longdf)
        longdf.to_csv("{}/datawrapperlong_{}.csv".format(results_out, potus))        
        