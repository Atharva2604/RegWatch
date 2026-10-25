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
    """Scrape a single page URL and return list of items."""
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

def scrape_all_pages(base_url, max_pages=50):
    """
    Scrapes all paginated pages of a SEBI listing URL.
    SEBI uses &currPage=N for pagination.
    Stops when a page returns no results or max_pages is reached.
    """
    all_items = []

    for page_num in range(1, max_pages + 1):
        # SEBI pagination: append &currPage=N (skip for page 1 — it's the default)
        if page_num == 1:
            url = base_url
        else:
            url = f"{base_url}&currPage={page_num}"

        print(f"  Fetching page {page_num}: {url}")

        try:
            items = scrape_page(url)
        except Exception as e:
            print(f"  Error fetching page {page_num}: {e}")
            break

        if not items:
            print(f"  No items found on page {page_num}. Stopping pagination.")
            break

        all_items.extend(items)
        print(f"  Page {page_num}: found {len(items)} items (total so far: {len(all_items)})")

    return all_items

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

def fetch_sebi_circulars():
    """Scrape all SEBI legal sources, detect changes by hash, upsert to Supabase."""
    source_id = get_or_create_source("SEBI", "https://www.sebi.gov.in", "cybersecurity_resilience")

    for source in LEGAL_SOURCES:
        print(f"\n=== Scraping {source['legal_type']} ===")
        results = scrape_all_pages(source["url"], max_pages=50)
        print(f"Found {len(results)} total rows across all pages")

        for c in results:
            if not c["link"]:
                continue

            existing_reg = supabase.table("regulations").select("id, content_hash").eq("url", c["link"]).execute()
            if existing_reg.data and existing_reg.data[0].get("content_hash"):
                # Already downloaded, hashed, and stored in Supabase!
                continue

            try:
                content_text = fetch_circular_text(c["link"])
                content_hash = get_hash(content_text)
            except Exception as e:
                print(f"Failed to fetch content for {c['link']}: {e}")
                continue

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

            # Fix date format for Postgres (it crashes if date is just "2015")
            safe_date = c["date"]
            if safe_date:
                safe_date = safe_date.strip()
                if len(safe_date) == 4 and safe_date.isdigit():  # e.g., "2015"
                    safe_date = f"{safe_date}-01-01"
            else:
                safe_date = None

            supabase.table("regulations").insert({
                "source_id": source_id,
                "title": c["title"],
                "url": c["link"],
                "content_hash": content_hash,
                "content_text": content_text,
                "legal_type": source["legal_type"],
                "effective_date": safe_date
            }).execute()

    print("\nDone. All legal sources scraped, duplicates skipped, changes detected.")


if __name__ == "__main__":
    fetch_sebi_circulars()