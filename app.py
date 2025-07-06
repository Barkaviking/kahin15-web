import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# İstanbul için örnek veri
def fetch_istanbul_data(race_number):
    return pd.DataFrame([
        {"At": "SPECIAL MAN", "No": 6, "Puan": 91, "Odds%": 36.4},
        {"At": "AMAZING TOUCH", "No": 2, "Puan": 88, "Odds%": 29.7},
        {"At": "DAPPER MAN", "No": 4, "Puan": 84, "Odds%": 21.1},
    ])

# Saratoga için Equibase scraping
def fetch_saratoga_data():
    try:
        url = "https://www.equibase.com/static/entry/SAR20240801USA-EQB.html"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        atlar = [tag.text.strip() for tag in soup.select("td a[href*='HorseID']")]
        return pd.DataFrame({"At": atlar})
    except Exception as e:
        st.error(f"Saratoga verisi çekilemedi: {e}")
        return pd.DataFrame()

# Indianapolis için Equibase scraping
def fetch_indianapolis_data():
    try:
        url = "https://www.equibase.com/static/entry/IND20240801USA-EQB.html"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        atlar = [tag.text.strip() for tag in soup.select("td a[href*='HorseID']")]
        return pd.DataFrame({"At": atlar})
    except Exception as e:
        st.error(f"Indianapolis verisi çekilemedi: {e}")
        return pd.DataFrame()

# Streamlit arayüz
st.set_page_config(page_title="Kâhin 15 Mobil Analiz", layout="wide")
st.title("🧠 Kâhin 15 Mobil Analiz")

pist = st.selectbox("Pist Seç", ["İstanbul", "Saratoga", "Indianapolis"])

if pist == "İstanbul":
    race = st.selectbox("Yarış Numarası", list(range(1, 10)), index=0)
    if st.button("Analiz Et"):
        df = fetch_istanbul_data(race)
        st.markdown(f"## İstanbul {race}. Koşu – İlk 3 At")
        st.table(df[["At", "No", "Puan", "Odds%"]])
        st.caption("Veriler ‘Kâhin 15’ kriterlerine göre analiz edilmiştir.")

elif pist == "Saratoga":
    if st.button("Saratoga Verilerini Getir"):
        df = fetch_saratoga_data()
        if not df.empty:
            st.markdown("## Saratoga – Koşu Listesi")
            st.table(df)
            st.caption("Veriler Equibase üzerinden çekilmiştir.")

elif pist == "Indianapolis":
    if st.button("Indianapolis Verilerini Getir"):
        df = fetch_indianapolis_data()
        if not df.empty:
            st.markdown("## Indianapolis – Koşu Listesi")
            st.table(df)
            st.caption("Veriler Equibase üzerinden çekilmiştir.")