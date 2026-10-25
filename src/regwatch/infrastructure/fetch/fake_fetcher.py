"""Deterministic Fake Fetcher for unit and integration testing without network calls."""

from regwatch.domain.models import FetchedContent
from regwatch.domain.ports import Fetcher


class FakeFetcher(Fetcher):
    """In-memory fake fetcher returning deterministic content for testing."""

    def __init__(self, sample_html: str = "", sample_text: str = "") -> None:
        self.sample_html = sample_html or "<table><tr><td>Oct 22, 2026</td><td><a href='/test.html'>Test Doc</a></td></tr></table>"
        self.sample_text = sample_text or "Regulated entities must report cyber incidents to SEBI within 6 hours of discovery."

    def fetch_listing_page(self, url: str) -> str:
        return self.sample_html

    def fetch_paged_listing(self, url: str, page_num: int) -> str:
        if page_num > 1:
            return ""
        return self.sample_html

    def fetch_document_content(self, url: str) -> FetchedContent:
        return FetchedContent(
            url=url,
            text=self.sample_text,
            content_type="html",
            needs_ocr=False,
            raw_sha256="fake_sha256_for_unit_tests",
        )
