import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"

def scrape_sebi():
    response = requests.get(URL, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.select("table tr")  # we'll refine this selector once we see real output
    circulars = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            date = cells[0].get_text(strip=True)
            title_cell = cells[1]
            title = title_cell.get_text(strip=True)
            link_tag = title_cell.find("a")
            link = link_tag["href"] if link_tag else None
            if link and not link.startswith("http"):
                link = "https://www.sebi.gov.in" + link
            circulars.append({"date": date, "title": title, "link": link})

    return circulars

if __name__ == "__main__":
    results = scrape_sebi()
    print(f"Found {len(results)} rows")

    # ensure a 'SEBI' source row exists
    existing = supabase.table("sources").select("id").eq("name", "SEBI").execute()
    if existing.data:
        source_id = existing.data[0]["id"]
    else:
        inserted = supabase.table("sources").insert({
            "name": "SEBI",
            "base_url": URL,
            "category_focus": "cybersecurity_resilience"
        }).execute()
        source_id = inserted.data[0]["id"]
  
    from scrapers.circular_fetcher import fetch_circular_text, get_hash
    
    for c in results:
        try:
            content_text = fetch_circular_text(c["link"])
            content_hash = get_hash(content_text)
        except Exception as e:
            print(f"Failed to fetch content for {c['link']}: {e}")
            continue

        existing_reg = supabase.table("regulations").select("id, content_hash").eq("url", c["link"]).execute()
        if existing_reg.data:
            old_hash = existing_reg.data[0].get("content_hash")
            if old_hash != content_hash:
                print(f"Hash changed for {c['title']}! Updating...")
                supabase.table("regulations").update({"content_hash": content_hash}).eq("id", existing_reg.data[0]["id"]).execute()
            continue

        print(f"Inserting new circular: {c['title']}")
        supabase.table("regulations").insert({
            "source_id": source_id,
            "title": c["title"],
            "url": c["link"],
            "content_hash": content_hash
        }).execute()

    print("Done. New circulars inserted, duplicates skipped, and changes detected.")
    

import hashlib

def get_page_hash(html_text: str) -> str:
    return hashlib.sha256(html_text.encode()).hexdigest()