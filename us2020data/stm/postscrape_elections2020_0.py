################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

from __future__ import print_function
import pandas as pd
from pathlib import Path
import regex
import pathlib
from us2020data.stm.textsentenciser import TextSentenciser
from plotly import graph_objects as go
from us2020data.stm.utils import fix_plot_layout_and_save

exclude_words = ['Applause', 'Laughter', 'Inaudible', 'Applause.', 'Laughter.', 'Inaudible.','applause', 
                 'inaudible', 'laughter', 'applause.', 'inaudible.', 'laughter.', 'Laughs.', 'Laughs', 'laughs.', 'laughs']
exclude_pattern = "|".join(map(regex.escape, exclude_words))
all_but_audience = regex.compile(r'\((?!(?:' + exclude_pattern + ')\))([^()]*(?:(?R)[^()]*)*)\)')
proper_names_with_middle = regex.compile(r'\b([A-Z][a-z]+) ([A-Z])\.')

def clean_parentheses(text):

    text = regex.sub(all_but_audience, "", text)
    text = regex.sub(r'\s+', ' ', text)
    
    return text

if __name__ == "__main__":

    cwd = pathlib.Path.cwd()
    def replace_escapeapostr(x) : return regex.sub(r"\'s", "", x)
    def remove_name_dot(x) : return regex.sub(r'\s+', ' ', regex.sub(proper_names_with_middle, r'\1', x))
    DIR_in = "{}/us2020data/data_clean/".format(cwd)    
    outputdirectory = "{}/us2020data/stm/postprocessed4stm/".format(cwd)
    Path(outputdirectory).mkdir(parents=True, exist_ok=True)
    potusnames = ["Donald Trump", "Joe Biden", "Mike Pence", "Kamala Harris"]
    potuses_terms = {"Donald Trump": {"term": ["2017-2021"], "party":"Republicans"},
                     "Mike Pence": {"term": ["2017-2021"], "party":"Republicans"}, 
                     "Kamala Harris": {"term": ["2021-Incumbent"], "party":"Democrats"},
                     "Joe Biden": {"term": ["2021-Incumbent"], "party":"Democrats"}}
    dataset = {"POTUS": [], "Term": [], "Party": [], "#Speeches": [], "#Sentences": [], 
               "#Tokens": [], "#RawSpaceSeparatedTokens": [], "#CleanSpaceSeparatedTokens": []}    
        
    textsenten = TextSentenciser(language="english")    
    fig = go.Figure()
    figtok = go.Figure()
    for potus in potusnames:
        
        dataset["POTUS"].append(potus)
        dataset["Term"].append(potuses_terms[potus]["term"])
        dataset["Party"].append(potuses_terms[potus]["party"])
        potus_all_sents = None
        potus_sents = 0
        # tokens after applying the tokeniser
        potus_tokens = 0
        # simple whitespace splitting on raw text
        potus_tokens_raw = 0
        # simple whitespace splitting on text after data curation
        potus_tokens_clean = 0
        potus_speeches = 0     
        df_potus = None
    
        if potus == "Donald Trump" or potus == "Joe Biden":
            df_potus = pd.read_csv("{}/millercenter/{}/cleantext_{}.tsv".format(DIR_in, potus.replace(" ", ""), potus.replace(" ", "")), sep="\t")           
            df_potus["CleanText"] = df_potus.CleanText.apply(remove_name_dot)
            df_potus["CleanText"] = df_potus.CleanText.apply(clean_parentheses)

            all_sentdf = None
            for i, row in df_potus.iterrows():
                speech_id = row["SpeechID"]
                all_sentdf = textsenten.extract_sentences(row["CleanText"], speech_id=speech_id)            
                all_sentdf["RawSents"] = all_sentdf["Sentences"].copy()
                all_sentdf["Sentences"] = all_sentdf.Sentences.apply(replace_escapeapostr)
                all_sentdf["SpeechTitle"] = [row["SpeechTitle"]]*len(all_sentdf["Sentences"])
                all_sentdf["Date"] = [row["Date"]]*len(all_sentdf["Sentences"])
                all_sentdf["SpeechURL"] = [row["SpeechURL"]]*len(all_sentdf["Sentences"])
                all_sentspeechdf = textsenten.speechtokeniser(all_sentdf, remove_all_punctuation=False)    
                if potus_all_sents is None:
                    potus_all_sents = all_sentspeechdf                    
                else:
                    potus_all_sents = pd.concat([potus_all_sents, all_sentspeechdf], ignore_index=True)               
                potus_sents += len(all_sentdf)
                potus_tokens += all_sentspeechdf["SentenceEnd"].values.tolist()[-1]
                potus_tokens_raw += len(row.RawText.split())
                potus_tokens_clean += len(row.CleanText.split())
            potus_speeches = len(df_potus)

            df_potus = pd.read_csv("{}/votesmart/{}/cleantext_{}.tsv".format(DIR_in, potus.replace(" ", ""), potus.replace(" ", "")), sep="\t")
            df_potus["CleanText"] = df_potus.CleanText.apply(remove_name_dot)
            df_potus["CleanText"] = df_potus.CleanText.apply(clean_parentheses)
            
            all_sentdf = None
            for i, row in df_potus.iterrows():
                speech_id = row["SpeechID"]
                all_sentdf = textsenten.extract_sentences(row["CleanText"], speech_id=speech_id)            
                all_sentdf["RawSents"] = all_sentdf["Sentences"].copy()
                all_sentdf["Sentences"] = all_sentdf.Sentences.apply(replace_escapeapostr)
                all_sentdf["SpeechTitle"] = [row["SpeechTitle"]]*len(all_sentdf["Sentences"])
                all_sentdf["Date"] = [row["Date"]]*len(all_sentdf["Sentences"])
                all_sentdf["SpeechURL"] = [row["SpeechURL"]]*len(all_sentdf["Sentences"])
                all_sentspeechdf = textsenten.speechtokeniser(all_sentdf, remove_all_punctuation=False)    
                if potus_all_sents is None:
                    potus_all_sents = all_sentspeechdf
                else:
                    potus_all_sents = pd.concat([potus_all_sents, all_sentspeechdf], ignore_index=True)            
                potus_sents += len(all_sentdf)
                potus_tokens += all_sentspeechdf["SentenceEnd"].values.tolist()[-1]
                potus_tokens_raw += len(row.RawText.split())
                potus_tokens_clean += len(row.CleanText.split())
            potus_speeches += len(df_potus)

            if potus == "Joe Biden":
                df_potus = pd.read_csv("{}/medium/{}/cleantext_{}.tsv".format(DIR_in, potus.replace(" ", ""), potus.replace(" ", "")), sep="\t")                  
                df_potus["CleanText"] = df_potus.CleanText.apply(remove_name_dot)
                df_potus["CleanText"] = df_potus.CleanText.apply(clean_parentheses)

                all_sentdf = None
                for i, row in df_potus.iterrows():
                    speech_id = row["SpeechID"]
                    all_sentdf = textsenten.extract_sentences(row["CleanText"], speech_id=speech_id)            
                    all_sentdf["RawSents"] = all_sentdf["Sentences"].copy() 
                    all_sentdf["Sentences"] = all_sentdf.Sentences.apply(replace_escapeapostr)
                    all_sentdf["SpeechTitle"] = [row["SpeechTitle"]]*len(all_sentdf["Sentences"])
                    all_sentdf["Date"] = [row["Date"]]*len(all_sentdf["Sentences"])
                    all_sentdf["SpeechURL"] = [row["SpeechURL"]]*len(all_sentdf["Sentences"])
                    all_sentspeechdf = textsenten.speechtokeniser(all_sentdf, remove_all_punctuation=False)   
                    if potus_all_sents is None:
                        potus_all_sents = all_sentspeechdf
                    else:
                        potus_all_sents = pd.concat([potus_all_sents, all_sentspeechdf], ignore_index=True)                                
                    potus_sents += len(all_sentdf)
                    potus_tokens += all_sentspeechdf["SentenceEnd"].values.tolist()[-1]
                    potus_tokens_raw += len(row.RawText.split())
                    potus_tokens_clean += len(row.CleanText.split())
                potus_speeches += len(df_potus)  
            
        else:
            df_potus = pd.read_csv("{}/votesmart/{}/cleantext_{}.tsv".format(DIR_in, potus.replace(" ", ""), potus.replace(" ", "")), sep="\t")
            df_potus["CleanText"] = df_potus.CleanText.apply(remove_name_dot)
            df_potus["CleanText"] = df_potus.CleanText.apply(clean_parentheses)

            all_sentdf = None
            for i, row in df_potus.iterrows():
                speech_id = row["SpeechID"]
                all_sentdf = textsenten.extract_sentences(row["CleanText"], speech_id=speech_id)            
                all_sentdf["RawSents"] = all_sentdf["Sentences"].copy()
                if potus == "Kamala Harris":
                    all_sentdf = all_sentdf[(all_sentdf["RawSents"]!="said Harris.") | (all_sentdf["RawSents"]!="said Harris") | (all_sentdf["RawSents"]!="said Senator Harris.") | (all_sentdf["RawSents"]!="said Senator Harris")]                    
                all_sentdf["Sentences"] = all_sentdf.Sentences.apply(replace_escapeapostr)
                all_sentdf["SpeechTitle"] = [row["SpeechTitle"]]*len(all_sentdf["Sentences"])
                all_sentdf["Date"] = [row["Date"]]*len(all_sentdf["Sentences"])
                all_sentdf["SpeechURL"] = [row["SpeechURL"]]*len(all_sentdf["Sentences"])
                all_sentspeechdf = textsenten.speechtokeniser(all_sentdf, remove_all_punctuation=False)    

                if potus_all_sents is None:
                    potus_all_sents = all_sentspeechdf
                else:
                    potus_all_sents = pd.concat([potus_all_sents, all_sentspeechdf], ignore_index=True)            
                
                potus_sents += len(all_sentdf)
                potus_tokens += all_sentspeechdf["SentenceEnd"].values.tolist()[-1]          
                potus_tokens_raw += len(row.RawText.split())
                potus_tokens_clean += len(row.CleanText.split())  
            potus_speeches = len(df_potus)

            if potus == "Kamala Harris":                
                df_potus = pd.read_csv("{}/medium/{}/cleantext_{}.tsv".format(DIR_in, potus.replace(" ", ""), potus.replace(" ", "")), sep="\t")                              
                df_potus["CleanText"] = df_potus.CleanText.apply(remove_name_dot)
                df_potus["CleanText"] = df_potus.CleanText.apply(clean_parentheses)

                all_sentdf = None
                for i, row in df_potus.iterrows():
                    speech_id = row["SpeechID"]
                    all_sentdf = textsenten.extract_sentences(row["CleanText"], speech_id=speech_id)            
                    all_sentdf["RawSents"] = all_sentdf["Sentences"].copy() 
                    if potus == "Kamala Harris":
                        all_sentdf = all_sentdf[(all_sentdf["RawSents"]!="said Harris.") | (all_sentdf["RawSents"]!="said Harris") | (all_sentdf["RawSents"]!="said Senator Harris.") | (all_sentdf["RawSents"]!="said Senator Harris")]                        
                    all_sentdf["Sentences"] = all_sentdf.Sentences.apply(replace_escapeapostr)
                    all_sentdf["SpeechTitle"] = [row["SpeechTitle"]]*len(all_sentdf["Sentences"])
                    all_sentdf["Date"] = [row["Date"]]*len(all_sentdf["Sentences"])
                    all_sentdf["SpeechURL"] = [row["SpeechURL"]]*len(all_sentdf["Sentences"])
                    all_sentspeechdf = textsenten.speechtokeniser(all_sentdf, remove_all_punctuation=False)    

                    if potus_all_sents is None:
                        potus_all_sents = all_sentspeechdf
                    else:
                        potus_all_sents = pd.concat([potus_all_sents, all_sentspeechdf], ignore_index=True)                                
                    potus_sents  += len(all_sentdf)
                    potus_tokens += all_sentspeechdf["SentenceEnd"].values.tolist()[-1]
                    potus_tokens_raw += len(row.RawText.split())
                    potus_tokens_clean += len(row.CleanText.split())       
                potus_speeches += len(df_potus)     

        # C-SPAN
        df_potus = pd.read_csv("{}/cspan/{}/cleantext_{}.tsv".format(DIR_in, potus.replace(" ", ""), potus.replace(" ", "")), sep="\t")    
        df_potus["CleanText"] = df_potus.CleanText.apply(remove_name_dot)
        df_potus["CleanText"] = df_potus.CleanText.apply(clean_parentheses)
        
        all_sentdf = None
        for i, row in df_potus.iterrows():
            speech_id = row["SpeechID"]
            all_sentdf = textsenten.extract_sentences(row["CleanText"], speech_id=speech_id)            
            all_sentdf["RawSents"] = all_sentdf["Sentences"].copy().str.lower()
            all_sentdf["Sentences"] = all_sentdf.Sentences.str.lower().apply(replace_escapeapostr)
            all_sentdf["SpeechTitle"] = [row["SpeechTitle"]]*len(all_sentdf["Sentences"])
            all_sentdf["Date"] = [row["Date"]]*len(all_sentdf["Sentences"])
            all_sentdf["SpeechURL"] = [row["SpeechURL"]]*len(all_sentdf["Sentences"])
            all_sentspeechdf = textsenten.speechtokeniser(all_sentdf, remove_all_punctuation=False)
            if potus_all_sents is None:
                potus_all_sents = all_sentspeechdf
            else:
                potus_all_sents = pd.concat([potus_all_sents, all_sentspeechdf], ignore_index=True)             
            potus_sents += len(all_sentdf)
            potus_tokens += all_sentspeechdf["SentenceEnd"].values.tolist()[-1]
            potus_tokens_raw += len(row.RawText.split())
            potus_tokens_clean += len(row.CleanText.split())  
        potus_speeches += len(df_potus)  
        
        dataset["#Speeches"].append(potus_speeches)
        # approximate, due to uncurated C-SPAN speeches
        dataset["#Sentences"].append(potus_sents) 
        dataset["#Tokens"].append(potus_tokens)
        dataset["#RawSpaceSeparatedTokens"].append(potus_tokens_raw)
        dataset["#CleanSpaceSeparatedTokens"].append(potus_tokens_clean)    

        if potus == "Joe Biden":
            fig.add_trace(go.Bar(x=["{}<br>{}".format(potus, potuses_terms[potus]["term"][0])], y=[potus_speeches], name='Democrats', marker_color='blue'))            
        elif potus == "Donald Trump":
            fig.add_trace(go.Bar(x=["{}<br>{}".format(potus, potuses_terms[potus]["term"][0])], y=[potus_speeches], name='Republicans', marker_color='red'))            
        else:
            if potuses_terms[potus]["party"] == "Democrats":
                fig.add_trace(go.Bar(x=["{}<br>{}".format(potus, potuses_terms[potus]["term"][0])], y=[potus_speeches], marker_color='blue', showlegend=False))                
            else:
                fig.add_trace(go.Bar(x=["{}<br>{}".format(potus, potuses_terms[potus]["term"][0])], y=[potus_speeches], marker_color='red', showlegend=False))

        potus_all_sents = potus_all_sents.sort_values(["Date"], ascending=True).reset_index(drop=True)                
        Path("{}/{}".format(outputdirectory, potus.replace(" ", ""))).mkdir(parents=True, exist_ok=True)
        potus_all_sents.to_csv("{}/{}/cleandataset_sentences.tsv".format(outputdirectory, potus.replace(" ", "")), index=False, sep="\t")
    
    datasetdf = pd.DataFrame.from_dict(dataset)
    datasetdf.to_csv("{}/datasummary.csv".format(outputdirectory), index=False)
    fix_plot_layout_and_save(fig, "{}/datasummary.html".format(outputdirectory), xaxis_title="US Presidents/Term served", yaxis_title="#Speeches", title="", showgrid=False, showlegend=True,
                             print_png=True)
    figtok = go.Figure(data=[
                go.Bar(name='Raw text', marker_color='blue', opacity=0.3, x=["Joe Biden", "Kamala Harris"], y=[datasetdf[datasetdf.POTUS=="Joe Biden"]["#RawSpaceSeparatedTokens"].values[0], datasetdf[datasetdf.POTUS=="Kamala Harris"]["#RawSpaceSeparatedTokens"].values[0]]),
                go.Bar(name='Clean text', marker_color='blue', opacity=1, x=["Joe Biden", "Kamala Harris"], y=[datasetdf[datasetdf.POTUS=="Joe Biden"]["#CleanSpaceSeparatedTokens"].values[0], datasetdf[datasetdf.POTUS=="Kamala Harris"]["#CleanSpaceSeparatedTokens"].values[0]])                
            ])
    figtok.update_layout(barmode='group')    
    fix_plot_layout_and_save(figtok, "{}/datasummary_tokens_dem.html".format(outputdirectory), xaxis_title="US Presidents/Term served", yaxis_title="#Tokens", title="", showgrid=False, showlegend=True,
                             print_png=True)
    figtok = go.Figure(data=[
                go.Bar(name='Raw text', marker_color='red', opacity=0.3, x=["Donald Trump", "Mike Pence"], y=[datasetdf[datasetdf.POTUS=="Donald Trump"]["#RawSpaceSeparatedTokens"].values[0], datasetdf[datasetdf.POTUS=="Mike Pence"]["#RawSpaceSeparatedTokens"].values[0]]),
                go.Bar(name='Clean text', marker_color='red', opacity=1, x=["Donald Trump", "Mike Pence"], y=[datasetdf[datasetdf.POTUS=="Donald Trump"]["#CleanSpaceSeparatedTokens"].values[0], datasetdf[datasetdf.POTUS=="Mike Pence"]["#CleanSpaceSeparatedTokens"].values[0]])
            ])
    figtok.update_layout(barmode='group')    
    fix_plot_layout_and_save(figtok, "{}/datasummary_tokens_rep.html".format(outputdirectory), xaxis_title="Candidates", yaxis_title="#Tokens", title="", showgrid=False, showlegend=True,
                             print_png=True)
    
    
    
