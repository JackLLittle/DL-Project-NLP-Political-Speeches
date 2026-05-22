################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

from __future__ import absolute_import, division, print_function, unicode_literals
import re
import numpy as np
import pandas as pd

class TextSentenciser:

    def __init__(self, language="english", extra_sentencesplitters=None):
            
            self.language = language
                    
    
    def segment2sentences(self, text, trie_searcher_special=None):
        """
        Simple sentence segmenter. Split text at punctuation symbols: . ; ? !. Remove ":".

        Exceptions: 1) if the new 'sentence' is less than 3 chars long (e.g. of min. acceptable: I am) then concatenate it with previous sentence
                    2) if a full stop is found, don't create new sentence if it is part of a set of phrases that include a dot -
                        create new sentence if next token after dot (and the space after it) is uppercase
        """       

        text_size = len(text)
        punct = ['.', ';', '?', '!']
        sentences = []
        sent = ""
        next_sent = False
        i = 0
        while i < text_size:
            if text[i] not in punct:
                sent += text[i]
            elif text[i] == ".":  
                    k = i                    
                    while k < text_size and text[k] != " ":
                        k = k + 1                    
                    j = i - 1                    
                    while j >= 0 and j <= i-1:
                        if text[j] == ' ':
                            break
                        j = j - 1                       
                    # i = k #            
                    # extract word that contains the dot.        
                    w = text[j + 1:k].strip()
                    wlow = w.lower()
                    wnodot = w.replace(".", "")
                    if (len(w) - len(wnodot) > 1 and len(w) < 6) or wlow in ['mr.', 'mrs.', 'ms.', 'tel.', 'ref.', 'etc.', 'et.',
                        'al.', 'jan.', 'feb.', 'mar.', 'apr.', 'aug.', 'sep.', 'dr.',
                        'oct.', 'nov.', 'dec.', 'approx.', 'dept.', 'apt.',
                        'appt.', 'est.', 'misc.', 'e.g.', 'u.s.', 'u.s.a.', 'u.k.'] or (trie_searcher_special is not None and wlow in trie_searcher_special):
                        # assume e.g. abbreviation containing .                        
                        # sent += text[i]                        
                        sent += text[i:k] + " "                      
                        i += len(text[i:k])
                    elif k + 1 < text_size and text[k] == " " and text[k+1].isupper(): # i                       
                        # sent += "."
                        # next_sent = True        
                        sent += text[i:k] 
                        if sent[-1] not in punct and sent[-1] != ",":
                            sent += "."
                        next_sent = True                    
                        i += len(text[i:k])
            else:                
                sent += text[i]
                next_sent = True

            if next_sent:   
                # print(sent)                
                if text != ".":
                    if len(sent) < 3:
                        if len(sentences) > 0:
                            sentences[-1] += sent.strip()
                        else:
                            if sent != "" and sent != " ":
                                sentences.append(self.tidy_up_sentence(sent))
                    else:
                        if sent != "" and sent != " ":
                            sentences.append(self.tidy_up_sentence(sent))
                else:
                    if sent != "" and sent != " ":
                        sentences.append(self.tidy_up_sentence(sent))
                sent = ""
                next_sent = False
            i = i + 1
        if len(sent) < 3:
            if len(sentences) > 0:
                sentences[-1] += sent.strip()
            else:
                if sent != "" and sent != " ":
                    sentences.append(self.tidy_up_sentence(sent))
        else:
            if sent != "" and sent != " ":
                sentences.append(self.tidy_up_sentence(sent))

        pd_out = pd.DataFrame(sentences, columns=["sentences"])

        return pd_out

    def tidy_up_sentence(self, text) -> str:
                
        text = text.strip()
        if text[0] == "'" and text[-1] == "'":
            text = text[1:-1]
        elif text[-1] == "," or text[-1] == ":":
            text = text[0:-1] + "."
        if text[-1] != "." and text[-1] != "?" and text[-1] != "!" and text[-1] != ";":
            text = text + "."
        
        def replace_spaces(x) : return re.sub(r'\s+', ' ', x)        
        def commas_spaces(x) : return re.sub(r'\s,', ',', x)
        text = commas_spaces(text)
        text = replace_spaces(text)
        text = text.strip()

        return text

    def __annotate_sentence(self, t) -> str:

        if t != "" and t[0] == "(" and (t[-1]==")" or t[-2:]==")."):
            return "audience"
        elif t != "":
            return "speaker"
        else:
            return "emptysent"
    
    def segment2parts(self, text) -> tuple:
        """
        Segment text into portions within single-word parentheses and single quotes.
        """      

        segments = []
        seg = ""
        for i in range(len(text)):
            if text[i] == "(":
                if i > 0 and text[i-1] != ".":                    
                    segments.append(seg)
                    seg = "("  
            elif text[i] == ")":
                seg += text[i]
                if "." in seg:
                    seg = seg.replace(".", "")
                segments.append(seg)
                seg = ""
            elif text[i] == " " and i < len(text)-1 and text[i+1] == "'":                                    
                    segments.append(seg)
                    seg = ""
            elif text[i] == "'" and i < len(text)-1 and text[i+1] == " ":
                    seg += text[i] 
                    segments.append(seg)
                    seg = ""
            else:
                seg += text[i]
        segments.append(seg)
        
        # concatenate quoted parts if they have max 3 tokens
        label_segs = [] # speaker, audience
        filter_segs = []
        j = 0
        filt_seg = ""
        while j < len(segments):
            s = segments[j]
            if s == "" or s == " ":
                j += 1
                continue
            if s[0] == "'" and s[-1] == "'":
                s_tmp = s.replace("'", "")
                s_tmp = s_tmp.split()
                if len(s_tmp) <= 3:
                   filt_seg += " " + s + " "
                   j += 1
                else:
                    filter_segs.append(filt_seg)
                    label_segs.append(self.__annotate_sentence(filt_seg))
                    filt_seg = ""
                    filter_segs.append(s)
                    label_segs.append(self.__annotate_sentence(s))
                    j += 1
            elif "(" in s:
                filter_segs.append(filt_seg)
                label_segs.append(self.__annotate_sentence(filt_seg))
                filt_seg = ""
                filter_segs.append(s)
                label_segs.append(self.__annotate_sentence(s))
                j += 1
            else:
                filt_seg += s + " "
                j += 1
        if filt_seg != "" and filt_seg != " ":
            filter_segs.append(filt_seg)
            label_segs.append(self.__annotate_sentence(filt_seg))
        filter_segs = [self.tidy_up_sentence(i) for i in filter_segs if i != " " and i != ""]
        label_segs = [i for i in label_segs if i != "emptysent"]

        return filter_segs, label_segs

    def extract_sentences(self, text, trie_searcher_special=None, speech_id=None):

        text_parts, part_labels = self.segment2parts(text)
        sentences = []
        labels = []
        for i in range(len(text_parts)):
            tp = text_parts[i]
            lp = part_labels[i]
            tp_sentences = self.segment2sentences(tp, trie_searcher_special)
            sentences.extend(tp_sentences.sentences.tolist())
            labels.extend([lp]*len(tp_sentences.sentences))
        
        speech_ids = ["{}".format(speech_id)]*len(sentences)
        sentence_ids = ["{}{}".format(speech_id, i) for i in np.arange(1, len(sentences)+1, 1)]        
        pd_out = pd.DataFrame.from_dict({"SpeechID": speech_ids, "SentenceID": sentence_ids, "Labels": labels, "Sentences": sentences})

        return pd_out

    @staticmethod
    def speechtokeniser(sentences, remove_all_punctuation=False):

        """
        Sentences is a dataframe as produced from extract sentences. 
        Tokeniser for speech segmentation only. 
        Take the sentences, remove unicode '\ufffd' and split on whitespace.
        Afterwards, clean sentences of all punctuation and 's.
        """
                
        def clean_for_speech_seg(x): return x.replace("\ufffd", "").strip()
        def clean_for_speech_seg2(x): return re.sub(r'[^\w\s]', '', x).replace("'s", "").strip()
        def split_on_space(x) : return clean_for_speech_seg(x).split()
        
        sentences["Tokens"] = sentences.Sentences.apply(split_on_space)
        sentences["SentenceEnd"] = sentences.Tokens.apply(len)
        sentences["SentenceEnd"] = sentences.SentenceEnd.cumsum(axis=0)
        if remove_all_punctuation:
            sentences.Sentences = sentences.Sentences.apply(clean_for_speech_seg2)

        return sentences
        
  

        