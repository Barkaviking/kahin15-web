import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date
import io

# 1) Yenibeygir – Ön Yarış Bülteni
def fetch_yenibeygir_bulten():
    url = "https://yenibeygir.com/"
    r = requests.get(url, timeout=10); r.raise_for_status()
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
    df.columns = [c.strip() for c in df.columns]
    return df

# 2) LiderForm – Galop Bülteni
def fetch_liderform_galop():
    url = "https://liderform.com.tr/program/galop-bulten"
    r = requests.get(url, timeout=10); r.raise_for_status()
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
    return df

# 3) Sonduzluk – Koşu Listesi & Altılı Ganyan Kuponları
def fetch_sonduzluk():
    url = "https://sonduzluk.com/"
    r = requests.get(url, timeout=10); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # Günün koşu programı
    items = soup.select("ul li")
    sched = []
    for li in items:
        txt = li.get_text(" ", strip=True)
        if "Koşu" in txt and "-" in txt:
            race, time = txt.split(" - ")
            hip, num = race.rsplit(" ", 1)
            sched.append({
                "Hipodrom": hip.strip(),
                "KoşuNo": num.replace("Koşu", "").strip(),
                "Saat": time.strip()
            })
    df_sched = pd.DataFrame(sched)
    # Altılı ganyan kuponları
    coupons = []
    for pre in soup.find_all("pre"):
        text = pre.get_text("\n", strip=True)
        if "6'LI GANYAN" in text:
            coupons.append(text)
    return df_sched, coupons

# 4) AltılıGanyan.com – Sonuçlar & Oranlar
def fetch_altiliganyan():
    url = "https://www.altiliganyan.com/tjk/at-yarisi-sonuclari"
    r = requests.get(url, timeout=10); r.raise_for_status()
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
    return df

# 5) Merge & Eksik Veriyi Tamamlama
def merge_data(yb, gb, sd_sched, ag):
    # Normalize column names
    yb = yb.rename(columns=lambda c: c.lower().replace(" ", "_"))
    gb = gb.rename(columns=lambda c: c.lower().replace(" ", "_"))
    sd = sd_sched.rename(columns=lambda c: c.lower().replace(" ", "_"))
    ag = ag.rename(columns=lambda c: c.lower().replace(" ", "_"))
    
    # Standart sütunlar
    if "blt_no" in yb.columns:
        yb["race"] = yb["blt_no"].astype(str)
    if "kosu_no" in sd.columns:
        sd["race"] = sd["kosu_no"].astype(str)
    if "no" in gb.columns:
        gb["race"] = gb["no"].astype(str)
    if "koşu_no" in ag.columns:
        ag["race"] = ag["koşu_no"].astype(str)
    
    # At ismi standarizasyonu
    for df in (yb, ag):
        if "at_ismi" in df.columns:
            df.rename(columns={"at_ismi": "horse"}, inplace=True)
    if "adi" in gb.columns:
        gb.rename(columns={"adi": "horse"}, inplace=True)
    if "at_ismi" in gb.columns:
        gb.rename(columns={"at_ismi": "horse"}, inplace=True)
    
    # Merge akışı
    df = pd.merge(yb, sd[["race","hipodrom","saat"]], on="race", how="left")
    df = pd.merge(df, gb[["race","gp","hp"]], on="race", how="left")
    df = pd.merge(df, ag[["race","horse","ganyan","agf"]], on=["race","horse"], how="left")
    
    # Yerli/Yabancı ayrımı
    if "menşei" in yb.columns:
        df["yerli_mi"] = df["menşei"].str.contains("Türkiye", case=False, na=False)
    
    return df

# ───────── Streamlit UI ─────────
st.set_page_config(page_title="Kâhin 15 – Geniş Bülten", layout="wide")
st.title("🏇 Tüm Kaynaklardan At Yarışı Bülteni")

tarih = st.date_input("Tarih", value=date.today())

if st.button("Bülteni Derle"):
    # Veri çekme
    yb          = fetch_yenibeygir_bulten()
    gb          = fetch_liderform_galop()
    sd_sched, sd_coupons = fetch_sonduzluk()
    ag          = fetch_altiliganyan()

    # Görselleştirme
    st.subheader("► Yenibeygir Bülteni")
    st.dataframe(yb, use_container_width=True)

    st.subheader("► LiderForm Galop Bülteni")
    if gb.empty:
        st.warning("Galop bülteni bulunamadı.")
    else:
        st.dataframe(gb, use_container_width=True)

    st.subheader("► Sonduzluk – Koşu Listesi")
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

    # Birleştirilmiş geniş tablo
    merged = merge_data(yb, gb, sd_sched, ag)
    st.subheader("► Birleştirilmiş At Listesi")
    st.dataframe(merged, use_container_width=True)

    # İndirme
    csv = merged.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Tam Bülteni CSV İndir", data=csv,
                       file_name=f"bulten_{tarih}.csv", mime="text/csv")