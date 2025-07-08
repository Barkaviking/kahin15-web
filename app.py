import requests
from bs4 import BeautifulSoup
from datetime import date

def fetch_daily_program(race_date: date):
    """
    Verilen tarihe ait yarış programını hipodromx.com’dan çeker.
    """
    date_str = race_date.strftime("%d.%m.%Y")
    url = f"https://hipodromx.com/program.aspx?Tarih={date_str}"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    if not table:
        return []

    rows = table.find_all("tr")[1:]
    program = []
    for tr in rows:
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cols) < 7:
            continue
        program.append({
            "Saat":        cols[0],
            "Koşu No":     cols[1],
            "At Türü":     cols[2],
            "Şart":        cols[3],
            "Mesafe":      cols[4],
            "İkramiye":    cols[5],
            "Pist":        cols[6],
        })
    return program

if __name__ == "__main__":
    from datetime import date
    data = fetch_daily_program(date.today())
    for item in data:
        print(item)