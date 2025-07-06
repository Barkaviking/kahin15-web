import streamlit as st
import pandas as pd
import requests
from datetime import date

st.set_page_config(page_title="Kâhin 15 – At İsimleri", layout="wide")
st.title("🏇 Kâhin 15 – Program Sekmesi")

# Bugünün tarihi
date_str = date.today().strftime("%Y-%m-%d")
track    = "ISTANBUL"
race_no   = st.selectbox("Koşu Numarası", list(range(1, 13)))

# Oluşan URL
url = f"https://liderform.com.tr/program/{date_str}/{track}/{race_no}"
st.markdown(f"**URL:** `{url}`")

# İsteği yap ve pandas ile tabloyu al
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}
try:
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    tables = pd.read_html(resp.text)
    df = tables[0] if tables else pd.DataFrame()
except Exception:
    df = pd.DataFrame()

# At isimlerini çıkar ve göster
if df.empty:
    st.error("Veri bulunamadı. URL, tarih veya site yapısı değişmiş olabilir.")
else:
    cols = [c for c in df.columns if "at" in c.lower() or "horse" in c.lower()]
    st.dataframe(df[cols] if cols else df, use_container_width=True)