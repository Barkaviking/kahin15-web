import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

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
        # header
        headers = [cell.text.strip() for cell in table.find("tr").find_all(["th","td"])]
        data = []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) != len(headers):
                continue
            record = {headers[i]: cols[i].text.strip() for i in range(len(headers))}
            data.append(record)
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# —————————————————————————————————————————————————————————————
# SECTION FETCHERS
# —————————————————————————————————————————————————————————————
def fetch_data(section, date_str, pist, race_number):
    if section:
        url = f"https://liderform.com.tr/program/{section}/{date_str}/{pist}/{race_number}"
    else:
        url = f"https://liderform.com.tr/program/{date_str}/{pist}/{race_number}"
    return generic_table_scraper(url)

# —————————————————————————————————————————————————————————————
# STREAMLIT APP
# —————————————————————————————————————————————————————————————
st.set_page_config(page_title="Kâhin 15 – İstanbul Analiz", layout="wide")
st.title("🏇 Kâhin 15 – İstanbul 07.06.2025 Analiz")

date_str = "2025-07-06"
race_number = st.selectbox("Koşu Numarası Seç", list(range(1, 13)))
pist = st.selectbox("Pist Seç", [
    "ISTANBUL","ANKARA","IZMIR","ADANA",
    "BURSA","KOCAELI","ELAZIG","URFA",
    "SAMSUN","SARATOGA","INDIANAPOLIS"
])

tabs = st.tabs([
    "Program", "Performans", "Galop",
    "Sprint", "Orijin", "Kim Kimi Geçti", "Jokey"
])
sections = [
    "",            # Program
    "performans",  # Performans
    "galop",       # Galop
    "sprintler",   # Sprint
    "orijin",      # Orijin
    "kim-kimi-gecti",  # Kim Kimi Geçti
    "jokey"        # Jokey
]
keys = ["prog","perf","galo","spri","ori","kim","jok"]

for tab, section_key, key in zip(tabs, sections, keys):
    with tab:
        if st.button(f"{tab} Verilerini Göster", key=key):
            df = fetch_data(section_key, date_str, pist, race_number)
            if df.empty:
                st.warning(f"{tab} verisi bulunamadı.")
            else:
                st.success(f"{tab} verisi yüklendi.")
                st.dataframe(df, use_container_width=True)