from typing import Dict, List, Optional
import logging
import re
from scrapy import Request
from .base_spider import BaseInsuranceSpider
from dental_scraper.processors.pdf_processor import PDFProcessor
from dental_scraper.utils.data_cleaner import DataCleaner

logger = logging.getLogger(__name__)

class MetLifeSpider(BaseInsuranceSpider):
    name = 'metlife'
    allowed_domains = ['metlife.com', 'metdental.com']
    carrier_name = 'MetLife'
    base_url = 'https://www.metlife.com/dental-providers/resources/'
    pdf_enabled = True
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 3,
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_TIMEOUT': 60,
        'COOKIES_ENABLED': True
    }

    def __init__(self, *args, **kwargs):
        super().__init__(name=self.name, 
                         allowed_domains=self.allowed_domains, 
                         start_urls=[self.base_url], 
                         *args, **kwargs)
        self.pdf_processor = PDFProcessor()
        self.data_cleaner = DataCleaner()
        self.metlife_patterns = {
            'procedure_start': r'Procedure\s+(?:Code|Guidelines):\s*D\d{4}',
            'documentation_block': r'Required\s+Documentation:.*?(?=Procedure|Special Considerations|$)',
            'special_notes': r'Special\s+Considerations:.*?(?=\n\n|\Z)'
        }

    def start_requests(self):
        yield Request(
            url=self.base_url,
            callback=self.parse_provider_resources,
            errback=self.handle_error,
            dont_filter=True
        )

    def parse_provider_resources(self, response):
        """Parse the provider resources page to find dental guidelines PDFs."""
        logger.info(f"Parsing provider resources page: {response.url}")
        # Look for links containing '2025' and 'guidelines' or similar keywords
        pdf_links = response.xpath('//a[contains(@href, ".pdf")]/@href').getall()
        
        for link in pdf_links:
            if any(keyword in link.lower() for keyword in ['2025', 'guideline', 'documentation']):
                logger.info(f"Found relevant PDF link: {link}")
                yield Request(
                    url=response.urljoin(link),
                    callback=self.parse_pdf,
                    errback=self.handle_error,
                    meta={'pdf_url': link}
                )

    async def parse_pdf(self, response):
        """Process downloaded PDF and extract dental guidelines."""
        logger.info(f"Processing PDF from: {response.url}")
        try:
            pdf_content = await self.pdf_processor.extract_text(response.body)
            procedures = self.extract_procedures(pdf_content)
            
            logger.info(f"Extracted {len(procedures)} procedures from PDF")
            for procedure in procedures:
                yield self.format_procedure(procedure)
                
        except Exception as e:
            logger.error(f"Error processing PDF from {response.url}: {str(e)}")
            self.handle_error(e)

    def extract_procedures(self, content: str) -> List[Dict]:
        """Extract procedure information from PDF content."""
        logger.info("Extracting procedures from PDF content")
        procedures = []
        # Split content into procedure blocks using the procedure_start pattern
        blocks = self.split_into_procedure_blocks(content)
        logger.debug(f"Found {len(blocks)} procedure blocks")
        
        for block in blocks:
            procedure = self.parse_procedure_block(block)
            if procedure:
                procedures.append(procedure)
                
        return procedures

    def split_into_procedure_blocks(self, content: str) -> List[str]:
        """Split PDF content into individual procedure blocks."""
        logger.info("Splitting PDF content into procedure blocks")
        blocks = []
        
        # Find all matches of procedure start pattern
        matches = list(re.finditer(self.metlife_patterns['procedure_start'], content))
        if not matches:
            logger.warning("No procedure blocks found in content")
            return blocks
            
        # Extract each block (from one procedure start to the next or EOF)
        for i in range(len(matches)):
            start_pos = matches[i].start()
            # If this is the last match, extract to the end of content
            if i == len(matches) - 1:
                end_pos = len(content)
            else:
                end_pos = matches[i + 1].start()
                
            block = content[start_pos:end_pos].strip()
            blocks.append(block)
            
        return blocks

    def parse_procedure_block(self, block: str) -> Optional[Dict]:
        """Parse a single procedure block to extract relevant information."""
        logger.debug(f"Parsing procedure block: {block[:100]}...")
        try:
            # Extract CDT code
            cdt_match = re.search(r'D\d{4}', block)
            if not cdt_match:
                logger.warning("No CDT code found in procedure block")
                return None
                
            cdt_code = cdt_match.group()
            logger.debug(f"Found CDT code: {cdt_code}")
            
            # Extract documentation requirements
            doc_match = re.search(self.metlife_patterns['documentation_block'], block)
            requirements = []
            if doc_match:
                requirements = self.clean_requirements(doc_match.group())
                logger.debug(f"Found requirements: {requirements}")
            else:
                logger.warning(f"No documentation requirements found for {cdt_code}")
                
            # Extract special notes
            notes_match = re.search(self.metlife_patterns['special_notes'], block)
            notes = notes_match.group() if notes_match else None
            if notes:
                # Remove the "Special Considerations:" prefix
                notes = re.sub(r'^Special\s+Considerations:', '', notes).strip()
                logger.debug(f"Found notes: {notes}")
            
            return {
                'code': cdt_code,
                'requirements': requirements,
                'notes': notes
            }
            
        except Exception as e:
            logger.error(f"Error parsing procedure block: {str(e)}")
            return None

    def clean_requirements(self, requirements_text: str) -> List[str]:
        """Clean and normalize requirements text into a list of requirements."""
        logger.debug(f"Cleaning requirements text: {requirements_text[:50]}...")
        # Remove the "Required Documentation:" header
        clean_text = re.sub(r'^Required\s+Documentation:', '', requirements_text).strip()
        
        # Split by bullet points or newlines
        raw_requirements = re.split(r'[•●■◆\n]', clean_text)
        
        # Clean each requirement
        requirements = []
        for req in raw_requirements:
            req = req.strip()
            if req:
                clean_req = self.data_cleaner.clean_text(req)
                requirements.append(clean_req)
                logger.debug(f"Added requirement: {clean_req}")
                
        return requirements

    def format_procedure(self, procedure: Dict) -> Dict:
        """Format the procedure data according to the standard model."""
        logger.debug(f"Formatting procedure: {procedure['code']}")
        return {
            'carrier': self.carrier_name,
            'year': 2025,
            'source_url': self.base_url,
            'code': procedure['code'],
            'requirements': procedure['requirements'],
            'notes': procedure['notes']
        }

    def handle_error(self, failure):
        """Handle any errors during the scraping process."""
        logger.error(f"Error in MetLife spider: {str(failure)}")
        # Implement retry logic or error reporting as needed
        return None 