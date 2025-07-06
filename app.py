import streamlit as st
import pandas as pd
import requests
import datetime

# —————————————————————————————————————————————————————————————
# SMART TABLE SCRAPER
# —————————————————————————————————————————————————————————————
def smart_table_scraper(url):
    """
    1) URL’den tüm tabloları çek (pd.read_html)
    2) Başlığı 'At' veya 'Jokey Adı' içeren tabloyu döndür
    3) Bulamazsa ilk tabloyu döndür
    """
    try:
        # pandas ile tabloları al
        tables = pd.read_html(url)
        if not tables:
            return pd.DataFrame()
        
        # Öncelikle 'At' barındıran tabloyu ara
        for df in tables:
            cols = [c.lower() for c in df.columns.astype(str)]
            if any("at" in c for c in cols) or any("jokey" in c for c in cols):
                return df

        # Yoksa ilk tabloyu al
        return tables[0]

    except Exception:
        return pd.DataFrame()

# —————————————————————————————————————————————————————————————
# VERİ ÇEKME FONKSİYONU
# —————————————————————————————————————————————————————————————
def fetch_section(section, date_str, track, race_no):
    """
    section = ""              → /program/<date>/<track>/<race_no>
    section = "performans"    → /program/performans/<date>/<track>/<race_no>
    vs.
    """
    if section:
        url = f"https://liderform.com.tr/program/{section}/{date_str}/{track}/{race_no}"
    else:
        url = f"https://liderform.com.tr/program/{date_str}/{track}/{race_no}"
    return smart_table_scraper(url)

# —————————————————————————————————————————————————————————————
# STREAMLIT APP
# —————————————————————————————————————————————————————————————
st.set_page_config(page_title="Kâhin 15 – Yarış Analiz", layout="wide")
st.title("🏇 Kâhin 15 – Yarış Verileri")

# Tarih seçimi: bugün varsayılan, dilediğini seçebilirsin
selected_date = st.date_input("Tarih Seç", datetime.date.today())
date_str       = selected_date.strftime("%Y-%m-%d")

race_no = st.selectbox("Koşu Numarası", list(range(1, 13)))
track   = st.selectbox("Hipodrom/Şehir", [
    "ISTANBUL","ANKARA","IZMIR","ADANA","BURSA",
    "KOCAELI","ELAZIG","URFA","SAMSUN",
    "GULFSTREAM PARK","SARATOGA","INDIANAPOLIS"
])

# Sekme tanımları
tabs     = st.tabs(["Program","Performans","Galop","Sprint","Orijin","Birincilikler","Jokey"])
sections = ["","performans","galop","sprintler","orijin","birincilikler","jokey"]
labels   = ["Program","Performans","Galop","Sprint","Orijin","Birincilikler","Jokey"]
keys     = ["p","f","g","s","o","b","j"]

for tab, sec, lbl, key in zip(tabs, sections, labels, keys):
    with tab:
        if st.button(f"{lbl} Verilerini Göster", key=key):
            df = fetch_section(sec, date_str, track, race_no)
            if df.empty:
                st.warning(f"{lbl} verisi bulunamadı.")
            else:
                st.success(f"{lbl} verisi yüklendi ({len(df)} satır).")
                st.dataframe(df, use_container_width=True)