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