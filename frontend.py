import streamlit as st
import pandas as pd
import readwiki
import datetime

st.set_page_config(page_title="🛡️Westlande JSON Generator")
st.title("⚔️Westlande Turney🛡️")
st.subheader("JSON Generator")
st.caption("Beta")
st.divider()


turney_name = st.text_input('Name des Turniers:')

today = datetime.date.today()
if today.month > 6:
    year_sug = today.year - 977
else:
    year_sug = today.year - 976

turney_year = st.text_input('Jahr des Turniers:',value=year_sug)


turney_wikipage = st.text_input('Link zur Wikipage des Turniers:',value= "")
 
@st.cache_data
def load_Data(wikipage):
    return readwiki.generateTurneycontestants(readwiki.getTurneyContestants(wikipage),wikipage)
    

if turney_wikipage == "":
    st.info("Bitte trage einen Link ein.",icon="ℹ️")
    st.stop()
turneytable = load_Data(turney_wikipage)

t1, t2 = st.columns(2)
with t1:
    st.subheader("Turniertabelle")
with t2:
    allow_add = st.checkbox("Hinzufügen von Teilnehmern erlauben", value=False)

st.caption("ℹ Du kannst fehlende Werte direkt in der Tabelle nachtragen")

if allow_add:
    dyn = "dynamic"
else:
    dyn = "static"


def configureColumns():
    col_config = {}
    col_config["Geburtsjahr"] = st.column_config.TextColumn(required=True)
    col_config["Kampfstil"] = st.column_config.SelectboxColumn(options=readwiki.getStyles())
    col_config["Ambition"] = st.column_config.SelectboxColumn(options=readwiki.getAmbitions())
    skillcols = [x for x in turneytable.columns.tolist() if "Erfahrungsgrad" in x]

    for col in skillcols:
        col_config[col] = st.column_config.SelectboxColumn(label=col
                                                       ,options=readwiki.getSkills()
                                                        )
    disc_cols = [x for x in turneytable.columns.tolist() if "Wettkampf" in x]
    for col in disc_cols:
        col_config[col] = st.column_config.CheckboxColumn()

    return col_config


edited_df = st.data_editor(turneytable,num_rows=dyn,column_config=configureColumns())


error_noBirth = edited_df[pd.isnull(edited_df["Geburtsjahr"])]["Name"]
error_noSkill_lh = edited_df[(pd.isnull(edited_df["ErfahrungsgradLh"])) & edited_df["WettkampfEinhand"]]["Name"]
error_noSkill_sh = edited_df[(pd.isnull(edited_df["ErfahrungsgradSh"])) & edited_df["WettkampfZweihand"]]["Name"]
error_noSkill_lr = edited_df[(pd.isnull(edited_df["ErfahrungsgradLr"])) & edited_df["WettkampfTjost"]]["Name"]
error_noSkill_bu = edited_df[(pd.isnull(edited_df["ErfahrungsgradBu"])) & edited_df["WettkampfBuhurt"]]["Name"]
error_noSkill_sw = edited_df[(pd.isnull(edited_df["ErfahrungsgradSc"])) & edited_df["WettkampfSchusswaffen"]]["Name"]
error_noSkill_wu = edited_df[(pd.isnull(edited_df["ErfahrungsgradWu"])) & edited_df["WettkampfWurfwaffen"]]["Name"]


if len(error_noBirth) + len(error_noSkill_lh) + len(error_noSkill_sh) + len(error_noSkill_lr) + len(error_noSkill_bu) > 0:
    st.divider()
    st.warning("Es sieht so aus als gäbe es noch ein paar Probleme in dem Teilnehmerfeld"
                ,icon="⚠️")
    if len(edited_df[edited_df["Springer"]]) == 0:
        st.error("Es wurde kein Springer definiert!"
                ,icon="❗")
    
    if len(error_noBirth) > 0:
        st.error("Die folgenden Teilnehmenden haben kein Geburtsjahr hinterlegt")
        st.dataframe(error_noBirth,use_container_width=True)

    if len(error_noSkill_lh) > 0:
        st.error("Die folgenden Teilnehmenden haben keinen Wert \"Erfahrungsgrad Lh\" hinterlegt, obwohl sie an der Disziplin teilnehmen")
        st.dataframe(error_noSkill_lh,use_container_width=True)

    if len(error_noSkill_sh) > 0:
        st.error("Die folgenden Teilnehmenden haben keinen Wert \"Erfahrungsgrad Sh\" hinterlegt, obwohl sie an der Disziplin teilnehmen")
        st.dataframe(error_noSkill_sh,use_container_width=True)

    if len(error_noSkill_lr) > 0:
        st.error("Die folgenden Teilnehmenden haben keinen Wert \"Erfahrungsgrad Lr\" hinterlegt, obwohl sie an der Disziplin teilnehmen")
        st.dataframe(error_noSkill_lr,use_container_width=True)

    if len(error_noSkill_bu) > 0:
        st.error("Die folgenden Teilnehmenden haben keinen Wert \"Erfahrungsgrad Bu\" hinterlegt, obwohl sie an der Disziplin teilnehmen")
        st.dataframe(error_noSkill_bu,use_container_width=True)

st.divider()
st.subheader("Konfiguration")
tab1, tab2, tab3 = st.columns(3)
 
with tab1:
    config_1h_bruch = st.text_input('Bruchwert Einhand:',value="7")
    config_2h_bruch = st.text_input('Bruchwert Zweihand:',value="9")
    config_tjost_bruch = st.text_input('Bruchwert Tjost:',value="11")

with tab2:
    config_1h_tp = st.text_input('TP Mod Einhand:',value="1")
    config_2h_tp = st.text_input('TP Mod Zweihand:',value="3")
    config_tjost_tp = st.text_input('TP Mod Tjost:',value="8")

with tab3:
    config_hand_rs = st.text_input('RS Handwaffen:',value="5")
    config_tjost_rs = st.text_input('RS Tjost:',value="8")
    config_siegpunkte = st.text_input('Siegpunkte:',value="5")


tab21,tab22 = st.columns(2)
with tab21:
    config_ambition_start = st.text_input('Ambition Handwaffen Startwert:',value="20")
    config_ambition_schritt = st.text_input('Ambition Handwaffen Schrittwert:',value="20")
with tab22:
    config_ambition_start_lr = st.text_input('Ambition Tjost Startwert:',value="10")
    config_ambition_schritt_lr = st.text_input('Ambition Tjost Schrittwert:',value="15")

    

st.divider()


config = pd.DataFrame.from_dict(
    {
    "Austragungsjahr": [turney_year],
    "BruchwertEinhandwaffen": [config_1h_bruch],
    "BruchwertZweihandwaffen": [config_2h_bruch],
    "BruchwertTjost": [config_tjost_bruch],
    "TrefferpunktModEinhandwaffen": [config_1h_tp],
    "TrefferpunktModZweihandwaffen": [config_2h_tp],
    "TrefferpunktModTjost": [config_tjost_tp],
    "RuestungHandwaffen": [config_hand_rs],
    "RuestungTjost": [config_tjost_rs],
    "SiegpunktMaximum": [config_siegpunkte],
    "AmbitionHandwaffenStart": [config_ambition_start],
    "AmbitionHandwaffenSchritt": [config_ambition_schritt],
    "AmbitionTjostStart": [config_ambition_start_lr],
    "AmbitionTjostSchritt": [config_ambition_schritt_lr]
    }
)

output_file = "".join(['{\r\n',
                        '"Type": "Ritterliste",\r\n',
                        '"Version": "1.1",\r\n',
                        '"Konfiguration":',
                        config.to_json(orient="records")[1:-1],
                        '\r\n,\r\n"Ritter":',
                        edited_df.to_json(orient="records"),
                        '\r\n}'
]
)


st.download_button("erstellte JSON herunterladen",output_file,f'{turney_name}_{turney_year}.json')
