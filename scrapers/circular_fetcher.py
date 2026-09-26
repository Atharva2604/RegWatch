import requests
from bs4 import BeautifulSoup
import hashlib

def fetch_circular_text(url: str) -> str:
    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    # SEBI circular pages usually have the main content in a specific div —
    # we'll inspect and refine this selector once we see real output
    content_div = soup.find("div", class_="pagecontent") or soup.find("body")
    return content_div.get_text(strip=True) if content_div else response.text

def get_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

if __name__ == "__main__":
    test_url = "https://www.sebi.gov.in/legal/circulars/aug-2026/alignment-of-sebi-s-cyber-incident-reporting-portal-with-fire-format_103915.html"
    text = fetch_circular_text(test_url)
    print(text[:500])  # print first 500 characters to check it looks right
    print("---")
    print("Hash:", get_hash(text))