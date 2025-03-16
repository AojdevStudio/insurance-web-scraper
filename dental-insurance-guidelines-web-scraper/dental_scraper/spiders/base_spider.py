"""
Base spider class providing common functionality for all dental insurance guideline spiders.
"""
from typing import Optional, Dict, Any
from pathlib import Path
import json

from scrapy import Spider
from scrapy.http import Response, Request
from loguru import logger

from ..exceptions import (
    ScraperException,
    AuthenticationException,
    ParsingException,
    DownloadException
)

class BaseInsuranceSpider(Spider):
    """
    Base spider class with common functionality for scraping dental insurance guidelines.
    
    Attributes:
        name (str): Name of the spider
        allowed_domains (list): List of domains this spider is allowed to crawl
        start_urls (list): List of URLs to start crawling from
        credentials (dict): Login credentials if required
        output_dir (Path): Directory to store downloaded files
    """
    
    def __init__(self, 
                 name: str,
                 allowed_domains: list,
                 start_urls: list,
                 credentials: Optional[Dict[str, str]] = None,
                 output_dir: Optional[Path] = None,
                 *args, **kwargs):
        """Initialize the spider with required parameters."""
        super().__init__(name, *args, **kwargs)
        self.allowed_domains = allowed_domains
        self.start_urls = start_urls
        self.credentials = credentials or {}
        self.output_dir = output_dir or Path('data/pdfs')
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized {self.name} spider")
        
    def start_requests(self):
        """
        Start the crawling process. Override this method if login is required.
        """
        for url in self.start_urls:
            yield Request(url=url, callback=self.parse)
            
    def parse(self, response: Response, **kwargs) -> Any:
        """
        Default parse method. Must be implemented by child classes.
        """
        raise NotImplementedError("Subclasses must implement parse method")
    
    def handle_error(self, failure):
        """
        Generic error handler for failed requests.
        """
        logger.error(f"Request failed: {failure.value}")
        if hasattr(failure.value, 'response') and failure.value.response:
            logger.error(f"Response status: {failure.value.response.status}")
            logger.error(f"Response headers: {failure.value.response.headers}")
        
        # Re-raise the exception for the middleware to handle
        raise ScraperException(f"Request failed: {failure.value}")
    
    def save_pdf(self, content: bytes, filename: str) -> Path:
        """
        Save PDF content to the output directory.
        
        Args:
            content: PDF file content in bytes
            filename: Name to save the file as
            
        Returns:
            Path to the saved file
        """
        try:
            file_path = self.output_dir / filename
            file_path.write_bytes(content)
            logger.info(f"Saved PDF to {file_path}")
            return file_path
        except Exception as e:
            raise DownloadException(f"Failed to save PDF {filename}: {e}")
    
    def save_metadata(self, metadata: Dict[str, Any], filename: str) -> Path:
        """
        Save metadata for a downloaded PDF.
        
        Args:
            metadata: Dictionary containing metadata
            filename: Name of the JSON file to save
            
        Returns:
            Path to the saved metadata file
        """
        try:
            file_path = self.output_dir / filename
            with open(file_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Saved metadata to {file_path}")
            return file_path
        except Exception as e:
            raise ParsingException(f"Failed to save metadata {filename}: {e}") 