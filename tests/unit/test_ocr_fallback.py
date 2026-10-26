"""
Unit Tests for Loophole 2: OCR Fallback on Scanned Image PDFs
Verifies that when PyMuPDF extracts < 50 characters, Tesseract OCR is invoked.
"""
from unittest.mock import MagicMock, patch
import io
import fitz
from scrapers.circular_fetcher import _extract_text_from_pdf_bytes, _ocr_page_fallback


def test_ocr_fallback_triggered_when_extracted_text_under_50_chars():
    # Create a blank 1-page PDF using PyMuPDF (0 characters extracted natively)
    doc = fitz.open()
    doc.new_page(width=300, height=300)
    pdf_bytes = doc.tobytes()
    doc.close()

    mock_ocr_text = "SEBI CIRCULAR 2026: Mandate for Cyber Security Incident Response"

    with patch("scrapers.circular_fetcher._ocr_page_fallback", return_value=mock_ocr_text) as mock_ocr:
        result = _extract_text_from_pdf_bytes(pdf_bytes)

        # Assert OCR fallback was executed
        assert mock_ocr.called
        assert mock_ocr_text in result


def test_native_text_retained_when_over_50_chars():
    # Create a PDF with native text (> 50 chars)
    doc = fitz.open()
    page = doc.new_page(width=800, height=400)
    long_native_text = "Securities and Exchange Board of India Circular on Margin Trading Facility compliance obligations."
    page.insert_text((50, 50), long_native_text)
    pdf_bytes = doc.tobytes()
    doc.close()

    with patch("scrapers.circular_fetcher._ocr_page_fallback") as mock_ocr:
        result = _extract_text_from_pdf_bytes(pdf_bytes)

        # Should NOT trigger OCR fallback when native text is abundant
        assert not mock_ocr.called
        assert "Margin Trading Facility" in result
