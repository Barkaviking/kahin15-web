
import streamlit as st
import pandas as pd
import requests 
from bs4 
import BeautifulSoup

# —————————————————————————————————————————————————————————————
# GENERIC TABLE SCRAPER
# —————————————————————————————————————————————————————————————
def generic_table_scraper(url):
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        if not table:
            return pd.DataFrame()
        headers = [cell.text.strip() for cell in table.find("tr").find_all(["th","td"])]
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
# FETCHER
# —————————————————————————————————————————————————————————————
def fetch_data(section, date_str, track, race_no):
    if section:
        url = f"https://liderform.com.tr/program/{section}/{date_str}/{track}/{race_no}"
    else:
        url = f"https://liderform.com.tr/program/{date_str}/{track}/{race_no}"
    return generic_table_scraper(url)

# —————————————————————————————————————————————————————————————
# APP
# —————————————————————————————————————————————————————————————
st.set_page_config(page_title="Kâhin 15 – Analiz", layout="wide")
st.title("🏇 Kâhin 15 – İstanbul 07.06.2025")

# inputs
date_str = "2025-07-06"
race_no   = st.selectbox("Koşu Numarası", list(range(1,13)))
track     = st.selectbox("Pist Seçimi", [
    "ISTANBUL","ANKARA","IZMIR","ADANA","BURSA",
    "KOCAELI","ELAZIG","URFA","SAMSUN","SARATOGA","INDIANAPOLIS"
])

# tabs & config
tabs     = st.tabs(["Program","Performans","Galop","Sprint","Orijin","Kim Kimi Geçti","Jokey"])
sections = ["","performans","galop","sprintler","orijin","kim-kimi-gecti","jokey"]
labels   = ["Program","Performans","Galop","Sprint","Orijin","Kim Kimi Geçti","Jokey"]
keys     = ["p","f","g","s","o","k","j"]

# loop through each tab
for tab, sec, lbl, key in zip(tabs, sections, labels, keys):
    with tab:
        if st.button(f"{lbl} Verilerini Göster", key=key):
            df = fetch_data(sec, date_str, track, race_no)
            if df.empty:
                st.warning(f"{lbl} verisi bulunamadı.")
            else:
                st.success(f"{lbl} verisi yüklendi.")
                st.dataframe(df, use_container_width=True)