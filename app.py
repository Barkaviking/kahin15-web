import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date

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

# 3) İki kaynaktan gelen sonuçları at ismi üzerinden birleştir
def merge_results(lf, yb):
    lf = lf.rename(columns=lambda c: c.lower())
    yb = yb.rename(columns=lambda c: c.lower())
    left_on  = "adi"        # LiderForm at ismi kolonu
    right_on = "at ismi"    # Yenibeygir at ismi kolonu

    if left_on in lf.columns and right_on in yb.columns:
        merged = pd.merge(
            lf, yb,
            left_on=left_on, right_on=right_on,
            how="outer",
            suffixes=("_ldr", "_ybg")
        )
    else:
        merged = pd.concat([lf, yb], axis=1)
    return merged

# 4) 12 kriterli puanlama: ilk 4 kriter örnek, 5–12 için şablon
def calculate_kahin15_score(df):
    df = df.copy()

    # --- Criterion 1: Ortalama AGF > 20%
    for col in ["agf_ldr", "agf_ybg"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace("%",""), errors="coerce")
    df["avg_agf"] = df[["agf_ldr","agf_ybg"]].mean(axis=1)
    df["c1"] = (df["avg_agf"] > 20).astype(int)

    # --- Criterion 2: Sprint süresi < 36 (örn.)
    sprint_cols = [c for c in df.columns if "sprint" in c]
    if sprint_cols:
        df["avg_sprint"] = df[sprint_cols].astype(float).mean(axis=1)
        df["c2"] = (df["avg_sprint"] < 36).astype(int)
    else:
        df["c2"] = 0

    # --- Criterion 3: Jokey win rate > %10 (placeholder)
    df["c3"] = 0  # TODO: jokey win rate logic ekle

    # --- Criterion 4: Trainer win rate > %10 (placeholder)
    df["c4"] = 0  # TODO: antrenör win rate logic ekle

    # --- Criterion 5–12: Kendi tanımladığın diğer kriterler
    for i in range(5, 13):
        df[f"c{i}"] = 0  # TODO: her kriter için binarize çözüm ekle

    # Toplam Kâhin 15 puanı
    crit_cols = [f"c{i}" for i in range(1, 13)]
    df["k15_score"] = df[crit_cols].sum(axis=1)

    return df

# Streamlit arayüzü
st.set_page_config(layout="wide", page_title="Kâhin 15 – Karşılaştırmalı Analiz")
st.title("🏇 Günün Sonuçları: LiderForm vs Yenibeygir + Kâhin 15 Skor")

if st.button("Verileri Çek ve Analiz Et"):
    with st.spinner("LiderForm’dan çekiliyor…"):
        lf_df = fetch_liderform_results()
    with st.spinner("Yenibeygir’den çekiliyor…"):
        yb_df = fetch_yenibeygir_results()

    if lf_df.empty and yb_df.empty:
        st.error("Veri alınamadı.")
    else:
        st.subheader("► LiderForm Sonuçları")
        st.dataframe(lf_df, use_container_width=True)

        st.subheader("► Yenibeygir Sonuçları")
        st.dataframe(yb_df, use_container_width=True)

        merged = merge_results(lf_df, yb_df)
        scored = calculate_kahin15_score(merged)

        st.subheader("► Kâhin 15 Puanlaması")
        st.dataframe(
            scored.sort_values("k15_score", ascending=False),
            use_container_width=True
        )