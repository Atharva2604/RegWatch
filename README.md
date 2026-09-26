# RegWatch (Proof of Concept)

RegWatch is a regulatory compliance tracking pipeline designed to monitor regulatory changes, detect modifications, and compare company policies against the latest regulations to identify compliance gaps and risk scores.

This is a proof-of-concept slice of a larger planned system (SEBI scraping → change detection → structured comparison → risk scoring → alerts).

## Architecture Status

* **Real/Live Components:** 
  * **SEBI Scraping:** The application actively fetches and parses the latest circulars from the live SEBI website.
  * **Change Detection (Hashing):** The SHA-256 hashing utility demonstrates the mathematical foundation for detecting even the smallest modifications in regulatory text.
  
* **Illustrative/Mock Components:** 
  * **Comparison Engine & Risk Scoring:** Currently uses hardcoded mock data to demonstrate how the system will evaluate a company's internal policies against extracted regulatory requirements. In the full version, these structured rules will be dynamically generated using NLP/LLMs from the scraped text.

## How to Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the pipeline:
   ```bash
   python main.py
   ```
