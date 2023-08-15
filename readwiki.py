import requests
from bs4 import BeautifulSoup

def normaliseSkill (skill):
    skill = str(skill).lower()
    if "unerfahren" in skill:
        return "unerfahren"
    elif "durchschnittlich" in skill:
        return "durchschnittlich"
    elif "erfahren" in skill:
        return "erfahren"
    elif "kompetent" in skill:
        return "kompetent"
    elif "veteran" in skill:
        return "Veteran"
    elif "meisterlich" in skill:
        return "meisterlich"
    elif "brilliant" in skill:
        return "brilliant"
    elif "legendär" in skill:
        return "legendär"
    else:
        return None
    
def normaliseStyle (style):
    style = str(style).lower()
    if "offensiv" in style:
        return "offensiv"
    elif "defensiv" in style:
        return "defensiv"
    else:
        return "ausgeglichen"
    
def getTurneyContestants(turneypage):
    import pandas as pd
    tables = pd.read_html(turneypage)
    for table in tables:
        tcol = table.columns.tolist()
        if "Name" in tcol and ("Leichte Handwaffen" in tcol  or "Schwere Handwaffen" in tcol or "Lanzenreiten" in tcol):
            return table    

def getPageLinks(turneypage):
    try:
        page = requests.get(turneypage)
    except ConnectionError:
        return None
    
    soup = BeautifulSoup(page.content, "html.parser")
    linkprefix = r"https://www.westlande.de"
    
    links = []
    htmltable = soup.find_all("table", class_="wikitable sortable")[0]
    for a_el in htmltable.find_all("a"):
        linktext = a_el["href"]
        if linktext[:3] != "http":
            linktext = linkprefix + linktext
        
        links.append([a_el.text,linktext])
    return links

def getTurneyprofile(fighterpage):
    try:
        page = requests.get(fighterpage)
    except requests.exceptions.ConnectionError:
        return None
    except requests.exceptions.MissingSchema:
        return None
    
    soup = BeautifulSoup(page.content, "html.parser")
    skills = []

    
    
    for lst in soup.find_all("ul"):
        if "Leichte Handwaffen" in lst.text and "Kampfstil" in lst.text:
            for el in lst.find_all("li"):
                if ":" in el.text:
                    skills.append([el.text.split(":")[0].strip(), el.text.split(":")[1].strip()])
            break
            
    profile = {}
    for item in skills:
        if "Kampfstil" in item[0]:
            item[1] = normaliseStyle(item[1])
        else:
            item[1] = normaliseSkill(item[1])
        if item[1] is not None:
            profile[item[0].split("(")[0].strip()] = item[1]
    
    
    import re
    if soup.find("div",class_="InfoEnd"):
        endbox = soup.find("div",class_="InfoEnd").text
    else:
        endbox = ""
            
    try:
        if "Angaben von:" in endbox and len(re.findall(r"(\d{4})", endbox)) > 0:
            profile["WerteVon"] = re.findall(r"(\d{4})", endbox)[0]
        else:
            profile["WerteVon"] = None
    except AttributeError:
        profile["WerteVon"] = None
        pass
    
    try:
        if "NSC: Nein" in endbox:
            profile["Nsc"] = False
        else:
            profile["Nsc"] = True
    except AttributeError:
        pass


    
    try:
        birthday = soup.find("div",class_="InfoContent").find(lambda tag:tag.name=="tr" and "Tsatag" in tag.text).text
        profile["Geburtsjahr"] = re.search(r"(\d{3,4})",birthday).group(1)
    except AttributeError:
        profile["Geburtsjahr"] = None
        pass


    return profile         

def generateTurneycontestants(contestants, wikipage):

    import pandas as pd
    
    discipline_subs = {"Leichte Handwaffen":"WettkampfEinhand",
                       "Schwere Handwaffen":"WettkampfZweihand",
                       "Lanzenreiten":"WettkampfTjost",
                       "Tjost":"WettkampfTjost",
                       "Buhurt":"WettkampfBuhurt"
                    }


    ttbl = contestants
    linktbl = pd.DataFrame(getPageLinks(wikipage))
    linktbl.set_index(0, inplace=True)
    ttbl.set_index("Name", inplace=True)

    turneytab = ttbl.join(linktbl)
    turneytab.rename({1:"link"},axis=1,inplace=True)

    for dis in discipline_subs.keys():
        if dis in turneytab.columns:
            turneytab[dis] = turneytab[dis].apply(lambda x: x.upper().strip() == "X")
    turneytab.rename(discipline_subs,axis=1,inplace=True)

    
    profiles = []
    for index, row in turneytab.iterrows():
         prof  = getTurneyprofile(row["link"])
         if prof is not None:
            prof["link"] = row["link"]
            profiles.append(prof)
    
    profile_frame = pd.DataFrame(profiles)
    profile_frame.set_index("link",inplace=True)

    profile_subs = {
                    "Leichte Handwaffen":"ErfahrungsgradLh",
                    "Schwere Handwaffen":"ErfahrungsgradSh",
                    "Lanzenreiten":"ErfahrungsgradLr",
                    "Buhurt":"ErfahrungsgradBu",
                    "Wurfwaffen":"ErfahrungsgradWu",
                    "Schusswaffen":"ErfahrungsgradSc"
                    }
    
    profile_frame.rename(profile_subs,axis=1,inplace=True)
    
    
    
    turneytab.insert(0,"Name",turneytab.index)
    #turneytab.insert(1,"WerteStand","1045")
    turneytab.insert(1,"Knappe","")
    turneytab.insert(1,"KnappeStufe","0")
    turneytab.insert(1,"Springer",False)


    turneytab = pd.merge(turneytab, profile_frame, how="left", on="link")

    turneytab = turneytab[["Name"
                           ,"Geburtsjahr"
                           ,"WerteVon"
                           ,"Kampfstil"
                           ,"Sattelfestigkeit"
                           ,"ErfahrungsgradLh"
                           ,"ErfahrungsgradSh"
                           ,"ErfahrungsgradLr"
                           ,"ErfahrungsgradBu"
                           ,"ErfahrungsgradSc"
                           ,"ErfahrungsgradWu"
                           ,"WettkampfEinhand"
                           ,"WettkampfZweihand"
                           ,"WettkampfTjost"
                           ,"WettkampfBuhurt"
                           ,"Knappe"
                           ,"KnappeStufe"
                           ,"Nsc"
                           ,"Springer"
                           ]
                        ]
    
    return turneytab
