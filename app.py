# app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

# ----------------------------
# Generic HTML table scraper
# ----------------------------
def generic_table_scraper(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if not table:
            return pd.DataFrame()
        headers = [th.text.strip() for th in table.find("tr").find_all(["th","td"])]
        rows = table.find_all("tr")[1:]
        data = []
        for row in rows:
            cols = row.find_all("td")
            if len(cols) != len(headers):
                continue
            data.append({headers[i]: cols[i].text.strip() for i in range(len(headers))})
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# ----------------------------
# Fetcher functions
# ----------------------------
def fetch_liderform_program(date_str, track, race_no):
    url = f"https://liderform.com.tr/program/{date_str}/{track}/{race_no}"
    return generic_table_scraper(url)

def fetch_liderform_performance(date_str, track, race_no):
    url = f"https://liderform.com.tr/{date_str}/{track}/{race_no}"
    return generic_table_scraper(url)

def fetch_tjk_results(date_str, track, race_no):
    api = f"https://tjk.org/API/RaceResult/{date_str}/{track}/{race_no}"
    try:
        data = requests.get(api, timeout=10).json()
        return pd.DataFrame(data.get("Results", []))
    except:
        return pd.DataFrame()

def fetch_tjk_pedigree(horse_id):
    api = f"https://tjk.org/API/Horse/Pedigree/{horse_id}"
    try:
        data = requests.get(api, timeout=10).json()
        return pd.DataFrame(data.get("Pedigree", []))
    except:
        return pd.DataFrame()

def fetch_hipodrom_sprint(date_str, track, race_no):
    url = f"https://hipodrom.com/{date_str}/{track}/sprint/{race_no}"
    return generic_table_scraper(url)

# ----------------------------
# Data models
# ----------------------------
class Horse:
    def __init__(self, name, jockey, trainer, pedigree_df, perf_df, sprint_df):
        self.name = name
        self.jockey = jockey
        self.trainer = trainer
        self.pedigree_df = pedigree_df
        self.perf_df = perf_df
        self.sprint_df = sprint_df

class Race:
    def __init__(self, date_str, track, race_no):
        self.date_str = date_str
        self.track = track
        self.race_no = race_no
        self.horses = []

    def load_from_dataframes(self, prog_df, tjk_df, hipo_df):
        for _, row in prog_df.iterrows():
            name    = row.get("At İsmi","")
            jockey  = row.get("Jokey","")
            trainer = row.get("Antrenör","")
            horse_id= row.get("AtID", None)
            pedigree= fetch_tjk_pedigree(horse_id) if horse_id else pd.DataFrame()
            perf    = tjk_df[tjk_df.get("HorseName","")==name]
            sprint  = hipo_df[hipo_df.get("At İsmi","")==name]
            self.horses.append(Horse(name,jockey,trainer,pedigree,perf,sprint))

# ----------------------------
# 12 Criteria scorers
# ----------------------------
def sprint_tempo_score(h):
    times = pd.to_numeric(h.sprint_df.get("Zaman",[]),errors="coerce").dropna()
    return 1 - (times.mean()/times.max()) if len(times) else 0.5

def agf_percentage_score(h):
    agf = pd.to_numeric(h.perf_df.get("AGF",[]),errors="coerce").dropna()
    return agf.mean()/100 if len(agf) else 0.5

def jockey_trainer_score(h):
    combo = f"{h.jockey}-{h.trainer}"
    strong = {"X-Y":0.9,"A-B":0.8}
    return strong.get(combo,0.5)

def pedigree_score(h):
    wins = pd.to_numeric(h.pedigree_df.get("Wins",[]),errors="coerce").dropna()
    return np.tanh(wins.mean()/10) if len(wins) else 0.5

def form_trend_score(h):
    places = pd.to_numeric(h.perf_df.get("Place",[]),errors="coerce").dropna()
    if len(places)<3: return 0.5
    trend = np.polyfit(range(len(places)),places,1)[0]
    return max(0,1 - trend/max(places))

# (buraya kendi 7 kriterini ekle)
CRITERIA_FUNCS = [
    sprint_tempo_score,
    agf_percentage_score,
    jockey_trainer_score,
    pedigree_score,
    form_trend_score,
    # ... +7
]
DEFAULT_WEIGHTS = np.ones(len(CRITERIA_FUNCS))/len(CRITERIA_FUNCS)

# ----------------------------
# Synthesizer (Softmax + Monte Carlo)
# ----------------------------
def calculate_softmax(horses, weights):
    raw = [sum(w*f(h) for w,f in zip(weights,CRITERIA_FUNCS)) for h in horses]
    exp = np.exp(raw - np.max(raw))
    p = exp/exp.sum()
    return dict(zip([h.name for h in horses],p))

def monte_carlo_simulation(horses, weights, trials=5000, sigma=0.1):
    counts = {h.name:0 for h in horses}
    for _ in range(trials):
        samples = [
            np.random.normal(sum(w*f(h) for w,f in zip(weights,CRITERIA_FUNCS)),sigma)
            for h in horses
        ]
        winner = horses[int(np.argmax(samples))].name
        counts[winner] += 1
    return {k:v/trials for k,v in counts.items()}

def calculate_probabilities(horses, weights=DEFAULT_WEIGHTS):
    return calculate_softmax(horses,weights), monte_carlo_simulation(horses,weights)

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Kâhin 15 Analiz", layout="wide")
st.title("🏇 Kâhin 15 – Analiz")

date    = st.date_input("Tarih")
track   = st.selectbox("Pist", ["ISTANBUL","ANKARA","IZMIR","ADANA","BURSA","KOCAELI"])
race_no = st.selectbox("Koşu No", list(range(1,13)))

if st.button("Verileri Çek ve Analiz Et"):
    ds       = date.isoformat()
    prog_df  = fetch_liderform_program(ds,track,race_no)
    perf_df  = fetch_liderform_performance(ds,track,race_no)
    tjk_df   = fetch_tjk_results(ds,track,race_no)
    hipo_df  = fetch_hipodrom_sprint(ds,track,race_no)
    race     = Race(ds,track,race_no)
    race.load_from_dataframes(prog_df,tjk_df,hipo_df)

    soft, mc = calculate_probabilities(race.horses, DEFAULT_WEIGHTS)

    df_soft = (
        pd.DataFrame.from_dict(soft,orient="index",columns=["Softmax"])
          .assign(Softmax=lambda d:(d*100).round(1).astype(str)+"%")
          .sort_values("Softmax",ascending=False)
    )
    df_mc = (
        pd.DataFrame.from_dict(mc,orient="index",columns=["Monte Carlo"])
          .assign(**{"Monte Carlo":lambda d:(d*100).round(1).astype(str)+"%"})
          .sort_values("Monte Carlo",ascending=False)
    )

    st.subheader("Olasılıklar: Softmax vs Monte Carlo")
    st.dataframe(df_soft.join(df_mc), use_container_width=True)