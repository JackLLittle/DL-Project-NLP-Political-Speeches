################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

import html
import unicodedata
import re
import regex
from us2020data.src.quotes import OPENQUOTES, CLOSEQUOTES
import string
import time
import pandas as pd

# dialogue or not addressing mainly the public but rather a member of staff
patternremtext = re.compile(r'.*?(PRESIDENT DUDA|MRS. TRUMP|INTERIM PRESIDENT GUAIDÓ|CHIEF BIEHL|ADMINISTRATOR MCMAHON|MILITARY AIDE|SHERIFF O\'CONNOR|SECRETARY AZAR|LIEUTENANT COLONEL TIMOTHY REDHAIR|TO THE SENATE OF THE UNITED STATES|INTERPRETER ON BEHALF OF|MRS. GLORIA GUILLÉN|MS. KHAWAM|MS. PETERS|SHERIFF BETH|SECRETARY BERNHARDT|AMBASSADOR PENCE|MR. GIULIANI|GOVERNOR DESANTIS|BISHOP JACKSON|SENIOR CHIEF PETTY OFFICER SCHAEFFER|MR. TURNER|SECRETARY CARSON|MRS PENCE|MS DAVIS|SECRETARY MNUCHIN|MS. BROWNLEE|TO THE CONGRESS OF THE UNITED STATES|GOVERNOR ABBOTT|GOVERNOR BURGUM|ADMINISTRATOR BRIDENSTIN|HOUSE MAJORITY LEADER HOYER|LIEUTENANT GENERAL LINNINGTON|MR. ROSS|DR. LAFFER|DR. GEORGE|SECRETARY POMPEO|ACTING ADMINISTRATOR GAYNOR|GENERAL MILLEY|MR. GALLOGLY):', re.DOTALL)
# introduction of speaker at the beginning of the speech
patternbegin = re.compile(r'^\s*?(THE VICE PRESIDENT|THE PRESIDENT|PRESIDENT TRUMP|VICE PRESIDENT PENCE|VICE PRESIDENT HARRIS|VICE PRESIDENT|PRESIDENT):', re.DOTALL)
patternbeginharris = re.compile(r'^\s*.*?(U.S. Senator Kamala D. Harris (D-CA), a member of the Senate Judiciary Committee, on Monday released the following statement on her vote against the confirmation of Judge Amy Coney Barrett to be Associate Justice of the Supreme Court of the United States|A full transcript of Harris\' statement, as delivered: HARRIS|Full transcript of Harris\' remarks below|Full transcript of Harris\' remarks|HARRIS):', re.DOTALL)
patternremovetrump = re.compile(r'(PRES. TRUMP:|Mr. Trump:|GUEST:|MR. TRUMP:|PRESIDENT TRUMP::|TRUMP:|PRESIDENT TRUMP:)', re.DOTALL)
patternremovepence = re.compile(r'(V.P. PENCE:|VICE PRES. PENCE:|PENCE:|VICE PRESIDENT PENCE:)', re.DOTALL)
patternremovebiden = re.compile(r'(VICE PRESIDENT BIDEN:|VP BIDEN:|FRMR V.P. BIDEN:|JOE BIDEN:|FORMER VP BIDEN:|VICE-PRESIDENT BIDEN:|VICE PRES. BIDEN:|FMR. VP BIDEN:|PRESIDENT-ELECT BIDEN:)', re.DOTALL)
# end signatures
patternend = re.compile(r'(\bEND\b(?=\s*\.|$)|FOR FURTHER INFORMATION MEDIA SHOULD CONTACT).*$', re.DOTALL)
patternendwithtime = re.compile(r'\s*END\s*\b(?:[0-1]?[0-9]|2[0-3]):[0-5]\d\b\s*(A.M.|P.M.)\s*(?!,).*$', re.DOTALL)
patternstartwithtime = re.compile(r'^(.*?\s*(\b(?:[0-1]?[0-9]|2[0-3]):[0-5]\d\b)\s*(A.M.|P.M.)\s*\b\w+\b\s*(THE VICE PRESIDENT|THE PRESIDENT|PRESIDENT TRUMP|VICE PRESIDENT PENCE|VICE PRESIDENT HARRIS):)', re.DOTALL)
patternjrbjr = re.compile(r'(. JOSEPH R. BIDEN JR.|.JOSEPH R. BIDEN JR.|.DONALD J. TRUMP|. DONALD J. TRUMP)(?!,).*$', re.DOTALL)
# remove Q&A session
patternqs = re.compile(r' Q (?:Thank you, Mr. President|Mr. President|.*?)(?=\n|$)', re.DOTALL)
# remove audience interruptions
patterninbetween = re.compile(r'AUDIENCE:.*? THE PRESIDENT:', re.DOTALL)
patterninbetweendialogue = re.compile(r' (DR.|MS.|MR.|THE VICE|REPRESENTATIVE|GOVERNOR|STATE ATTORNEY GENERAL)* \b(\w+):.*? (THE PRESIDENT|THE VICE PRESIDENT):', re.DOTALL)
patternsen = re.compile(r'Sen\.\s(?:[A-Z])')
def replace_beginwithtime(text) : return re.sub(patternstartwithtime, '', text)
def replace_allup2vp(text) : return re.sub(patternbegin, '', text)
def replace_allup2harris(text) : return re.sub(patternbeginharris, '', text)
def remove_alltext(text): return "" if len(re.findall(patternremtext, text)) > 0 else text
def remove_qsession(text) : return re.sub(patternqs, '', text)
def remove_audiencesession(text) : return re.sub(patterninbetween, '', text)        
def replace_proclamation(text) : return re.sub("^\s*BY THE PRESIDENT OF THE UNITED STATES OF AMERICA A PROCLAMATION", '', text)
def replace_transcript_init(text) : return re.sub(r'^\s*Transcript[^\n.]*[.!?]', '', text)
def replace_contentwarning_init(text) : return re.sub(r'^\s*Content warning:[^\n.]*[.!?]', '', text)
def replace_exec_order(text) : return re.sub("\(The executive order is signed.\)", '', text)
def replace_breaktranscript(text) : return re.sub("(BREAK IN TRANSCRIPT|Read Vice President Mike Pence's speech from the 2020 Republican National Convention, as prepared for delivery:)", '', text)
def remove_url(text) : return re.sub(r'https?://\S+|www\.\S+|\S+\.com/\S*|\S+\.org/\S*|\S+\.net/\S*', '', text)
def remove_interruptionsession(text) : return re.sub(patterninbetweendialogue, '', text)
def remove_square_brackets(text) : return re.sub(r'\[.*?\]', '', text)
def remove_round_brackets(text) : return re.sub(r'\(.*?\)', '', text) 
def replace_senator(text): return re.sub(patternsen, "Senator ", text)
def replace_endwithtime(text) : return re.sub(patternendwithtime, '', text)
def remove_bidenend(text) : return re.sub(patternjrbjr, '', text)
def replace_allafterend(text) : return re.sub(patternend, '', text)         
def remove_hashprint(text) : return text.replace("### Print", "")
def remove_hashprint2(text) : return text.replace("###", "")
def remove_hashprint3(text) : return text.replace("Bill text can be found HERE. A one-pager on the bill can be found HERE.", "")
def remove_hashprint4(text) : return text.replace("For further background on the bill, click here. For full bill text, click here.", "")
def replace_ps(text) : return re.sub(r'\s*P.S.*YouTube.(?=\s|$)', '', text)
def replace_ps2(text) : return re.sub(r'^\s*P.S. [^\n.]*[.!?](?=\s|$)', '', text)       
def remove_dots(x) : return x.replace("…", "").replace("--", "")
def remove_trump(text) : return re.sub(patternremovetrump, '', text)    
def remove_pence(text) : return re.sub(patternremovepence, '', text)
def remove_biden(text) : return re.sub(patternremovebiden, '', text)    
    

def apply_unicode_normalisation(text, unicode_class):

    # convert all named and numeric character references (e.g. &gt;, &#62;, &#x3e;) in the string text
    # to the corresponding Unicode characters.        
    text = html.unescape(text)

    # Apply Unicode normalisation according to given Unicode class        
    text = unicodedata.normalize(unicode_class, text)

    return text

def clean_char_repetitions(text) -> str:
            
    def replace_newlines(x) : return re.sub(r'[\n*\xa0*\n*]', ' ', x)
    def replace_spaces(x) : return re.sub(r'\s+', ' ', x)
    def replace_tabs(x) : return re.sub(r'\t+', '\t', x)
    def replace_ret(x) : return re.sub(r'\r+', '\r', x)
    
    tmp_text = text
    remove_repetitions = re.compile(r"([a-zA-Z])\1\1+")
    match = remove_repetitions.search(tmp_text)
    while match:
        text_part = match.group(0)
        rep_part = remove_repetitions.sub(r"\1", text_part)
        tmp_text = tmp_text.replace(text_part, rep_part)
        match = remove_repetitions.search(tmp_text)

    tmp_text = replace_newlines(tmp_text)
    tmp_text = replace_spaces(tmp_text)
    tmp_text = replace_tabs(tmp_text)
    tmp_text = replace_ret(tmp_text)

    tmp_text = tmp_text.strip()

    return tmp_text

def clean_speech_texts(data, cleaner, unicode_class, potus=None):
    
    def clean_with_encodingclass(x) : return cleaner(x, unicode_class, potus)
    data["CleanText"] = data.RawText.apply(clean_with_encodingclass)
    dataclean = data
    df_out = dataclean[dataclean["CleanText"] != ""].reset_index(drop=True)

    return df_out

def unicode_cleanup(text):
                
    def replace_apostr(x) : return re.sub(r'[\']+', '\'', x)
    def same_dash(x) : return regex.sub("\p{Pd}+", "-", x)    #  - 

    # replace all quotes with apostrophes - note that , is included in OPENQUOTES and we want to keep it
    text = "".join([i if (i not in OPENQUOTES and i not in CLOSEQUOTES) or i == "," else "'" for i in text])
    text = replace_apostr(text)
    text = same_dash(text)
    
    # remove non-unicode characters (default) or any character not in character_set
    # Replace unencodable character with '\ufffd'
    
    try:
        text_tmp = text.encode("utf-8", errors="ignore").decode("utf-8", "replace")
        if len(text_tmp) != len(text):
            raise AttributeError
    except UnicodeDecodeError:
        import warnings
        print(text)
        warnings.warn("UnicodeDecodeError while trying to remove non-unicode characters - Check your input!")
    except AttributeError:
        import warnings
        print(text)
        warnings.warn("Spurious input? Better check!")
    
    # replace all chars that are not in admissible lists with "\ufffd" to apply a common rule for cleanup later
    character_set = string.printable.replace('`', '')
    extra_admissible_chars = []
    special_chars  = []
    all_admissible = "{}{}{}".format(character_set, extra_admissible_chars, special_chars)
    def remove_inadmissible(x) : return [i if i in all_admissible else "\ufffd" for i in text]
    text = "".join(remove_inadmissible(text))        

    return text

def tidy_up_sentence(text):
                
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

def segment2quotes(text):
        
        segments = []
        seg = ""
        for i in range(len(text)):
            if text[i] == "'" and seg == "":                                    
                seg += text[i]                    
            elif text[i] == "'" and seg != "":
                seg += text[i]      
                if "'A'" == seg or "'gold standard'" == seg or "'eligible child'" == seg or "'Chuy'" == seg\
                    or "'Level 4: Do Not Travel'" == seg or "'real estate investors in President Trump@0@ inner circle.'" == seg:
                    seg = ""
                    continue        
                if "but for" in seg or "but-for" in seg:
                    seg = seg.replace("but for", "")
                    seg = seg.replace("but-for", "")
                if "'People need health insurance that is affordable and covers what they need it to, especially during a pandemic. '" in seg:
                    seg += "By stalling COVID-19 testing and trying to rip health insurance away from people, the president is knowingly putting lives at risk for political gain. Republicans and Democrats have a moral responsibility to speak out against Trump's unprecedented sabotage of Americans' health."
                segments.append(seg)               
                seg = ""
            elif seg != "":    
                seg += text[i]                    
                    
        # concatenate quoted parts if they have max 3 tokens        
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
                    filt_seg = ""
                    filter_segs.append(s)                    
                    j += 1
            else:
                filt_seg += s + " "
                j += 1
        if filt_seg != "" and filt_seg != " ":
            filter_segs.append(filt_seg)            
        filter_segs = [tidy_up_sentence(i) for i in filter_segs if i != " " and i != ""]      

        return filter_segs

def find_substring(s, s1, s2):
    
    start_index = s.find(s1)
    end_index = s.find(s2, start_index + len(s1))

    if start_index != -1 and end_index != -1:
        result = s[start_index:end_index + len(s2)]
        return result
    else:
        return None

def remove_candidates_dicts(df, removedict, column):
    
    for k in removedict.keys():
        for item in removedict[k]:
            if isinstance(item, str):                
                df.loc[df.SpeechID==k, column].values[0] = df.loc[df.SpeechID==k, column].values[0].replace(item, "")                    
            else:                
                start = item[0]
                end = item[1]
                remstr = find_substring(df.loc[df.SpeechID==k, column].values[0], start, end)
                if remstr is None:
                    print(k)
                    print(start)
                    print(end)
                    print(df.loc[df.SpeechID==k, column].values[0])                               
                df.loc[df.SpeechID==k, column].values[0] = df.loc[df.SpeechID==k, column].values[0].replace(remstr, "")
    
    return df

def extract_sentences_between_single_quotes(text):
    
    if "said Sen. Harris" in text or "issued the following statement" in text or "said Harris" in text or "said Senator Harris" in text or "Senator Harris said" in text\
        or "released the following statement" in text or "released a statement" in text \
        or "said Senator arris" in text or "crack down on gun trafficking and negligent gun dealers, and allow researchers, for the first time" in text:
        contracts = ["\'s", "s\'", "won\'t", "isn\'t", "don\'t", "can\'t", "I\'m", "doesn\'t", "we\'re", "Trump's", "Americans'", "\'ve", "aren\'t", "shouldn\'t"] 
        for i in range(len(contracts)):
            text = text.replace(contracts[i], "@{}@".format(i))        
        segs = segment2quotes(text)
        segs = [seg.replace(",.", ".") for seg in segs]
        quotedtext = " ".join(segs)
        quotedtext = quotedtext.replace("'", "")
        if quotedtext[-2:] == " .":
            quotedtext = quotedtext[:-2]
        if "other than honorable, general discharge dishonorable, t Ask, Don." in quotedtext:
            quotedtext = quotedtext.replace("other than honorable, general discharge dishonorable, t Ask, Don.", "")
        for i in range(len(contracts)):
            quotedtext = quotedtext.replace("@{}@".format(i), contracts[i])
    
        return quotedtext
    else:
        return text

def textclean_medium(text, unicode_class="NFC", potus=None):
        
    text = replace_senator(text)
    text = remove_url(text)
    text = replace_ps(text)    
    text = replace_ps2(text)    
    text = replace_transcript_init(text)
    text = replace_contentwarning_init(text)
    text = text.replace("Read Joe Biden's full plan to end gun violence at", "")
    text = text.replace("Thank you,Joseph R. Biden, Jr.47th Vice President of the United States", "")
    text = text.replace("Joe Biden would also support further rule changes to the P that would ensure deserving small businesses get all the help they need for as long as they need, including:", "")
    text = text.replace("He will ensure these workers receive:", "")
    text = text.replace("Specifically, Joe Biden will work with Congress to pass legislation that:Read Biden's full immigration plan at", "")
    text = text.replace("As President, Biden will build upon the historic progress made during the Obama-Biden administration, taking additional steps to support the rights of Black, Brown and Native farmers by:", "")
    text = text.replace("He will:", "")
    txt  = apply_unicode_normalisation(text, unicode_class)
    txt2 = clean_char_repetitions(txt)
    txt3 = unicode_cleanup(txt2)
    txt3 = txt3.strip()

    return txt3

def textclean_votesmart(text, unicode_class="NFC", potus=None):

    # remove introductory president announcement
    text = replace_beginwithtime(text)
    text = replace_allup2vp(text)
    text = replace_allup2harris(text)

    # body
    text = remove_qsession(text)
    text = remove_interruptionsession(text)
    text = remove_audiencesession(text)
    # manual fix
    if "THE PRESIDENT: Come on up, family. Come on up, family." in text:
        text = text.replace("THE PRESIDENT", "")
    if "South Court AuditoriumEisenhower Executive Office Building4:43 P.M. EST THE VICE PRESIDENT:" in text:
        text = text.replace("South Court AuditoriumEisenhower Executive Office Building4:43 P.M. EST THE VICE PRESIDENT:", "")    
    if "For further background, click here." in text:
        text = text.replace("For further background, click here.", text)
    if "For a section-by-section summary, click here." in text:
        text = text.replace("For a section-by-section summary, click here.", text)
    if "For the full text of the legislation, click here." in text:
        text = text.replace("For the full text of the legislation, click here.", text)
    if "Donald Trump: (00:00)" in text:
        text = text.replace("Donald Trump: (00:00)", "")

    text = replace_proclamation(text)   
    # start                   
    text = replace_transcript_init(text)
    text = replace_contentwarning_init(text)
    # body 
    text = replace_exec_order(text)       
    text = replace_breaktranscript(text)
    text = remove_url(text)        

    if potus is not None and potus == "KamalaHarris":
        text = replace_senator(text)

    # end
    text = remove_square_brackets(text)
    text = replace_endwithtime(text)
    text = remove_bidenend(text)        
    text = replace_allafterend(text)        
    text = remove_hashprint(text)
    text = remove_hashprint2(text)
    text = remove_hashprint3(text)
    text = remove_hashprint4(text)        
    text = replace_ps(text)    
    text = replace_ps2(text)  
    
    txt = apply_unicode_normalisation(text, unicode_class=unicode_class)
    txt2 = clean_char_repetitions(txt)
    txt3 = unicode_cleanup(txt2)
    txt3 = txt3.strip()
    
    if "Read Democratic presidential nominee Joe Biden's speech to the 2020 Democratic National Convention, as prepared for delivery: " in txt3:        
        txt3 = txt3.replace("Read Democratic presidential nominee Joe Biden's speech to the 2020 Democratic National Convention, as prepared for delivery: ", "")

    return txt3

def textclean_miller(text, unicode_class="NFC", potus=None):
        
        # remove introductory president announcement
        text = replace_beginwithtime(text)            
        text = replace_allup2vp(text)
        # body
        text = remove_qsession(text)
        text = remove_interruptionsession(text)
        text = remove_audiencesession(text)
        # manual fix
        if "THE PRESIDENT: Come on up, family. Come on up, family." in text:
            text = text.replace("THE PRESIDENT", "")
        if "AUDIENCE: H.R.3! H.R.3! H.R.3!" in text:
            text = text.replace("AUDIENCE: H.R.3! H.R.3! H.R.3!", "")
        text = replace_proclamation(text)
        # normally there should be no occurrence of the following from here on
        if len(re.findall(r'(THE VICE PRESIDENT|THE PRESIDENT|PRESIDENT TRUMP|PRESIDENT BIDEN):', text)) > 0:            
            return ""
        # start                   
        text = replace_transcript_init(text)
        text = replace_contentwarning_init(text)
        # end
        text = remove_square_brackets(text)            
        text = replace_endwithtime(text)
        text = remove_bidenend(text)
        text = replace_allafterend(text)
        text = remove_hashprint(text)
        text = remove_hashprint2(text)
        text = remove_hashprint3(text)
        text = remove_hashprint4(text)
        text = replace_ps(text)
        text = replace_ps2(text)
        
        txt = apply_unicode_normalisation(text, unicode_class=unicode_class)
        txt2 = clean_char_repetitions(txt)
        txt3 = unicode_cleanup(txt2)
        txt3 = txt3.strip()

        return txt3

def clean_miller(directoryin, directoryout, potus, cleanerfunc, unicode_class="NFC", show=False):
            
    miller = pd.read_csv("{}/{}/rawtext_{}.tsv".format(directoryin, potus, potus), sep="\t")    
    print("Miller raw - {}".format(potus))     
    print(len(miller))
    miller = clean_speech_texts(miller, cleanerfunc, unicode_class)
    print("Miller clean - {}".format(potus))     
    print(len(miller))  
    miller = miller.sort_values(by=["Date", "SpeechID"]).reset_index(drop=False)   
    
    if "index" in miller.columns:
        miller = miller.drop(columns=["index"])
    
    miller.to_csv("{}/{}/cleantext_{}.tsv".format(directoryout, potus, potus), index=False, sep="\t")
    miller.to_parquet("{}/{}/cleantext_{}.parquet".format(directoryout, potus, potus), index=False, compression=None)
    miller.to_json("{}/{}/cleantext_{}.jsonl".format(directoryout, potus, potus), orient='records', lines=True)        
    if show:
        for i, row in miller.iterrows():            
            print(i)
            print(row.SpeechURL)
            print(row.RawText)
            print("\n")
            print("\n")
            print("\n")
            time.sleep(3)
    
    return miller

def clean_votesmart(directoryin, directoryout, potus, cleanerfunc, unicode_class="NFC", show=False, droplist=None, dropcolumn=None):
    
    votesmart = pd.read_csv("{}/{}/rawtext_{}.tsv".format(directoryin, potus, potus), sep="\t")
    print("Votesmart raw - {}".format(potus))            
    print(len(votesmart))      
    if droplist is not None and dropcolumn is not None:
        votesmart = votesmart[~votesmart[dropcolumn].isin(droplist)]    
        votesmart = votesmart.reset_index(drop=True)
    print(len(votesmart))    
    votesmart = clean_speech_texts(votesmart, cleanerfunc, unicode_class, potus)       
    print("Votesmart clean - {}".format(potus))            
    print(len(votesmart))    
    if potus == "KamalaHarris":
        votesmart.CleanText = votesmart.CleanText.apply(replace_allup2harris)
        votesmart.CleanText = votesmart.CleanText.apply(extract_sentences_between_single_quotes)
        votesmart = votesmart[votesmart.CleanText != ""]
        votesmart = votesmart.reset_index(drop=True)            
        votesmart = votesmart.drop_duplicates(subset=["SpeechTitle", "CleanText"]).reset_index(drop=False)        
    votesmart = votesmart.sort_values(by=["Date", "SpeechID"]).reset_index(drop=False)
    
    if "index" in votesmart.columns:
        votesmart = votesmart.drop(columns=["index"])

    votesmart.to_csv("{}/{}/cleantext_{}.tsv".format(directoryout, potus, potus), index=False, sep="\t")
    votesmart.to_parquet("{}/{}/cleantext_{}.parquet".format(directoryout, potus, potus), index=False, compression=None)
    votesmart.to_json("{}/{}/cleantext_{}.jsonl".format(directoryout, potus, potus), orient='records', lines=True)
    if show:
        for i, row in votesmart.iterrows():            
            print(i)
            print(row.SpeechURL)
            print(row.CleanText)
            print("\n")
            print("\n")
            print("\n")
            time.sleep(3)
    
    return votesmart

def clean_cspan(directoryin, directoryout, potus, unicode_class="NFC", show=False, dropsegments=None, speechbounds=None):

    # load file, also manually cleaned
    cspan = pd.read_csv("{}/{}/rawtext_droptitles_{}_edit1.tsv".format(directoryin, potus, potus), sep="\t")

    cspandf = {"SpeechID": [], "POTUS": [], "Date": [], "SpeechTitle": [],	"Type": [], 
               "RawText": [], "CleanText": [], "SpeechURL": [], "Summary": [], "Source": [], 
               "Original Source": [], "Location": []}
    for i, row in cspan.iterrows():       
        remainingstr = None
        if speechbounds[i] is None:
            print(i+2) # row in _edit1 tsv
            print(row.SpeechURL)                                            
            continue
        if row.RawText == row.SpeechID:
            with open("{}{}/specialcleanneeded/{}.txt".format(directoryin, potus, row.SpeechID), "r") as f:
                content = f.read()
                row.RawText = content                
        if row.RawText is None:
            raise AttributeError
        s1, s2 = speechbounds[i]
        remainingstr = find_substring(row.RawText, s1, s2)       
        if s1 not in row.RawText or s2 not in row.RawText or remainingstr is None:
            print(i+2) # row in _edit1 tsv
            print(row.SpeechURL)
            print(row.RawText)
            print(speechbounds[i])                   
            raise AttributeError            
        if remainingstr is not None:
            row["SpeechSegment"] = remainingstr
            cspandf["SpeechID"].append(row["SpeechID"])
            cspandf["POTUS"].append(row["POTUS"])
            cspandf["Date"].append(row["Date"])
            cspandf["SpeechTitle"].append(row["SpeechTitle"])
            cspandf["RawText"].append(row["RawText"])
            cspandf["SpeechURL"].append(row["SpeechURL"])
            cspandf["Summary"].append(row["Summary"])
            cspandf["Source"].append(row["Source"])
            cspandf["Original Source"].append(None)
            cspandf["Location"].append(None)
            cspandf["Type"].append(row["Type"])
            cspandf["CleanText"].append(row["SpeechSegment"])
    cspandf = pd.DataFrame.from_dict(cspandf).sort_values(by=["Date", "SpeechID"]).reset_index(drop=False)

    if "index" in cspandf.columns:
        cspandf = cspandf.drop(columns=["index"])

    cspandf.to_csv("{}/{}/rawtext_droptitles_{}_edit2.tsv".format(directoryin, potus, potus), sep="\t", index=False)
    if dropsegments is not None:
        cspandf = remove_candidates_dicts(cspandf, dropsegments, "CleanText")     
    if potus == "DonaldTrump":   
        cspandf.CleanText = cspandf.CleanText.apply(remove_trump)
    if potus == "MikePence":   
        cspandf.CleanText = cspandf.CleanText.apply(remove_pence)       
    if potus == "JoeBiden":   
        cspandf.CleanText = cspandf.CleanText.apply(remove_biden)       
    cspandf.CleanText = cspandf.CleanText.apply(remove_dots)
    cspandf.CleanText = cspandf.CleanText.apply(remove_square_brackets)
    cspandf.CleanText = cspandf.CleanText.apply(remove_round_brackets)    

    def clean_with_encodingclass(x) : return apply_unicode_normalisation(x, unicode_class)
    def clean_strip(x) : return x.strip()
    cspandf.CleanText = cspandf.CleanText.apply(clean_with_encodingclass)    
    cspandf.CleanText = cspandf.CleanText.apply(clean_char_repetitions)        
    cspandf.CleanText = cspandf.CleanText.apply(unicode_cleanup)        
    cspandf.CleanText = cspandf.CleanText.apply(clean_strip)        
    cspandf = cspandf.sort_values(by=["Date", "SpeechID"]).reset_index(drop=False)

    if "index" in cspandf.columns:
        cspandf = cspandf.drop(columns=["index"])
    if "level_0" in cspandf.columns:
        cspandf = cspandf.drop(columns=["level_0"])

    cspandf.to_csv("{}/{}/cleantext_{}.tsv".format(directoryout, potus, potus), sep="\t", index=False)
    cspan.to_parquet("{}/{}/cleantext_{}.parquet".format(directoryout, potus, potus), index=False, compression=None)
    cspan.to_json("{}/{}/cleantext_{}.jsonl".format(directoryout, potus, potus), orient='records', lines=True)
    if show:    
        for i, row in cspandf.iterrows():        
            print(i)
            print(row.SpeechURL)
            print(row.CleanText)
            print("\n")
            print("\n")
            print("\n")
            time.sleep(3)

def clean_medium(directoryin, directoryout, potus, cleanerfunc, unicode_class="NFC", show=False, droplist=None, dropcolumn=None):

    medium = pd.read_csv("{}/{}/rawtext_{}.tsv".format(directoryin, potus, potus), sep="\t")
    print("Medium raw - {}".format(potus))            
    print(len(medium))      
    if droplist is not None and dropcolumn is not None:
        medium = medium[~medium[dropcolumn].isin(droplist)]    
        medium = medium.reset_index(drop=True)
    medium = clean_speech_texts(medium, cleanerfunc, unicode_class)
    print("Medium clean - {}".format(potus))
    print(len(medium)) 
    medium = medium.sort_values(by=["Date", "SpeechID"]).reset_index(drop=False)
    
    if "index" in medium.columns:
        medium = medium.drop(columns=["index"])
    
    medium.to_csv("{}/{}/cleantext_{}.tsv".format(directoryout, potus, potus), index=False, sep="\t")
    medium.to_parquet("{}/{}/cleantext_{}.parquet".format(directoryout, potus, potus), index=False, compression=None)
    medium.to_json("{}/{}/cleantext_{}.jsonl".format(directoryout, potus, potus), orient='records', lines=True) 
    if show:
        for i, row in medium.iterrows():
            print(i)
            print(row.SpeechURL)
            print(row.CleanText)
            print("\n")
            print("\n")
            print("\n")
            time.sleep(3)

