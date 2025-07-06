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

        # Header row
        header_cells = table.find("tr").find_all(["th", "td"])
        headers = [hc.text.strip() for hc in header_cells]

        # Data rows
        data = []
        for row in table.find_all("tr")[1:]:
            cells = row.find_all("td")
            if len(cells) == len(headers):
                record = {headers[i]: cells[i].text.strip() for i in range(len(headers))}
                data.append(record)

        return pd.DataFrame(data)

    except Exception as e:
        return pd.DataFrame([{"Hata": f"{e}"}])

# —————————————————————————————————————————————————————————————
# SCRAPER FUNCTIONS
# —————————————————————————————————————————————————————————————
def fetch_galop_data(race_number):
    url = f"https://liderform.com.tr/program/galop/2025-07-06/ISTANBUL/{race_number}"
    return generic_table_scraper(url)

def fetch_performans_data(race_number):
    url = f"https://liderform.com.tr/program/performans/2025-07-06/ISTANBUL/{race_number}"
    return generic_table_scraper(url)

def fetch_sprint_data(race_number):
    url = f"https://liderform.com.tr/program/sprintler/2025-07-06/ISTANBUL/{race_number}"
    return generic_table_scraper(url)

def fetch_orijin_data(race_number):
    url = f"https://liderform.com.tr/program/orijin/2025-07-06/ISTANBUL/{race_number}"
    return generic_table_scraper(url)

def fetch_kim_kimi_data(race_number):
    url = f"https://liderform.com.tr/program/kim-kimi-gecti/2025-07-06/ISTANBUL/{race_number}"
    return generic_table_scraper(url)

def fetch_jokey_data(race_number):
    url = f"https://liderform.com.tr/program/jokey/2025-07-06/ISTANBUL/{race_number}"
    return generic_table_scraper(url)

# —————————————————————————————————————————————————————————————
# STREAMLIT APP
# —————————————————————————————————————————————————————————————
st.set_page_config(page_title="Kâhin 15 – İstanbul Analiz", layout="wide")
st.title("🏇 Kâhin 15 – İstanbul 07.06.2025 Analiz")

race_number = st.selectbox("Koşu Numarası Seç", list(range(1, 10)))

tabs = st.tabs([
    "Program", "Performans", "Galop",
    "Sprint", "Orijin", "Kim Kimi Geçti", "Jokey"
])

with tabs[0]:
    st.header("Program Verileri")
    df = generic_table_scraper(
        f"https://liderform.com.tr/program/2025-07-06/ISTANBUL/{race_number}"
    )
    if df.empty:
        st.warning("Program verisi bulunamadı.")
    else:
        st.dataframe(df, use_container_width=True)

with tabs[1]:
    if st.button("Performans Verilerini Göster", key="btn_perf"):
        df = fetch_performans_data(race_number)
        if df.empty:
            st.warning("Performans verisi bulunamadı.")
        else:
            st.dataframe(df, use_container_width=True)

with tabs[2]:
    if st.button("Galop Verilerini Göster", key="btn_galop"):
        df = fetch_galop_data(race_number)
        if df.empty:
            st.warning("Galop verisi bulunamadı.")
        else:
            st.dataframe(df, use_container_width=True)

with tabs[3]:
    if st.button("Sprint Verilerini Göster", key="btn_sprint"):
        df = fetch_sprint_data(race_number)
        if df.empty:
            st.warning("Sprint verisi bulunamadı.")
        else:
            st.dataframe(df, use_container_width=True)

with tabs[4]:
    if st.button("Orijin Verilerini Göster", key="btn_orijin"):
        df = fetch_orijin_data(race_number)
        if df.empty:
            st.warning("Orijin verisi bulunamadı.")
        else:
            st.dataframe(df, use_container_width=True)

with tabs[5]:
    if st.button("Kim Kimi Geçti Verilerini Göster", key="btn_kim"):
        df = fetch_kim_kimi_data(race_number)
        if df.empty:
            st.warning("Kim kimi geçti verisi bulunamadı.")
        else:
            st.dataframe(df, use_container_width=True)

with tabs[6]:
    if st.button("Jokey Verilerini Göster", key="btn_jokey"):
        df = fetch_jokey_data(race_number)
        if df.empty:
            st.warning("Jokey verisi bulunamadı.")
        else:
            st.dataframe(df, use_container_width=True)