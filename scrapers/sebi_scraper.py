import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def fetch_sebi_circulars():
    url = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=1&ssid=7&smid=0"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Search for tables which typically contain the circulars
        table = soup.find('table')
        
        if not table:
            print("Could not find a table on the SEBI page. The page structure might have changed.")
            return

        rows = table.find_all('tr')
        circulars_found = 0
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 0:
                # SEBI tables usually have the date in the first column
                date_str = cols[0].text.strip()
                
                # The title and link are usually in an 'a' tag within the row
                link_tag = row.find('a')
                if link_tag and 'href' in link_tag.attrs:
                    title = link_tag.text.strip()
                    link = urljoin(url, link_tag['href'])
                    
                    if title and link:
                        print(f"Date : {date_str}")
                        print(f"Title: {title}")
                        print(f"Link : {link}")
                        print("-" * 50)
                        
                        circulars_found += 1
                        if circulars_found >= 5:
                            break
        
        if circulars_found == 0:
            print("No circulars found in the table. The HTML structure might have changed.")

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch SEBI circulars: {e}")

if __name__ == "__main__":
    fetch_sebi_circulars()
