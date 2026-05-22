################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

from nltk.corpus import stopwords
import pandas as pd
from collections import Counter
from plotly import io as pio
from us2020data.stm.dictionary import Dictionary
from sklearn.feature_extraction.text import _make_int_array
from sklearn.utils import _IS_32BIT
import numpy as np
import scipy.sparse as sp

def stopwords_politicalscience(lexica_in):
    
    # Gentzkow, M., Shapiro, J. and Taddy, M., 2016. Measuring polarization in high-dimensional data: Method and application to congressional speech (No. id: 11114).
    df = pd.read_fwf('{}stopwordpoliticalscience.txt'.format(lexica_in), header=None)
    stops = set(stopwords.words('english'))
    stops = list(stops.union(set(flatten(df.values.tolist()))))    
    d = Dictionary(topic="StopwordsPoliticalScience", dictionary_elements=stops, workspace_in_dir="{}/".format(lexica_in), 
                   workspace_out_dir="{}/".format(lexica_in))
    dd = d.tokenlist()
    
    return dd

def dataset_descr_per_source(df, potus):

    if potus == "DonaldTrump":
        inits = "DT"
    elif potus == "JoeBiden":
        inits = "JB"
    elif potus == "KamalaHarris":
        inits = "KH"
    else:
        inits = "MP"
    def split_on_name(x): return x.split(inits)[0]

    df.SpeechID = df.SpeechID.apply(split_on_name)
    cntr = Counter(df.SpeechID.values.tolist())
    print(potus, cntr)



def fix_plot_layout_and_save(fig, savename, xaxis_title="", yaxis_title="", title="", showgrid=False, showlegend=False,
                             print_png=True):
    fig.update_xaxes(showline=True, linewidth=2, linecolor='black')
    fig.update_yaxes(showline=True, linewidth=2, linecolor='black')
    fig.update_layout(title=title, plot_bgcolor='rgb(255,255,255)',
                      yaxis=dict(
                          title=yaxis_title,
                          titlefont_size=20,
                          tickfont_size=20,
                          showgrid=showgrid,
                      ),
                      xaxis=dict(
                          title=xaxis_title,
                          titlefont_size=20,
                          tickfont_size=20,
                          showgrid=showgrid
                      ),
                      font=dict(
                          size=20
                      ),
                      showlegend=showlegend)
    if showlegend:
        fig.update_layout(legend=dict(
            yanchor="top",
            y=1.1,  # 0.01
            xanchor="right",  # "left", #  "right"
            x=1,    #0.01,  # 0.99
            bordercolor="Black",
            borderwidth=0.3,
            font=dict(
                size=18,
    )))

    pio.write_html(fig, savename, auto_open=False)    
    if print_png:        
        pio.write_image(fig, savename.replace("html", "png"), width=1540, height=871, scale=1)
        

def flatten(l):
    return [item for sublist in l for item in sublist]


def get_counts(dictionary, textunit):
           
    j_indices = []
    indptr = []
    
    textunit_hist = Counter(textunit)
    values = _make_int_array()
    indptr.append(0)    
    set_base = set(dictionary.wordlist)
    feature_basis_counter = dict()
    for basis_element in textunit:
        if basis_element in set_base:
            element_idx = dictionary.wordlist.index(basis_element)
            if element_idx not in feature_basis_counter.keys():
                feature_basis_counter[element_idx] = textunit_hist[basis_element]
            else:                
                continue
        else:            
            continue
    j_indices.extend(feature_basis_counter.keys())
    values.extend(feature_basis_counter.values())
    indptr.append(len(j_indices))

    if indptr[-1] > 2147483648:  # = 2**31 - 1
        if _IS_32BIT:
            raise ValueError(('sparse CSR array has {} non-zero '
                                'elements and requires 64 bit indexing, '
                                'which is unsupported with 32 bit Python.')
                                .format(indptr[-1]))
        indices_dtype = np.int64
    else:
        indices_dtype = np.int32
    
    j_indices = np.asarray(j_indices, dtype=indices_dtype)
    indptr = np.asarray(indptr, dtype=indices_dtype)
    values = np.frombuffer(values, dtype=np.intc)
    check_bits_num = values > 2**32 - 1
    if check_bits_num.any():
        # need 64bit integer
        X = sp.csr_matrix((values, j_indices, indptr), shape=(len(indptr) - 1, 
                            dictionary.size()), dtype=np.uint)  ### unsigned 64 bit, originally np.int
    else:
        X = sp.csr_matrix((values, j_indices, indptr), shape=(len(indptr) - 1, 
                            dictionary.size()), dtype="uint32")  ### unsigned 32bits        
    if not np.allclose(values, X.data):
        print("TextEmbedder precision error in ngram processing?")
        raise OverflowError    
    X.sort_indices()

    return X