import json
import os
import re
from datetime import datetime, timezone
import cloudscraper
from bs4 import BeautifulSoup

URL = "https://partyflock.nl/agenda"

def fetch_partyflock_events():
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    events = []

    # Maak een cloudscraper instance aan om Cloudflare Turnstile/403 te omzeilen
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    print(f"Ophalen van {URL} via cloudscraper...")
    try:
        response = scraper.get(URL, timeout=30)
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            print(f"Paginatitel: {soup.title.string if soup.title else 'Geen titel'}")

            # Zoek naar alle links die verwijzen naar feesten
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
