################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

from __future__ import absolute_import, division, print_function, unicode_literals
import string
import unicodedata
from string import digits

class TextTokeniser:

    def __init__(self, dictionary=None, stem=False, stopwords=None, remove_punctuation=True, remove_oov=True, remove_numbers=True):
        
        # Dictionary object
        if dictionary is None:        
            print("Please provide Dictionary object.")
            raise AttributeError
        
        self.dictionary = dictionary
        self.stem = stem
        self.stopwords = stopwords
        self.remove_punctuation = remove_punctuation
        self.remove_numbers = remove_numbers
        # count out-of-vocabulary words
        self.oov_num = 0
        self.remove_oov = remove_oov

    
    def _number_remove(self, text):
                
        remove_num = str.maketrans('', '', digits)
        res = text.translate(remove_num)
        if res == "":
            return False
        else:
            return res

    def _stopword_check(self, text) -> bool:
        # return True if text is a stopword
        return bool(text.lower() in self.stopwords)

    @staticmethod
    def is_punctuation(char) -> bool:

        if len(char) > 1 or char == "":
            return False
        
        """Checks whether `chars` is a punctuation character."""
        cp = ord(char)
        # We treat all non-letter/number ASCII as punctuation.
        # Characters such as "^", "$", and "`" are not in the Unicode
        # Punctuation class but we treat them as punctuation anyways, for
        # consistency.
        if ((cp >= 33 and cp <= 47) or (cp >= 58 and cp <= 64) or
                (cp >= 91 and cp <= 96) or (cp >= 123 and cp <= 126)):
            return True
        cat = unicodedata.category(char)
        if cat.startswith("P"):
            return True
        if char in string.punctuation:
            return True

        return False

    def postprocess_single_token(self, token, valid_chars, stem=False, language="english", clean_token=False):      

        # extract dictionary trie searcher
        word_basis_trie = self.dictionary.wordsearcher
        if not clean_token:
            cleaned_token = self.dictionary.clean_dictionary_token(token, valid_chars, language, stem=stem)
        else:
            cleaned_token = token
    
        if self._stopword_check(token):
            # Note that stopwords that are part of a compound word will remain, e.g. track and field
            # is a single token therefore stopword 'and' remains in this context
            return False
        elif self.is_punctuation(token) and self.remove_punctuation:
            # remove punctuation at this stage
            return False
        elif self.remove_oov and (cleaned_token not in word_basis_trie):
            # Remove OOV? only reason to keep them is to allow for changing dictionary later without having to re-postprocess
            # If we want to keep punctuation and remove OOV words, make sure that punctuation
            # characters are also included in the dictionary
            # Regardless of that, only print OOV words to count for the OOV rate
            if len(token) > 1:
                self.oov_num += 1
            return False
        elif len(token) == 1:
            # remove single character tokens that are not punctuation - we consider them noise
            return False
        else:            
            # return token in a form that is consistent with the token format in the dictionary
            if self.remove_numbers and (cleaned_token not in word_basis_trie):
                # returns False or clean_token without number
                return self._number_remove(cleaned_token)
            else:
                return cleaned_token


    def postprocess_tokens(self, tokens, valid_chars, stem=False, language="english", clean_token=False) -> list:
        # Get list of clean tokens and return list of postprocessed tokens
        # If this is applied after tokenise(), call with clean_token=True

        pp_tokens = [self.postprocess_single_token(i, valid_chars, stem, language, clean_token) for i in tokens]
        ret_tokens = [i for i in pp_tokens if isinstance(i, str)]        

        return ret_tokens

    
    def tokenise(self, text, valid_chars, language="english", stem=False):
        
        tokens = []
        word_basis_trie = self.dictionary.wordsearcher
        # start by processing text in the same way as the dictionary has been processed        
        dict_clean_text = [self.dictionary.clean_dictionary_token(token, valid_chars, 
                                            language, stem=stem) for token in text.split()]            
        dict_clean_text = " ".join([i for i in dict_clean_text if isinstance(i, str)])  
                    
        # extract dictionary words/phrases and remaining text pieces        
        spans_no_split = word_basis_trie.extract_keywords(dict_clean_text, span_info=True)
        init = 0
        for span in spans_no_split:
            start = init
            end = span[1]
            if start != end:
                w = dict_clean_text[start:end].strip()
                if w != ' ' and w != '':
                    wl = w.split()                      
                    if " " in w and len(wl) > 1:
                        tokens.extend([ws for ws in wl])
                    else:
                        tokens.append(w)
            # Keyword token
            w = dict_clean_text[span[1]:span[2]].strip()
            if w != ' ' and w != '':
                tokens.append(w)
            init = span[2]
        if init < len(dict_clean_text):
            w = dict_clean_text[init:].strip()  
            wl = w.split()                      
            if " " in w and len(wl) > 1:
                tokens.extend([ws for ws in wl])
            else:
                tokens.append(w)

        return tokens