import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import date

st.set_page_config(page_title="Kâhin15 – Bülten", layout="wide")
st.title("🏇 Günlük At Yarışı Bülteni")

# — Helper: “güvenli fetch” decorator
def safe_fetch(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            return pd.DataFrame()
    return wrapper

# 1) AltılıGanyan – Ana Bülten
@safe_fetch
def fetch_ag_bulten():
    url = ("https://www.altiliganyan.com/"
           "tjk/at-yarisi-bulteni?bt=18&dt=1&ln=1&rt=1-2-3-4-5-6")
    resp = requests.get(url, timeout=10); resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    out = []
    for tbl in soup.find_all("table"):
        # başlıktan hipodrom & koşu no
        tit = tbl.find_previous(string=re.compile(r".+?\d+\.Koşu"))
        m = re.search(r"(.+?)\s+(\d+)\.Koşu", tit or "")
        hip, kosu = (m.group(1), m.group(2)) if m else (None, None)

        heads = [th.get_text(strip=True) for th in tbl.find_all("th")]
        cols = [h.lower().replace(" ","_") for h in heads]
        rows = []
        for tr in tbl.find_all("tr")[1:]:
            vals = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if len(vals)==len(cols):
                rows.append(vals)
        if not rows: continue

        df = pd.DataFrame(rows, columns=cols)
        df["hipodrom"], df["kosu_no"] = hip, kosu
        # normalize önemli alanlar
        ren = {}
        for c in df.columns:
            if "orijin" in c:  ren[c]="orijin"
            if "sahip" in c:   ren[c]="sahip"
            if "jokey" in c:   ren[c]="jokey"
            if "antren" in c:  ren[c]="antrenor"
            if "idman" in c:   ren[c]="idman"
            if "derece" in c:  ren[c]="sinif_seviyesi"
            if "son_3" in c:   ren[c]="son_3_yaris"
            if "agf" in c:     ren[c]="agf"
        df.rename(columns=ren, inplace=True)
        out.append(df)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()

# 2) Sporx
@safe_fetch
def fetch_sporx():
    url = "https://m.sporx.com/at-yarisi"
    r = requests.get(url, timeout=8); r.raise_for_status()
    doc = BeautifulSoup(r.text, "html.parser")
    rows=[]
    for sec in doc.select("section.race"):
        track = sec.select_one(".hipodrom").get_text(strip=True)
        no    = sec.select_one(".race-no").get_text(strip=True).replace("Koşu","")
        time  = sec.select_one(".time").get_text(strip=True)
        for li in sec.select("ul.horse-list li"):
            rows.append({
                "hipodrom": track,
                "kosu_no": no,
                "saat": time,
                "horse": li.select_one(".name").get_text(strip=True),
                "agf_sporx": li.select_one(".agf").get_text(strip=True)
            })
    return pd.DataFrame(rows)

# 3) BiTalih
@safe_fetch
def fetch_bitalih():
    url="https://www.bitalih.com/at-yarisi"
    r=requests.get(url, timeout=8); r.raise_for_status()
    dom=BeautifulSoup(r.text,"html.parser")
    rows=[]
    for tr in dom.select("table.program tr")[1:]:
        td=tr.find_all("td")
        rows.append({
            "hipodrom": td[0].get_text(strip=True),
            "kosu_no": td[1].get_text(strip=True),
            "horse": td[2].get_text(strip=True)
        })
    return pd.DataFrame(rows)

# 4) Hipodrom.com
@safe_fetch
def fetch_hipo():
    url="https://www.hipodrom.com"
    r=requests.get(url, timeout=8); r.raise_for_status()
    doc=BeautifulSoup(r.text,"html.parser")
    rows=[]
    for card in doc.select(".race-card"):
        trk=card.select_one(".race-track").get_text(strip=True)
        no =card.select_one(".race-number").get_text(strip=True)
        tm =card.select_one(".race-time").get_text(strip=True)
        for li in card.select(".horses li"):
            rows.append({
                "hipodrom": trk,
                "kosu_no": no,
                "saat": tm,
                "horse": li.get_text(strip=True)
            })
    return pd.DataFrame(rows)

# Derleme & Merge
def compile_all():
    a = fetch_ag_bulten()
    s = fetch_sporx()
    b = fetch_bitalih()
    h = fetch_hipo()

    if a.empty:
        return pd.DataFrame()  

    df=a.copy()
    for src in (s,b,h):
        df = pd.merge(df, src, on=["hipodrom","kosu_no","horse"], how="left")

    return df

if st.button("Bülteni Derle"):
    df = compile_all()
    if df.empty:
        st.error("Bülten alınamadı.")
    else:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 CSV İndir", csv, file_name=f"bulten_{date.today()}.csv")