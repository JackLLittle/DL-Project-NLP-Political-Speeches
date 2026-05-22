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


def get_president_speech_list(url, potus, chrome_options, keywords=[], p=1):

    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)  
    speeches_out = []

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
    time.sleep(1)
    soup = BeautifulSoup(browser.page_source, "html.parser")
    try:
        pagestotal = soup.find("div", {"id": "mainStatementsContent"}).find("div", class_="col mb-2").find("h7").get_text().strip().split()[3]
    except:
        browser.quit()
        return speeches_out
    print(p, pagestotal)
    if p > int(pagestotal):
        browser.quit()
        return speeches_out

    speech_list = soup.find("table", class_="table statements-table-header statements-table").find("tbody").find_all("tr")
    print(potus)
    for speech in speech_list:
        content = speech.find("td", class_="statements-table-data").find("a")
        title = content.get_text()
        if len(keywords) > 0:
            of_interest = [k for k in keywords if k in title.lower()]
            if len(of_interest) == 0:
                continue 
        link = content["href"]
        date = speech.find_all("td")[0].get_text().strip()
        dateparts = date.split("/")
        date = pd.Timestamp("{}-{}-{}".format(dateparts[2], dateparts[0], dateparts[1]))
        speeches_out.append((title, date, link))
        print(link)

    browser.quit()

    return speeches_out
      

def get_president_speech(url, chrome_options, potusspeech_cnt=0, speech_id_init="xyz", date=None):

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
    except:
        print("sleep", ret.getcode() )
        time.sleep(360)
        ret = urlopen(req)
        http_code = ret.getcode()
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

    def replace_allup2harrisannounce(x) : return re.sub(r'^.*?(VICE PRESIDENT HARRIS|VICE PRESIDENT PENCE):', '', x)
    def replace_allup2vp(x) : return re.sub(r'^.*?THE VICE PRESIDENT:', '', x)
    def replace_vpresidentannounce1(x) : return re.sub(r'^\nTHE VICE PRESIDENT:', ' ', x)
    def replace_presidentannounce1(x) : return re.sub(r'^\nTHE PRESIDENT:', ' ', x)
    def replace_newlines(x) : return re.sub(r'[\n*\xa0*\n*]', ' ', x)
    def replace_dashes(x) : return re.sub(r'—w*', ', ', x)
    def replace_dashes2(x) : return re.sub(r'—+', ', ', x)
    def replace_dashes3(x) : return re.sub(r'--+', ', ', x)    
    def replace_spaces(x) : return re.sub(r'\s+', ' ', x)

    soup = BeautifulSoup(browser.page_source, "html.parser")
    
    transcript_part = soup.find("div", {"id": "publicStatementDetailSpeechContent"})
    try:
        originalsource = transcript_part.find("strong").find("a")["href"]
    except:
        originalsource = None
    transcript = transcript_part.get_text()
    
    if len(re.findall(r'THE VICE PRESIDENT:', transcript)) > 1 \
        or len(re.findall(r'HARRIS:', transcript)) > 1 \
            or len(re.findall(r'VICE PRESIDENT HARRIS:', transcript)) > 1\
             or len(re.findall(r'PENCE:', transcript)) > 1 \
                or len(re.findall(r'VICE PRESIDENT PENCE:', transcript)) > 1:
        print(url)
        return None, None, None, None, None, None
    if "Statement by Hunter Biden" in transcript\
          or "Statement from the Biden-Harris Transition" in transcript:
        print(url)
        return None, None, None, None, None, None

    transcript = remove_qa_session(transcript)
    transcript = replace_allup2vp(transcript)
    transcript = replace_vpresidentannounce1(transcript)
    transcript = replace_presidentannounce1(transcript)
    transcript = replace_newlines(transcript)
    transcript = replace_allup2harrisannounce(transcript)
    transcript = replace_dashes(transcript)
    transcript = replace_dashes2(transcript)
    transcript = replace_dashes3(transcript)    
    transcript = replace_spaces(transcript)
    transcript = transcript.strip()
    if transcript[-6:] == "Source":
        transcript = transcript[:-6].strip()

    details_part = soup.find_all("div",class_="col-md-6 text-left")
    givenby = details_part[0].find("div", {"id":"statementDetailTruncatedSpeakerList"}).get_text().replace("By:", "").strip()
    if "Joe Biden, Jr." in givenby and ("SEE MORE SPEAKERS" in details_part[0].get_text() or len(givenby.split(",")) > 2):
        print(url)
        # ipdb.set_trace()
        return None, None, None, None, None, None
    elif "Joe Biden, Jr." not in givenby and ("SEE MORE SPEAKERS" in details_part[0].get_text() or len(givenby.split(",")) > 1):
        print(url)
        return None, None, None, None, None, None

    try:
        location = details_part[0].find_all("div", class_="col")[2].get_text().replace("Location:", "").strip()
    except:
        location = None
    try:
        issues = details_part[1].find("div", class_="col").get_text().replace("Issues:", "").strip()
    except:
        issues = None

    datetimestamp = date
    # VS for Vote Smart
    speechID = "VS{}{}{}{}{}".format(speech_id_init, datetimestamp.day, datetimestamp.month, datetimestamp.year, potusspeech_cnt)

    browser.quit()

    return transcript, speechID, givenby, location, issues, originalsource
      


if __name__ == "__main__":

    cwd = pathlib.Path.cwd()
    DIR_out = "{}/votesmart/".format(cwd)
    Path(DIR_out).mkdir(parents=True, exist_ok=True)

    potusnames = ["joe-biden-jr", "donald-trump", "mike-pence", "kamala-harris"]
    speech_types = {"newsarticle": 8,
                    "statement": 6,
                    "speech": 1,                    
                    "op-ed": 9}
    dataset = {"SpeechID": [], "POTUS": [], "Date": [], "SpeechTitle": [], 
               "Type": [], "RawText": [], "SpeechURL": [], "Summary": [], 
               "Source": [], "Location": [], "Original source": []}
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.headless = True
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--profile-directory=Default')
    chrome_options.add_argument("--incognito")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("window-size=1280,800")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/44.0.2403.157 Safari/537.36")
    
    keywords = []
    for potus in potusnames:
        dataset_potus = {"SpeechID": [], "POTUS": [], "Date": [], "SpeechTitle": [], "Type": [], "RawText": [],
                         "SpeechURL": [], "Summary": [], "Source": [], "Location": [], "Original source": []}
        potusspeech_cnt = 0
        nameparts = potus.replace("-", " ").split()
        speech_id_init = "{}{}".format(nameparts[0][0].upper(), nameparts[1][0].upper())
        for speechtype in speech_types.keys():
            speeches_out = []
            for p in range(1, 200, 1):
                if potus == "kamala-harris":
                    potus = "Kamala Harris"
                    url = "https://justfacts.votesmart.org/candidate/public-statements/120012/{}?start=2019-01-01&end=2021-01-31&speechType={}&p={}".format(potus, 
                                                                                                                                    speech_types[speechtype], p)
                elif potus == "mike-pence":
                    potus = "Mike Pence"
                    url = "https://justfacts.votesmart.org/candidate/public-statements/34024/{}?start=2019-01-01&end=2021-01-31&speechType={}&p={}".format(potus, 
                                                                                                                                    speech_types[speechtype], p)
                elif potus == "joe-biden-jr":
                    potus = "Joe Biden"
                    url = "https://justfacts.votesmart.org/candidate/public-statements/53279/{}?start=2019-01-01&end=2021-01-31&speechType={}&p={}".format(potus,
                                                                                                                                    speech_types[speechtype], p)
                elif potus == "donald-trump":
                    potus = "Donald Trump"
                    url = "https://justfacts.votesmart.org/candidate/public-statements/15723/{}?start=2019-01-01&end=2021-01-31&speechType={}&p={}".format(potus,
                                                                                                                                    speech_types[speechtype], p)

                print("Starting collecting speeches from: {}...".format(url))
                speeches_outp = get_president_speech_list(url, potus, chrome_options, keywords, p)
               
                if len(speeches_outp) > 0:
                    speeches_out.extend(speeches_outp) 
                else:
                    break
            for i in speeches_out:
                if (i[1] < pd.Timestamp("2019-01-01")) or (i[1] > pd.Timestamp("2021-01-31")):
                    continue
                speechurl = i[2]
                transcript, speechID, givenby, location, issues, originalsource = get_president_speech(speechurl, 
                                                            chrome_options, 
                                                            potusspeech_cnt=potusspeech_cnt, 
                                                            speech_id_init=speech_id_init, date=i[1])
                if transcript is None and speechID is None and givenby is None and location is None and issues is None and originalsource is None:
                    print(speechurl)
                    continue
                dataset["POTUS"].append(potus)
                dataset["Date"].append(i[1])
                dataset["SpeechTitle"].append(i[0])
                dataset["SpeechURL"].append(speechurl)
                dataset["Type"].append(speechtype)
                dataset["Source"].append(givenby)
                dataset["Summary"].append(issues)
                dataset["RawText"].append(transcript)
                dataset["SpeechID"].append(speechID)
                dataset["Location"].append(location)
                dataset["Original source"].append(originalsource)
                
                dataset_potus["POTUS"].append(potus)
                dataset_potus["Date"].append(i[1])
                dataset_potus["SpeechTitle"].append(i[0])
                dataset_potus["SpeechURL"].append(speechurl)
                dataset_potus["Type"].append(speechtype)           
                dataset_potus["Source"].append(givenby)
                dataset_potus["Summary"].append(issues)
                dataset_potus["RawText"].append(transcript)
                dataset_potus["SpeechID"].append(speechID)
                dataset_potus["Location"].append(location)
                dataset_potus["Original source"].append(originalsource)
                print(len(dataset_potus["RawText"]), len(dataset["RawText"]))
                potusspeech_cnt = potusspeech_cnt + 1
                title = i[0]
                # print(speechurl)
                print(title)
                print(speechID)
                assert dataset["Date"][-1] == i[1]
                
                time.sleep(4)
        
        datasetout_df_potus = pd.DataFrame.from_dict(dataset_potus)    
        print(datasetout_df_potus)        
        d_potus = datasetout_df_potus.sort_values(['Date'],ascending=True).groupby('POTUS')
        datasetout_df_potus = d_potus.head(len(datasetout_df_potus)).reset_index(drop=True) 
        Path("{}/{}/".format(DIR_out, potus.replace(" ", ""))).mkdir(parents=True, exist_ok=True)
        datasetout_df_potus.to_csv("{}/{}/rawtext_{}.tsv".format(DIR_out, 
                            potus.replace(" ", ""), potus.replace(" ", "")), index=False, sep="\t")