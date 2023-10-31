import requests
import globals
from bs4 import BeautifulSoup

def normaliseSkill(skill):
    skill = str(skill).lower()
    
    for reference in globals.skills:
        if reference.lower() in skill:
            return reference
    return None

def normaliseStyle (style):
    style = str(style).lower()
    
    for reference in globals.styles:
        if reference.lower() in style:
            return reference
    return "Ausgeglichen"

def normaliseAmbition(ambition):
    ambition = str(ambition).lower()
    
    for reference in globals.ambitions:
        if reference.lower() in ambition:
            return reference
    return "Bedacht"

def getContestantLists(wikipage):
    import pandas as pd
    tables = pd.read_html(wikipage)
    output = []
    for table in tables:
        if "Name" in table.columns.tolist():
            output.append(table)
    return output


def getTurneyContestants(wikitable,turneypage):
    import pandas as pd
    linktbl = pd.DataFrame(getPageLinks(turneypage))
    linktbl.set_index(0, inplace=True)
    wikitable.set_index("Name", inplace=True)
    wikitable = wikitable.join(linktbl)
    wikitable.rename({1:"link"},axis=1,inplace=True)
    return wikitable    

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

def getTurneyprofile(fighterpage,turney_year):
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
        elif "Ambition" in item[0]:
            item[0]= item[0].replace("(","").replace(")","")
            item[1] = normaliseAmbition(item[1])
        else:
            item[1] = normaliseSkill(item[1])
        
        if item[1] is not None:
            profile[item[0].split("(")[0].strip()] = item[1]
    

    if "Ambition" not in profile.keys():
        if "Ambition Handwaffen" in profile.keys():
            profile["Ambition"] = profile["Ambition Handwaffen"]
        elif "Ambition Tjost" in profile.keys():
            profile["Ambition"] = profile["Ambition Tjost"]
        else:
            profile["Ambition"] = None
         
    if "Ambition Handwaffen" not in profile.keys():
        profile["Ambition Handwaffen"] = profile["Ambition"]
    if "Ambition Tjost" not in profile.keys():
        profile["Ambition Tjost"] = profile["Ambition"]

    
    squires = []
    squirename = ""
    squirebirth = ""
    infocontent = soup.find("div",class_="InfoContent")
    if infocontent is not None:
        for trow in infocontent.find_all("tr"):
            if "Zöglinge:" in trow.text:
                for a in trow.find_all("a",href=True):
                    squires.append("https://www.westlande.de" + a["href"] + "&action=edit")
                break
        
        if len(squires) > 0:
            for squire in squires:
                squiresoup = BeautifulSoup(requests.get(squire).content,"html.parser")
                if "{{InfoBoxPerson" in squiresoup.text:
                    infobox = squiresoup.text.split("{{InfoBoxPerson")[1].split("}}")[0]
                    squirename = infobox.split("|")[1].replace("NAME=","").strip()
                    squirebirth = infobox[infobox.find("|GEBURTSJAHR="):].split("|")[1].replace("GEBURTSJAHR=","").strip()
                    break
                    
        profile["Knappe"] = squirename

        squirelevel = ""
        if squirebirth == "":
            squireage = None
        else:
            squireage = int(squirebirth) - int(turney_year)
            if squireage >= 18:
                squirelevel = "Erfahren"
            elif squireage >= 16:
                squirelevel = "Durchschnittlich"
            elif squireage is not None:
                squirelevel = "Unerfahren"
        
        profile["KnappeStufe"] = squirelevel



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
 
def generateTurneycontestants(turneytab, wikipage, turney_year):
    import pandas as pd
    turneytab.insert(0,"Name",turneytab.index)
    
    profiles = []
    for index, row in turneytab.iterrows():
         prof  = getTurneyprofile(row["link"], turney_year)
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
                    "Schusswaffen":"ErfahrungsgradSc",
                    "Ambition Handwaffen":"AmbitionHandwaffen"
                    ,"Ambition Tjost":"AmbitionTjost"
                    }
    
    profile_frame.rename(profile_subs,axis=1,inplace=True)
    

    turneytab = pd.merge(turneytab, profile_frame, how="left", on="link")


    discipline_subs = {"Leichte Handwaffen":"WettkampfEinhand",
                       "Schwere Handwaffen":"WettkampfZweihand",
                       "Lanzenreiten":"WettkampfTjost",
                       "Tjost":"WettkampfTjost",
                       "Buhurt":"WettkampfBuhurt",
                       "Schusswaffen":"WettkampfSchusswaffen",
                       "Wurfwaffen":"WettkampfWurfwaffen",
                    }
    

    for dis in discipline_subs.keys():
        if dis in turneytab.columns:
            turneytab[dis] = turneytab[dis].apply(lambda x: x.upper().strip() == "X")
    turneytab.rename(discipline_subs,axis=1,inplace=True)


    turneytab.insert(1,"Springer",False)


    turneytab["AmbitionHandwaffen"].fillna(turneytab["Ambition"])
    turneytab["AmbitionTjost"].fillna(turneytab["Ambition"])


    resultcols = ["Name"
                  ,"Geburtsjahr"
                  ,"WerteVon"
                  ,"Kampfstil"
                  ,"Ambition"
                  ,"AmbitionTjost"
                  ,"AmbitionHandwaffen"
                  ,"Sattelfestigkeit"
                  ,"ErfahrungsgradLh"
                  ,"ErfahrungsgradSh"
                  ,"ErfahrungsgradLr"
                  ,"ErfahrungsgradBu"
                  ,"ErfahrungsgradSc"
                  ,"ErfahrungsgradWu"
                ]
    for col in [x for x in turneytab if "Wettkampf" in x]:
        resultcols.append(col)
    
    for col in ["Knappe","KnappeStufe","Nsc","Springer"]:
        resultcols.append(col)


    turneytab = turneytab[resultcols]
    
    return turneytab
