import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Kâhin 15 – At İsimleri", layout="wide")
st.title("🏇 Kâhin 15 – Program Sekmesi")

date_str = date.today().strftime("%Y-%m-%d")
track    = "ISTANBUL"
race_no   = st.selectbox("Koşu Numarası", list(range(1, 13)))

url = f"https://liderform.com.tr/program/{date_str}/{track}/{race_no}"

try:
    df = pd.read_html(url)[0]
except:
    df = pd.DataFrame()

if df.empty:
    st.error("Veri bulunamadı.")
else:
    cols = [c for c in df.columns if "at" in c.lower() or "horse" in c.lower()]
    if cols:
        st.dataframe(df[cols], use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)