import json
import os
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

# Partyflock Agenda
TARGET_URL = "https://partyflock.nl/agenda"

# We gebruiken Google Translate als web proxy om Cloudflare IP blocks te omzeilen
PROXY_URL = f"https://translate.google.com/website?sl=auto&tl=en&u={TARGET_URL}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8"
}

def fetch_partyflock_events():
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    events = []

    print(f"Ophalen van Partyflock via Google Proxy Interface...")
    try:
        response = requests.get(PROXY_URL, headers=HEADERS, timeout=30)
        print(f"HTTP Status: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            print(f"Paginatitel: {soup.title.string if soup.title else 'Geen'}")

            # Zoek alle links naar feesten
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                
                # Check op party links in de html
                if "/party/" in href or "partyflock.nl/party" in href:
                    title = a_tag.get_text(strip=True)
                    
                    # Schoon de titel en URL op van Google Translate wrappers
                    clean_url = re.sub(r'.*?u=(https?://[^&]+).*', r'\1', href)
                    if not clean_url.startswith("http"):
                        # Herstel Partyflock URL als Google relatieve links heeft gemaakt
                        clean_url = f"https://partyflock.nl{clean_url}"

                    if title and len(title) > 2 and title.lower() not in ["feesten", "party", "meer", "agenda", "translate"]:
                        parent = a_tag.find_parent(["tr", "li", "div", "article", "td"])
                        info_text = parent.get_text(" | ", strip=True) if parent else title

                        events.append({
                            "title": title,
                            "url": clean_url,
                            "info": info_text
                        })

    except Exception as e:
        print(f"Fout tijdens scrapen: {e}")

    # Fallback op directe RSS via Google Feed API als de eerste methode 0 resultaten geeft
    if not events:
        print("Proberen via Google Feed Proxy...")
        try:
            feed_proxy = "https://api.rss2json.com/v1/api.json?rss_url=https%3A%2F%2Fpartyflock.nl%2Frss%2Fagenda"
            res = requests.get(feed_proxy, timeout=15)
            if res.status_code == 200:
                feed_data = res.json()
                for item in feed_data.get("items", []):
                    events.append({
                        "title": item.get("title"),
                        "url": item.get("link"),
                        "info": item.get("description", "")
                    })
        except Exception as e:
            print(f"Fout bij RSS proxy: {e}")

    unique_events = list({ev['url']: ev for ev in events if ev.get('url')}.values())
    print(f"Totaal aantal unieke feesten gevonden: {len(unique_events)}")

    os.makedirs("data", exist_ok=True)
    output_file = f"data/partyflock_events_{today_date}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_events, f, ensure_ascii=False, indent=2)

    print(f"Opgeslagen in {output_file}")

if __name__ == "__main__":
    fetch_partyflock_events()
