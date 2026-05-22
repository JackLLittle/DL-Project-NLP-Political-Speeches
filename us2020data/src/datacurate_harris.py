################################################################
################################################################

# Copyright (C) 2024 Ioannis Chalkiadakis - All Rights Reserved.
# Subject to the MIT license.

################################################################
################################################################

import pandas as pd
from us2020data.src.utils import textclean_votesmart, textclean_medium, \
                                    clean_votesmart, clean_cspan, clean_medium
import pathlib


if __name__ == "__main__":
    
    drop_column = "SpeechID"
    potus = "KamalaHarris"
    toplevel = pathlib.Path.cwd()

    # Vote Smart
    directoryin = "{}/us2020data/data/votesmart/".format(toplevel)
    directoryout = "{}/us2020data/data_clean/votesmart/".format(toplevel)
    pathlib.Path("{}/{}".format(directoryout, potus)).mkdir(parents=True, exist_ok=True)       
    drop_speechID = pd.read_csv("{}/{}/drop_speech_id.tsv".format(directoryin, potus), sep="\t")   
    drop_speechID = drop_speechID.SpeechIDdrop.values.tolist()       
    clean_votesmart(directoryin, directoryout, potus, textclean_votesmart, "NFC", True, drop_speechID, drop_column)

    # C-SPAN
    directoryin = "{}/us2020data/data/cspan/".format(toplevel)
    directoryout = "{}/us2020data/data_clean/cspan/".format(toplevel)       
    pathlib.Path("{}/{}".format(directoryout, potus)).mkdir(parents=True, exist_ok=True)   
    cspan = pd.read_csv("{}/{}/rawtext_{}.tsv".format(directoryin, potus, potus), sep="\t")            
    drop_speechID = pd.read_csv("{}/{}/drop_speech_id.tsv".format(directoryin, potus), sep="\t")       
    drop_speechID = drop_speechID.SpeechIDdrop.values.tolist()    
    cspan = cspan[~cspan[drop_column].isin(drop_speechID)] 
    cspan = cspan.reset_index(drop=True)         
    cspan.to_csv("{}/{}/rawtext_droptitles_{}.tsv".format(directoryin, potus, potus), index=False, sep="\t")   

    #####################################
    # At this point, some manual curation was needed before proceeding to the next cleaning steps,
    # to identify which speeches were captioned well-enough, their starting and ending points
    # and the speakers segments.
    #####################################

    speechbounds = [("THANK YOU. THANK YOU, THANK YOU, THANK YOU. MY HEART IS FULL RIGHT NOW.", "AND LET'S DO IT TOGETHER, AND LET'S START NOW, AND I THANK YOU AND GOD BLESS YOU, AND GOD BLESS THE UNITED STATES OF AMERICA! [CHEERS AND APPLAUSE]"),
                    ("HI, EVERYONE. HI! IT'S GREAT TO BE WITH YOU!", "[APPLAUSE] THAT IS WHAT WE WILL TELL THEM. [APPLAUSE] OK, QUESTIONS?"),
                    ("SO THIS IS MY FIRST OFFICIAL TRIP TO NEW HAMPSHIRE AS A CANDIDATE FOR PRESIDENT OF THE UNITED STATES", "I WOULD LOVE TO TAKE QUESTIONS FROM YOU."),
                    ("WHAT 'S UP, DARTMOUTH?", "I WOULD SUGGEST TO YOU THEY ARE NONPARTISAN. BUT WE HAVE TO HAVE REAL LEADERSHIP AT THE TOP, AND THAT IS WHY I AM RUNNING FOR PRESIDENT. [CHEERS AND APPLAUSE] THANK YOU ALL VERY MUCH."),
                    None,
                    ("THANK YOU SO VERY MUCH. PLEASE, CAN WE GIVE IT UP FOR ONE OF THE GREAT LEADERS OF IOWA AND AMERICA.", "WITH ALL THAT IN OUR HEARTS AND OUR SOULS, I PROMISE YOU, DES MOINES, WE WILL WIN THIS ELECTION."),
                    ("HELLO EVERYONE. IT IS GREAT TO BE IN THE LAKES REGION.", "THANK YOU, EVERYONE. THANK YOU, EVERYONE. I GUESS WE ARE HAVING SOME TECHNICAL DIFFICULTIES, SO WE ARE NOT GOING TO HAVE THE QUESTIONS"),
                    ("HI EVERYONE. WOW, I AM AT THE IOWA STATE FAIR. ON THE SOAPBOX.", "THAT IS WHO WE ARE. MY TIME IS UP. THANK YOU, GUYS. THANK YOU."),
                    ("I WANT TO THANK YOU PUBLICLY, AND I HOPE I DO OFTEN ENOUGH PRIVATELY", "THIS IS A FIGHT THAT IS NOT ONLY FOR THE SOUL OF OUR COUNTRY, THIS IS A FIGHT BORN OUT OF LOVE OF COUNTRY AND THIS IS A FIGHT WE WILL WIN. THANK YOU."),
                    ("WHAT IS UP, NEW HAMPSHIRE DEMOCRATS? HELLO, WHAT IS UP?", "THIS IS A FIGHT BORN OUT OF LOVE OF COUNTRY, AND THIS IS A FIGHT NEW HAMPSHIRE DEMOCRATS, THAT WE WILL WIN."),
                    ("HOW ARE YOU DOING. I FEEL LIKE I SHOULD START TELLING JOKES. [LAUGHTER]", "THAT IS THE AMERICA WE ARE FIGHTING FOR AND I BELIEVE WE WILL WIN. THANK YOU, GUYS."),
                    ("THANK YOU. THANK YOU, ANN. WHAT A WONDERFUL INTRODUCTION. THIS IS WHAT YOU DO ALWAYS AND I KNOW THAT ABOUT YOU.", "AND I DO BELIEVE IT WILL BE THAT SPIRIT AND APPROACH THAT BRINGS US TO THE POINT OF ACTUALLY WINNING THIS CAMPAIGN SO THANK YOU ALL VERY MUCH. I REALLY APPRECIATE YOU. [APPLAUSE]"),
                    ("WHAT'S UP, DETROIT! IT IS GOOD TO BE BACK.", "AND JOE BIDEN IS ON THE BALLOT IN 2020. WITH THAT I INTRODUCE THE NEXT PRESIDENT OF THE UNITED STATES, JOE BIDEN."),
                    None,
                    ("THANK YOU, JOE. THANK YOU, JOE. AS I SAID WHEN YOU CALLED ME, I AM INCREDIBLY HONORED BY THIS RESPONSIBILITY AND I AM READY TO GET TO WORK.", "THANK YOU, AND MAY GOD BLESS THE UNITED STATES OF AMERICA. (music) (music) (music)"),
                    ("GOOD AFTERNOON. ON THE EVE OF THE 57TH MARCH ON WASHINGTON, I WILL SPEAK ABOUT RECENT EVENTS IN KENOSHA, WISCONSIN, WILDFIRES RAGING ACROSS THE CALIFORNIA COAST TOMORROW", "I BELIEVE AMERICA WILL CHOOSE THE LIGHT. THANK YOU."),
                    None,
                    None,
                    ("IT IS SO GOOD TO BE BACK IN DETROIT. IT IS SO GOOD TO BE WITH YOU GUYS. I LOVE DETROIT.", "WE POSSIBLY CAN TO MAKING SURE WE VOTE AND EVERYONE WE KNOW VOTES AND IN THAT WAY, FIGHTS FOR THIS COUNTRY WE LOVE. THANK YOU, DETROIT. THANK YOU. THANK YOU. [APPLAUSE] (music)"),
                    ("GOOD AFTERNOON. ON FRIDAY MORNING, I ATTENDED THE MEMORIAL SERVICE OF JUSTICE RUTH BADER GINSBURG IN THE UNITED STATES CAPITOL.", "MAY GOD BLESS JUSTICE RUTH BADER GINSBURG. MAY GOD BLESS YOU ALL, AND MAY GOD BLESS THE UNITED STATES OF AMERICA."),
                    ("IT IS SO GOOD TO BE WITH YOU ALL. CONGRESSWOMAN, THANK YOU FOR THAT INTRODUCTION AND ALL THAT YOU DO.", "THANK YOU, NEVADA. THANK YOU. [CARS HONKING] (music) [CARS HONKING] (music)"),
                    ("HI, EVERYBODY. WHERE IS VANESSA?", "SO LET'S ELECT JOE BIDEN AS THE NEXT PRESIDENT OF THE UNITED STATES OF AMERICA AND LADIES AND GENTLEMEN, I INTRODUCE TO YOU THE GREAT JOE BIDEN."),
                    ("HELLO, EVERYBODY! IT IS WONDERFUL TO BE IN JACKSONVILLE.", "THAT IS WHY WE WILL VOTE EVERY DAY UNTIL ELECTION DAY AND GET THIS THING DONE. THANK YOU. (music)"),
                    ("CAN WE HEAR IT FOR ALLISON? [APPLAUSE] I LOVE OUR YOUNG LEADERS. ALLISON IS A JUNIOR. SHE IS STUDYING INTERDISCIPLINARY STUDIES AND WE WERE TALKING ABOUT", "WE MADE SURE THAT PEOPLE KNOW WHAT IS HAD STEAK, HOW WE REMINDED PEOPLE WE ARE ALL IN THIS TOGETHER, AND WE WILL TELL THEM ABOUT WHAT WE DID TO FIGHT FOR THE SOUL OF OUR NATION. THANK YOU ALL. [APPLAUSE]"),
                    ("WHAT'S UP ATLANTA? I'M SO HAPPY TO BE BACK. HEY EVERYBODY. CAN WE HEAR IT FOR RICK HART?", "DETHANK YOU JOHN FOR YOUR SUPPORT AND FOR YOUR DEFINING MOMENTS OF THIS DEVELOPMENT. [INAUDIBLE]. LET ME AND HERE ATTORNEY OVER TO YOU JOHN."),
                    ("GOOD MORNING. GOOD MORNING, ROBIN, FOR HOSTING ME TODAY, AND FOR THE WARM WELCOME.", "PASTOR, THANK YOU, AND THE FIRST FAMILY, FOR ALL THE LOVE YOU HAVE GIVEN ME AND THIS COMMUNITY, AND THANK YOU , EVERYONE, FOR YOUR PRAYERS. I FEEL THEM EVERY DAY. GOD BLESS. (music) [APPLAUSE] (music)"),
                    ("HEY, RENO. HI, EVERYBODY. IT IS SO GOOD.", "SO THAT IS WHAT WE ARE GOING TO DO, RENO, AND THANK YOU, THANK YOU, THANK YOU. THANK YOU, THANK YOU, THANK YOU. (music)"),                    
                    ("WHAT'S UP, TUCSON? HEY, EVERYBODY. CAN WE PLEASE HERE FOR MAYOR ROMERO?", "AND WE WILL TELL THEM THAT'S HOW WE ELECT TO JOE BIDEN, THE NEXT PRESIDENT OF THE UNITED STATES"),                    
                    ("Uh, Alicia Keys. Honestly, I just want to say something. Alicia Keys.", "And we will tell them we elected Joe Biden, president of the United States. Thank you, Phoenix."),
                    ("IT IS SO GOOD TO BE BACK IN HARRIS COUNTY.", "AND WE WILL TELL THEM WE ELECTED JOE BIDEN THE PRESIDENT OF THE UNITED STATES. THANK YOU, HOUSTON. THANK YOU."),
                    ("Can we please hear for Rebecca Al Kona, she is phenomenal. You know, when I look at Rebecca, I know our future is bright.", "And God bless Texas."),
                    ("I am so excited to be here. You are going to make the difference.", "We will tell them that we elected Joe Biden, president of the United States. Thank you. Thank you. Rio Grande."),
                    ("Can we hear for Sergeant paul Cruz man?", "And we will tell them we elected joe biden the next president of the United States. Thank you."),
                    ("Hi everybody. Hi Broward County and all our young leaders. Hi. Hi everyone.", "Thank you Broward County."),
                    ("WHAT'S UP, PALM BEACH? [APPLAUSE] CAN WE HEAR IT FOR RAFAEL GUTIERREZ?", "[CHEERING] THANK YOU, PALM BEACH. THANK YOU. (music)"),
                    ("HELLO EVERYBODY. CAN WE GIVE IT UP FOR STACEY ABRAMS?", "AND WE WILL TELL THEM WE ELECTED JOE BIDEN THE NEXT PRESIDENT OF THE UNITED STATES. THANK YOU ALL. (music)"),
                    ("Hi. Oh, it's so good to see everybody. Maria, Thank you for that introduction. Where is she?", "We will tell them We emailed and we texted and we call till folks got sick of us. But we knew They get over it and we will tell them Bethlehem that we elected Joe Biden the next president of the United States. Thank you."),
                    ("HELLO, PENNSYLVANIA! ARE YOU READY? [APPLAUSE] JOE IS HERE! YOU ARE HERE! WE ARE HERE! [APPLAUSE] AND WE ARE HERE TO BRING THIS ELECTION HOME.", "THANK YOU, MAY GOD BLESS YOU, AND MAY GOD BLESS AMERICA."),
                    ("THANK YOU. GOOD EVENING. SO CONGRESSMAN JOHN LEWIS", "AND IT IS NOW MY GREAT HONOR TO INTRODUCE THE PRESIDENT ELECT OF THE UNITED STATES OF AMERICA, JOE BIDEN! [CHEERS AND APPLAUSE] (music) [HONKING] (music)"),
                    ("HELLO, COLUMBUS GEORGIA. YOU SOUND LIKE YOU ARE READY TO WIN AN ELECTION.", "LET'S STRUGGLE TOGETHER, LET'S STAY TOGETHER, LET'S PRAY TOGETHER, LET'S MERGE TOGETHER AND TOGETHER WE WIN. GOD BLESS YOU. [CHEERS AND APPLAUSE]")]
    clean_cspan(directoryin, directoryout, potus, "NFC", False, None, speechbounds)

    # Medium
    directoryin = "{}/us2020data/data/medium/".format(toplevel)
    directoryout = "{}/us2020data/data_clean/medium/".format(toplevel)
    pathlib.Path("{}/{}".format(directoryout, potus)).mkdir(parents=True, exist_ok=True)           
    drop_speechID = pd.read_csv("{}/{}/drop_speech_id.tsv".format(directoryin, potus), sep="\t")       
    drop_speechID = drop_speechID.SpeechIDdrop.values.tolist()            
    clean_medium(directoryin, directoryout, potus, textclean_medium, "NFC", True, drop_speechID, drop_column)    
    