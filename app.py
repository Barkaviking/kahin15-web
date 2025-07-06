import streamlit as st
import pandas as pd
import requests
import datetime

# —————————————————————————————————————————————————————————————
# SMART TABLE SCRAPER
# —————————————————————————————————————————————————————————————
def smart_table_scraper(url):
    try:
        tables = pd.read_html(url)
        if not tables:
            return pd.DataFrame()
        # "At" veya "Jokey" başlığı olan tabloyu bul
        for df in tables:
            cols = [c.lower() for c in df.columns.astype(str)]
            if any("at" in c for c in cols) or any("jokey" in c for c in cols):
                return df
        return tables[0]
    except:
        return pd.DataFrame()

# —————————————————————————————————————————————————————————————
# VERİ ÇEKME
# —————————————————————————————————————————————————————————————
def fetch_section(sec, date_str, track, race_no):
    base = f"https://liderform.com.tr/program"
    url = (
        f"{base}/{sec}/{date_str}/{track}/{race_no}"
        if sec else
        f"{base}/{date_str}/{track}/{race_no}"
    )
    return smart_table_scraper(url)

# —————————————————————————————————————————————————————————————
# APP CONFIG & STATE
# —————————————————————————————————————————————————————————————
st.set_page_config("Kâhin 15 – Döngüsel Analiz", layout="wide")
st.title("🏇 Kâhin 15 – Döngüsel Yarış Analizi")

# Tarih seçimi
sel_date = st.date_input("Tarih", datetime.date.today())
date_str = sel_date.strftime("%Y-%m-%d")

# Hipodrom/Şehir seçimi
track = st.selectbox("Pist", [
    "ISTANBUL","ANKARA","IZMIR","ADANA","BURSA",
    "KOCAELI","ELAZIG","URFA","SAMSUN",
    "GULFSTREAM PARK","SARATOGA","INDIANAPOLIS"
])

# Döngüsel sekme & koşu state
if "sec_idx" not in st.session_state:
    st.session_state.sec_idx = 0
if "race_idx" not in st.session_state:
    st.session_state.race_idx = 0

sections = ["","performans","galop","sprintler","orijin","birincilikler","jokey"]
labels   = ["Program","Performans","Galop","Sprint","Orijin","Birincilikler","Jokey"]
N_SECS   = len(sections)
N_RACES  = 12

col1, col2, col3 = st.columns([1,2,1])
with col1:
    if st.button("◀ Sekmeye Geri"):
        st.session_state.sec_idx = (st.session_state.sec_idx - 1) % N_SECS
with col3:
    if st.button("Sekmeye Geç ▶"):
        st.session_state.sec_idx = (st.session_state.sec_idx + 1) % N_SECS
with col2:
    st.markdown(f"### **Sekme:** {labels[st.session_state.sec_idx]}")

col4, col5, col6 = st.columns([1,2,1])
with col4:
    if st.button("◀ Koşuya Geri"):
        st.session_state.race_idx = (st.session_state.race_idx - 1) % N_RACES
with col6:
    if st.button("Koşuya Geç ▶"):
        st.session_state.race_idx = (st.session_state.race_idx + 1) % N_RACES
with col5:
    # +1 çünkü 0-based index
    st.markdown(f"### **Koşu No:** {st.session_state.race_idx+1}")

# Veri çek ve göster
sec_key  = sections[st.session_state.sec_idx]
race_no  = st.session_state.race_idx + 1
df       = fetch_section(sec_key, date_str, track, race_no)

st.divider()
if df.empty:
    st.warning(f"{labels[st.session_state.sec_idx]} verisi bulunamadı.")
else:
    st.success(f"{labels[st.session_state.sec_idx]} verisi yüklendi ({len(df)} satır).")
    st.dataframe(df, use_container_width=True)