import json
import os
import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

URL = "https://partyflock.nl/agenda"

def fetch_partyflock_events():
    today_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    events = []

    with sync_playwright() as p:
        # Start een echte headles browser om Cloudflare te omzeilen
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            locale="nl-NL"
        )
        page = context.new_page()

        print(f"Navigeren naar {URL}...")
        response = page.goto(URL, wait_until="networkidle", timeout=60000)
        
        status_code = response.status if response else 0
        print(f"HTTP Status: {status_code}")

        # Wacht tot de pagina of agenda-elementen zijn geladen
        page.wait_for_timeout(3000)
        html_content = page.content()
        browser.close()

    soup = BeautifulSoup(html_content, "html.parser")

    # Zoek alle links naar feesten
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if "/party/" in href:
            title = a_tag.get_text(strip=True)
            if title and len(title) > 2 and title.lower() not in ["feesten", "party", "meer"]:
                full_url = f"https://partyflock.nl{href}" if href.startswith('/') else href
                parent = a_tag.find_parent(["td", "tr", "div", "li", "article"])
                info_text = parent.get_text(" | ", strip=True) if parent else title

                events.append({
                    "title": title,
                    "url": full_url,
                    "info": info_text
                })

    unique_events = list({ev['url']: ev for ev in events}.values())
    print(f"Totaal aantal unieke feesten gevonden: {len(unique_events)}")

    os.makedirs("data", exist_ok=True)
    output_file = f"data/partyflock_events_{today_date}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_events, f, ensure_ascii=False, indent=2)

    print(f"Opgeslagen in {output_file}")

if __name__ == "__main__":
    fetch_partyflock_events()
