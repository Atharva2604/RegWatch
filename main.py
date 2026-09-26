from scrapers.sebi_scraper import fetch_sebi_circulars
from pipeline.hash_utils import demo_hashing
from pipeline.comparison_engine import run_comparison_demo

def main():
    print("=== STEP 1: Scraping SEBI ===")
    fetch_sebi_circulars()
    print("\n")
    
    print("=== STEP 2: Change Detection ===")
    demo_hashing()
    print("\n")
    
    print("=== STEP 3: Comparison & Risk Score (using mock data) ===")
    run_comparison_demo()
    print("\n")

if __name__ == "__main__":
    main()
