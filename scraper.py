import json
import os
import re
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup

# Partyflock Agenda URL
PARTYFLOCK_URL = "https://partyflock.nl/agenda"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

def fetch_via_jina():
    """Haalt de pagina op via Jina AI Reader (omzeilt Cloudflare IP-blocks)"""
    url = f"https://r.jina.ai/{PARTYFLOCK_URL}"
    print(f"Ophalen via Jina AI Reader ({url})...")
    events = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        print(f"Jina HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Zoek naar party links en titels uit de Jina markdown/text output
            # Partyflock URLs hebben het formaat /party/123456:Naam of https://partyflock.nl/party/...
            matches = re.findall(r'\[([^\]]+)\]\((https?://partyflock\.nl/party/[^\)]+|/party/[^\)]+)\)', content)
            
            for title, link in matches:
                title_clean = title.strip()
                if title_clean and len(title_clean) > 2 and title_clean.lower() not in ["feesten", "party", "meer", "agenda"]:
                    full_url = link if link.startswith("http") else f"https://partyflock.nl{link}"
                    events.append({
                        "title": title_clean,
                        "url": full_url,
                        "info": title_clean
                    })
                    
            # Als regex niks vond in Markdown, probeer algemene link matching
            if not events:
                for line in content.split("\n"):
                    if "/party/" in line:
                        parts = line.split("http")
                        if len(parts) > 1:
                            party_url = "http" + parts[1].split()[0].rstrip(")")
                            events.append({
                                "title": "Partyflock Event",
                                "url": party_url,
                                "info": line.strip()
                            })
    except Exception as e:
        print(f"Fout bij Jina AI: {e}")
    return events

def fetch_via_allorigins():
    """Fallback via AllOrigins CORS Proxy"""
    url = f"https://api.allorigins.win/get?url={requests.utils.quote(PARTYFLOCK_URL)}"
    print("Ophalen via AllOrigins Proxy Fallback...")
    events = []
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        print(f"AllOrigins HTTP Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            html_content = data.get("contents", "")
            if html_content:
                soup = BeautifulSoup(html_content, "html.parser")
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    if "/party/" in href:
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
        print(f"Fout bij AllOrigins: {e}")
    return events

def main():
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    # 1. Probeer Jina AI Reader
    events = fetch_via_jina()

    # 2. Fallback op AllOrigins
    if not events:
        events = fetch_via_allorigins()

    # Ontdubbelen op basis van URL
    unique_events = list({ev['url']: ev for ev in events if ev.get('url')}.values())
    print(f"Totaal aantal unieke feesten gevonden: {len(unique_events)}")

    os.makedirs("data", exist_ok=True)
    output_file = f"data/partyflock_events_{today_date}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_events, f, ensure_ascii=False, indent=2)

    print(f"Opgeslagen in {output_file}")

if __name__ == "__main__":
    main()
