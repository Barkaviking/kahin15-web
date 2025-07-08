import streamlit as st
import pandas as pd
from datetime import date
from scraper import fetch_daily_program

st.set_page_config(page_title="Günlük Yarış Programı", layout="wide")
st.title("Günlük Yarış Programı")

tarih = st.sidebar.date_input("Tarih Seçin", value=date.today())

with st.spinner("Veriler çekiliyor..."):
    program = fetch_daily_program(tarih)

if program:
    df = pd.DataFrame(program)
    st.table(df)
else:
    st.warning("Seçilen tarih için program bulunamadı.")