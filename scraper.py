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
        # Start Chromium in headless modus met realistischer browserprofiel
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="nl-NL"
        )
        page = context.new_page()

        print(f"Navigeren naar {URL}...")
        try:
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            # Wacht kort tot eventuele Cloudflare-checks voorbij zijn
            page.wait_for_timeout(5000)
            
            # Print de titel van de geladen pagina ter controle
            print(f"Paginatitel: {page.title()}")
            
            html_content = page.content()
        except Exception as e:
            print(f"Fout bij laden van pagina: {e}")
            html_content = ""
        finally:
            browser.close()

    if html_content:
        soup = BeautifulSoup(html_content, "html.parser")

        # Doorzoek alle hyperlinks
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            
            # Partyflock gebruikt links zoals /party/12345:naam of party/12345
            if re.search(r'/party/|/party\?', href) or "partyflock.nl/party/" in href:
                title = a_tag.get_text(strip=True)
                
                # Filter korte menulinks uit
                if title and len(title) > 2 and title.lower() not in ["feesten", "party", "meer", "agenda", "overzicht"]:
                    full_url = href if href.startswith("http") else f"https://partyflock.nl{href}"
                    
                    # Haal de ouder-rij of div op om de locatie/datum mee te pakken
                    parent = a_tag.find_parent(["tr", "li", "div", "article", "td"])
                    info_text = parent.get_text(" | ", strip=True) if parent else title

                    events.append({
                        "title": title,
                        "url": full_url,
                        "info": info_text
                    })

    # Ontdubbelen
    unique_events = list({ev['url']: ev for ev in events}.values())
    print(f"Totaal aantal unieke feesten gevonden: {len(unique_events)}")

    os.makedirs("data", exist_ok=True)
    output_file = f"data/partyflock_events_{today_date}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_events, f, ensure_ascii=False, indent=2)

    print(f"Opgeslagen in {output_file}")

if __name__ == "__main__":
    fetch_partyflock_events()
