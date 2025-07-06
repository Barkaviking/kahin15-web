import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup

# Generic table scraper
def generic_table_scraper(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table")
        if table is None:
            return pd.DataFrame()
        headers = [th.text.strip() for th in table.find("tr").find_all(["th","td"])]
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

# Fetch daily program from TJK
def fetch_daily_program(date_str):
    url = ("https://www.tjk.org/TR/yarissever/Info/Page/GunlukYarisProgrami"
           f"?QueryParameter_Tarih={date_str}")
    return generic_table_scraper(url)

# Streamlit UI
st.set_page_config(page_title="Kâhin 15 Program", layout="wide")
st.title("🏇 Kâhin 15 – Günlük Program")

date = st.date_input("Tarih")
if st.button("Programı Getir"):
    # TJK formatı: DD/MM/YYYY
    d, m, y = date.day, date.month, date.year
    qdate = f"{d:02d}/{m:02d}/{y}"
    df = fetch_daily_program(qdate)

    if df.empty:
        st.error("Program verisi alınamadı.")
    else:
        st.dataframe(df, use_container_width=True)