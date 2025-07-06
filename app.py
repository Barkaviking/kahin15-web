import streamlit as st
import pandas as pd

def fetch_race_data(race_number):
    return pd.DataFrame([
        {"At": "SPECIAL MAN", "No": 6, "Puan": 91, "Odds%": 36.4},
        {"At": "AMAZING TOUCH", "No": 2, "Puan": 88, "Odds%": 29.7},
        {"At": "DAPPER MAN", "No": 4, "Puan": 84, "Odds%": 21.1},
    ])

st.set_page_config(page_title="Kâhin 15 Mobil Analiz", layout="mobile")
st.title("🧠 Kâhin 15 Mobil Analiz")

race = st.selectbox("Yarış Numarası", list(range(1,10)), index=0)
if st.button("Analiz Et"):
    df = fetch_race_data(race)
    st.markdown(f"## İstanbul {race}. Koşu – İlk 3 At")
    st.table(df[["At","No","Puan","Odds%"]])
    st.caption("Veriler ‘Kâhin 15’ kriterlerine göre analiz edilmiştir.")
