import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date

def fetch_daily_program(date_str):
    url = f"https://www.tjk.org/TR/yarissever/Info/Page/GunlukYarisProgrami?QueryParameter_Tarih={date_str}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
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
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
        return pd.DataFrame()

# Streamlit UI
st.set_page_config(page_title="Kâhin 15 Program", layout="wide")
st.title("🏇 Kâhin 15 – Günlük Program")

today = date.today()
selected_date = st.date_input("Tarih", value=today)

if st.button("Programı Getir"):
    # GG/AA/YYYY formatına çevir
    gun = f"{selected_date.day:02d}"
    ay = f"{selected_date.month:02d}"
    yil = f"{selected_date.year}"
    tjk_date = f"{gun}/{ay}/{yil}"

    df = fetch_daily_program(tjk_date)

    if df.empty:
        st.warning(f"{tjk_date} tarihli program bulunamadı veya tablo çekilemedi.")
    else:
        st.success(f"{tjk_date} tarihli program yüklendi.")
        st.dataframe(df, use_container_width=True)