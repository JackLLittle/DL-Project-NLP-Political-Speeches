################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

from __future__ import print_function
import numpy as np
import pandas as pd
import pathlib
from us2020data.stm.utils import flatten, stopwords_politicalscience
from datetime import datetime
import calendar
from us2020data.stm.dictionary import Dictionary
from us2020data.stm.texttokeniser import TextTokeniser
import string

def get_cluster(topic, clusterdict):

    for c in clusterdict.keys():
        if topic in clusterdict[c]:
            return c
    return topic

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

    if timecovariate:
        stm_out = pd.read_csv("{}/stm/selected_models_with_time_covariate.csv".format(outputdirectory))
    else:
        stm_out = pd.read_csv("{}/stm/selected_models.csv".format(outputdirectory))
    results_out = "{}/stm_analysis/timecovariate{}/".format(outputdirectory, timecovariate)
    pathlib.Path(results_out).mkdir(parents=True, exist_ok=True)
    # period_folders = [f.name for f in os.scandir("{}/".format(outputdirectory)) if f.is_dir()]
    topic_labelling_long = {"STMTopics": [], "LASSOTopics":[], "summary": [], "time": [], "period": [], "median": [], "party": []}
    for i, row in stm_out.iterrows(): 
        period = row["times"]
        topics = row["ks"]
        if timecovariate:
            stm_model_out = pd.read_csv("{}/stm/{}/LDAbeta_false/time_covariate/topics{}/party_prevalence_content/modelout_dataframe.csv".format(outputdirectory, period, topics), sep="\t")  
            # load graph LASSO-based topic (positive) correlations
            topiccorr = pd.read_csv("{}/stm/{}/LDAbeta_false/time_covariate/topics{}/party_prevalence_content/topicCorr_posAdj.csv".format(outputdirectory, period, topics), sep=",")
            # topic word lists, based on different criteria (frex, score, lift, prob)
            sage_marginal = pd.read_csv("{}/stm/{}/LDAbeta_false/time_covariate/topics{}/party_prevalence_content/sage_marginal.csv".format(outputdirectory, period, topics), sep=",")
            sage_topickappa = pd.read_csv("{}/stm/{}/LDAbeta_false/time_covariate/topics{}/party_prevalence_content/sage_topickappa.csv".format(outputdirectory, period, topics), sep=",")
            sage_covbetas = pd.read_csv("{}/stm/{}/LDAbeta_false/time_covariate/topics{}/party_prevalence_content/sage_covbetas.csv".format(outputdirectory, period, topics), sep=",")
        else:
            stm_model_out = pd.read_csv("{}/stm/{}/LDAbeta_false/topics{}/party_prevalence_content/modelout_dataframe.csv".format(outputdirectory, period, topics), sep="\t")
            # load graph LASSO-based topic (positive) correlations
            topiccorr = pd.read_csv("{}/stm/{}/LDAbeta_false/topics{}/party_prevalence_content/topicCorr_posAdj.csv".format(outputdirectory, period, topics), sep=",")
            # topic word lists, based on different criteria (frex, score, lift, prob)
            sage_marginal = pd.read_csv("{}/stm/{}/LDAbeta_false/topics{}/party_prevalence_content/sage_marginal.csv".format(outputdirectory, period, topics), sep=",")
            sage_topickappa = pd.read_csv("{}/stm/{}/LDAbeta_false/topics{}/party_prevalence_content/sage_topickappa.csv".format(outputdirectory, period, topics), sep=",")
            sage_covbetas = pd.read_csv("{}/stm/{}/LDAbeta_false/topics{}/party_prevalence_content/sage_covbetas.csv".format(outputdirectory, period, topics), sep=",")

        # build correlation clusters
        clusters = dict()
        ll = 1
        topiccorr = topiccorr.values
        for p in range(topiccorr.shape[0]):
            if np.sum(topiccorr[p,:]) == 0:
                continue
            # init cluster
            clustermembs = [p+1]
            # cluster members - the nodes and their neighboorhoods
            members_idx = np.argwhere(topiccorr[p,:]).flatten().tolist()
            for pp in members_idx:
                if np.sum(topiccorr[pp,:]) == 0:
                    if pp+1 not in clustermembs:
                        clustermembs.append(pp+1)
                    continue
                if pp+1 not in clustermembs:
                    clustermembs.append(pp+1)
                members_idx_pp = np.argwhere(topiccorr[pp,:])
                for ppp in members_idx_pp.flatten().tolist():
                    if ppp not in members_idx:
                        members_idx.append(ppp)
            clustermembs = sorted(clustermembs)
            if not clustermembs in clusters.values():
                clusters[ll] = clustermembs
                # print(ll, clustermembs)
                ll += 1   
        for p in range(topiccorr.shape[0]):
            if p+1 in flatten([*clusters.values()]):
                continue
            clusters[ll] = [p+1]
            ll += 1
            
        results_out_period = "{}/{}/".format(results_out, period)  
        pathlib.Path(results_out_period).mkdir(parents=True, exist_ok=True)
        # keep all docs per topic, sorted by proportion of topic, big to low
        for jj in range(1,topics+1,1):
            topic_df_out = stm_model_out
            for jjj in range(1,topics+1,1):
                if jj != jjj:
                    topic_df_out = topic_df_out.drop(columns=["Topic{}".format(jjj)]).reset_index(drop=True)
            sorted_df = topic_df_out.sort_values(by="Topic{}".format(jj), ascending=False).reset_index(drop=True)
            # print(sorted_df)
            sorted_df.to_csv("{}/topic{}.csv".format(results_out_period, jj))

        ######### topic labelling #########
            
        # first apply clustering and then percentile discovery
        doc_topic_proportion_medians = []
        for l in clusters.keys():
            clusterdocs = []
            for ll in clusters[l]:
                clusterdocs.append(stm_model_out["Topic{}".format(ll)])
            # take median topic proportion over all docs
            doc_topic_proportion_medians.append(np.percentile(clusterdocs, 50, method="higher"))
        
        # sorted_median_idx = sorted(range(len(doc_topic_proportion_medians)), key=lambda k: doc_topic_proportion_medians[k])        
        # keep **supertopics** (clusters keys) whose proportion in the documents is in the 6th decile of all supertopic median proportions
        dominant_topics = np.argwhere(doc_topic_proportion_medians >= np.percentile(doc_topic_proportion_medians, 60, method="higher")).flatten()        

        ######################
        # dominant_topics = np.argwhere(doc_topic_proportion_medians >= np.percentile(doc_topic_proportion_medians, 50, method="higher")).flatten()        
        ######################

        # print(np.asarray(doc_topic_proportion_medians)[dominant_topics.flatten()])
        dominant_topics = [jjj+1 for jjj in dominant_topics]        

        # keep docs with proportion > 0.8 per topic: their summaries, parties, speechID, speaker, speech dates, speech url
        # in one csv per period: for each topic: summary label, median party percentage among all topic documents, sort in order of topic proportion in that period
        topic_labelling = {"STMTopics": [], "LASSOTopics":[], "label": [], "sumlabel": [], 
                           "median-dem-documentproportion": [], 
                           "median-rep-documentproportion": [], 
                           "median-proportion-alltopicdocs": [], 
                           "topicWords": []}
        
        for jj in dominant_topics:            
            topic_labelling["STMTopics"].append(clusters[jj])
            topic_labelling["LASSOTopics"].append(jj)
            clusterdocs = None
            for ll in clusters[jj]:
                topicdocs = pd.read_csv("{}/topic{}.csv".format(results_out_period, ll), index_col=0)
                topicdocs = topicdocs.rename(columns={"Topic{}".format(ll): "Topic"})
                if clusterdocs is None:
                    clusterdocs = topicdocs
                else:
                    clusterdocs = pd.concat([clusterdocs, topicdocs])
            # docs to consider for the labelling
            topdocs = clusterdocs.loc[clusterdocs["Topic"] > 0.8]            
            if len(topdocs) == 0:
                # else take the document with the highest topic proportion
                clusterdocs = clusterdocs.sort_values(by="Topic", ascending=False).reset_index(drop=True)
                topdocs = clusterdocs.iloc[0]

                ##########################
                clean_sentence = topdocs["speeches.summary"]
                tokenised_sentence = texttokeniser.tokenise(clean_sentence, valid_chars=string.printable, 
                                                        language="english", stem=kwargs_cfg["stemming"])
                postprocessed_sentence_tokens = texttokeniser.postprocess_tokens(tokenised_sentence, 
                                                        valid_chars=string.printable, stem=kwargs_cfg["stemming"], 
                                                        language="english", clean_token=False) # summaries have not been postprocessed
                sumlabel = ",".join(postprocessed_sentence_tokens)
                topic_labelling["sumlabel"].append(sumlabel)
                ##########################
                
                topic_labelling["label"].append(topdocs["speeches.summary"])
            else:
                
                ##########################
                clean_sentence = ",".join(np.unique(topdocs["speeches.summary"].values.tolist()).tolist())
                tokenised_sentence = texttokeniser.tokenise(clean_sentence, valid_chars=string.printable, 
                                                        language="english", stem=kwargs_cfg["stemming"])
                postprocessed_sentence_tokens = texttokeniser.postprocess_tokens(tokenised_sentence, 
                                                        valid_chars=string.printable, stem=kwargs_cfg["stemming"], 
                                                        language="english", clean_token=False) # summaries have not been postprocessed
                sumlabel = ",".join(np.unique(postprocessed_sentence_tokens))
                topic_labelling["sumlabel"].append(sumlabel)
                ##########################

                topic_labelling["label"].append(" - ".join(np.unique(topdocs["speeches.summary"].values.tolist()).tolist()))
                
            # collect all topic words, including the summary words, and keep those that are in the dictionary            
            alltopicWords = postprocessed_sentence_tokens
            for ll in clusters[jj]:
                alltopicWords.extend(sage_topickappa.iloc[ll-1].dropna().values.tolist()) # note: stm topics are stored with +1 in clusters dict
                alltopicWords.extend(sage_marginal.iloc[ll-1].dropna().values.tolist())                
                alltopicWords.extend(sage_covbetas.iloc[ll-1].dropna().values.tolist())
            alltopicWords = np.unique(alltopicWords).tolist()
            alltopicWords = [ww for ww in alltopicWords if ww in dictionary.wordsearcher]            
            topic_labelling["topicWords"].append(alltopicWords)
            
            # print(topic_labelling["label"])
            dem_docs = clusterdocs[clusterdocs["speeches.party"] == "Democrats"]
            topic_labelling["median-dem-documentproportion"].append(np.percentile(dem_docs["Topic"].values, 50, method="higher"))
            rep_docs = clusterdocs[clusterdocs["speeches.party"] == "Republicans"]
            topic_labelling["median-rep-documentproportion"].append(np.percentile(rep_docs["Topic"].values, 50, method="higher"))
            topic_labelling["median-proportion-alltopicdocs"].append(np.percentile(clusterdocs["Topic"].values, 50, method="higher"))

            dateperiod = datetime.strptime(period, '%b%Y')
            _, monthdays = calendar.monthrange(dateperiod.year, dateperiod.month) 
            dateperiodendmonth = datetime.strptime("{}-{}-{}".format(monthdays, dateperiod.month, dateperiod.year), '%d-%m-%Y')
            topic_labelling_long["time"].append(dateperiodendmonth)
            topic_labelling_long["period"].append(period)
            topic_labelling_long["STMTopics"].append(clusters[jj]) 
            topic_labelling_long["LASSOTopics"].append(jj)
            topic_labelling_long["summary"].append(topic_labelling["label"][-1])
            topic_labelling_long["median"].append(topic_labelling["median-dem-documentproportion"][-1])
            topic_labelling_long["party"].append("Democrats")

            topic_labelling_long["time"].append(dateperiodendmonth)
            topic_labelling_long["period"].append(period)
            topic_labelling_long["STMTopics"].append(clusters[jj]) 
            topic_labelling_long["LASSOTopics"].append(jj)
            topic_labelling_long["summary"].append(topic_labelling["label"][-1])
            topic_labelling_long["median"].append(topic_labelling["median-rep-documentproportion"][-1])
            topic_labelling_long["party"].append("Republicans")

            topic_labelling_long["time"].append(dateperiodendmonth)
            topic_labelling_long["period"].append(period)
            topic_labelling_long["STMTopics"].append(clusters[jj]) 
            topic_labelling_long["LASSOTopics"].append(jj)
            topic_labelling_long["summary"].append(topic_labelling["label"][-1])
            topic_labelling_long["median"].append(topic_labelling["median-proportion-alltopicdocs"][-1])
            topic_labelling_long["party"].append("all")

        outlabelling = pd.DataFrame.from_dict(topic_labelling)
        outlabelling = outlabelling.sort_values(by="median-proportion-alltopicdocs", ascending=False).reset_index(drop=True)
        outlabelling.to_csv("{}/topiclabelling.csv".format(results_out_period), index=False)  
        
        # print(topic_labelling["sumlabel"][-1].split(","))

    outlabellinglong = pd.DataFrame.from_dict(topic_labelling_long)
    outlabellinglong = outlabellinglong.sort_values(by="time", ascending=False).reset_index(drop=True)
    outlabellinglong.to_csv("{}/topiclabellinglong.csv".format(results_out), index=False)  

       
            