import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from datetime import date

# 1) ALTILIGANYAN – Günün Tüm Ayaklarıyla “Bülten”
def fetch_altiliganyan_bulteni():
    url = ("https://www.altiliganyan.com/"
           "tjk/at-yarisi-bulteni?bt=18&dt=1&ln=1&rt=1-2-3-4-5-6")
    r = requests.get(url, timeout=10); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    out = []
    for tbl in soup.find_all("table"):
        # find hipodrom & koşu no from the preceding header
        title = tbl.find_previous(string=re.compile(r".+?\d+\.Koşu"))
        hip, kosu = None, None
        if title:
            m = re.search(r"(.+?)\s+(\d+)\.Koşu", title)
            hip, kosu = m.group(1).strip(), m.group(2).strip()

        # headers → snake_case
        headers = [th.get_text(strip=True) for th in tbl.find_all("th")]
        cols = [h.lower().replace(" ","_") for h in headers]

        # rows
        rows = []
        for tr in tbl.find_all("tr")[1:]:
            vals = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
            if len(vals)==len(cols):
                rows.append(vals)
        if not rows:
            continue

        df = pd.DataFrame(rows, columns=cols)
        df["hipodrom"], df["kosu_no"] = hip, kosu

        # normalize key fields
        rename_map = {}
        for c in df.columns:
            if "orijin" in c:      rename_map[c] = "orijin"
            if "sahip" in c:       rename_map[c] = "sahip"
            if "jokey" in c:       rename_map[c] = "jokey"
            if "antren" in c:      rename_map[c] = "antrenor"
            if "idman" in c:       rename_map[c] = "idman"
            if "derece" in c:      rename_map[c] = "sinif_seviyesi"
            if "son_3" in c:       rename_map[c] = "son_3_yaris"
            if "agf" in c:         rename_map[c] = "agf_raw"
            if "hp" == c:          rename_map[c] = "hp"
            if "gp" == c:          rename_map[c] = "gp"
        df.rename(columns=rename_map, inplace=True)
        out.append(df)

    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


# 2) SPORX – Mobil At Yarışı Programı & AGF
def fetch_sporx_bulten():
    url = "https://m.sporx.com/at-yarisi"
    r = requests.get(url, timeout=10); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    # assume each race section
    for sec in soup.select("section.race"):
        hip = sec.select_one(".hipodrom").get_text(strip=True)
        kosu = sec.select_one(".race-no").get_text(strip=True).replace("Koşu","").strip()
        saat = sec.select_one(".time").get_text(strip=True)
        for li in sec.select("ul.horse-list li"):
            horse = li.select_one(".name").get_text(strip=True)
            agf    = li.select_one(".agf").get_text(strip=True)
            rows.append({
                "hipodrom": hip,
                "kosu_no": kosu,
                "saat": saat,
                "horse": horse,
                "agf_sporx": agf
            })
    return pd.DataFrame(rows)


# 3) BİTALİH – At Yarışı Program Tablosu
def fetch_bitalih_bulten():
    url = "https://www.bitalih.com/at-yarisi"
    r = requests.get(url, timeout=10); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    # assumes there's a <table class="program">
    for tr in soup.select("table.program tr")[1:]:
        cols = tr.find_all("td")
        hip    = cols[0].get_text(strip=True)
        kosu   = cols[1].get_text(strip=True)
        horse  = cols[2].get_text(strip=True)
        rows.append({
            "hipodrom": hip,
            "kosu_no": kosu,
            "horse": horse
        })
    return pd.DataFrame(rows)


# 4) HİPODROM.COM – Genel Koşu Kartları
def fetch_hipodrom_bulten():
    url = "https://www.hipodrom.com"
    r = requests.get(url, timeout=10); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for card in soup.select(".race-card"):
        hip  = card.select_one(".race-track").get_text(strip=True)
        kosu = card.select_one(".race-number").get_text(strip=True)
        saat= card.select_one(".race-time").get_text(strip=True)
        for li in card.select(".horses li"):
            horse = li.get_text(strip=True)
            rows.append({
                "hipodrom": hip,
                "kosu_no": kosu,
                "saat": saat,
                "horse": horse
            })
    return pd.DataFrame(rows)


# 5) LİDERFORM – Galop & GP/HP
def fetch_liderform_galop():
    url = "https://www.liderform.com.tr/program/galop-bulten"
    r = requests.get(url, timeout=10); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tbl = soup.find("table")
    if not tbl:
        return pd.DataFrame()
    cols = [th.get_text(strip=True).lower().replace(" ","_") for th in tbl.find_all("th")]
    rows = []
    for tr in tbl.find_all("tr")[1:]:
        vals = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(vals)==len(cols):
            rows.append(vals)
    df = pd.DataFrame(rows, columns=cols)
    if "no" in df.columns:
        df["kosu_no"] = df["no"]
    return df.rename(columns={"adi":"horse"})


# 6) BÜLTEN DERLEME & MERGE
def compile_bulten():
    a = fetch_altiliganyan_bulteni()
    s = fetch_sporx_bulten()
    b = fetch_bitalih_bulten()
    h = fetch_hipodrom_bulten()
    l = fetch_liderform_galop()

    # start from altılı-ganyan bülteni
    df = a.copy()

    # merge in order of priority
    for src in (s,b,h,l):
        df = pd.merge(
            df,
            src,
            on=["hipodrom","kosu_no","horse"],
            how="left",
            suffixes=("","_x")
        )

    # fill col list
    cols = [
        "hipodrom","kosu_no","horse",
        "orijin","sahip","jokey","antrenor",
        "idman","sinif_seviyesi","son_3_yaris",
        "agf_raw","agf_sporx","gp","hp","saat"
    ]
    return df[[c for c in cols if c in df.columns]]


# ───── Streamlit UI ─────
st.set_page_config(page_title="Kâhin15 – Çoklu Bülten", layout="wide")
st.title("🏇 Günlük At Yarışı Bülteni (5 Kaynak)")

if st.button("Bülteni Derle"):
    df = compile_bulten()
    if df.empty:
        st.error("Hiç kaynaktan veri çekilemedi.")
    else:
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 CSV İndir",
            data=csv,
            file_name=f"bulten_{date.today()}.csv",
            mime="text/csv"
        )