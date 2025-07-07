# app.py

import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date

# 1) Yenibeygir – Ön Yarış Bülteni
def fetch_yenibeygir_bulten():
    url = "https://yenibeygir.com/"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tbl = soup.find("table")
    raw = [th.get_text(strip=True) for th in tbl.find_all("th")]
    seen, cols = {}, []
    for h in raw:
        key = h or "Unnamed"
        seen[key] = seen.get(key, 0) + 1
        suffix = f"_{seen[key]}" if seen[key] > 1 else ""
        cols.append(key + suffix)

    rows = []
    for tr in tbl.find_all("tr")[1:]:
        vals = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(vals) == len(cols):
            rows.append(vals)

    df = pd.DataFrame(rows, columns=cols)
    # normalize columns
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    # race number
    if "blt_no" in df.columns:
        df["race"] = df["blt_no"].astype(str)
    # horse name
    if "at_ismi" in df.columns:
        df.rename(columns={"at_ismi": "horse"}, inplace=True)
    return df

# 2) LiderForm – Galop Bülteni
def fetch_liderform_galop():
    url = "https://liderform.com.tr/program/galop-bulten"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tbl = soup.find("table")
    if tbl is None:
        return pd.DataFrame()

    cols = [th.get_text(strip=True) for th in tbl.find_all("th")]
    rows = []
    for tr in tbl.find_all("tr")[1:]:
        vals = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(vals) == len(cols):
            rows.append(vals)

    df = pd.DataFrame(rows, columns=cols)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    # race number
    if "no" in df.columns:
        df["race"] = df["no"].astype(str)
    # horse name
    for key in ("adi", "at_ismi"):
        if key in df.columns:
            df.rename(columns={key: "horse"}, inplace=True)
            break
    return df

# 3) Sonduzluk – Koşu Listesi & Altılı Ganyan Kuponları
def fetch_sonduzluk():
    url = "https://sonduzluk.com/"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    # koşu programı
    items = soup.select("ul li")
    sched = []
    for li in items:
        txt = li.get_text(" ", strip=True)
        if "Koşu" in txt and "-" in txt:
            race, time = txt.split(" - ")
            hip, num = race.rsplit(" ", 1)
            sched.append({
                "hipodrom": hip.strip(),
                "koşu_no": num.replace("Koşu", "").strip(),
                "saat": time.strip()
            })
    df_sched = pd.DataFrame(sched)
    # prepare race as string
    if not df_sched.empty:
        df_sched["race"] = df_sched["koşu_no"].astype(str)

    # altılı kuponları
    coupons = []
    for pre in soup.find_all("pre"):
        text = pre.get_text("\n", strip=True)
        if "6'LI GANYAN" in text:
            coupons.append(text)

    return df_sched, coupons

# 4) AltılıGanyan.com – Sonuçlar & Oranlar
def fetch_altiliganyan():
    url = "https://www.altiliganyan.com/tjk/at-yarisi-sonuclari"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    tbl = soup.find("table")
    if tbl is None:
        return pd.DataFrame()

    cols = [th.get_text(strip=True) for th in tbl.find_all("th")]
    rows = []
    for tr in tbl.find_all("tr")[1:]:
        vals = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(vals) == len(cols):
            rows.append(vals)

    df = pd.DataFrame(rows, columns=cols)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    # race number
    if "koşu_no" in df.columns:
        df["race"] = df["koşu_no"].astype(str)
    # horse
    if "at_ismi" in df.columns:
        df.rename(columns={"at_ismi": "horse"}, inplace=True)
    return df

# 5) Merge & Eksik Veriyi Tamamlama
def merge_data(yb, gb, sd_sched, ag):
    # start with yenibeygir
    df = yb.copy()

    # 5.1 merge schedule if present
    if all(col in sd_sched.columns for col in ["race", "hipodrom", "koşu_no", "saat"]):
        df = pd.merge(
            df,
            sd_sched[["race", "hipodrom", "koşu_no", "saat"]],
            on="race", how="left"
        )
    else:
        df["hipodrom"] = None
        df["koşu_no"] = None
        df["saat"] = None

    # 5.2 merge galop puanları
    if all(col in gb.columns for col in ["race", "gp", "hp"]):
        df = pd.merge(df, gb[["race", "gp", "hp"]], on="race", how="left")
    else:
        df["gp"] = None
        df["hp"] = None

    # 5.3 merge altılıganyan sonuç & oran
    if all(col in ag.columns for col in ["race", "horse", "ganyan", "agf"]):
        df = pd.merge(
            df,
            ag[["race", "horse", "ganyan", "agf"]],
            on=["race", "horse"], how="left"
        )
    else:
        df["ganyan"] = None
        df["agf"] = None

    # 5.4 yerli/yabancı
    if "menşei" in yb.columns:
        df["yerli_mi"] = df["menşei"].str.contains("Türkiye", case=False, na=False)
    else:
        df["yerli_mi"] = None

    return df

# ───────── Streamlit UI ─────────
st.set_page_config(page_title="Kâhin 15 – Geniş Bülten", layout="wide")
st.title("🏇 Tüm Kaynaklardan At Yarışı Bülteni")

tarih = st.date_input("Tarih", value=date.today())

if st.button("Bülteni Derle"):
    yb, gb = fetch_yenibeygir_bulten(), fetch_liderform_galop()
    sd_sched, sd_coupons = fetch_sonduzluk()
    ag = fetch_altiliganyan()

    # Görünümler
    st.subheader("► Yenibeygir Bülteni")
    st.dataframe(yb, use_container_width=True)

    st.subheader("► LiderForm Galop Bülteni")
    if gb.empty:
        st.warning("Galop bülteni bulunamadı.")
    else:
        st.dataframe(gb, use_container_width=True)

    st.subheader("► Sonduzluk – Koşu Listesi")
    if sd_sched.empty:
        st.warning("Sonduzluk programı alınamadı.")
    else:
        st.dataframe(sd_sched, use_container_width=True)

    if sd_coupons:
        st.subheader("► Sonduzluk – Altılı Ganyan Kuponları")
        for c in sd_coupons:
            st.code(c)

    st.subheader("► AltılıGanyan – Sonuç & Oranlar")
    if ag.empty:
        st.warning("AltılıGanyan sonuç tablosu bulunamadı.")
    else:
        st.dataframe(ag, use_container_width=True)

    # Birleştirilmiş tablo
    merged = merge_data(yb, gb, sd_sched, ag)
    st.subheader("► Birleştirilmiş At Listesi")
    # Öne çıkarmak istediğin sütunlar
    cols = [
        "hipodrom", "koşu_no", "race", "horse", "yerli_mi",
        "ganyan", "agf", "gp", "hp", "saat"
    ]
    available = [c for c in cols if c in merged.columns]
    st.dataframe(merged[available], use_container_width=True)

    # CSV indir
    csv = merged.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Tam Bülteni CSV İndir",
        data=csv,
        file_name=f"bulten_{tarih}.csv",
        mime="text/csv"
    )