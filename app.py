import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Galop verisini çeken fonksiyon
def fetch_galop_data(race_number):
    try:
        url = f"https://liderform.com.tr/program/galop/2025-07-06/ISTANBUL/{race_number}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        data = []
        at_bloklari = soup.find_all("div", class_="col-12")

        for blok in at_bloklari:
            at_adi_tag = blok.find("h4")
            if not at_adi_tag:
                continue
            at_adi = at_adi_tag.text.strip()

            tablo = blok.find("table")
            if not tablo:
                continue

            satirlar = tablo.find_all("tr")[1:4]  # Son 3 galop
            for satir in satirlar:
                hucreler = satir.find_all("td")
                if len(hucreler) >= 6:
                    derece = hucreler[0].text.strip()
                    mesafe = hucreler[1].text.strip()
                    pist = hucreler[2].text.strip()
                    ic_dis = hucreler[3].text.strip()
                    jokey = hucreler[4].text.strip()
                    tarih = hucreler[5].text.strip()

                    data.append({
                        "At": at_adi,
                        "Tarih": tarih,
                        "Mesafe": mesafe,
                        "Derece": derece,
                        "Pist": pist,
                        "İç/Dış": ic_dis,
                        "Jokey": jokey
                    })

        return pd.DataFrame(data)

    except Exception as e:
        return pd.DataFrame([{"Hata": f"Galop verisi çekilemedi: {e}"}])

# Streamlit arayüzü
st.set_page_config(page_title="Kâhin 15 - Galop Analizi", layout="wide")
st.title("📊 Kâhin 15 - İstanbul Galop Analizi")

race_number = st.selectbox("🏇 Koşu Numarası Seç", list(range(1, 10)))

if st.button("Galop Verilerini Göster"):
    df = fetch_galop_data(race_number)
    if df.empty:
        st.warning("Veri bulunamadı veya sayfa yapısı değişmiş olabilir.")
    else:
        st.success(f"{race_number}. koşu için galop verileri yüklendi.")
        st.dataframe(df, use_container_width=True)