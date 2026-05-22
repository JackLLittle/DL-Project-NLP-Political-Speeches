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
from datetime import datetime
from us2020data.stm.utils import stopwords_politicalscience
from us2020data.stm.texttokeniser import TextTokeniser
from us2020data.stm.dictionary import Dictionary


if __name__ == "__main__":

    # choose model with stepwise (True) or countdown only time-covariate (False)
    timecovariate = True
    cwd = pathlib.Path.cwd()
    kwargs_cfg = dict()    
    kwargs_cfg["run_parent_folder"] = "{}/".format(cwd)    
    kwargs_cfg["stemming"] = True 
    DIR_in = "{}us2020data/stm/postprocessed4stm/".format(kwargs_cfg["run_parent_folder"])    
    dictionary_topic = "POTUS2020"
    outputdirectory = "{}us2020data/stm/postprocessed4stm/{}/".format(kwargs_cfg["run_parent_folder"], dictionary_topic)
    pathlib.Path(outputdirectory).mkdir(parents=True, exist_ok=True)          
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

    if timecovariate:
        stm_out = pd.read_csv("{}/stm/selected_models_with_time_covariate.csv".format(outputdirectory))
    else:
        stm_out = pd.read_csv("{}/stm/selected_models.csv".format(outputdirectory))
    results_out = "{}/stm_analysis/timecovariate{}".format(outputdirectory, timecovariate)    
    period_folders = sorted([f.name for f in os.scandir("{}/stm/".format(outputdirectory)) if f.is_dir()]    )
    analysis_dict_time = {"period": [], "periodpp": [],"10topics": [], "15topics": [], "20topics": [], "25topics": [], "bestmodel": []}
    analysis_dict_timeparty = {"period": [], "periodpp": [], "10topics": [], "15topics": [], "20topics": [], "25topics": [], "bestmodel": []}
    
    for datafold in period_folders: 
        analysis_dict_time["period"].append(datafold)        
        analysis_dict_time["periodpp"].append(datetime.strptime(datafold, "%b%Y"))
        analysis_dict_timeparty["period"].append(datafold)
        analysis_dict_timeparty["periodpp"].append(datetime.strptime(datafold, "%b%Y"))
        for k in [10,15,20,25]:
            period = datafold
            topics = k
            if timecovariate:
                stm_time = pd.read_csv("{}/stm/{}/LDAbeta_false/time_covariate/topics{}/party_prevalence_content/estimateEffects/timecovariate_significance.csv".format(outputdirectory, period, topics), sep=",")                  
            else:
                stm_time = pd.read_csv("{}/stm/{}/LDAbeta_false/topics{}/party_prevalence_content/estimateEffects/timecovariate_significance.csv".format(outputdirectory, period, topics), sep=",")           
            # get percentage of spline coefficients that were significant at 5% level
            # percentage of stat. signif. coefficients per topic
            statsigniftopic = stm_time["timeInTopicSignif"].values/stm_time["timecoef"].values 
            # mean percentage over all topics
            analysis_dict_time["{}topics".format(int(k))].append(statsigniftopic.sum()/topics)
            # only one coefficient of interaction, get avg over topics
            analysis_dict_timeparty["{}topics".format(int(k))].append(stm_time["timeInPartySignif"].sum()/len(stm_time["timeInPartySignif"]))
        analysis_dict_time["bestmodel"].append(stm_out.loc[stm_out["times"]==datafold, "ks"].values[0])
        analysis_dict_timeparty["bestmodel"].append(stm_out.loc[stm_out["times"]==datafold, "ks"].values[0])    
    sortedidx = np.argsort(analysis_dict_time["periodpp"])
    analysis_dict_time["period"] = np.asarray(analysis_dict_time["period"])[sortedidx].tolist()
    analysis_dict_time["periodpp"] = np.asarray(analysis_dict_time["periodpp"])[sortedidx].tolist()
    analysis_dict_time["periodpp"] = [i.strftime("%m / %Y") for i in analysis_dict_time["periodpp"]]
    analysis_dict_time["10topics"] = np.asarray(analysis_dict_time["10topics"])[sortedidx].tolist()
    analysis_dict_time["15topics"] = np.asarray(analysis_dict_time["15topics"])[sortedidx].tolist()
    analysis_dict_time["20topics"] = np.asarray(analysis_dict_time["20topics"])[sortedidx].tolist()
    analysis_dict_time["25topics"] = np.asarray(analysis_dict_time["25topics"])[sortedidx].tolist()
    analysis_dict_time["bestmodel"] = np.asarray(analysis_dict_time["bestmodel"])[sortedidx].tolist()

    analysis_dict_timeparty["period"] = np.asarray(analysis_dict_timeparty["period"])[sortedidx].tolist()
    analysis_dict_timeparty["periodpp"] = np.asarray(analysis_dict_timeparty["periodpp"])[sortedidx].tolist()
    analysis_dict_timeparty["periodpp"] = [i.strftime("%m / %Y") for i in analysis_dict_timeparty["periodpp"]]
    analysis_dict_timeparty["10topics"] = np.asarray(analysis_dict_timeparty["10topics"])[sortedidx].tolist()
    analysis_dict_timeparty["15topics"] = np.asarray(analysis_dict_timeparty["15topics"])[sortedidx].tolist()
    analysis_dict_timeparty["20topics"] = np.asarray(analysis_dict_timeparty["20topics"])[sortedidx].tolist()
    analysis_dict_timeparty["25topics"] = np.asarray(analysis_dict_timeparty["25topics"])[sortedidx].tolist()
    analysis_dict_timeparty["bestmodel"] = np.asarray(analysis_dict_timeparty["bestmodel"])[sortedidx].tolist()

    analysis_dict_time["period"].append("median_all")
    analysis_dict_timeparty["period"].append("median_all")
    analysis_dict_time["periodpp"].append(None)
    analysis_dict_timeparty["periodpp"].append(None)
    
    for k in [10,15,20,25]:
        analysis_dict_time["{}topics".format(int(k))].append(np.percentile(analysis_dict_time["{}topics".format(int(k))], 50, method="higher"))
        analysis_dict_timeparty["{}topics".format(int(k))].append(np.percentile(analysis_dict_timeparty["{}topics".format(int(k))], 50, method="higher"))
    analysis_dict_time["bestmodel"].append(None)
    analysis_dict_timeparty["bestmodel"].append(None)    
    pd.DataFrame.from_dict(analysis_dict_time).to_csv("{}/timecovariate_significance_all.csv".format(results_out), index=False)
    pd.DataFrame.from_dict(analysis_dict_timeparty).to_csv("{}/timeparty_significance_all.csv".format(results_out), index=False)
