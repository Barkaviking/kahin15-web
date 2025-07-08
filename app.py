import requests
from bs4 import BeautifulSoup
from datetime import datetime

url = "https://www.sihirlikantarma.org/2025/07/08-temmuz-nalkapon-ankara-at-yarisi.html"
headers = {"User-Agent": "Mozilla/5.0"}

yerli_sehirler = ["İstanbul", "İzmir", "Ankara", "Bursa", "Adana", "Elazığ", "Kocaeli"]
bugun = datetime.now().strftime("%d %B")

resp = requests.get(url, headers=headers)
soup = BeautifulSoup(resp.text, "html.parser")

print("📌 Bugünkü Yerli Yarış Bültenleri:\n")
for h3 in soup.find_all("h3", class_="post-title"):
    a_tag = h3.find("a")
    if not a_tag:
        continue
    title = a_tag.get_text(strip=True)
    link = a_tag["href"]
    
    if bugun in title:
        for sehir in yerli_sehirler:
            if sehir in title:
                print(f"✅ {sehir} → {title}")
                print(f"🔗 Link: {link}\n")