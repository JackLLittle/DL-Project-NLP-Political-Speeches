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
from us2020data.stm.utils import stopwords_politicalscience, \
                                    dataset_descr_per_source, flatten, \
                                        fix_plot_layout_and_save
from us2020data.stm.texttokeniser import TextTokeniser
from us2020data.stm.dictionary import Dictionary
from plotly import graph_objects as go
import string
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer


if __name__ == "__main__":

    cwd = pathlib.Path.cwd()
    kwargs_cfg = dict()    
    kwargs_cfg["run_parent_folder"] = "{}/".format(cwd)    
    kwargs_cfg["stemming"] = True # So that we do not do it within R's stm package
    DIR_in = "{}us2020data/stm/postprocessed4stm/".format(kwargs_cfg["run_parent_folder"])    
    dictionary_topic = "POTUS2020"
    outputdirectory = "{}us2020data/stm/postprocessed4stm/{}/".format(kwargs_cfg["run_parent_folder"], dictionary_topic)
    pathlib.Path(outputdirectory).mkdir(parents=True, exist_ok=True)        
    potusnames = ["Donald Trump", "Joe Biden", "Mike Pence", "Kamala Harris"]
    potuses_terms = {"Donald Trump": {"term": ["2017-2021"], "party":"Republicans"},
                     "Mike Pence": {"term": ["2017-2021"], "party":"Republicans"},
                     "Joe Biden": {"term": ["2021-Incumbent"], "party":"Democrats"},
                     "Kamala Harris": {"term": ["2021-Incumbent"], "party":"Democrats"}}
    dataset = {"POTUS": [], "Party": [], "#PostprocessedTokens": []}    

    dictionary = Dictionary(topic="USSpeeches_election2020_STM",
                            workspace_in_dir="{}us2020data/stm/lexica/".format(kwargs_cfg["run_parent_folder"]),                             
                            stem=kwargs_cfg["stemming"]) 
    stopwords = stopwords_politicalscience("{}us2020data/stm/lexica/".format(kwargs_cfg["run_parent_folder"]))
    stopwords.extend(["thank", "kamala", "harris", "kamala harris", "mike", 
                       "mike pence", "pence", "donald", "donald trump", 
                       "trump", "joe", "biden", "joe biden", "hi", "hello", 
                       "well", "america", "president", "vice president"])  
    if kwargs_cfg["stemming"]:
        stemmer = SnowballStemmer("english")
        stopwords = np.unique([stemmer.stem(i) for i in stopwords]).tolist()
    texttokeniser = TextTokeniser(dictionary=dictionary, stem=kwargs_cfg["stemming"], 
                                stopwords=stopwords, remove_punctuation=True, 
                                remove_oov=True, remove_numbers=True)
    
    def apply_tokenise(x) : return texttokeniser.tokenise(x, valid_chars=string.printable, 
                                                    language="english", 
                                                    stem=kwargs_cfg["stemming"])
    def apply_postprocess(x) : return texttokeniser.postprocess_tokens(x, 
                                                        valid_chars=string.printable, 
                                                        stem=kwargs_cfg["stemming"], 
                                                        language="english", clean_token=True)
    fig = go.Figure()
    spotted_tokens = []
    for potus in potusnames:        
        dataset["POTUS"].append(potus)
        dataset["Party"].append(potuses_terms[potus]["party"])
        df_potus = pd.read_csv("{}/{}/cleandataset_sentences.tsv".format(DIR_in, potus.replace(" ", "")), sep="\t")
        assert(np.all(df_potus.Date==sorted(df_potus.Date)))
        df_potus = df_potus[df_potus.Labels=="speaker"].reset_index(drop=True)
        
        print(potus)        
        postprocessed_data_per_speech = {"SpeechID": [], "Date": [], "Title": [], "PostprocessedTokens": [], "SpeechURL": [], "jointtokens": [], "RawText": []}
        potus_postprocessed = None        
        potus_postprocessedtokens = 0                    
        for speech_id, group in df_potus.groupby("SpeechID"):            
            tokenised_sentences = group.Sentences.apply(apply_tokenise)            
            group["TokenisedSentences"] = tokenised_sentences
            # clean_token=True since we precede the call with texttokeniser.tokenise
            postprocessed_sentence_tokens = group.TokenisedSentences.apply(apply_postprocess)
            group["PostprocessedTokens"] = postprocessed_sentence_tokens
            group = group.drop(["Tokens", "SentenceEnd"], axis=1)            
            postprocessed_data_per_speech["SpeechID"].append(speech_id)
            
            date = group["Date"].values[0]
            sptitle = group["SpeechTitle"].values[0]
            spurl = group["SpeechURL"].values[0]
            
            postprocessed_data_per_speech["Date"].append(date)
            postprocessed_data_per_speech["Title"].append(sptitle)
            postprocessed_data_per_speech["SpeechURL"].append(spurl)
            postprocessed_data_per_speech["PostprocessedTokens"].append(flatten(group.PostprocessedTokens.values.tolist()))
            postprocessed_data_per_speech["jointtokens"].append(" ".join(flatten(group.PostprocessedTokens.values.tolist())))
            postprocessed_data_per_speech["RawText"].append(" ".join(group.RawSents.values.tolist()))
            spotted_tokens.extend(np.unique(flatten(group.PostprocessedTokens.values.tolist())).tolist())

            if potus_postprocessed is None:
                potus_postprocessed = group
            else:
                potus_postprocessed = pd.concat([potus_postprocessed, group], ignore_index=True)            
            
            potus_postprocessedtokens += group["PostprocessedTokens"].apply(len).sum()
        pathlib.Path("{}/{}/".format(outputdirectory, potus.replace(" ", ""))).mkdir(parents=True, exist_ok=True)        
        potus_postprocessed = potus_postprocessed.sort_values(["Date"], ascending=True).reset_index(drop=True)
        potus_postprocessed.to_csv("{}/{}/postprocesseddataset_stem_{}.tsv".format(outputdirectory, potus.replace(" ", ""), kwargs_cfg["stemming"]), index=False, sep="\t")
        potus_postprocessed_perspeech_df = pd.DataFrame.from_dict(postprocessed_data_per_speech)
        potus_postprocessed_perspeech_df = potus_postprocessed_perspeech_df.sort_values(["Date"], ascending=True).reset_index(drop=True)

        # deduplication over all data per speaker - 95% overlap in content
        potus_postprocessed_perspeech_df_dup = np.zeros((len(potus_postprocessed_perspeech_df),))
        for i, row in potus_postprocessed_perspeech_df.iterrows():
            for j, row2 in potus_postprocessed_perspeech_df.iterrows():
                if i<=j:
                    continue
                intersec = set(row["PostprocessedTokens"]).intersection(set(row2["PostprocessedTokens"]))
                if len(intersec) >= 0.95*len(set(row["PostprocessedTokens"])):
                    if ("millercenter" in row.SpeechURL and "votesmart" in row2.SpeechURL):
                        potus_postprocessed_perspeech_df_dup[j] = 1 #drop                        
                    elif ("millercenter" in row2.SpeechURL and "votesmart" in row.SpeechURL):
                        potus_postprocessed_perspeech_df_dup[i] = 1 #drop                        
                    else:
                        # keep both
                        continue
                else:
                    continue
        # after removing duplicate speeches
        potus_postprocessed_perspeech_df = potus_postprocessed_perspeech_df[potus_postprocessed_perspeech_df_dup < 1]
        potus_postprocessed_perspeech_df = potus_postprocessed_perspeech_df.sort_values(["Date"], ascending=True).reset_index(drop=True)
        potus_postprocessed_perspeech_df.to_csv("{}/{}/postprocesseddataset_perspeech_stem_{}.tsv".format(outputdirectory, potus.replace(" ", ""), kwargs_cfg["stemming"]), index=False, sep="\t")

        dataset_descr_per_source(potus_postprocessed_perspeech_df, potus.replace(" ", ""))
        dataset["#PostprocessedTokens"].append(potus_postprocessed_perspeech_df.PostprocessedTokens.apply(len).sum())
        if potus == "Joe Biden":
            fig.add_trace(go.Bar(x=["{}".format(potus)], y=[potus_postprocessed_perspeech_df.PostprocessedTokens.apply(len).sum()], name='Democrats', marker_color='blue'))
        elif potus == "Donald Trump":
            fig.add_trace(go.Bar(x=["{}".format(potus)], y=[potus_postprocessed_perspeech_df.PostprocessedTokens.apply(len).sum()], name='Republicans', marker_color='red'))
        else:
            if potuses_terms[potus]["party"] == "Democrats":
                fig.add_trace(go.Bar(x=["{}".format(potus)], y=[potus_postprocessed_perspeech_df.PostprocessedTokens.apply(len).sum()], marker_color='blue', showlegend=False))
            else:
                fig.add_trace(go.Bar(x=["{}".format(potus)], y=[potus_postprocessed_perspeech_df.PostprocessedTokens.apply(len).sum()], marker_color='red', showlegend=False))
    
    datasetdf = pd.DataFrame.from_dict(dataset)
    datasetdf.to_csv("{}/postprocess_datasummary_{}_stem_{}.csv".format(outputdirectory, dictionary_topic, kwargs_cfg["stemming"]), index=False)
    # dictionary tokens that are in the dataset
    spotted_tokens_df = pd.DataFrame.from_dict({"words": list(set(spotted_tokens))})
    spotted_tokens_df.to_csv("{}/spottedtokens_{}_stem_{}.csv".format(outputdirectory, dictionary_topic, kwargs_cfg["stemming"]), index=False)
    fix_plot_layout_and_save(fig, "{}/postprocess_datasummary_{}_stem_{}.html".format(outputdirectory, dictionary_topic, kwargs_cfg["stemming"]), 
                             xaxis_title="(Vice-)Presidential candidates", yaxis_title="#Postprocessed Tokens", 
                             title="", showgrid=False, showlegend=True, print_png=True)
    
