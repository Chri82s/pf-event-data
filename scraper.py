import json
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

# URL voor de agenda van Partyflock
URL = "https://partyflock.nl/agenda"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://partyflock.nl/"
}

def fetch_partyflock_events():
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    events = []

    try:
        session = requests.Session()
        response = session.get(URL, headers=HEADERS, timeout=15)
        print(f"HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Zoek alle links die verwijzen naar feesten (/party/ of /party/id:naam)
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if "/party/" in href or "/party?" in href:
                    title = a_tag.get_text(strip=True)
                    
                    # Negeer korte teksten zoals knoppen of paginanummers
                    if title and len(title) > 2 and title.lower() not in ["feesten", "party", "meer", "next"]:
                        full_url = f"https://partyflock.nl{href}" if href.startswith('/') else href
                        
                        # Haal omliggende tekst op voor locatie/datum informatie
                        parent = a_tag.find_parent(["td", "tr", "div", "li", "article"])
                        info_text = parent.get_text(" | ", strip=True) if parent else title

                        events.append({
                            "title": title,
                            "url": full_url,
                            "info": info_text
                        })

    except Exception as e:
        print(f"Fout tijdens het scrapen: {e}")

    # Ontdubbelen op basis van URL
    unique_events = list({ev['url']: ev for ev in events}.values())
    print(f"Totaal aantal unieke feesten gevonden: {len(unique_events)}")

    os.makedirs("data", exist_ok=True)
    output_file = f"data/partyflock_events_{today_date}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_events, f, ensure_ascii=False, indent=2)

    print(f"Opgeslagen in {output_file}")

if __name__ == "__main__":
    fetch_partyflock_events()
