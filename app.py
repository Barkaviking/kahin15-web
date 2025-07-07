import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import numpy as np

# 1) Yenibeygir – Ön Yarış Bülteni
def fetch_yeni_bulten():
    url = "https://yenibeygir.com/"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tbl = soup.find("table")

    # Başlıkları temizle
    raw_cols = [th.get_text(strip=True) for th in tbl.find_all("th")]
    cols, seen = [], {}
    for h in raw_cols:
        key = h or "Unnamed"
        seen[key] = seen.get(key, 0) + 1
        cols.append(f"{key}" + (f"_{seen[key]}" if seen[key] > 1 else ""))
        
    # Satırları oku
    rows = []
    for tr in tbl.find_all("tr")[1:]:
        vals = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(vals) == len(cols):
            rows.append(vals)
    return pd.DataFrame(rows, columns=cols)

# 2) LiderForm – Galop Bülteni
def fetch_galop_bulten():
    url = "https://liderform.com.tr/program/galop-bulten"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tbl = soup.find("table")
    cols = [th.get_text(strip=True) for th in tbl.find_all("th")]
    rows = []
    for tr in tbl.find_all("tr")[1:]:
        vals = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(vals) == len(cols):
            rows.append(vals)
    return pd.DataFrame(rows, columns=cols)

# 3) Ek CSV ile pedigrik + antrenman puanları yükleme
def load_extra_data():
    up = st.file_uploader("📥 Pedigree & Training CSV (opsiyonel)", type="csv")
    if up:
        df = pd.read_csv(up)
        df.columns = [c.strip().lower() for c in df.columns]
        return df
    return pd.DataFrame()

# 4) Birleştir ve normalize et
def merge_pre_race(yb, gb, extra):
    yb = yb.rename(columns=lambda c: c.lower())
    gb = gb.rename(columns=lambda c: c.lower())
    # ortak anahtar: at ismi
    if "at ismi" in yb.columns and "adi" in gb.columns:
        df = pd.merge(yb, gb, left_on="at ismi", right_on="adi", how="outer")
    else:
        df = pd.concat([yb, gb], axis=1)
    # ekstra verileri ekle
    if not extra.empty and "at ismi" in extra.columns:
        df = pd.merge(df, extra, on="at ismi", how="left")
    return df

# 5) 12 kriterden 8 öncesi + kazanma tahmini
def score_pre_race(df):
    df = df.copy()

    # c1: GP puanı > 60
    if "gp" in df:
        df["gp"] = pd.to_numeric(df["gp"], errors="coerce")
        df["c1"] = (df["gp"] > 60).astype(int)
    else:
        df["c1"] = 0

    # c2: HP puanı > 60
    if "hp" in df:
        df["hp"] = pd.to_numeric(df["hp"], errors="coerce")
        df["c2"] = (df["hp"] > 60).astype(int)
    else:
        df["c2"] = 0

    # c3: Handikap seviyesi <= 15 (örn.)
    if "hnd" in df:
        df["hnd"] = pd.to_numeric(df["hnd"], errors="coerce")
        df["c3"] = (df["hnd"] <= 15).astype(int)
    else:
        df["c3"] = 0

    # c4: Son 10 yarışta ilk 3 bitirme sayısı >= 3
    if "son 10 yarış" in df:
        df["top3_count"] = df["son 10 yarış"].apply(
            lambda s: sum(int(x)<=3 for x in s.split() if x.isdigit())
        )
        df["c4"] = (df["top3_count"] >= 3).astype(int)
    else:
        df["c4"] = 0

    # c5: Jokey-trainer kombinasyonu (örnek eşik)
    df["c5"] = 0  # bu alanı geçmiş verilerle genişletin

    # c6: Pedigree puanı > 50
    if "pedigree_score" in df:
        df["c6"] = (pd.to_numeric(df["pedigree_score"], errors="coerce") > 50).astype(int)
    else:
        df["c6"] = 0

    # c7: Trainer rapor > 50
    if "trainer_report_score" in df:
        df["c7"] = (pd.to_numeric(df["trainer_report_score"], errors="coerce") > 50).astype(int)
    else:
        df["c7"] = 0

    # c8: Training result > 50
    if "training_result_score" in df:
        df["c8"] = (pd.to_numeric(df["training_result_score"], errors="coerce") > 50).astype(int)
    else:
        df["c8"] = 0

    # c9–c12: kendi ek kriterleriniz (örn. orijin, galop-harmoni, jokey wr, trainer wr)
    for i in range(9, 13):
        df[f"c{i}"] = 0

    # Toplam skor + kazanma yüzdesi
    crits = [f"c{i}" for i in range(1, 13)]
    df["k15_score"] = df[crits].sum(axis=1)
    mn, mx = df["k15_score"].min(), df["k15_score"].max()
    df["win_chance_%"] = ((df["k15_score"]-mn)/(mx-mn)*100).round(1)

    return df

# ─────── Streamlit UI ───────
st.set_page_config(page_title="Kâhin 15 – Ön Yarış Tahmin", layout="wide")
st.title("🏇 Ön Yarış Bülteni & Tahmin – Kâhin 15")

if st.button("Bülteni Çek ve Tahmin Et"):
    yb = fetch_yeni_bulten()
    gb = fetch_galop_bulten()
    extra = load_extra_data()

    st.subheader("► Yenibeygir Bülteni")
    st.dataframe(yb, use_container_width=True)

    st.subheader("► LiderForm Galop Bülteni")
    st.dataframe(gb, use_container_width=True)

    merged = merge_pre_race(yb, gb, extra)
    scored = score_pre_race(merged)

    st.subheader("► Tahminli At Listesi")
    st.dataframe(scored.sort_values("k15_score", ascending=False),
                 use_container_width=True)