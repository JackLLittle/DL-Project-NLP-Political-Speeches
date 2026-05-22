################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

import numpy as np
import pandas as pd
import pathlib
from us2020data.stm.dictionary import Dictionary
from us2020data.stm.utils import flatten, get_counts
from us2020data.src.utils import unicode_cleanup, apply_unicode_normalisation, clean_char_repetitions
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import pyreadr

if __name__ == "__main__":

    cwd = pathlib.Path.cwd()
    kwargs_cfg = dict()    
    kwargs_cfg["run_parent_folder"] = "{}/".format(cwd)    
    kwargs_cfg["stemming"] = True
    DIR_in = "{}us2020data/stm/postprocessed4stm/".format(kwargs_cfg["run_parent_folder"])    
    dictionary_topic = "POTUS2020"
    outputdirectory = "{}us2020data/stm/postprocessed4stm/{}/".format(kwargs_cfg["run_parent_folder"], dictionary_topic)
    potusnames = ["Donald Trump", "Joe Biden", "Mike Pence", "Kamala Harris"]
    potuses_terms = {"Donald Trump": {"term": ["2017-2021"], "party":"Republicans"},
                     "Mike Pence": {"term": ["2017-2021"], "party":"Republicans"},
                     "Joe Biden": {"term": ["2021-Incumbent"], "party":"Democrats"},
                     "Kamala Harris": {"term": ["2021-Incumbent"], "party":"Democrats"}}
    
    dictionary = Dictionary(topic="USSpeeches_election2020_STM",
                            workspace_in_dir="{}us2020data/stm/lexica/".format(kwargs_cfg["run_parent_folder"]),                             
                            stem=kwargs_cfg["stemming"])
    alldata_df = None
    for potus in potusnames: 
        df_potus = pd.read_csv("{}/{}/postprocesseddataset_perspeech_stem_{}.tsv".format(outputdirectory, potus.replace(" ", ""), kwargs_cfg["stemming"]), sep="\t")
        print("{}/{}/postprocesseddataset_perspeech_stem_{}.tsv".format(outputdirectory, potus.replace(" ", ""), kwargs_cfg["stemming"]))
        if potuses_terms[potus]["party"] == "Republicans":            
            df_potus["party"] = ["Republicans"]*len(df_potus)
        else:            
            df_potus["party"] = ["Democrats"]*len(df_potus)

        summaries = []
        speechids = []
        for ii, row in df_potus.iterrows():            
            if row.SpeechID[0:2] == "ME":
                df_potus_inittranscript = pd.read_csv("{}us2020data/data_clean/medium/{}/cleantext_{}.tsv".format(kwargs_cfg["run_parent_folder"], potus.replace(" ", ""), potus.replace(" ", "")), sep="\t")
            elif row.SpeechID[0:2] == "MC":
                df_potus_inittranscript = pd.read_csv("{}us2020data/data_clean/millercenter/{}/cleantext_{}.tsv".format(kwargs_cfg["run_parent_folder"], potus.replace(" ", ""), potus.replace(" ", "")), sep="\t")
            elif row.SpeechID[0:2] == "VS":
                df_potus_inittranscript = pd.read_csv("{}us2020data/data_clean/votesmart/{}/cleantext_{}.tsv".format(kwargs_cfg["run_parent_folder"], potus.replace(" ", ""), potus.replace(" ", "")), sep="\t")
            elif row.SpeechID[0:5] == "CSPAN":
                df_potus_inittranscript = pd.read_csv("{}us2020data/data_clean/cspan/{}/cleantext_{}.tsv".format(kwargs_cfg["run_parent_folder"], potus.replace(" ", ""), potus.replace(" ", "")), sep="\t")
            else:
                raise NotImplementedError
            summary = df_potus_inittranscript.loc[df_potus_inittranscript.SpeechID==row.SpeechID, "Summary"]            
            if len(summary) == 0 or not isinstance(summary.values[0], str) or summary.values[0]=="EmptySummary":
                summary = df_potus_inittranscript.loc[df_potus_inittranscript.SpeechID==row.SpeechID, "SpeechTitle"]            
            
            summary = summary.values[0].replace(",", " ").replace('"', " ").replace("\n", " ")
            summary = apply_unicode_normalisation(summary, "NFC")
            summary = clean_char_repetitions(summary)
            summary = unicode_cleanup(summary)
            summary = summary.strip()
            summaries.append(summary)
            speechids.append(row.SpeechID)
                    
        # as extra covariate: 
        # countdown to May 7, 2019 (Heartbeat Bill)
        # 0 until May 30, 2019 (tariffs on goods from Mexico/immigration)
        # 1 until Dec 10, 2019 (Trump accused)
        # 2 until January 19, 2020 (MeToo) 
        # 3 until Mar 3, 2020 (Super Tuesday)
        # 4 until Apr 5, 2020 (1st lockdown) 
        # 5 until May 1st 2020 (BLM demonstrations)
        # 6 until August 11, 2020 (official announcement of Harris as running mate)
        # 7 until November 7, 2020 (Biden declared winner, Trump starts legal battle to overturn election result)
        # 8 until January 6, 2021 (nomination of Biden, assault of Capitol)
        # 9 afterwards        
        df_potus["campaigndaysend"] = [(datetime.strptime(i, '%Y-%m-%d') - datetime.strptime("31-01-2021", '%d-%m-%Y')).days for i in df_potus["Date"].values.tolist()]                
        df_potus["campaigndays"] = [(datetime.strptime(i, '%Y-%m-%d') - datetime.strptime("07-05-2019", '%d-%m-%Y')).days for i in df_potus["Date"].values.tolist()]                
        df_potus["Date"] = df_potus["Date"].apply(pd.Timestamp)
        df_potus.loc[df_potus["Date"]>=pd.Timestamp(datetime.strptime("07-05-2019", '%d-%m-%Y')), "campaigndays"] = 0
        df_potus.loc[df_potus["Date"]>=pd.Timestamp(datetime.strptime("30-05-2019", '%d-%m-%Y')), "campaigndays"] = 1
        df_potus.loc[df_potus["Date"]>=pd.Timestamp(datetime.strptime("10-12-2019", '%d-%m-%Y')), "campaigndays"] = 2
        df_potus.loc[df_potus["Date"]>=pd.Timestamp(datetime.strptime("19-01-2020", '%d-%m-%Y')), "campaigndays"] = 3
        df_potus.loc[df_potus["Date"]>=pd.Timestamp(datetime.strptime("03-03-2020", '%d-%m-%Y')), "campaigndays"] = 4
        df_potus.loc[df_potus["Date"]>=pd.Timestamp(datetime.strptime("05-04-2020", '%d-%m-%Y')), "campaigndays"] = 5
        df_potus.loc[df_potus["Date"]>=pd.Timestamp(datetime.strptime("01-05-2020", '%d-%m-%Y')), "campaigndays"] = 6
        df_potus.loc[df_potus["Date"]>=pd.Timestamp(datetime.strptime("11-08-2020", '%d-%m-%Y')), "campaigndays"] = 7
        df_potus.loc[df_potus["Date"]>=pd.Timestamp(datetime.strptime("07-11-2020", '%d-%m-%Y')), "campaigndays"] = 8
        df_potus.loc[df_potus["Date"]>=pd.Timestamp(datetime.strptime("06-01-2021", '%d-%m-%Y')), "campaigndays"] = 9
        df_potus["summary"] = summaries
        df_potus["SpeechID"] = speechids
        df_potus["POTUS"] = [potus]*len(summaries)
        df_potus["shorts"] = [" ".join(eval(i)[:100]) for i in df_potus["PostprocessedTokens"].values.tolist()]        
        
        if alldata_df is None:
            alldata_df = df_potus
        else:
            alldata_df = pd.concat([alldata_df, df_potus], ignore_index=True)     
        
    alldata_df = alldata_df.sort_values(['Date'], ascending=True).reset_index(drop=True) 
    alldata_df.Date = alldata_df.Date.apply(pd.Timestamp)

    start_date = datetime.strptime("01-01-2019", '%d-%m-%Y')
    end_date = datetime.strptime("31-01-2021", '%d-%m-%Y')
    current_date = start_date
    # split into windows of time and construct document-term matrices
    while current_date <= end_date:
        
        last_day_of_month = datetime(current_date.year, current_date.month, 1) + timedelta(days=32)
        current_date = last_day_of_month.replace(day=1)
        
        lower_end = current_date-relativedelta(months=3)
        upper_end = current_date.strftime('%Y-%m-%d')
        slicedata =  alldata_df[(alldata_df["Date"]>=lower_end) & (alldata_df["Date"]<upper_end)].reset_index(drop=True)        
        local_dict = np.unique(flatten([eval(i) for i in slicedata.PostprocessedTokens.values.tolist()])).tolist()

        all_dtm = []        
        droprows = []
        for i, row in slicedata.iterrows():            
            counts_sentence_tokens = get_counts(dictionary, eval(row.PostprocessedTokens))            
            token_counts = counts_sentence_tokens.data
            if token_counts.sum() == 0:
                droprows.append(i)
                continue
            r, c = counts_sentence_tokens.nonzero()
            token_idx = c
            tokens = [dictionary.wordlist[ti] for ti in token_idx]
            tokens_idx_in_local_dict = [local_dict.index(t) for t in tokens]
            assert tokens == [local_dict[t] for t in tokens_idx_in_local_dict]
            
            cnts = np.zeros((1,len(local_dict)))
            cnts[0,np.asarray(tokens_idx_in_local_dict)] = token_counts
            all_dtm.append(cnts)
        
        all_dtm = pd.DataFrame(np.vstack(all_dtm))
        
        local_dict = pd.DataFrame.from_dict({"vocab": local_dict})
        if len(droprows) > 0:
            slicedata = slicedata.drop(droprows)
            slicedata = slicedata.reset_index(drop=True)        
        print(slicedata)
        pathlib.Path("{}/stm/{}/".format(outputdirectory, (current_date-relativedelta(months=1)).strftime('%b%Y').lower())).mkdir(parents=True, exist_ok=True)
        # save dtm for stm        
        pyreadr.write_rdata("{}/stm/{}/data_dtm.RData".format(outputdirectory, (current_date-relativedelta(months=1)).strftime('%b%Y').lower()), all_dtm, df_name="stmdocuments")        
        pyreadr.write_rdata("{}/stm/{}/vocab.RData".format(outputdirectory, (current_date-relativedelta(months=1)).strftime('%b%Y').lower()), local_dict, df_name="vocab")        
        slicedata.to_csv("{}/stm/{}/data.csv".format(outputdirectory, (current_date-relativedelta(months=1)).strftime('%b%Y').lower()), index=False)
            

       
            