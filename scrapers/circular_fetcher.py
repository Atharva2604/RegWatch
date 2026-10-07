import requests
from bs4 import BeautifulSoup
import hashlib
import fitz  # PyMuPDF
import io

def fetch_circular_text(url: str) -> str:
    response = requests.get(url, timeout=15)
    
    # Check if the URL itself is directly a PDF
    if url.lower().endswith(".pdf") or response.headers.get("Content-Type") == "application/pdf":
        return _extract_text_from_pdf_bytes(response.content)

    # If it's HTML, parse it and look for the iframe containing the PDF
    soup = BeautifulSoup(response.text, "html.parser")
    iframe = soup.find("iframe")
    
    if iframe and iframe.get("src"):
        pdf_url = iframe.get("src")
        
        # If the iframe uses a viewer (e.g. web/?file=https://...), extract the real PDF URL first
        if "file=" in pdf_url:
            pdf_url = pdf_url.split("file=")[-1]
            
        # Ensure the PDF URL is absolute if it's still relative
        if pdf_url.startswith("../"):
            # remove all occurrences of ../
            while pdf_url.startswith("../"):
                pdf_url = pdf_url[3:]
            pdf_url = "https://www.sebi.gov.in/" + pdf_url
        elif pdf_url.startswith("/"):
            pdf_url = "https://www.sebi.gov.in" + pdf_url
            
        # Download the PDF
        pdf_response = requests.get(pdf_url, timeout=15)
        return _extract_text_from_pdf_bytes(pdf_response.content)

    # Fallback if no iframe is found
    content_div = soup.find("div", class_="pagecontent") or soup.find("body")
    return content_div.get_text(separator=" ", strip=True) if content_div else response.text

def _extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    text = []
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            text.append(page.get_text())
    return "\n".join(text)

def get_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

if __name__ == "__main__":
    # Test with a known circular URL containing an iframe
    test_url = "https://www.sebi.gov.in/legal/circulars/aug-2026/alignment-of-sebi-s-cyber-incident-reporting-portal-with-fire-format_103915.html"
    text = fetch_circular_text(test_url)
    print(text[:500])  # print first 500 characters to check it looks right
    print("---")
    print("Hash:", get_hash(text))