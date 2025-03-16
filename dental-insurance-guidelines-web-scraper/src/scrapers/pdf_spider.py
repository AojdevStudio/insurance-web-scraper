"""
Example Scrapy spider for PDF scraping.

This module contains an example Scrapy spider that finds and downloads PDF files from websites.
"""

import os
from pathlib import Path
import scrapy
from scrapy.http import Request


class PDFSpider(scrapy.Spider):
    """Spider for scraping PDF files from websites."""

    name = "pdf_spider"
    # Add your list of URLs to scrape
    start_urls = [
        "https://example.com/documents/",
        # Add more URLs as needed
    ]
    
    def __init__(self, *args, **kwargs):
        """Initialize the spider with custom parameters."""
        super(PDFSpider, self).__init__(*args, **kwargs)
        # Create directory for storing PDFs if it doesn't exist
        self.pdf_dir = os.path.join(os.getcwd(), "data", "pdfs")
        Path(self.pdf_dir).mkdir(parents=True, exist_ok=True)

    def parse(self, response):
        """
        Parse the response and extract PDF links.
        
        Args:
            response: The response object from the request
            
        Yields:
            Request objects for each PDF file found
        """
        # Extract all links from the page
        links = response.css("a::attr(href)").getall()
        
        # Filter for PDF links (case-insensitive)
        pdf_links = [link for link in links if link.lower().endswith(".pdf")]
        
        for pdf_link in pdf_links:
            # Create absolute URL if needed
            pdf_url = response.urljoin(pdf_link)
            
            # Extract filename from URL
            filename = pdf_url.split("/")[-1]
            
            # Request the PDF file with a callback to save it
            yield Request(
                url=pdf_url,
                callback=self.save_pdf,
                meta={"filename": filename}
            )
            
        # Follow pagination or other links if needed
        next_page = response.css("a.next-page::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def save_pdf(self, response):
        """
        Save the downloaded PDF file.
        
        Args:
            response: The response object containing the PDF data
            
        Returns:
            A dictionary with information about the saved PDF
        """
        filename = response.meta.get("filename")
        file_path = os.path.join(self.pdf_dir, filename)
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Save the PDF file
        with open(file_path, "wb") as f:
            f.write(response.body)
            
        # Log the saved file path
        self.logger.info(f"Saved PDF file: {file_path}")
        
        # Return information about the saved PDF
        return {
            "url": response.url,
            "filename": filename,
            "path": file_path,
            "size": len(response.body)
        }
