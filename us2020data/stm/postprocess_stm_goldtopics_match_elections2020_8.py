################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

import numpy as np
import pandas as pd
import pathlib
from us2020data.stm.utils import stopwords_politicalscience
from us2020data.stm.dictionary import Dictionary
from us2020data.stm.texttokeniser import TextTokeniser
from scipy.spatial.distance import cosine
import calendar
from datetime import datetime

if __name__ == "__main__":

    # choose model with stepwise (True) or countdown only time-covariate (False)
    timecovariate = False
    cwd = pathlib.Path.cwd()
    kwargs_cfg = dict()    
    kwargs_cfg["run_parent_folder"] = "{}/".format(cwd)    
    kwargs_cfg["stemming"] = True

    DIR_in = "{}us2020data/stm/postprocessed4stm/".format(kwargs_cfg["run_parent_folder"])    
    dictionary_topic = "POTUS2020"
    outputdirectory = "{}us2020data/stm/postprocessed4stm/{}/".format(kwargs_cfg["run_parent_folder"], dictionary_topic)
    
    potusnames = ["Donald Trump", "Joe Biden", "Mike Pence", "Kamala Harris"]
    potuses_terms = {"Donald Trump" : {"term": ["2017-2021"],      "party":"Republicans"},
                     "Mike Pence"   : {"term": ["2017-2021"],      "party":"Republicans"},
                     "Joe Biden"    : {"term": ["2021-Incumbent"], "party":"Democrats"},
                     "Kamala Harris": {"term": ["2021-Incumbent"], "party":"Democrats"}}
 
    dictionary = Dictionary(topic="USSpeeches_election2020_STM",
                            workspace_in_dir="{}us2020data/stm/lexica/".format(kwargs_cfg["run_parent_folder"]),                             
                            workspace_out_dir="{}us2020data/stm/lexica/".format(kwargs_cfg["run_parent_folder"]),                             
                            stem=kwargs_cfg["stemming"])
    texttokeniser = TextTokeniser(dictionary=dictionary, stem=kwargs_cfg["stemming"], 
                                stopwords=stopwords_politicalscience("{}us2020data/stm/lexica/".format(kwargs_cfg["run_parent_folder"])), remove_punctuation=True, 
                                remove_oov=True)
        
    distributionOndictionaries = {"goldTopics": [], "politics": [], 
                                                    "contemporaryhistory": [], 
                                                    "immigration": [], 
                                                    "uspolitics": [],
                                                    "economy_and_society": []}

    results_out = "{}/stm_analysis/".format(outputdirectory)
    pathlib.Path(results_out).mkdir(parents=True, exist_ok=True)
    goldtopics = pd.read_csv("{}/distributionsOnGolddictionaries.csv".format(results_out))  
    topiclabellinglong = pd.read_csv("{}/timecovariate{}/topiclabellinglong.csv".format(results_out, timecovariate))  
    topiclabellinglong["best_topic_match"] = [None]*len(topiclabellinglong)
    if timecovariate:
        stm_out = pd.read_csv("{}/stm/selected_models_with_time_covariate.csv".format(outputdirectory))
    else:
        stm_out = pd.read_csv("{}/stm/selected_models.csv".format(outputdirectory))
    
    for i, row in stm_out.iterrows(): 
        period = row["times"]
        topics = row["ks"]
        results_out_period = "{}/{}/".format(results_out, period)  
        topiclabelling = pd.read_csv("{}/timecovariate{}/{}/topiclabelling.csv".format(results_out, timecovariate, period))  
        topicdistrOnDicts = pd.read_csv("{}/timecovariate{}/{}/distributionsOndictionaries.csv".format(results_out, timecovariate, period))  
        
        for jj, jjrow in topicdistrOnDicts.iterrows():
            lassotop = jjrow["LASSOTopics"]

            labelvec_stm = np.array([jjrow["politics"], jjrow["contemporaryhistory"], jjrow["immigration"], jjrow["uspolitics"], jjrow["economy_and_society"]])
            bestmatch = None
            mincosinedst = np.inf        
            for j, jrow in goldtopics.iterrows(): 
                if jrow["goldTopics"] not in topiclabelling.columns:
                    topiclabelling[jrow["goldTopics"]] = np.zeros((len(topiclabelling),))
                goldtopicvec = np.array([jrow["politics"], jrow["contemporaryhistory"], jrow["immigration"], jrow["uspolitics"], jrow["economy_and_society"]])
                cosinedst = cosine(labelvec_stm, goldtopicvec)                
                topiclabelling.loc[jj, jrow["goldTopics"]] = cosinedst
            
                if cosinedst < mincosinedst:
                    mincosinedst = cosinedst
                    bestmatch = jrow["goldTopics"]
                if "bestmatch" not in topiclabelling.columns:
                    topiclabelling["bestmatch"] = np.zeros((len(topiclabelling),))
                topiclabelling.loc[jj, "bestmatch"] = bestmatch
            topiclabelling.to_csv("{}/timecovariate{}/{}/topiclabelling.csv".format(results_out, timecovariate, period))  

            dateperiod = datetime.strptime(period, '%b%Y')
            _, monthdays = calendar.monthrange(dateperiod.year, dateperiod.month) 
            dateperiodendmonth = datetime.strptime("{}-{}-{}".format(monthdays, dateperiod.month, dateperiod.year), '%d-%m-%Y')
            
            if (topiclabellinglong["period"]==period).sum() > 0 and (topiclabellinglong["LASSOTopics"]==lassotop).sum() > 0:            
                topiclabellinglong.loc[(topiclabellinglong["period"]==period) & (topiclabellinglong["LASSOTopics"]==lassotop), "best_topic_match"] = [bestmatch]*len(topiclabellinglong.loc[(topiclabellinglong["period"]==period) & (topiclabellinglong["LASSOTopics"]==lassotop)])
    
    longdf = {"time": [], "period": [], "party": [], "best_topic_match": [], "median": []}
    for name, group in topiclabellinglong.groupby(["period", "party", "best_topic_match"]):
        longdf["time"].append(group["time"].values[0])
        longdf["period"].append(name[0])
        longdf["party"].append(name[1])
        longdf["best_topic_match"].append(name[2])
        longdf["median"].append(group["median"].sum())
        
    pd.DataFrame.from_dict(longdf).to_csv("{}/timecovariate{}/datawrapper_topiclabellinglong.csv".format(results_out, timecovariate), index=False)     
    topiclabellinglong.to_csv("{}/timecovariate{}/topiclabellinglong.csv".format(results_out, timecovariate), index=False)  

  
       
            