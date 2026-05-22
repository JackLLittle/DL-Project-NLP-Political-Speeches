################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

from flashtext import KeywordProcessor
from pathlib import Path
import pickle5 as pickle
import pandas as pd     
import re
import regex
from us2020data.src.quotes import OPENQUOTES
from us2020data.src.quotes import CLOSEQUOTES
import numpy as np
from nltk.stem.snowball import SnowballStemmer
import warnings 
import string


class Dictionary:

    def __init__(self, topic=None, dictionary_elements=None, workspace_out_dir="./lexica/", workspace_in_dir="./lexica/", 
                assess_dictionary=False,
                name=None, save=False, save_trie=False, stem=False):
        
        # make sure stem arg is the same for all processing stages
        self.workspace_in_dir = workspace_in_dir
        self.workspace_out_dir = workspace_out_dir
        Path(self.workspace_out_dir).mkdir(parents=True, exist_ok=True)
        self.topic = topic
        self.dictionary_elements = None
        self.__load_existing_dict = False
        self.__load_existing_dict_multiple = False
        self.__create_and_save_dict = False
        self.wordlist = None
        self.wordsearcher = None
        self.existing_topics = sorted(["Cryptocurrency", "USPolitics", "Video gaming", "Business, economics, and finance", 
                                  "Philosophy and religion", "Royalty and nobility", "Environment Conservation",
                                  "Heraldry, honors, and vexillology", "Engineering and technology", 
                                  "Art, architecture, and archaeology", "Literature and theater", 
                                  "Sports and recreation", "Natural sciences", "Music", "Warfare", 
                                  "Media", "Religion", "Transport", "History", "Culture and society",
                                  "Meteorology", "Food and drink", "Biology", "Health and medicine", 
                                  "Geography and places", "Language and linguistics", "Chemistry and mineralogy", 
                                  "Mathematics", "Education", "Politics and government", "Law", 
                                  "Computing", "Geology and geophysics", "Philosophy and psychology", 
                                  "Physics and astronomy", "Agribusiness", "Everyday English", 
                                  "Epidemics", "General positive English words", 
                                  "General negative English words", "testagri"])

        if topic is None and dictionary_elements is None:
            print("Initialise Dictionary class with a topic to load corresponding dictionary, or with a list of words to create a new dictionary.")
            print("List of available topic dictionaries:")
            for t in range(len(self.existing_topics)):
                print("{}: {}".format(t, self.existing_topics[t]))
        
        if isinstance(topic, str) and dictionary_elements is None:
            # pass name of existing dictionary to load it
            self.__load_existing_dict = True
        elif isinstance(topic, list) and dictionary_elements is None:
            # pass list of names of existing dictionaries to join them
            self.__load_existing_dict_multiple = True
        elif isinstance(topic, str) and isinstance(dictionary_elements, list):
            # pass list of words and name for the dictionary to create and save a new one
            self.__create_and_save_dict = True
            self.dictionary_elements = dictionary_elements
        else:
            print("Either load an existing dictionary as topic or create a new one by passing a list of words as dictionary_elements.")
            raise AttributeError

        if (self.__load_existing_dict or self.__load_existing_dict_multiple) and not self.__create_and_save_dict:
            self.wordlist = self.tokenlist(name=name, save=save, save_trie=save_trie, stem=stem)
            self.wordsearcher = self.trie_object(stem=stem)
           
    def tokenlist(self, name=None, save=False, save_trie=False, stem=False, character_set=None, 
                  special_chars={}, extra_admissible_chars={}, language="english") -> list:

        if self.__load_existing_dict:
            return self.load_single_dict(self.topic, self.workspace_in_dir, stem)["words"].values.tolist()
        elif self.__load_existing_dict_multiple:
            return self.load_multiple_dict(name=name, save=save, save_trie=save_trie, stem=stem)["words"].values.tolist()            
        elif self.__create_and_save_dict:
            return self.create_store_dict(character_set, special_chars, extra_admissible_chars, stem, language, save_trie)["words"].values.tolist()            

    def trie_object(self, stem=False) -> KeywordProcessor:

        trie_searcher = None
        if stem:
            load_dir = "{}/topicdictionaries_stemmed/trie/".format(self.workspace_in_dir)
        else:
            load_dir = "{}/topicdictionaries/trie/".format(self.workspace_in_dir)
        
        try:
            with open("{}{}_trie.pickle".format(load_dir, self.topic.replace(",", "").replace(" ", "")), "rb") as f:
                trie_searcher = pickle.load(f)        
        except AssertionError:
            print("To load an efficient trie searcher, pass the name of the dictionary and make sure the trie searcher has already been created.")
            raise AttributeError        
        
        return trie_searcher

    # @staticmethod
    def load_single_dict(self, topic, workspace_in_dir, stem):                
        
        def turn2string(x) : return "{}".format(x)
        if stem:        
            load_dir = "{}/topicdictionaries_stemmed/list/".format(workspace_in_dir)
            Path(load_dir).mkdir(parents=True, exist_ok=True)        
        else:
            load_dir = "{}/topicdictionaries/list/".format(workspace_in_dir)
            Path(load_dir).mkdir(parents=True, exist_ok=True)                    

        vocabulary = pd.read_csv("{}{}.csv".format(load_dir, topic.replace(",", "").replace(" ", "")), index_col=0, dtype=str)
        vocabulary.words = vocabulary.words.apply(turn2string)

        return vocabulary


    def load_multiple_dict(self, name=None, save=False, save_trie=False, stem=False):

        if not isinstance(self.topic, list):        
            print("For buliding a single dictionary out of a collection, provide a list of topics.")
            raise AttributeError
        def turn2string(x) : return "{}".format(x)        
        
        joint_v = []
        for t in self.topic:
            v = self.load_single_dict(t, self.workspace_in_dir, stem)
            joint_v.extend(v.words.values.tolist())
        joint_v = list(set(joint_v))    
        joint_v_pd = pd.DataFrame.from_dict({"words": joint_v})
        joint_v_pd.words = joint_v_pd.words.apply(turn2string)

        if save or save_trie:
            if stem:        
                save_dir = "{}/topicdictionaries_stemmed/".format(self.workspace_out_dir)
                Path(save_dir).mkdir(parents=True, exist_ok=True)        
            else:
                save_dir = "{}/topicdictionaries/".format(self.workspace_out_dir)
                Path(save_dir).mkdir(parents=True, exist_ok=True)                    
        if save:
            if name is None:
               print("Provide a name to save the joint dictionary.")
               raise AttributeError
            self.topic = name
            joint_v_pd.to_csv("{}list/{}.csv".format(save_dir, name))
        if save_trie:
            self.dictionary_to_trie_searcher(tokenlist=joint_v, name="{}_trie".format(name), 
                directory_out="{}trie/".format(save_dir))

        return joint_v_pd
    
    def create_store_dict(self, character_set=None, special_chars={}, extra_admissible_chars={}, stem=False, language="english", save_trie=False):

        if not isinstance(self.topic, str) and not isinstance(self.dictionary_elements, list):        
            print("For buliding a new provide a name and a list of tokens.")
            raise AttributeError
        def turn2string(x) : return "{}".format(x)
        
        v = self.dictionary_elements        
        v = list(set(v))            
        v = self.dictionary_cleaner(tokenlist=v, character_set=character_set, special_chars=special_chars, 
                                    extra_admissible_chars=extra_admissible_chars, language=language, stem=stem)
        if len(v) <= 1:        
            print("Error creating dictionary after cleaning words - check your word list.")
            raise AttributeError
        
        v_pd = pd.DataFrame.from_dict({"words": v})
        v_pd.words = v_pd.words.apply(turn2string)
        v_pd.words = v_pd.words.dropna().reset_index(drop=True)
        v_pd = v_pd.drop(v_pd[v_pd.words=="nan"].index).reset_index(drop=True)        
        v_pd.to_csv("{}{}.csv".format(self.workspace_out_dir, self.topic))        
        if save_trie:
            self.wordsearcher = self.dictionary_to_trie_searcher(tokenlist=v, 
                                                name="{}_trie".format(self.topic), 
                                                directory_out=self.workspace_out_dir)
        else:
            self.wordsearcher = None
            print("{}: Note that a fast search trie structure has not been stored.".format(self.topic))
        self.wordlist = v_pd.words.values.tolist()

        return v_pd
    
    @staticmethod
    def dictionary_to_trie_searcher(tokenlist=None, name=None, directory_out=None) -> KeywordProcessor:

        trie_searcher = KeywordProcessor()
        trie_searcher.add_keywords_from_list(list(set(tokenlist)))
        with open("{}{}.pickle".format(directory_out, name), "wb") as f:
            pickle.dump(trie_searcher, f, pickle.HIGHEST_PROTOCOL)
        
        return trie_searcher
        

    @staticmethod
    def clean_dictionary_token(w, valid_chars, language, stem=False) -> str:
        
        def replace_apostr(x) : return re.sub(r'[\']+', '', x)
        def replace_spaces(x) : return re.sub(r'\s+', ' ', x)
        def replace_tabs2spaces(x) : return re.sub(r'\t+', ' ', x)        
        def same_dash(x) : return regex.sub("\p{Pd}+", "-", x)    #  -   
        def clean_for_speech_seg2(x): return re.sub(r'[^\w\s]', '', x).replace("'s", "").strip()
        def clean_encode_err(x): return x if "\ufffd" not in x else np.nan
        
        if stem:            
            stemmer = SnowballStemmer("english")
      
        if language == "english":
                try:                     
                    text_tmp = w.encode("utf-8", errors="ignore").decode("utf-8", "replace")      
                    check_chars = np.all([True if i in valid_chars else False for i in text_tmp])
                    if not check_chars:
                        ww = np.nan                        
                    else:
                        if len(text_tmp.split()) > 5:                            
                            ww = np.nan
                        else:
                            ww = "".join([i if (i not in OPENQUOTES and i not in CLOSEQUOTES) else "'" for i in w])
                            ww = replace_apostr(ww)
                            ww = same_dash(ww)
                            ww = replace_spaces(ww)
                            ww = replace_tabs2spaces(ww)                            
                            ww = clean_encode_err(ww)
                except UnicodeDecodeError:                                              
                        ww = np.nan
                        warnings.warn("UnicodeDecodeError while trying to remove non-unicode characters - Check your input!")
                except AttributeError:                                             
                        ww = np.nan
                        warnings.warn("Spurious input? Better check!")    
                
                if isinstance(ww, str):
                    ww = clean_for_speech_seg2(ww)
                    ww = ww.strip().lower()       
                    if stem:
                        wwlist = [stemmer.stem(p) for p in ww.split()]
                        ww = " ".join(wwlist).strip()         
                return ww                    
        else:
            print("Working with non-English language - update framework first!")
            raise IOError

    def dictionary_cleaner(self, tokenlist=None, character_set=None, special_chars={}, 
                           extra_admissible_chars={}, language="english", stem=False) -> list:

        if character_set is None:            
            character_set = string.printable        

        valid_chars = set(character_set).union(set(special_chars)).union(set(extra_admissible_chars))
        dict_words = [self.clean_dictionary_token(w, valid_chars, language, stem) for w in tokenlist if isinstance(w, str)]
        dict_words = np.unique(dict_words).tolist()
        
        return dict_words

    def size(self) -> int:
        
        return len(self.wordlist) 
            

        