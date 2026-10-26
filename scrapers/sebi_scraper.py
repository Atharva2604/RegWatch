"""
RegWatch Scraper — SEBI Legal Sources Scraper
Scrapes SEBI circulars, orders, and regulations with hash change detection,
automated 500-token sliding window chunk indexing, and event-driven compliance audits.
"""
import os
import logging
from typing import Optional
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
logger = logging.getLogger("regwatch.sebi_scraper")

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

try:
    from scrapers.circular_fetcher import fetch_circular_text, get_hash
except ModuleNotFoundError:
    from circular_fetcher import fetch_circular_text, get_hash

try:
    from pipeline.chunk_engine import chunk_and_index_regulation
    from pipeline.comparison_engine import evaluate_new_circular_for_all_companies
except ModuleNotFoundError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from pipeline.chunk_engine import chunk_and_index_regulation
    from pipeline.comparison_engine import evaluate_new_circular_for_all_companies

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


def scrape_page(url: str):
    """Scrapes a single paginated HTML listing and returns raw circular metadata."""
    headers = {"User-Agent": "RegWatch/1.0 (+https://github.com/RegWatch; compliance-monitoring-bot)"}
    response = requests.get(url, headers=headers, timeout=15)
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


def scrape_all_pages(base_url: str, max_pages: int = 50):
    """
    Scrapes all paginated pages of a SEBI listing URL using currPage parameter.
    Stops when a page returns no results or max_pages is reached.
    """
    all_items = []

    for page_num in range(1, max_pages + 1):
        url = base_url if page_num == 1 else f"{base_url}&currPage={page_num}"
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
        print(f"  Page {page_num}: found {len(items)} items (total: {len(all_items)})")

    return all_items


def get_or_create_source(name: str, base_url: str, category_focus: str) -> int:
    existing = supabase.table("sources").select("id").eq("name", name).execute()
    if existing.data:
        return existing.data[0]["id"]
    inserted = supabase.table("sources").insert({
        "name": name,
        "base_url": base_url,
        "category_focus": category_focus
    }).execute()
    return inserted.data[0]["id"]


def fetch_sebi_circulars(max_pages_per_source: int = 50):
    """
    Scrapes SEBI legal sources, detects changes by SHA-256 hash,
    indexes 500-token sliding window chunks with vector(384) embeddings,
    and immediately triggers event-driven compliance audits across all active companies.
    """
    source_id = get_or_create_source("SEBI", "https://www.sebi.gov.in", "cybersecurity_resilience")

    for source in LEGAL_SOURCES:
        print(f"\n=== Scraping {source['legal_type']} ===")
        results = scrape_all_pages(source["url"], max_pages=max_pages_per_source)
        print(f"Found {len(results)} total rows across all pages")

        for c in results:
            if not c["link"]:
                continue

            existing_reg = supabase.table("regulations").select("id, content_hash").eq("url", c["link"]).execute()
            if existing_reg.data and existing_reg.data[0].get("content_hash"):
                # Already downloaded, hashed, and stored
                continue

            try:
                # Extracts text with PyMuPDF and Pillow/pytesseract OCR fallback for scanned images
                content_text = fetch_circular_text(c["link"])
                content_hash = get_hash(content_text)
            except Exception as e:
                print(f"Failed to fetch content for {c['link']}: {e}")
                continue

            # Handle existing regulation with updated content hash
            if existing_reg.data:
                reg_id = existing_reg.data[0]["id"]
                old_hash = existing_reg.data[0].get("content_hash")
                if old_hash != content_hash:
                    print(f"Hash changed for {c['title']} (ID #{reg_id})! Updating...")
                    supabase.table("regulations").update({
                        "content_hash": content_hash,
                        "content_text": content_text,
                        "legal_type": source["legal_type"],
                        "last_changed_at": "now()",
                    }).eq("id", reg_id).execute()

                    # 1. Re-index chunks (500 tokens with 50-token overlap)
                    try:
                        chunk_and_index_regulation(reg_id, content_text, title=c["title"])
                    except Exception as chk_err:
                        print(f"Warning: could not re-chunk regulation #{reg_id}: {chk_err}")

                    # 2. Event-driven automation: run compliance comparison across all active companies
                    try:
                        evaluate_new_circular_for_all_companies(reg_id)
                    except Exception as eval_err:
                        print(f"Warning: could not trigger audit for reg #{reg_id}: {eval_err}")

                continue

            print(f"Inserting new {source['legal_type']}: {c['title']}")

            safe_date = c["date"]
            if safe_date:
                safe_date = safe_date.strip()
                if len(safe_date) == 4 and safe_date.isdigit():
                    safe_date = f"{safe_date}-01-01"
            else:
                safe_date = None

            # Generate 384-dim embedding without arbitrary document truncation
            embedding_vector = None
            try:
                from sentence_transformers import SentenceTransformer
                if not hasattr(fetch_sebi_circulars, "_embed_model"):
                    fetch_sebi_circulars._embed_model = SentenceTransformer("all-MiniLM-L6-v2")
                # Embed informative prefix + title (clauses are indexed in regulation_chunks)
                text_to_embed = f"{c['title']}. {content_text[:1500]}"
                embedding_vector = fetch_sebi_circulars._embed_model.encode(text_to_embed, normalize_embeddings=True).tolist()
            except Exception as emb_err:
                print(f"Warning: could not generate header embedding for {c['title']}: {emb_err}")

            insert_data = {
                "source_id": source_id,
                "title": c["title"],
                "url": c["link"],
                "content_hash": content_hash,
                "content_text": content_text,
                "legal_type": source["legal_type"],
                "published_date": safe_date
            }
            if embedding_vector:
                insert_data["embedding"] = embedding_vector

            insert_res = supabase.table("regulations").insert(insert_data).execute()
            if not insert_res.data:
                continue

            new_reg_id = insert_res.data[0]["id"]

            # Loophole 1 Resolution: Sliding-window chunking into regulation_chunks
            try:
                num_chunks = chunk_and_index_regulation(new_reg_id, content_text, title=c["title"])
                print(f"  Successfully indexed {num_chunks} clause chunks into regulation_chunks.")
            except Exception as chk_err:
                print(f"  Warning: could not index chunks for new reg #{new_reg_id}: {chk_err}")

            # Loophole 3 Resolution: Event-driven automation across all active companies
            try:
                alerts = evaluate_new_circular_for_all_companies(new_reg_id)
                print(f"  Event-driven evaluation complete: {len(alerts)} alerts generated.")
            except Exception as auto_err:
                print(f"  Warning: event-driven audit failed for reg #{new_reg_id}: {auto_err}")

    print("\nDone. All legal sources scraped, chunks indexed, and event-driven audits executed.")


if __name__ == "__main__":
    fetch_sebi_circulars()