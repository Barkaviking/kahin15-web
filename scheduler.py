import schedule
import time
import json
from datetime import date
from scraper import fetch_daily_program

def job():
    today = date.today()
    data = fetch_daily_program(today)
    filename = f"program_{today.strftime('%Y%m%d')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"{today}: Veri kaydedildi -> {filename}")

schedule.every().day.at("06:00").do(job)

if __name__ == "__main__":
    print("Scheduler başlatıldı. Her gün 06:00'da çalışacak.")
    while True:
        schedule.run_pending()
        time.sleep(30)