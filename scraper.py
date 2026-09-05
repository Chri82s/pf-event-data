import json
import os
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup

# Appic / Partyflock API endpoint voor evenementen in NL
API_URL = "https://appic.events/api/v2/events?country=NL&limit=100"
RSS_URL = "https://partyflock.nl/rss/agenda"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

def fetch_events_from_api():
    print("Ophalen via Partyflock Partner API...")
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=15)
        print(f"API HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            events_data = data.get("data", []) or data.get("events", [])
            
            events = []
            for item in events_data:
                title = item.get("name") or item.get("title")
                url = item.get("url") or f"https://partyflock.nl/party/{item.get('id')}"
                location = item.get("location", {}).get("name", "Nederland") if isinstance(item.get("location"), dict) else "Nederland"
                date_str = item.get("start_date") or item.get("date", "")

                if title:
                    events.append({
                        "title": title,
                        "url": url,
                        "info": f"{date_str} | {location}"
                    })
            return events
    except Exception as e:
        print(f"Fout bij API: {e}")
    return []

def fetch_events_from_rss():
    print("Ophalen via RSS Feed Fallback...")
    try:
        response = requests.get(RSS_URL, headers=HEADERS, timeout=15)
        print(f"RSS HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "xml")
            events = []
            for item in soup.find_all("item"):
                title = item.title.get_text(strip=True) if item.title else ""
                link = item.link.get_text(strip=True) if item.link else ""
                desc = item.description.get_text(strip=True) if item.description else ""

                if title:
                    events.append({
                        "title": title,
                        "url": link,
                        "info": desc
                    })
            return events
    except Exception as e:
        print(f"Fout bij RSS: {e}")
    return []

def main():
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    # 1. Probeer API
    events = fetch_events_from_api()

    # 2. Fallback op RSS als API geen resultaat geeft
    if not events:
        events = fetch_events_from_rss()

    # Ontdubbelen op basis van URL
    unique_events = list({ev['url']: ev for ev in events}.values())
    print(f"Totaal aantal unieke feesten gevonden: {len(unique_events)}")

    os.makedirs("data", exist_ok=True)
    output_file = f"data/partyflock_events_{today_date}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_events, f, ensure_ascii=False, indent=2)

    print(f"Opgeslagen in {output_file}")

if __name__ == "__main__":
    main()
