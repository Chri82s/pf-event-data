import json
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

URL = "https://partyflock.nl/agenda"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7"
}

def fetch_partyflock_events():
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    response = requests.get(URL, headers=HEADERS)
    
    print(f"HTTP Status: {response.status_code}")
    if response.status_code != 200:
        raise Exception(f"Kon Partyflock niet bereiken, statuscode: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")
    events = []

    for link in soup.find_all("a", href=True):
        href = link['href']
        if re.search(r'/party/\d+:', href):
            title = link.get_text(strip=True)
            if title and len(title) > 2:
                parent = link.find_parent(["td", "tr", "div", "li"])
                context_text = parent.get_text(" | ", strip=True) if parent else title

                events.append({
                    "title": title,
                    "url": f"https://partyflock.nl{href}" if href.startswith('/') else href,
                    "info": context_text
                })

    unique_events = list({ev['url']: ev for ev in events}.values())

    print(f"Aantal feesten gevonden op Partyflock: {len(unique_events)}")

    os.makedirs("data", exist_ok=True)
    output_file = f"data/partyflock_events_{today_date}.json"
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_events, f, ensure_ascii=False, indent=2)

    print(f"Succesvol opgeslagen in {output_file}")

if __name__ == "__main__":
    fetch_partyflock_events()
