"""PDF Text Extraction using PyMuPDF (fitz)."""

import hashlib
import io
import pymupdf as fitz


def extract_text_from_pdf(pdf_bytes: bytes) -> tuple[str, str]:
    """Extract full clean text from PDF bytes and compute content SHA-256.
    
    Returns:
        tuple of (extracted_text, sha256_hash)
    """
    text_chunks: list[str] = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text_chunks.append(page.get_text())

    full_text = "\n".join(text_chunks).strip()
    raw_hash = hashlib.sha256(pdf_bytes).hexdigest()
    return full_text, raw_hash
