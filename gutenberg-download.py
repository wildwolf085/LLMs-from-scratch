# domain list for gutenberg download

import requests
import time
import os
from bs4 import BeautifulSoup
import urllib.parse
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='gutenberg_download.log'
)

# Domain list for Project Gutenberg downloads
GUTENBERG_MIRROR_DOMAINS = [
    'gutenberg.org',
    'gutenberg.cc',
    'gutenberg.us',
    'gutenberg.net',
    'gutenberg.ca',
    'gutenberg.au',
    'gutenberg.co.uk',
    'pglaf.org',
    'promo.net/pg',
    'gutenberg.readingroo.ms',
]

class GutenbergDownloader:
    def __init__(self, output_dir: str = "gutenberg_books"):
        self.output_dir = output_dir
        self.base_url = "https://www.gutenberg.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; Educational/Research Download Bot; Contact: your@email.com)'
        })
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

    def download_book(self, book_id: int, formats: List[str] = ['txt']) -> Optional[str]:
        """
        Download a book by its ID in specified formats
        """
        try:
            # Respect rate limiting
            time.sleep(2)  # Be nice to Gutenberg servers
            
            book_url = f"{self.base_url}/ebooks/{book_id}"
            response = self.session.get(book_url)
            
            if response.status_code != 200:
                logging.error(f"Failed to access book {book_id}: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find download links
            for format_type in formats:
                download_link = soup.find('a', href=lambda x: x and f'.{format_type}' in x.lower())
                
                if download_link:
                    file_url = urllib.parse.urljoin(self.base_url, download_link['href'])
                    
                    # Download the file
                    file_response = self.session.get(file_url)
                    if file_response.status_code == 200:
                        filename = f"{book_id}.{format_type}"
                        filepath = os.path.join(self.output_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(file_response.content)
                        
                        logging.info(f"Successfully downloaded book {book_id} in {format_type} format")
                        return filepath
            
            logging.warning(f"No supported format found for book {book_id}")
            return None
            
        except Exception as e:
            logging.error(f"Error downloading book {book_id}: {str(e)}")
            return None

    def download_range(self, start_id: int, end_id: int, formats: List[str] = ['txt']):
        """
        Download a range of books by their IDs
        """
        successful = 0
        failed = 0
        
        for book_id in range(start_id, end_id + 1):
            result = self.download_book(book_id, formats)
            if result:
                successful += 1
            else:
                failed += 1
                
            # Log progress
            logging.info(f"Progress: {book_id}/{end_id} (Success: {successful}, Failed: {failed})")

def main():
    # Example usage
    downloader = GutenbergDownloader(output_dir="gutenberg_books")
    
    # Download books from ID 1 to 100 (as an example)
    # You can modify these numbers, but please be responsible
    downloader.download_range(1, 1000000, formats=['txt'])

if __name__ == "__main__":
    main()

    

