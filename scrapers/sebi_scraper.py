import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

try:
    from scrapers.circular_fetcher import fetch_circular_text, get_hash
except ModuleNotFoundError:
    from circular_fetcher import fetch_circular_text, get_hash

LEGAL_SOURCES = [
    {
        "legal_type": "circular",
        "url": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0",
    },
    {
        "legal_type": "regulation",
        "url": "https://www.sebi.gov.in/sebi_data/commondocs/Regulations.html",
    },
    {
        "legal_type": "act",
        "url": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=1&smid=0",
    },
    {
        "legal_type": "rule",
        "url": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=2&smid=0",
    },
    {
        "legal_type": "guideline",
        "url": "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=5&smid=0",
    }
]

def scrape_page(url):
    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("table tr")
    items = []

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
            items.append({"date": date, "title": title, "link": link})

    return items

def get_or_create_source(name, base_url, category_focus):
    existing = supabase.table("sources").select("id").eq("name", name).execute()
    if existing.data:
        return existing.data[0]["id"]
    inserted = supabase.table("sources").insert({
        "name": name,
        "base_url": base_url,
        "category_focus": category_focus
    }).execute()
    return inserted.data[0]["id"]

if __name__ == "__main__":
    source_id = get_or_create_source("SEBI", "https://www.sebi.gov.in", "cybersecurity_resilience")

    for source in LEGAL_SOURCES:
        print(f"\n=== Scraping {source['legal_type']} ===")
        results = scrape_page(source["url"])
        print(f"Found {len(results)} rows")

        for c in results:
            if not c["link"]:
                continue

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
                    supabase.table("regulations").update({
                        "content_hash": content_hash,
                        "content_text": content_text,
                        "legal_type": source["legal_type"]
                    }).eq("id", existing_reg.data[0]["id"]).execute()
                continue

            print(f"Inserting new {source['legal_type']}: {c['title']}")
            supabase.table("regulations").insert({
                "source_id": source_id,
                "title": c["title"],
                "url": c["link"],
                "content_hash": content_hash,
                "content_text": content_text,  # Added the text here!
                "legal_type": source["legal_type"]
            }).execute()

    print("\nDone. All legal sources scraped, duplicates skipped, changes detected.")