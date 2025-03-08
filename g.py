# domain list for gutenberg download

import requests
import time
import os
from bs4 import BeautifulSoup
import urllib.parse
from typing import List, Optional
import logging
from tqdm import tqdm
import argparse
from pathlib import Path

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

    def get_total_size(self) -> float:
        """
        Calculate total size of downloaded files in bytes
        """
        total_size = 0
        for file in Path(self.output_dir).glob('*'):
            total_size += file.stat().st_size
        return total_size

    def format_size(self, size_bytes: float) -> str:
        """
        Format size from bytes to human readable format
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} TB"

    def download_range(self, start_id: int, end_id: int, formats: List[str] = ['txt']):
        """
        Download a range of books by their IDs with progress bar
        """
        successful = 0
        failed = 0
        skipped = 0
        total_books = end_id - start_id + 1
        total_size = 0 # self.get_total_size()
        
        # Initialize progress bar
        pbar = tqdm(range(start_id, end_id + 1), 
                   desc=f"Success: 0, Failed: 0, Skipped: 0, Total: 0",
                   total=total_books)
        
        for book_id in pbar:
            result = self.download_book(book_id, formats)
            if result:
                total_size += os.path.getsize(result)
                if os.path.getmtime(result) < time.time() - 5:
                    skipped += 1
                else:
                    successful += 1
            else:
                failed += 1
            
            formatted_size = self.format_size(total_size)
            # Update progress bar description with current stats
            pbar.set_description(
                f"Success: {successful}, Failed: {failed}, Skipped: {skipped}, Total: {formatted_size}"
            )
            
            # # Log progress
            # logging.info(
            #     f"Progress: {book_id}/{end_id} (Success: {successful}, Failed: {failed}, "
            #     f"Skipped: {skipped}, Size: {formatted_size})"
            # )
        
        pbar.close()
        return successful, failed, skipped, total_size

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Download books from Project Gutenberg')
    parser.add_argument('--start', type=int, default=1, help='Starting book ID')
    parser.add_argument('--stop', type=int, default=1000000, help='Ending book ID')
    parser.add_argument('--output', type=str, default="gutenberg_books", help='Output directory')
    parser.add_argument('--formats', type=str, default='txt', help='Comma-separated list of formats to download (e.g., txt,pdf,epub)')
    
    args = parser.parse_args()
    
    # Create downloader instance
    downloader = GutenbergDownloader(output_dir=args.output)
    
    # Parse formats
    formats = [fmt.strip() for fmt in args.formats.split(',')]
    
    # Download books and get statistics
    successful, failed, skipped, total_size = downloader.download_range(
        args.start, args.stop, formats=formats
    )
    
    # Print final statistics
    print(f"\nDownload completed!")
    print(f"Total successful downloads: {successful}")
    print(f"Total failed downloads: {failed}")
    print(f"Total skipped (already existed): {skipped}")
    print(f"Total collection size: {downloader.format_size(total_size)}")

if __name__ == "__main__":
    main()

    

