import scrapy
from bs4 import BeautifulSoup
import re
from loguru import logger
from ..utils.download_handler import DownloadHandler

class CignaSpider(scrapy.Spider):
    name = 'cigna'
    allowed_domains = ['cigna.com']
    start_urls = ['https://www.cigna.com/dental/coverage-policies']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.download_handler = DownloadHandler()
        logger.info("Initialized Cigna spider")

    def parse(self, response):
        logger.info(f"Parsing page: {response.url}")
        soup = BeautifulSoup(response.body, 'html.parser')
        
        for block in soup.find_all('div', class_='procedure-block'):
            result = self.process_procedure_block(block)
            if result:
                pdf_path = self.download_pdf(result['pdf_url'])
                if pdf_path:
                    yield {
                        'procedure_code': result['procedure_code'],
                        'procedure_name': result['procedure_name'],
                        'pdf_path': pdf_path
                    }
                else:
                    logger.warning(f"Failed to download PDF for {result['procedure_code']}")

    def process_procedure_block(self, block):
        try:
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
        except Exception as e:
            logger.error(f"Error processing procedure block: {e}")
            return None

    def download_pdf(self, url):
        try:
            return self.download_handler.download_pdf(url, carrier_name='cigna')
        except Exception as e:
            logger.error(f"Error downloading PDF from {url}: {e}")
            return None 