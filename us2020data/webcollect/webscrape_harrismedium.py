################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

from __future__ import print_function
import time
from selenium import webdriver
from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from urllib.error import HTTPError
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

def get_harris_speech_list(url, chrome_options, keywords=[]):

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
    time.sleep(5)    
    lenOfPage = browser.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;") 
    time.sleep(4)
    match=False
    while(match==False):
        lastCount = lenOfPage
        time.sleep(4)
        lenOfPage = browser.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        if lastCount==lenOfPage:
            match=True  
    time.sleep(4)
    soup = BeautifulSoup(browser.page_source, "html.parser")
    speeches_out = []
    speech_list = soup.find("main").find_all("article")
    mp = 0
    for speech in speech_list:
        content = speech.find("div", class_="l").find_all("div")
        try:
            date = content[0].find("p").find("span").get_text()
        except:
            date = content[0].find("div").find_all("div")[1].find("div", class_="l").find("p").find_all("span")[1].get_text()
        pdate = pd.Timestamp(date)        
        if pdate.month != int(MONTHS[date.replace(",", "").split()[0]]) \
                or pdate.day != int(date.replace(",", "").split()[1]) \
                or pdate.year != int(date.replace(",", "").split()[2]):
            month = int(MONTHS[date.replace(",", "").split()[0]])
            day = int(date.replace(",", "").split()[1])
            year = pdate.year != int(date.replace(",", "").split()[2])
            pdate = pd.Timestamp(year=year, month=month, day=day)        
        titlepart = content[1].find("a")
        title = content[1].find("h2").get_text().strip()
        if len(keywords) > 0:
            of_interest = [k for k in keywords if k in title.lower()]
            if len(of_interest) == 0:
                continue 
        link = "https://kamalaharris.medium.com{}".format(titlepart["href"])
        try:
            if "Member-only" in content[0].get_text().strip():
                print("member")
                print(link)
                mp += 1
                continue
        except:
            pass
        date = pdate        
        speeches_out.append((title, date, link))
        print(link)

    browser.quit()
    print(mp)
    return speeches_out
      

def get_president_speech(potus, url, chrome_options, potusspeech_cnt=0, speech_id_init="xyz", date=None):

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
    
    transcript_part = soup.find("section")
    try:
        summary = transcript_part.find("h2", class_="pw-subtitle-paragraph").get_text().strip()    
        summary = replace_newlines(summary)
        summary = replace_dashes(summary)
        summary = replace_dashes2(summary)
        summary = replace_spaces(summary).strip()
    except AttributeError:
        summary = "EmptySummary"

    transcript = transcript_part.find_all("p", class_="pw-post-body-paragraph")
    tt = ""
    for p in transcript:
        pp = p.get_text().strip()
        if pp[-1] == "…":
            pp = pp[:-1] + "."
        if "…" in pp:
            pp = pp.replace("…", " ")
        if pp[-1] not in [",", "?", ";", ".", ":", " ", "!"] and pp[-2] not in [",", "?", ";", ".", ":", "!"] and transcript.index(p)!=len(transcript)-1:
            if tt == "":
                pp = pp[:-1] + "."
            else:
                pp = pp[:-1] + ","                    
        tt += pp.strip()
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

    source = "NoSourceInformation"
    browser.quit()

    return datetimestamp, source, summary, transcript, speechID
      


if __name__ == "__main__":

    cwd = pathlib.Path.cwd()
    DIR_out = "{}/medium/".format(cwd)
    Path(DIR_out).mkdir(parents=True, exist_ok=True)
    url = "https://kamalaharris.medium.com/"

    dataset = {"SpeechID": [], "POTUS": [], "Date": [], "SpeechTitle": [], "RawText": [], "SpeechURL": [], "Summary": [], "Source": []}    
    print("Starting collecting speeches from: {}...".format(url))
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
    keywords = []
    potusspeech_cnt = 0
    speech_id_init = "MEKH"
    
    speeches_out = get_harris_speech_list(url, chrome_options, keywords)
    for i in speeches_out:
        if (i[1] < pd.Timestamp("2019-01-01")) or (i[1] > pd.Timestamp("2021-01-31")):
            continue
        dataset["POTUS"].append("Kamala Harris")
        dataset["Date"].append(i[1])
        dataset["SpeechTitle"].append(i[0])        
        speechurl = i[2]
        dataset["SpeechURL"].append(speechurl)
        dataset["Source"].append("Kamala Harris Medium")
        title = i[0]
        print(speechurl)           
        datetimestamp, source, summary, transcript, speechID = get_president_speech("Kamala Harris", speechurl, 
                                                    chrome_options, potusspeech_cnt=potusspeech_cnt, 
                                                    speech_id_init=speech_id_init, date=i[1])
        potusspeech_cnt = potusspeech_cnt + 1
        print(speechurl)
        print(title)
        print(speechID)        
        dataset["Summary"].append(summary)
        dataset["RawText"].append(transcript)
        dataset["SpeechID"].append(speechID)
        
        time.sleep(2)

    datasetout_df = pd.DataFrame.from_dict(dataset)
    print(datasetout_df)
    d = datasetout_df.sort_values(['Date'],ascending=True).groupby('POTUS')
    datasetout_df = d.head(len(datasetout_df)).reset_index(drop=True) 
    datasetout_df.to_csv("{}/rawtext_KamalaHarris.tsv".format(DIR_out), index=False, sep="\t")
