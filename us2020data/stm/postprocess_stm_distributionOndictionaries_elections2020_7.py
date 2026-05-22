################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

import pandas as pd
import pathlib
from us2020data.stm.utils import flatten, stopwords_politicalscience
from us2020data.stm.dictionary import Dictionary
from us2020data.stm.texttokeniser import TextTokeniser


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
    
    # load individual topic dictionaries
    DIR_out = "{}/us2020data/stm/lexica/".format(cwd) 
    # politics dictionary topics: "US Politics", "Epidemics", "Politics and government", "Media", "Religion"
    d = Dictionary(topic="uspresidentialspeeches_STM",
                    workspace_in_dir="{}us2020data/stm/lexica/".format(kwargs_cfg["run_parent_folder"]),
                    workspace_out_dir="{}us2020data/stm/lexica/".format(kwargs_cfg["run_parent_folder"]),
                    save=False, 
                    save_trie=False, 
                    stem=kwargs_cfg["stemming"])
    politics = d.wordlist
    concisepolitics = pd.read_csv("{}/concisepolitics_oxford.csv".format(DIR_out), index_col=0)
    politics.extend(concisepolitics.values.tolist())
    politics = flatten(politics)
        
    contemporaryhistory = pd.read_csv("{}/contemporaryhistory_oxford.csv".format(DIR_out), index_col=0).values.tolist()
    contemporaryhistory = flatten(contemporaryhistory)
    
    immigration1 = pd.read_csv("{}/immigration_glossary.csv".format(DIR_out), index_col=0)
    immigration2 = pd.read_csv("{}/immigration_uscis.csv".format(DIR_out), index_col=0)
    immigration = immigration1.values.tolist()
    immigration.extend(immigration2.values.tolist())
    immigration = flatten(immigration)
    
    supremecourt = pd.read_csv("{}/supremecourt_oxford.csv".format(DIR_out), index_col=0)
    senate = pd.read_csv("{}/senatevocab.csv".format(DIR_out), index_col=0)
    presidentialparlance = pd.read_csv("{}/presidential_parlance.csv".format(DIR_out))["Unnamed: 0"]        
    presidentialparlance = presidentialparlance.to_frame().rename(columns={"Unnamed: 0":"words"})
    uspolitics = supremecourt.values.tolist()
    uspolitics.extend(senate.values.tolist())
    uspolitics.extend(presidentialparlance.values.tolist())
    uspolitics = flatten(uspolitics)

    economics = pd.read_csv("{}/economics_oxford.csv".format(DIR_out), index_col=0)
    gender = pd.read_csv("{}/gender_oxford.csv".format(DIR_out), index_col=0)
    sociology = pd.read_csv("{}/sociology_oxford.csv".format(DIR_out), index_col=0)
    economy_and_society = economics.values.tolist()
    economy_and_society.extend(gender.values.tolist())
    economy_and_society.extend(sociology.values.tolist())
    economy_and_society = flatten(economy_and_society)
   
    if timecovariate:
        stm_out = pd.read_csv("{}/stm/selected_models_with_time_covariate.csv".format(outputdirectory))
    else:
        stm_out = pd.read_csv("{}/stm/selected_models.csv".format(outputdirectory))
    results_out = "{}/stm_analysis/timecovariate{}/".format(outputdirectory, timecovariate)
    pathlib.Path(results_out).mkdir(parents=True, exist_ok=True)
    for i, row in stm_out.iterrows(): 
        period = row["times"]
        topics = row["ks"]

        results_out_period = "{}/{}/".format(results_out, period)          
        pathlib.Path(results_out_period).mkdir(parents=True, exist_ok=True)
        
        stm_analysis = pd.read_csv("{}/topiclabelling.csv".format(results_out_period), sep=",")  
        distributionOndictionaries = {"LASSOTopics":[], "politics": [], 
                                                        "contemporaryhistory": [], 
                                                        "immigration": [], 
                                                        "uspolitics": [],
                                                        "economy_and_society": []}
        for j, jrow in stm_analysis.iterrows():                                        
            alltopicWords = eval(jrow["topicWords"])
            totalwords = len(alltopicWords)
            distributionOndictionaries["LASSOTopics"].append(jrow["LASSOTopics"])
            distributionOndictionaries["politics"].append(len(set(alltopicWords).intersection(politics))/totalwords)
            distributionOndictionaries["contemporaryhistory"].append(len(set(alltopicWords).intersection(contemporaryhistory))/totalwords)
            distributionOndictionaries["immigration"].append(len(set(alltopicWords).intersection(immigration))/totalwords)
            distributionOndictionaries["uspolitics"].append(len(set(alltopicWords).intersection(uspolitics))/totalwords)
            distributionOndictionaries["economy_and_society"].append(len(set(alltopicWords).intersection(economy_and_society))/totalwords)            
            
           
        outlabelling = pd.DataFrame.from_dict(distributionOndictionaries)        
        outlabelling.to_csv("{}/distributionsOndictionaries.csv".format(results_out_period), index=False)  
        

  
       
            