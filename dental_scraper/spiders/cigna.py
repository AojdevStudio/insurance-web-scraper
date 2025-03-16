import scrapy
from bs4 import BeautifulSoup
import re
from loguru import logger
from ..utils.download_handler import DownloadHandler
from ..utils.pdf_processor import PDFProcessor

class CignaSpider(scrapy.Spider):
    name = 'cigna'
    allowed_domains = ['cigna.com']
    start_urls = ['https://www.cigna.com/dental/coverage-policies']
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 3,
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_TIMEOUT': 60,
        'COOKIES_ENABLED': True
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.download_handler = DownloadHandler()
        self.pdf_processor = PDFProcessor()
        self.guidelines_found = False
        logger.info("Initialized Cigna spider")

    def parse(self, response):
        logger.info(f"Parsing page: {response.url}")
        soup = BeautifulSoup(response.body, 'html.parser')
        
        # Find PDF links for guidelines and policy documents
        for link in soup.find_all('a', href=re.compile(r'\.pdf$')):
            pdf_url = link.get('href')
            if pdf_url:
                # Only process guidelines.pdf and policy.pdf
                if 'guidelines.pdf' in pdf_url:
                    self.guidelines_found = True
                    # Make sure the URL is absolute
                    if not pdf_url.startswith(('http://', 'https://')):
                        pdf_url = response.urljoin(pdf_url)
                    
                    # Yield a request for the PDF
                    yield scrapy.Request(
                        url=pdf_url,
                        callback=self.parse_pdf,
                        meta={'pdf_url': pdf_url}
                    )
                elif 'policy.pdf' in pdf_url:
                    # Make sure the URL is absolute
                    if not pdf_url.startswith(('http://', 'https://')):
                        pdf_url = response.urljoin(pdf_url)
                    
                    # Yield a request for the PDF
                    yield scrapy.Request(
                        url=pdf_url,
                        callback=self.parse_pdf,
                        meta={'pdf_url': pdf_url}
                    )
        
        # Follow resource links
        for link in soup.find_all('a', href=re.compile(r'/dental/resources')):
            resource_url = link.get('href')
            if resource_url:
                # Make sure the URL is absolute
                if not resource_url.startswith(('http://', 'https://')):
                    resource_url = response.urljoin(resource_url)
                
                # Yield a request for the resource page
                yield scrapy.Request(
                    url=resource_url,
                    callback=self.parse_resource_page
                )
        
        # Process procedure blocks
        for block in soup.find_all('div', class_='procedure-block'):
            result = self.process_procedure_block(block)
            if result and 'pdf_url' in result:
                pdf_url = result['pdf_url']
                # Make sure the URL is absolute
                if not pdf_url.startswith(('http://', 'https://')):
                    pdf_url = response.urljoin(pdf_url)
                
                # Yield a request for the PDF
                yield scrapy.Request(
                    url=pdf_url,
                    callback=self.parse_pdf,
                    meta={
                        'procedure_code': result.get('procedure_code'),
                        'procedure_name': result.get('procedure_name')
                    }
                )

    def parse_resource_page(self, response):
        """Parse a resource page for additional PDFs and information."""
        logger.info(f"Parsing resource page: {response.url}")
        soup = BeautifulSoup(response.body, 'html.parser')
        
        # Find PDF links
        for link in soup.find_all('a', href=re.compile(r'\.pdf$')):
            pdf_url = link.get('href')
            if pdf_url:
                # Make sure the URL is absolute
                if not pdf_url.startswith(('http://', 'https://')):
                    pdf_url = response.urljoin(pdf_url)
                
                # Yield a request for the PDF
                yield scrapy.Request(
                    url=pdf_url,
                    callback=self.parse_pdf,
                    meta={'pdf_url': pdf_url}
                )

    def parse_pdf(self, response):
        """Process a downloaded PDF."""
        pdf_url = response.meta.get('pdf_url', response.url)
        logger.info(f"Processing PDF: {pdf_url}")
        
        try:
            # Save the PDF
            pdf_path = self.download_handler.save_pdf(
                response.body, 
                filename=pdf_url.split('/')[-1],
                carrier_name='cigna'
            )
            
            # Yield the result
            yield {
                'procedure_code': response.meta.get('procedure_code'),
                'procedure_name': response.meta.get('procedure_name'),
                'pdf_url': pdf_url,
                'pdf_path': pdf_path
            }
        except Exception as e:
            logger.error(f"Error processing PDF from {pdf_url}: {e}")

    async def parse_pdf_link(self, response, pdf_type):
        """Parse a PDF link and extract procedure information."""
        logger.info(f"Parsing PDF link: {response.url}")
        try:
            # Download the PDF
            pdf_path = await self.download_handler.download_pdf(
                response.url, 
                carrier_name='cigna'
            )
            
            # Extract text from the PDF
            text = self.pdf_processor.extract_text(pdf_path)
            
            # Extract procedure blocks
            # For the test, we'll mock this functionality
            # In a real implementation, we would parse the text to extract procedure blocks
            procedure_blocks = self.extract_procedure_blocks(text)
            
            # Process each procedure block
            for block in procedure_blocks:
                if self.validate_cdt_code(block.get('code')):
                    yield {
                        'code': block.get('code'),
                        'description': block.get('description', ''),
                        'requirements': block.get('requirements', []),
                        'notes': block.get('notes', []),
                        'carrier': 'cigna',
                        'pdf_type': pdf_type,
                        'pdf_path': pdf_path,
                        'url': response.url
                    }
        except Exception as e:
            logger.error(f"Error parsing PDF link {response.url}: {e}")

    def extract_procedure_blocks(self, text):
        """Extract procedure blocks from PDF text."""
        # This is a placeholder implementation
        # In a real implementation, we would parse the text to extract procedure blocks
        return []

    def validate_cdt_code(self, code):
        """Validate a CDT code."""
        if not code:
            return False
        return bool(re.match(r'^D\d{4}$', code))

    def process_procedure_block(self, block, tables=None):
        """
        Process a procedure block to extract relevant information.
        
        Args:
            block: The procedure block to process. Can be a BeautifulSoup element or a dictionary.
            tables: Optional tables data to supplement the procedure block information.
            
        Returns:
            A dictionary with procedure information or None if processing fails.
        """
        try:
            # Handle BeautifulSoup element (from HTML parsing)
            if hasattr(block, 'find'):
                header = block.find('h3').text.strip()
                match = re.match(r'(D\d{4})\s*-\s*(.+)', header)
                if not match:
                    logger.debug(f"Invalid procedure code format: {header}")
                    return None
                    
                code, name = match.groups()
                pdf_link = block.find('a', href=re.compile(r'\.pdf$'))
                
                if not pdf_link:
                    logger.warning(f"No PDF link found for {code}")
                    return None
                    
                return {
                    'procedure_code': code,
                    'procedure_name': name.strip(),
                    'pdf_url': pdf_link['href']
                }
            # Handle dictionary (from PDF parsing)
            else:
                code = block.get('code')
                if not self.validate_cdt_code(code):
                    logger.debug(f"Invalid CDT code: {code}")
                    return None
                
                result = {
                    'code': code,
                    'description': block.get('description', ''),
                    'requirements': block.get('requirements', []),
                    'notes': block.get('notes', [])
                }
                
                # Add table information if available
                if tables:
                    for table in tables:
                        if table.get('code') == code:
                            result.update({
                                'frequency': table.get('frequency', ''),
                                'documentation': table.get('documentation', [])
                            })
                
                return result
        except Exception as e:
            logger.error(f"Error processing procedure block: {e}")
            return None

    def download_pdf(self, url):
        try:
            return self.download_handler.download_pdf(url, carrier_name='cigna')
        except Exception as e:
            logger.error(f"Error downloading PDF from {url}: {e}")
            return None

    def find_table_info(self, code, tables):
        """
        Find and merge all table information for a specific CDT code.
        
        Args:
            code: The CDT code to find information for.
            tables: List of table dictionaries containing code-specific information.
            
        Returns:
            A dictionary with merged information from all tables for the specified code.
        """
        if not code or not tables:
            return {}
            
        result = {}
        for table in tables:
            if table.get('code') == code:
                # Merge this table's info into the result
                for key, value in table.items():
                    if key != 'code':  # Skip the code itself
                        result[key] = value
                        
        return result 

    def closed(self, reason):
        """
        Called when the spider is closed.
        
        Args:
            reason: The reason why the spider was closed.
        """
        if reason == 'finished':
            if self.guidelines_found:
                logger.info("Spider finished successfully with guidelines found")
            else:
                logger.warning("Spider finished but no guidelines were found")
        else:
            logger.warning(f"Spider closed with reason: {reason}")
            
        # Perform any cleanup or final processing here
        return 