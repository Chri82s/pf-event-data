import json
import os
import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from curl_cffi import requests

# Partyflock agenda URL
URL = "https://partyflock.nl/agenda"

def fetch_partyflock_events():
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    events = []

    print(f"Ophalen van {URL} via curl_cffi Chrome impersonation...")
    try:
        # impersonate="chrome124" zorgt voor de exacte TLS/JA3 fingerprint van Chrome
        response = requests.get(
            URL,
            impersonate="chrome124",
            headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "accept-language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
                "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Windows"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "upgrade-insecure-requests": "1"
            },
            timeout=30
        )
        
        print(f"HTTP Status: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            print(f"Paginatitel: {soup.title.string if soup.title else 'Geen titel'}")

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if "/party/" in href or "/party?" in href:
                    title = a_tag.get_text(strip=True)
                    if title and len(title) > 2 and title.lower() not in ["feesten", "party", "meer", "agenda"]:
                        full_url = href if href.startswith("http") else f"https://partyflock.nl{href}"
                        parent = a_tag.find_parent(["tr", "li", "div", "article", "td"])
                        info_text = parent.get_text(" | ", strip=True) if parent else title

                        events.append({
                            "title": title,
                            "url": full_url,
                            "info": info_text
                        })

    except Exception as e:
        print(f"Fout tijdens het scrapen: {e}")

    unique_events = list({ev['url']: ev for ev in events}.values())
    print(f"Totaal aantal unieke feesten gevonden: {len(unique_events)}")

    os.makedirs("data", exist_ok=True)
    output_file = f"data/partyflock_events_{today_date}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_events, f, ensure_ascii=False, indent=2)

    print(f"Opgeslagen in {output_file}")

if __name__ == "__main__":
    fetch_partyflock_events()
