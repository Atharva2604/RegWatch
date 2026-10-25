"""Polite HTTP Fetcher implementing the domain Fetcher protocol."""

import hashlib
import logging
import requests
from bs4 import BeautifulSoup
from regwatch.domain.errors import FetchError
from regwatch.domain.models import FetchedContent
from regwatch.domain.ports import Fetcher
from regwatch.infrastructure.fetch.circuit_breaker import CircuitBreaker
from regwatch.infrastructure.fetch.pdf_extractor import extract_text_from_pdf
from regwatch.infrastructure.fetch.ratelimit import TokenBucketRateLimiter

logger = logging.getLogger(__name__)


class HttpFetcher(Fetcher):
    """Polite, rate-limited HTTP fetcher with automated HTML/PDF routing."""

    def __init__(
        self,
        user_agent: str,
        timeout_seconds: int = 20,
        rate_limiter: TokenBucketRateLimiter | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self.user_agent = user_agent
        self.timeout = timeout_seconds
        self.rate_limiter = rate_limiter or TokenBucketRateLimiter()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def fetch_listing_page(self, url: str) -> str:
        """Fetch raw HTML for a listing page with rate limiting and circuit breaker."""
        self.circuit_breaker.before_call()
        self.rate_limiter.acquire()

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            self.circuit_breaker.on_success()
            return response.text
        except Exception as exc:
            self.circuit_breaker.on_failure()
            logger.error("Failed to fetch listing page from %s: %s", url, exc)
            raise FetchError(f"HTTP request to {url} failed: {exc}") from exc

    def fetch_paged_listing(self, url: str, page_num: int) -> str:
        """Fetch raw HTML for page N of a listing.

        Handles SEBI's specific AJAX pagination endpoint seamlessly.
        """
        if page_num == 1:
            return self.fetch_listing_page(url)

        # SEBI listing pagination via internal AJAX service
        if "sebi.gov.in" in url and "sid=" in url:
            from urllib.parse import parse_qs, urlparse

            qs = parse_qs(urlparse(url).query)
            sid = qs.get("sid", ["1"])[0]
            ssid = qs.get("ssid", ["7"])[0]
            smid = qs.get("smid", ["0"])[0]

            self.circuit_breaker.before_call()
            self.rate_limiter.acquire()

            ajax_url = "https://www.sebi.gov.in/sebiweb/ajax/home/getnewslistinfo.jsp"
            data = {
                "nextValue": str(page_num - 1),
                "next": "n",
                "search": "",
                "fromDate": "",
                "toDate": "",
                "fromYear": "",
                "toYear": "",
                "sid": sid,
                "ssid": ssid,
                "smid": smid,
                "deptId": "",
                "intmid": "-1",
            }
            headers = {
                "Referer": url,
                "X-Requested-With": "XMLHttpRequest",
            }
            try:
                # Ensure session cookies exist
                if "JSESSIONID" not in self.session.cookies:
                    self.session.get(url, timeout=self.timeout)

                res = self.session.post(ajax_url, data=data, headers=headers, timeout=self.timeout)
                res.raise_for_status()
                self.circuit_breaker.on_success()
                return res.text
            except Exception as exc:
                self.circuit_breaker.on_failure()
                logger.error("Failed to fetch page %d for %s: %s", page_num, url, exc)
                raise FetchError(f"Pagination request to {url} failed: {exc}") from exc

        # Standard GET param fallback
        sep = "&" if "?" in url else "?"
        paged_url = f"{url}{sep}page={page_num}"
        return self.fetch_listing_page(paged_url)

    def fetch_document_content(self, url: str) -> FetchedContent:
        """Fetch regulatory detail page or PDF, extracting full clean text."""
        self.circuit_breaker.before_call()
        self.rate_limiter.acquire()

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            self.circuit_breaker.on_success()

            content_type_header = response.headers.get("Content-Type", "").lower()

            # 1. Direct PDF download
            if url.lower().endswith(".pdf") or "application/pdf" in content_type_header:
                text, raw_sha = extract_text_from_pdf(response.content)
                return FetchedContent(
                    url=url,
                    text=text,
                    content_type="pdf",
                    needs_ocr=len(text) < 200,
                    raw_sha256=raw_sha,
                )

            # 2. HTML page containing embedded PDF iframe
            soup = BeautifulSoup(response.text, "html.parser")
            iframe = soup.find("iframe")
            if iframe and iframe.get("src"):
                pdf_url = iframe.get("src", "")
                if "file=" in pdf_url:
                    pdf_url = pdf_url.split("file=")[-1]

                if not pdf_url.startswith("http"):
                    # Resolve relative URL against SEBI base
                    while pdf_url.startswith("../"):
                        pdf_url = pdf_url[3:]
                    pdf_url = f"https://www.sebi.gov.in/{pdf_url.lstrip('/')}"

                # Follow PDF link
                pdf_response = self.session.get(pdf_url, timeout=self.timeout)
                if pdf_response.ok:
                    text, raw_sha = extract_text_from_pdf(pdf_response.content)
                    return FetchedContent(
                        url=url,
                        text=text,
                        content_type="pdf",
                        needs_ocr=len(text) < 200,
                        raw_sha256=raw_sha,
                    )

            # 3. HTML main content fallback
            content_div = soup.find("div", class_="pagecontent") or soup.find("body")
            body_text = content_div.get_text(separator=" ", strip=True) if content_div else response.text
            raw_sha = hashlib.sha256(response.content).hexdigest()

            return FetchedContent(
                url=url,
                text=body_text,
                content_type="html",
                needs_ocr=False,
                raw_sha256=raw_sha,
            )

        except Exception as exc:
            self.circuit_breaker.on_failure()
            logger.error("Failed to fetch document content from %s: %s", url, exc)
            raise FetchError(f"Document download failed for {url}: {exc}") from exc
