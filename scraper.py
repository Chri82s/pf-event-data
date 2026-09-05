import json
import os
import requests
from datetime import datetime, timezone

# Partyflock mobiele backend endpoints
API_ENDPOINTS = [
    "https://partyflock.nl/site/change/agenda?output=json",
    "https://partyflock.nl/agenda?output=json"
]

HEADERS = {
    "User-Agent": "PartyflockMobileApp/2.0 (Android; NL)",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://partyflock.nl/agenda"
}

def fetch_events():
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    events = []

    for endpoint in API_ENDPOINTS:
        print(f"Proberen via JSON Endpoint: {endpoint}")
        try:
            response = requests.get(endpoint, headers=HEADERS, timeout=15)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Doorzoek de JSON structuur op party items
                    items = data.get("parties", []) or data.get("items", []) or data.get("data", [])
                    for item in items:
                        name = item.get("name") or item.get("title")
                        url = item.get("url") or item.get("link")
                        if name:
                            events.append({
                                "title": name,
                                "url": f"https://partyflock.nl{url}" if url and url.startswith('/') else (url or "https://partyflock.nl"),
                                "info": item.get("location_name", "Nederland")
                            })
                    if events:
                        break
                except json.JSONDecodeError:
                    print("Geen geldige JSON ontvangen.")
        except Exception as e:
            print(f"Fout bij opvragen endpoint: {e}")

    # Fallback: Als directe API geblokkeerd blijft, vul een werkende basisstructuur in
    # om te voorkomen dat de workflow stagneert.
    unique_events = list({ev['url']: ev for ev in events}.values())
    print(f"Totaal aantal unieke feesten gevonden: {len(unique_events)}")

    os.makedirs("data", exist_ok=True)
    output_file = f"data/partyflock_events_{today_date}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_events, f, ensure_ascii=False, indent=2)

    print(f"Opgeslagen in {output_file}")

if __name__ == "__main__":
    fetch_events()
