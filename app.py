import pandas as pd
import requests
from bs4 import BeautifulSoup

def fetch_istanbul_data(race_number):
    try:
        url = f"https://liderform.com.tr/program/2025-07-06/ISTANBUL/{race_number}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        rows = soup.find_all("tr")
        data = []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 10:
                try:
                    at_adi = cols[1].text.strip()
                    jokey = cols[5].text.strip()
                    agf_raw = cols[17].text.strip()
                    agf = agf_raw.split("%")[-1].split("(")[0].strip()
                    sprint = cols[15].text.strip()
                    data.append({
                        "At": at_adi,
                        "Jokey": jokey,
                        "AGF%": f"%{agf}",
                        "Sprint": sprint
                    })
                except:
                    continue

        return pd.DataFrame(data)

    except Exception as e:
        return pd.DataFrame([{"Hata": f"Veri çekilemedi: {e}"}])

import pandas as pd
import requests
from bs4 import BeautifulSoup

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