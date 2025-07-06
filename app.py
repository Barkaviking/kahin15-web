import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import datetime

# —————————————————————————————————————————————————————————————
# GENERIC TABLE SCRAPER
# —————————————————————————————————————————————————————————————
def generic_table_scraper(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if not table:
            return pd.DataFrame()
        headers = [th.text.strip() for th in table.find("tr").find_all(["th", "td"])]
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

# —————————————————————————————————————————————————————————————
# SECTION FETCHER
# —————————————————————————————————————————————————————————————
def fetch_section(section, date_str, track, race_no):
    if section:
        url = f"https://liderform.com.tr/program/{section}/{date_str}/{track}/{race_no}"
    else:
        url = f"https://liderform.com.tr/program/{date_str}/{track}/{race_no}"
    return generic_table_scraper(url)

# —————————————————————————————————————————————————————————————
# STREAMLIT APP CONFIG
# —————————————————————————————————————————————————————————————
st.set_page_config(page_title="Kâhin 15 – Yarış Analiz", layout="wide")
st.title("🏇 Kâhin 15 – Yarış Verileri")

# — Tarih Seçimi — bugün varsayılan, dilersen manuel değiştir
selected_date = st.date_input(
    "Tarih Seç",
    datetime.date.today()
)
date_str = selected_date.strftime("%Y-%m-%d")

# — Kullanıcı Girdileri
race_no = st.selectbox("Koşu Numarası", list(range(1, 13)))
track   = st.selectbox("Hipodrom/Şehir", [
    "ISTANBUL","ANKARA","IZMIR","ADANA","BURSA",
    "KOCAELI","ELAZIG","URFA","SAMSUN",
    "GULFSTREAM PARK","SARATOGA","INDIANAPOLIS"
])

# — Sekmeler & Bölüm Anahtarları
tabs     = st.tabs(["Program","Performans","Galop","Sprint","Orijin","Birincilikler","Jokey"])
sections = ["","performans","galop","sprintler","orijin","birincilikler","jokey"]
labels   = ["Program","Performans","Galop","Sprint","Orijin","Birincilikler","Jokey"]
keys     = ["prog","perf","galo","s","o","b","j"]

# — Her Sekme İçin Buton & Veri Çekme
for tab, sec, lbl, key in zip(tabs, sections, labels, keys):
    with tab:
        if st.button(f"{lbl} Verilerini Göster", key=key):
            df = fetch_section(sec, date_str, track, race_no)
            if df.empty:
                st.warning(f"{lbl} verisi bulunamadı.")
            else:
                st.success(f"{lbl} verisi yüklendi ({len(df)} satır).")
                st.dataframe(df, use_container_width=True)