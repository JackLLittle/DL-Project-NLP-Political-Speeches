################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

from __future__ import print_function
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
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


def get_president_speech_list(url, potus, chrome_options, keywords=[]):

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
    lenOfPage = browser.execute_script("window.scrollTo(0, document.body.scrollHeight/7);var lenOfPage=document.body.scrollHeight/7;return lenOfPage;")   
    time.sleep(5)
    browser.find_element(By.XPATH, "//*[@id='edit-field-president-target-id']/div/div[{}]".format(potus)).click()
    time.sleep(5)    
    lenOfPage = browser.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")  
    match=False
    differ = 0
    while(match==False):
        lastCount = lenOfPage
        time.sleep(4)
        lenOfPage = browser.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        print(lastCount, lenOfPage, differ)
        if lenOfPage - lastCount > differ:
            differ = lenOfPage - lastCount
        elif differ == lenOfPage - lastCount or lastCount==lenOfPage:
            match=True  
    time.sleep(4)
    soup = BeautifulSoup(browser.page_source, "html.parser")
    speeches_out = []
    speech_list = soup.find("div", class_="rows-wrapper").find_all("div", class_="views-row")
    print(potus)
    for speech in speech_list:
        content = speech.find("span").find("a")
        title = content.get_text()
        if len(keywords) > 0:
            of_interest = [k for k in keywords if k in title.lower()]
            if len(of_interest) == 0:
                continue 
        link = content["href"]
        date = title.split(":")[0]
        title = title.split(":")[1].replace(":", "").strip()
        speeches_out.append((title, date, link))
        print(link)

    browser.quit()

    return speeches_out
      

def get_president_speech(url, chrome_options, potusspeech_cnt=0, speech_id_init="xyz"):

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
    # def replace_escapeapostr(x) : return re.sub(r"\'s", "", x)

    soup = BeautifulSoup(browser.page_source, "html.parser")
    
    transcript_part = soup.find("div", class_="transcript-inner")
    transcript = transcript_part.get_text()
    
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

    title_part = soup.find("h2",class_="presidential-speeches--title").get_text()
    title_part = replace_newlines(title_part).strip()
    date = title_part.split(":")[0]
    title = title_part.split(":")[1].replace(":", "").strip()

    datetimestamp = pd.Timestamp(date)
    speechID = "{}{}{}{}{}".format(speech_id_init, datetimestamp.day, datetimestamp.month, datetimestamp.year, potusspeech_cnt)

    try:
        source = soup.find("div",class_="speech-location-container").find("span",class_="speech-loc").get_text().strip()
    except AttributeError:
        print("No source information")
        print(url)
        print("No source information")
        source = "NoSourceInformation"
    try:
        summary = soup.find("div",class_="about-sidebar--intro").get_text().strip()    
        summary = replace_newlines(summary)
        summary = replace_dashes(summary)
        summary = replace_dashes2(summary)
        summary = replace_spaces(summary).strip()
    except AttributeError:
        summary = "EmptySummary"

    browser.quit()

    return datetimestamp, title, source, summary, transcript, speechID
      


if __name__ == "__main__":

    cwd = pathlib.Path.cwd()
    DIR_out = "{}/millercenter/".format(cwd)
    Path(DIR_out).mkdir(parents=True, exist_ok=True)

    potusnames = ["Donald Trump", "Joe Biden"]
    potusno = {"Donald Trump": 44, "Joe Biden": 45}
    url = "https://millercenter.org/the-presidency/presidential-speeches"

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
    for potus in potusnames:
        dataset_potus = {"SpeechID": [], "POTUS": [], "Date": [], "SpeechTitle": [], "RawText": [],
                         "SpeechURL": [], "Summary": [], "Source": []}
        potusspeech_cnt = 0
        nameparts = potus.replace(".", "").split()
        if len(nameparts) > 2:
            speech_id_init = "MC{}{}{}".format(nameparts[0][0], nameparts[1][0], nameparts[2][0])
        else:
            speech_id_init = "MC{}{}".format(nameparts[0][0], nameparts[1][0])

        speeches_out = get_president_speech_list(url, potusno[potus], chrome_options, keywords)
        for i in speeches_out:
            if (pd.Timestamp(i[1]) < pd.Timestamp("2019-01-01")) or (pd.Timestamp(i[1]) > pd.Timestamp("2021-01-31")):
                continue
            dataset["POTUS"].append(potus)
            dataset["Date"].append(pd.Timestamp(i[1]))
            dataset["SpeechTitle"].append(i[0])
            dataset_potus["POTUS"].append(potus)
            dataset_potus["Date"].append(pd.Timestamp(i[1]))
            dataset_potus["SpeechTitle"].append(i[0])
            speechurl = i[2]
            dataset["SpeechURL"].append(speechurl)
            dataset_potus["SpeechURL"].append(speechurl)
            
            print(speechurl)           
            datetimestamp, title, source, summary, transcript, speechID = get_president_speech(speechurl, 
                                                        chrome_options, potusspeech_cnt=potusspeech_cnt, 
                                                        speech_id_init=speech_id_init)
            potusspeech_cnt = potusspeech_cnt + 1
            print(speechurl)
            print(title)
            print(speechID)
            assert dataset["Date"][-1] == datetimestamp
            dataset["Source"].append(source)
            dataset["Summary"].append(summary)
            dataset["RawText"].append(transcript)
            dataset["SpeechID"].append(speechID)
            dataset_potus["Source"].append(source)
            dataset_potus["Summary"].append(summary)
            dataset_potus["RawText"].append(transcript)
            dataset_potus["SpeechID"].append(speechID)
            time.sleep(2)

        datasetout_df_potus = pd.DataFrame.from_dict(dataset_potus)    
        print(datasetout_df_potus)
        d_potus = datasetout_df_potus.sort_values(['Date'],ascending=True).groupby('POTUS')
        datasetout_df_potus = d_potus.head(len(datasetout_df_potus)).reset_index(drop=True) 
        datasetout_df_potus.to_csv("{}/{}/rawtext_{}.tsv".format(DIR_out, 
                            potus.replace(".", "").replace(" ", ""), potus.replace(".", "").replace(" ", "")), 
                            index=False, sep="\t")
