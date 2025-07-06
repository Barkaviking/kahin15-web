import streamlit as st
import pandas as pd
from datetime import date

def fetch_tjk_csv_program(tarih):
    # GG/AA/YYYY → URL formatı
    gun = f"{tarih.day:02d}"
    ay = f"{tarih.month:02d}"
    yil = f"{tarih.year}"
    formatted = f"{gun}/{ay}/{yil}"
    url = f"https://www.tjk.org/TR/YarisSever/Info/Download/File/GunlukYarisProgramiCSV?date={formatted}"
    try:
        df = pd.read_csv(url, sep=";", encoding="ISO-8859-9")
        return df
    except Exception as e:
        st.error(f"CSV verisi alınamadı: {e}")
        return pd.DataFrame()

# Streamlit Arayüzü
st.set_page_config(page_title="Kâhin 15 – CSV Program", layout="wide")
st.title("🏇 Kâhin 15 – TJK Günlük Program (CSV)")

tarih = st.date_input("Tarih", value=date.today())

if st.button("Programı Getir"):
    df = fetch_tjk_csv_program(tarih)
    if df.empty:
        st.warning("Veri alınamadı. TJK sayfasında o tarihe ait CSV olmayabilir.")
    else:
        st.success(f"{tarih.strftime('%d/%m/%Y')} tarihli program yüklendi.")
        st.dataframe(df, use_container_width=True)