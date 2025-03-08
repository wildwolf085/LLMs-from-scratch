# domain list for gutenberg download

import requests
import time
import os
from bs4 import BeautifulSoup
import urllib.parse
from typing import List, Optional
import logging
from tqdm import tqdm

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
            # Check if file already exists
            for format_type in formats:
                filename = f"{book_id}.{format_type}"
                filepath = os.path.join(self.output_dir, filename)
                if os.path.exists(filepath):
                    logging.info(f"Book {book_id} already exists in {format_type} format")
                    return filepath

            # Respect rate limiting
            time.sleep(0.2)  # Be nice to Gutenberg servers
            
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
        Download a range of books by their IDs with progress bar
        """
        successful = 0
        failed = 0
        skipped = 0  # New counter for skipped (already existing) files
        total_books = end_id - start_id + 1
        
        # Initialize progress bar
        pbar = tqdm(range(start_id, end_id + 1), 
                   desc=f"Success: {successful}, Failed: {failed}, Skipped: {skipped}",
                   total=total_books)
        
        for book_id in pbar:
            result = self.download_book(book_id, formats)
            if result:
                if os.path.getmtime(result) < time.time() - 5:  # If file is older than 5 seconds
                    skipped += 1
                else:
                    successful += 1
            else:
                failed += 1
            
            # Update progress bar description with current stats
            pbar.set_description(f"Success: {successful}, Failed: {failed}, Skipped: {skipped}")
            
            # Log progress
            logging.info(f"Progress: {book_id}/{end_id} (Success: {successful}, Failed: {failed}, Skipped: {skipped})")
        
        pbar.close()
        return successful, failed, skipped

def main():
    downloader = GutenbergDownloader(output_dir="gutenberg_books")
    
    # Download books and get statistics
    successful, failed, skipped = downloader.download_range(1, 1000000, formats=['txt'])
    
    # Print final statistics
    print(f"\nDownload completed!")
    print(f"Total successful downloads: {successful}")
    print(f"Total failed downloads: {failed}")
    print(f"Total skipped (already existed): {skipped}")

if __name__ == "__main__":
    main()

    

