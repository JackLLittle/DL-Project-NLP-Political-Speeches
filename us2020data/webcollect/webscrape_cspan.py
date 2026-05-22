################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

import time
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import os
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from pathlib import Path
import sys
import re
import pathlib

MONTHS = {"Jan": "1", "Feb": "2", "Mar": "3", "Apr": "4", "May": "5", "Jun": "6", "Jul": "7",
          "Aug": "8", "Sep": "9", "Oct": "10", "Nov": "11", "Dec": "12"}

def get_president_speech(potus, url, chrome_options, potusspeech_cnt=0, speech_id_init="xyz", date=None):

    url = "{}&action=getTranscript&transcriptType=cc".format(url)
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)  
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Connection': 'keep-alive',
                        'Pragma': 'no-cache', 'Cache-Control': 'no-cache',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
    try:
        ret = urlopen(req)
        http_code = ret.getcode()
    except HTTPError as err:
        browser.quit()
        print("Exciting with error code: {}".format(err.code))
        sys.exit(1)
    else:
        print("HTTP response code: {}".format(http_code))

    browser.get(url)    
    time.sleep(0.5)
    
    def remove_qa_session(x) : 
        finds =  re.search(r'^(.+?)(?s).Q: ', x)  #'^(.+?) Q: '
        if finds is not None:
            return finds.group(1)
        else:
            return x
    def replace_allup2presidentannounce(x) : return re.sub(r'^.*?THE PRESIDENT:', '', x)
    def replace_presidentannounce1(x) : return re.sub(r'^\nTranscript\nTHE PRESIDENT:', ' ', x)
    def replace_presidentannounce2(x) : return re.sub(r'^[\s*\n*]Transcript[\s*\n*]', ' ', x)
    def replace_newlines(x) : return re.sub(r'[\n*\xa0*\n*]', ' ', x)
    def replace_dashes(x) : return re.sub(r'—w*', ', ', x)
    def replace_dashes2(x) : return re.sub(r'—+', ', ', x)
    def replace_dashes3(x) : return re.sub(r'--+', ', ', x)    
    def replace_spaces(x) : return re.sub(r'\s+', ' ', x)

    soup = BeautifulSoup(browser.page_source, "html.parser")
    try:
        transcript_part = soup.find("table").find("tbody")
    except:
        print(url)
        return None, None
    transcript = transcript_part.find_all("tr")
    tt = ""
    for p in transcript:
        pp = p.find_all("a", class_="transcript-time-seek")
        for ppp in pp:
            ppp = ppp.get_text().strip()
            if "Show Full Text" in ppp or "Show Less Text" in ppp or ppp=="":
                continue
            if ppp[-1] == "…":
                ppp = ppp[:-1] + "."
            if "…" in ppp:
                ppp = ppp.replace("…", " ")            
            tt += ppp.strip() + " "
    
    tt = tt.replace("Show Full Text", "").replace("Show Less Text", "")
    transcript = tt    
    transcript = remove_qa_session(transcript)
    transcript = replace_presidentannounce1(transcript)
    transcript = replace_presidentannounce2(transcript)
    transcript = replace_newlines(transcript)
    transcript = replace_allup2presidentannounce(transcript)
    transcript = replace_dashes(transcript)
    transcript = replace_dashes2(transcript)
    transcript = replace_dashes3(transcript)
    transcript = replace_spaces(transcript)
    transcript = transcript.strip()

    datetimestamp = date
    speechID = "{}{}{}{}{}".format(speech_id_init, datetimestamp.day, datetimestamp.month, datetimestamp.year, potusspeech_cnt)

    browser.quit()

    return transcript, speechID
      


      
if __name__ == "__main__":

    cwd = pathlib.Path.cwd()
    DIR_out = "{}/cspan/".format(cwd)
    Path(DIR_out).mkdir(parents=True, exist_ok=True)
    merge_url_csvs = False
    
    
    print("Starting collecting speeches from: C-SPAN")
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.headless = True
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--profile-directory=Default')
    chrome_options.add_argument("--incognito")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("window-size=1280,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/44.0.2403.157 Safari/537.36")
    
    potusnames = ["Mike Pence", "Kamala Harris", "Donald Trump", "Joe Biden"]
    for potus in potusnames:
        dataset = {"SpeechID": [], "POTUS": [], "Date": [], "SpeechTitle": [], 
               "RawText": [], "SpeechURL": [], "Summary": [], "Source": [], "Type": []}
        potusspeech_cnt = 0
        speech_id_init = "CSPAN"
        nameparts = potus.replace(".", "").split()
        if len(nameparts) > 2:
            speech_id_init += "{}{}{}".format(nameparts[0][0], nameparts[1][0], nameparts[2][0])
        else:
            speech_id_init += "{}{}".format(nameparts[0][0], nameparts[1][0])
        datadir = "{}/{}".format(DIR_out, potus.replace(".", "").replace(" ", ""))        
        datain = pd.read_csv("{}/cspan_{}.csv".format(datadir, potus.replace(".", "").replace(" ", "")))
        for i, row in datain.iterrows():
            if i == 36 and row["publicId"] == "462373-1":
                row["link"] = "https://www.c-span.org/video/?462373-1/vice-president-pence-remarks-christians-united-israel-conference"    
                row["date"] = "2019-07-08"
                row["videoTypeId"] = "speech"
            speechurl = row["link"]  
            if speechurl == "nan" or pd.isna(speechurl) or speechurl is None:
               if i==37:
                   continue       
            title = row["title"]
            summary = row["description"]
            print(speechurl)           
            transcript, speechID = get_president_speech(potus, speechurl, 
                                                        chrome_options, potusspeech_cnt=potusspeech_cnt, 
                                                        speech_id_init=speech_id_init, date=pd.Timestamp(row["date"]))
            if transcript is None and speechID is None:
                continue
            dataset["SpeechURL"].append(speechurl)
            dataset["Source"].append(row["publicId"])
            dataset["POTUS"].append(potus)
            dataset["Date"].append(pd.Timestamp(row["date"]))
            dataset["SpeechTitle"].append(row["title"])    
            potusspeech_cnt = potusspeech_cnt + 1
            print(speechurl)
            print(title)
            print(speechID)        
            dataset["Summary"].append(summary)
            dataset["RawText"].append(transcript)
            dataset["SpeechID"].append(speechID)
            dataset["Type"].append(row["videoTypeId"])
        datasetout_df_potus = pd.DataFrame.from_dict(dataset)    
        print(datasetout_df_potus)
        d_potus = datasetout_df_potus.sort_values(['Date'],ascending=True).groupby('POTUS')
        datasetout_df_potus = d_potus.head(len(datasetout_df_potus)).reset_index(drop=True) 
        datasetout_df_potus.to_csv("{}/{}/rawtext_{}.tsv".format(DIR_out, 
                            potus.replace(" ", ""), potus.replace(" ", "")), index=False, sep="\t")   
        time.sleep(2)
    