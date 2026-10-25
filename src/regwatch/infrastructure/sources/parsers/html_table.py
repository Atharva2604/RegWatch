"""Built-in HTML table listing parser plugin."""

import re
from collections.abc import Iterator
from datetime import date, datetime
from bs4 import BeautifulSoup
from regwatch.domain.models import LegalType, ListingItem


def parse_indian_date(date_str: str) -> date | None:
    """Parse dates commonly found on Indian regulatory websites (e.g. 'Oct 22, 2024' or '22/10/2024')."""
    cleaned = date_str.strip()
    for fmt in ("%b %d, %Y", "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def parse_html_table(
    html: str,
    source_key: str,
    legal_type: LegalType,
    base_url: str = "https://www.sebi.gov.in",
    row_selector: str = "table tr",
    date_col_idx: int = 0,
    title_col_idx: int = 1,
) -> Iterator[ListingItem]:
    """Parse HTML table rows into canonical ListingItems."""
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(row_selector)

    for row in rows:
        cells = row.find_all("td")
        if len(cells) > max(date_col_idx, title_col_idx):
            raw_date = cells[date_col_idx].get_text(strip=True)
            title_cell = cells[title_col_idx]
            title = title_cell.get_text(strip=True)

            link_tag = title_cell.find("a")
            if not link_tag or not link_tag.get("href"):
                continue

            link = link_tag["href"]
            if not link.startswith("http"):
                link = base_url.rstrip("/") + "/" + link.lstrip("/")

            pub_date = parse_indian_date(raw_date)

            yield ListingItem(
                source_key=source_key,
                url=link,
                title=title,
                legal_type=legal_type,
                published_date=pub_date,
            )
