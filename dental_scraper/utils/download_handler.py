import os
import aiohttp
import asyncio
from typing import Optional
from loguru import logger
from datetime import datetime
import hashlib

class DownloadHandler:
    """Handles downloading and saving of PDF files."""
    
    def __init__(self, download_dir: str = None):
        """
        Initialize the download handler.
        
        Args:
            download_dir: Directory to save downloaded files (default: ./downloads)
        """
        self.download_dir = download_dir or os.path.join(os.getcwd(), 'downloads')
        self._ensure_download_dir()
        
    def _ensure_download_dir(self):
        """Ensure the download directory exists."""
        try:
            os.makedirs(self.download_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating download directory: {str(e)}")
            raise
            
    def _generate_filename(self, url: str, carrier: str) -> str:
        """
        Generate a unique filename for the downloaded PDF.
        
        Args:
            url: URL of the PDF
            carrier: Insurance carrier name
            
        Returns:
            Generated filename
        """
        try:
            # Create a hash of the URL to ensure uniqueness
            url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
            
            # Get timestamp for versioning
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Clean carrier name
            carrier = ''.join(c for c in carrier.lower() if c.isalnum())
            
            return f"{carrier}_{timestamp}_{url_hash}.pdf"
            
        except Exception as e:
            logger.error(f"Error generating filename: {str(e)}")
            raise
            
    async def download_pdf(self, url: str, carrier: str) -> Optional[str]:
        """
        Download a PDF file from a URL.
        
        Args:
            url: URL of the PDF to download
            carrier: Insurance carrier name
            
        Returns:
            Path to the downloaded file, or None if download fails
        """
        try:
            filename = self._generate_filename(url, carrier)
            filepath = os.path.join(self.download_dir, filename)
            
            # Configure timeout and headers
            timeout = aiohttp.ClientTimeout(total=60)  # 60 seconds total timeout
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download PDF: {response.status} - {url}")
                        return None
                        
                    # Verify content type
                    content_type = response.headers.get('Content-Type', '').lower()
                    if 'application/pdf' not in content_type and 'application/octet-stream' not in content_type:
                        logger.error(f"Invalid content type: {content_type} - {url}")
                        return None
                        
                    # Read response in chunks
                    try:
                        with open(filepath, 'wb') as f:
                            chunk_size = 8192  # 8KB chunks
                            while True:
                                chunk = await response.content.read(chunk_size)
                                if not chunk:
                                    break
                                f.write(chunk)
                    except Exception as e:
                        logger.error(f"Error writing PDF file: {str(e)}")
                        # Clean up partial download
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        return None
                        
                    # Verify file size
                    file_size = os.path.getsize(filepath)
                    if file_size < 1024:  # Less than 1KB is probably not a valid PDF
                        logger.error(f"Downloaded file too small: {file_size} bytes")
                        os.remove(filepath)
                        return None
                        
                    logger.info(f"Successfully downloaded PDF: {url} -> {filepath}")
                    return filepath
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout downloading PDF: {url}")
            return None
            
        except aiohttp.ClientError as e:
            logger.error(f"Network error downloading PDF: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error downloading PDF: {str(e)}")
            return None
            
    async def cleanup_old_files(self, max_age_days: int = 7):
        """
        Clean up old downloaded files.
        
        Args:
            max_age_days: Maximum age of files to keep (default: 7 days)
        """
        try:
            now = datetime.now()
            for filename in os.listdir(self.download_dir):
                filepath = os.path.join(self.download_dir, filename)
                if not os.path.isfile(filepath):
                    continue
                    
                file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                age_days = (now - file_time).days
                
                if age_days > max_age_days:
                    try:
                        os.remove(filepath)
                        logger.info(f"Removed old file: {filepath}")
                    except Exception as e:
                        logger.error(f"Error removing old file {filepath}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old files: {str(e)}")
            
    def get_download_path(self, url: str, carrier: str) -> str:
        """
        Get the path where a file would be downloaded without actually downloading it.
        
        Args:
            url: URL of the PDF
            carrier: Insurance carrier name
            
        Returns:
            Path where the file would be downloaded
        """
        try:
            filename = self._generate_filename(url, carrier)
            return os.path.join(self.download_dir, filename)
            
        except Exception as e:
            logger.error(f"Error getting download path: {str(e)}")
            raise 