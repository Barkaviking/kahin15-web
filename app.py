import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# 1. Sayfa İndirme
def fetch_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")

# 2. Yarış Programı (Bugünün koşuları)
def parse_program(soup):
    data = []
    # Örnek: "At Yarışı Programı" başlıklı bölümü seç
    section = soup.find("h3", string=lambda t: "Program" in t)
    if section:
        table = section.find_next("table")
        for row in table.find_all("tr")[1:]:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            data.append(cols)
    return pd.DataFrame(data, columns=["Koşu No", "Saat", "Pist", "Koşu Şartları"])

# 3. Galop Verileri
def parse_galops(soup):
    records = []
    tabs = soup.find_all("h3", string=lambda t: "Galop" in t)
    for tab in tabs:
        race = tab.get_text(strip=True)
        tbl = tab.find_next("table")
        for r in tbl.find_all("tr")[1:]:
            cols = [td.get_text(strip=True) for td in r.find_all("td")]
            records.append([race] + cols)
    return pd.DataFrame(records, columns=["Yarış", "At", "Sprint", "Tarih", "Not"])

# 4. Performans Verileri
def parse_performance(soup):
    perf = []
    divs = soup.select("div.post-body p")
    for p in divs:
        if "Performans" in p.get_text():
            parts = p.get_text().split(":")
            perf.append([parts[0].strip(), parts[1].strip()])
    return pd.DataFrame(perf, columns=["At/Koşu", "Performans"])

# 5. Geçmiş Sonuçlar
def parse_results(soup):
    results = []
    sections = soup.find_all("h3", string=lambda t: "Sonuç" in t)
    for sec in sections:
        race = sec.get_text(strip=True)
        tbl = sec.find_next("table")
        for row in tbl.find_all("tr")[1:]:
            cols = [td.get_text(strip=True) for td in row.find_all("td")]
            results.append([race] + cols)
    return pd.DataFrame(results, columns=["Yarış", "Sıra", "At", "Jokey", "Zaman"])

# 6. At Sahipleri ve Antrenörler
def parse_connections(soup):
    conn = []
    items = soup.select("ul.connections li")
    for li in items:
        text = li.get_text(separator="|", strip=True).split("|")
        conn.append(text)
    return pd.DataFrame(conn, columns=["At", "Sahip", "Antrenör"])

# 7. Sprint Bilgileri
def parse_sprints(soup):
    sprints = []
    spans = soup.select("span.sprint-info")
    for sp in spans:
        info = sp.get_text(strip=True)
        race = sp.find_parent("h3").get_text(strip=True)
        sprints.append([race, info])
    return pd.DataFrame(sprints, columns=["Yarış", "Sprint"])

# 8. Ana Akış
def main():
    url = "https://www.sihirlikantarma.org/?m=1"
    soup = fetch_page(url)
    
    df_prog = parse_program(soup)
    df_galop = parse_galops(soup)
    df_perf = parse_performance(soup)
    df_res  = parse_results(soup)
    df_conn = parse_connections(soup)
    df_sprint = parse_sprints(soup)
    
    # Sonuçları ekrana bas veya CSV’ye yaz
    print("— Yarış Programı —")
    print(df_prog)
    print("\n— Galop Verileri —")
    print(df_galop)
    
    # İsteğe bağlı: CSV
    df_prog.to_csv("program.csv", index=False)
    df_galop.to_csv("galop.csv", index=False)
    df_perf.to_csv("performance.csv", index=False)
    df_res.to_csv("results.csv", index=False)
    df_conn.to_csv("connections.csv", index=False)
    df_sprint.to_csv("sprints.csv", index=False)

if __name__ == "__main__":
    main()