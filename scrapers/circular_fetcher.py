"""
RegWatch Scraper — Circular Fetcher with PyMuPDF & Tesseract OCR Fallback
Resolves the empty text flaw on scanned PDF circulars and photocopied notices.
"""
import io
import os
import shutil
import hashlib
import logging
from typing import Optional
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

logger = logging.getLogger("regwatch.circular_fetcher")

# Auto-configure Tesseract binary path on Windows / Linux environments
_TESSERACT_CONFIGURED = False


def _configure_tesseract() -> bool:
    """Detects and registers tesseract binary in PATH or standard system directories."""
    global _TESSERACT_CONFIGURED
    if _TESSERACT_CONFIGURED:
        return True

    custom_cmd = os.getenv("TESSERACT_CMD")
    if custom_cmd and os.path.exists(custom_cmd):
        pytesseract.pytesseract.tesseract_cmd = custom_cmd
        _TESSERACT_CONFIGURED = True
        return True

    # Check system PATH
    system_path = shutil.which("tesseract")
    if system_path:
        pytesseract.pytesseract.tesseract_cmd = system_path
        _TESSERACT_CONFIGURED = True
        return True

    # Standard Windows and Linux installation paths
    candidate_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            _TESSERACT_CONFIGURED = True
            return True

    return False


def _ocr_page_fallback(page: fitz.Page, zoom: float = 2.0) -> str:
    """Renders a PDF page to a high-resolution image and extracts text via Tesseract OCR."""
    try:
        _configure_tesseract()
        # Render high-resolution pixmap (2.0x zoom matrix ~ 144-200 DPI for optimal OCR)
        matrix = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))

        # Perform OCR
        text = pytesseract.image_to_string(image, lang="eng")
        return text.strip()
    except Exception as e:
        logger.warning(f"OCR execution warning on page {page.number}: {e}")
        return ""


def _extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extracts text from PDF bytes using PyMuPDF.
    If extracted text is fewer than 50 characters (e.g. scanned photocopies),
    automatically executes an OCR fallback using pytesseract and Pillow.
    """
    text_pages = []
    has_scanned_pages = False

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            page_text = page.get_text()
            text_pages.append(page_text)

        full_extracted = "\n".join(text_pages).strip()

        # Check for empty or scanned image PDF flaw (< 50 characters)
        if len(full_extracted) < 50 and len(doc) > 0:
            logger.info(
                f"[OCR Fallback Triggered] Extracted text ({len(full_extracted)} chars) < 50 chars. "
                f"Executing Tesseract OCR across {len(doc)} pages..."
            )
            ocr_pages = []
            for page in doc:
                ocr_text = _ocr_page_fallback(page)
                if ocr_text:
                    ocr_pages.append(ocr_text)

            ocr_result = "\n\n".join(ocr_pages).strip()
            if ocr_result:
                return ocr_result

    return full_extracted


def fetch_circular_text(url: str, timeout: int = 20) -> str:
    """
    Downloads and extracts full circular text from SEBI URL or iframe target.
    Supports native PDF, scanned image PDF with OCR fallback, and HTML pages.
    """
    headers = {
        "User-Agent": "RegWatch/1.0 (+https://github.com/RegWatch; compliance-monitoring-bot)"
    }
    response = requests.get(url, headers=headers, timeout=timeout)

    # Check if the URL is directly a PDF
    content_type = response.headers.get("Content-Type", "").lower()
    if url.lower().endswith(".pdf") or "application/pdf" in content_type:
        return _extract_text_from_pdf_bytes(response.content)

    # If it's HTML, parse it and look for the iframe containing the PDF
    soup = BeautifulSoup(response.text, "html.parser")
    iframe = soup.find("iframe")

    if iframe and iframe.get("src"):
        pdf_url = iframe.get("src")

        # Handle embedded viewer (e.g. web/?file=https://...)
        if "file=" in pdf_url:
            pdf_url = pdf_url.split("file=")[-1]

        # Ensure absolute URL
        if pdf_url.startswith("../"):
            while pdf_url.startswith("../"):
                pdf_url = pdf_url[3:]
            pdf_url = "https://www.sebi.gov.in/" + pdf_url
        elif pdf_url.startswith("/"):
            pdf_url = "https://www.sebi.gov.in" + pdf_url

        try:
            pdf_response = requests.get(pdf_url, headers=headers, timeout=timeout)
            return _extract_text_from_pdf_bytes(pdf_response.content)
        except Exception as e:
            logger.error(f"Failed to fetch embedded PDF from {pdf_url}: {e}")

    # Fallback to HTML content if no PDF iframe found
    content_div = soup.find("div", class_="pagecontent") or soup.find("body")
    return content_div.get_text(separator=" ", strip=True) if content_div else response.text


def get_hash(text: str) -> str:
    """Computes SHA-256 fingerprint for change detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()