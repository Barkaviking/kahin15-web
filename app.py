import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date
import io

# 1) TJK Günlük Programı (CSV)
def fetch_tjk_program(tarih):
    fmt = tarih.strftime("%d/%m/%Y")
    url = f"https://www.tjk.org/TR/YarisSever/Info/Download/File/GunlukYarisProgramiCSV?date={fmt}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.content.decode("ISO-8859-9")), sep=";")
    df.columns = [c.strip() for c in df.columns]
    return df

# 2) Yenibeygir – Ön Yarış Bülteni
def fetch_yenibeygir_bulten():
    url = "https://yenibeygir.com/"
    r = requests.get(url, timeout=10); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tbl = soup.find("table")
    raw = [th.get_text(strip=True) for th in tbl.find_all("th")]
    seen, cols = {}, []
    for h in raw:
        key = h or "Unnamed"
        seen[key] = seen.get(key, 0) + 1
        suffix = f"_{seen[key]}" if seen[key] > 1 else ""
        cols.append(key + suffix)
    rows = []
    for tr in tbl.find_all("tr")[1:]:
        vals = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(vals)==len(cols): rows.append(vals)
    return pd.DataFrame(rows, columns=cols)

# 3) LiderForm – Galop Bülteni
def fetch_liderform_galop():
    url = "https://liderform.com.tr/program/galop-bulten"
    r = requests.get(url, timeout=10); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tbl = soup.find("table")
    if tbl is None: return pd.DataFrame()
    cols = [th.get_text(strip=True) for th in tbl.find_all("th")]
    rows = []
    for tr in tbl.find_all("tr")[1:]:
        vals = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(vals)==len(cols): rows.append(vals)
    return pd.DataFrame(rows, columns=cols)

# 4) Sonduzluk – Günün Koşu Programı & Altılı Ganyan Kuponları
def fetch_sonduzluk():
    url = "https://sonduzluk.com/"
    r = requests.get(url, timeout=10); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # Günün koşuları listesi
    items = soup.select("ul li")  # generic li, gerekirse selector'u değiştirin
    sched = []
    for li in items:
        txt = li.get_text(" ", strip=True)
        # örn: "Bursa Osmangazi Hipodromu 1. Koşu - 13:30"
        if "Koşu" in txt and "-" in txt:
            parts = txt.split(" - ")
            race = parts[0]; time = parts[1]
            hip, num = race.rsplit(" ", 1)
            sched.append({"Hipodrom": hip, "KoşuNo": num.replace("Koşu","").strip(), "Saat": time})
    df_sched = pd.DataFrame(sched)
    # Altılı ganyan kuponları
    # sayfada "6'lı GANYAN" içeren bölümler <div> ya da <pre> olabilir
    coupons = []
    for pre in soup.find_all("pre"):
        text = pre.get_text("\n", strip=True)
        if "6'LI GANYAN" in text:
            coupons.append(text)
    return df_sched, coupons

# 5) AltılıGanyan.com – Anlık Sonuçlar & Oranlar
def fetch_altiliganyan():
    url = "https://www.altiliganyan.com/tjk/at-yarisi-sonuclari"
    r = requests.get(url, timeout=10); r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    tbl = soup.find("table")
    if tbl is None: return pd.DataFrame()
    # sütunları temizle
    cols = [th.get_text(strip=True) for th in tbl.find_all("th")]
    rows = []
    for tr in tbl.find_all("tr")[1:]:
        vals = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(vals)==len(cols): rows.append(vals)
    return pd.DataFrame(rows, columns=cols)

# Streamlit UI
st.set_page_config(page_title="Tam Günlük Bülten", layout="wide")
st.title("🏇 Kâhin 15 – Tüm Kaynaklardan Günlük Bülten")

tarih = st.date_input("Tarih", value=date.today())

if st.button("Bülteni Derle"):

    prog = fetch_tjk_program(tarih)
    yb   = fetch_yenibeygir_bulten()
    gb   = fetch_liderform_galop()
    sd_sched, sd_coupons = fetch_sonduzluk()
    ag   = fetch_altiliganyan()

    st.subheader("► TJK Günlük Programı")
    st.dataframe(prog, use_container_width=True)

    st.subheader("► Yenibeygir Bülteni")
    st.dataframe(yb, use_container_width=True)

    st.subheader("► LiderForm Galop Bülteni")
    if gb.empty:
        st.warning("Galop bülteni bulunamadı.")
    else:
        st.dataframe(gb, use_container_width=True)

    st.subheader("► Sonduzluk – Gün