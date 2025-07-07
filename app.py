# app.py

import streamlit as st
import pandas as pd
import requests
import io
from datetime import date

def fetch_tjk_csv_program(tarih):
    # GG/AA/YYYY formatı
    gun  = f"{tarih.day:02d}"
    ay   = f"{tarih.month:02d}"
    yil  = f"{tarih.year}"
    formatted = f"{gun}/{ay}/{yil}"
    url = (
        "https://www.tjk.org/TR/YarisSever/Info/Download/File/"
        f"GunlukYarisProgramiCSV?date={formatted}"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/csv,application/octet-stream;q=0.9,*/*;q=0.8",
        "Referer": "https://www.tjk.org/"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            st.error(f"CSV indirme hatası: HTTP {resp.status_code}")
            return pd.DataFrame()
        # Byte içeriği StringIO'ya alıp Pandas ile oku
        text_io = io.StringIO(resp.content.decode("ISO-8859-9"))
        df = pd.read_csv(text_io, sep=";")
        return df

    except Exception as e:
        st.error(f"CSV verisi alınamadı: {e}")
        return pd.DataFrame()


# Streamlit UI
st.set_page_config(page_title="Kâhin 15 – CSV Program", layout="wide")
st.title("🏇 Kâhin 15 – TJK Günlük Program (CSV)")

tarih = st.date_input("Tarih", value=date.today())

if st.button("Programı Getir"):
    df = fetch_tjk_csv_program(tarih)
    if df.empty:
        st.warning("Veri alınamadı. TJK IP engeli veya format değişikliği olabilir.")
    else:
        st.success(f"{tarih.strftime('%d/%m/%Y')} tarihli program yüklendi.")
        st.dataframe(df, use_container_width=True)

