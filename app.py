import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date
import numpy as np

# 1) LiderForm sonuçlarını çek
def fetch_liderform_results():
    url = "https://liderform.com.tr/sonuclar"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    dfs = []
    for tbl in soup.select("table"):
        headers = [th.get_text(strip=True) for th in tbl.find_all("th")]
        rows = []
        for tr in tbl.find_all("tr")[1:]:
            cells = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cells) == len(headers):
                rows.append(cells)
        if rows:
            dfs.append(pd.DataFrame(rows, columns=headers))
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

# 2) Yenibeygir sonuçlarını çek
def fetch_yenibeygir_results():
    url = "https://yenibeygir.com/sonuclar"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tbl = soup.find("table")
    headers = [th.get_text(strip=True) for th in tbl.find_all("th")]
    rows = []
    for tr in tbl.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cells) == len(headers):
            rows.append(cells)
    return pd.DataFrame(rows, columns=headers)

# 3) İki kaynaktan gelenleri at ismi üzerinden birleştir
def merge_results(lf, yb):
    lf = lf.rename(columns=lambda c: c.lower())
    yb = yb.rename(columns=lambda c: c.lower())
    left_on, right_on = "adi", "at ismi"
    if left_on in lf.columns and right_on in yb.columns:
        return pd.merge(lf, yb,
                        left_on=left_on, right_on=right_on,
                        how="outer",
                        suffixes=("_ldr", "_ybg"))
    else:
        return pd.concat([lf, yb], axis=1)

# 4) 12 kriterli puanlama ve kazanma şansı
def calculate_kahin15_score(df):
    df = df.copy()
    # c1: Ortalama AGF >20%
    for col in ["agf_ldr","agf_ybg"]:
        if col in df: df[col] = pd.to_numeric(df[col].str.rstrip("%"), errors="coerce")
    df["avg_agf"] = df[["agf_ldr","agf_ybg"]].mean(axis=1)
    df["c1"] = (df["avg_agf"] > 20).astype(int)

    # c2: Ortalama sprint <36s
    sprint_cols = [c for c in df if "sprint" in c]
    if sprint_cols:
        df["avg_sprint"] = df[sprint_cols].astype(float).mean(axis=1)
        df["c2"] = (df["avg_sprint"] < 36).astype(int)
    else:
        df["c2"] = 0

    # c3: Ortalama jokey win rate >10%
    for col in ["jokey_win_rate_ldr","jokey_win_rate_ybg"]:
        if col in df: df[col] = pd.to_numeric(df[col].str.rstrip("%"), errors="coerce")
    df["avg_jokey_wr"] = df[["jokey_win_rate_ldr","jokey_win_rate_ybg"]].mean(axis=1)
    df["c3"] = (df["avg_jokey_wr"] > 10).astype(int)

    # c4: Ortalama trainer win rate >10%
    for col in ["trainer_win_rate_ldr","trainer_win_rate_ybg"]:
        if col in df: df[col] = pd.to_numeric(df[col].str.rstrip("%"), errors="coerce")
    df["avg_trainer_wr"] = df[["trainer_win_rate_ldr","trainer_win_rate_ybg"]].mean(axis=1)
    df["c4"] = (df["avg_trainer_wr"] > 10).astype(int)

    # c5: Galop sapması küçükse
    if {"galop_ldr","galop_ybg"}.issubset(df.columns):
        df["galop_dev"] = (df["galop_ldr"].astype(float) - df["galop_ybg"].astype(float)).abs()
        max_dev = df["galop_dev"].max() or 1
        df["c5"] = (1 - df["galop_dev"]/max_dev > 0.7).astype(int)
    else: df["c5"] = 0

    # c6: Jokey+trainer uyumu >12%
    df["c6"] = ((df["avg_jokey_wr"]+df["avg_trainer_wr"])/2 > 12).astype(int)

    # c7–c9: Pedigree / trainer rapor / training puanları >60
    for i,col in enumerate(["pedigree_score","trainer_report_score","training_result_score"], start=7):
        df[f"c{i}"] = (pd.to_numeric(df.get(col,0), errors="coerce") > 60).astype(int)

    # c10: Origin_score >50
    df["c10"] = (pd.to_numeric(df.get("origin_score",0), errors="coerce") > 50).astype(int)

    # c11: Harmonik uyum (avg_agf/avg_sprint>0.6)
    df["c11"] = (df["avg_agf"]/df["avg_sprint"] > 0.6).astype(int)

    # c12: Genel form (normalize & >0.5)
    score_cols = ["avg_agf","avg_sprint","avg_jokey_wr","avg_trainer_wr",
                  "galop_dev","pedigree_score","trainer_report_score","training_result_score"]
    norm = {}
    for c in score_cols:
        if c in df:
            mn,mx = df[c].min(), df[c].max()
            if mx>mn: norm[c] = (df[c]-mn)/(mx-mn)
    df["form_index"] = pd.DataFrame(norm).mean(axis=1) if norm else 0
    df["c12"] = (df["form_index"] > 0.5).astype(int)

    # Toplam skor & kazanma şansı %
    crits = [f"c{i}" for i in range(1,13)]
    df["k15_score"] = df[crits].sum(axis=1)
    mn,mx = df["k15_score"].min(), df["k15_score"].max()
    df["win_chance_%"] = ((df["k15_score"]-mn)/(mx-mn)*100).round(1)

    return df

# Streamlit UI
st.set_page_config(layout="wide", page_title="Kâhin 15 – Karşılaştırmalı Analiz")
st.title("🏇 LiderForm vs Yenibeygir + Kâhin 15 Skor")

if st.button("Verileri Çek ve Analiz Et"):
    with st.spinner("LiderForm’dan…"):
        lf = fetch_liderform_results()
    with st.spinner("Yenibeygir’den…"):
        yb = fetch_yenibeygir_results()

    st.subheader("LiderForm")
    st.dataframe(lf, use_container_width=True)

    st.subheader("Yenibeygir")
    st.dataframe(yb, use_container_width=True)

    merged = merge_results(lf, yb)
    scored = calculate_kahin15_score(merged)

    st.subheader("Kâhin 15 Puanlama")
    st.dataframe(scored.sort_values("k15_score", ascending=False),
                 use_container_width=True)