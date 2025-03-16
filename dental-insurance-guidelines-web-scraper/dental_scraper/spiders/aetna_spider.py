"""
Spider implementation for scraping Aetna dental insurance guidelines.
"""
from typing import Dict, Generator, Any, List, Tuple
from pathlib import Path
from datetime import datetime
import re

from scrapy.http import Request, Response
from loguru import logger
import pdfplumber
from bs4 import BeautifulSoup

from ..models import CarrierGuidelines, Procedure, DataValidator
from .base_spider import BaseInsuranceSpider


class AetnaSpider(BaseInsuranceSpider):
    """
    Spider for scraping Aetna dental insurance guidelines.
    """
    
    name = 'aetna'
    allowed_domains = ['aetna.com']
    start_urls = ['https://www.aetna.com/health-care-professionals/dental-resources.html']
    
    custom_settings = {
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 7,  # Conservative delay as per carrier requirements
        'ROBOTSTXT_OBEY': True,
        'COOKIES_ENABLED': True,
        'DOWNLOAD_TIMEOUT': 60,  # Extended timeout for PDF downloads
    }
    
    def __init__(self, *args, **kwargs):
        """Initialize the Aetna spider."""
        super().__init__(
            name=self.name,
            allowed_domains=self.allowed_domains,
            start_urls=self.start_urls,
            *args, **kwargs
        )
        self.validator = DataValidator()
        self.pdf_pattern = re.compile(
            r'(?i).*(?:dental|guidelines|documentation).*2024.*\.pdf$'
        )
        # CDT code pattern (D followed by 4 digits)
        self.cdt_pattern = re.compile(r'D\d{4}')
        
    def parse(self, response: Response) -> Generator[Request, None, None]:
        """
        Parse the main dental resources page.
        
        Args:
            response: Response from the main page
            
        Yields:
            Requests for PDF guidelines or next pages to crawl
        """
        # Extract all PDF links
        pdf_links = response.css('a[href*=".pdf"]::attr(href)').getall()
        
        for link in pdf_links:
            if self.pdf_pattern.match(link):
                yield Request(
                    url=response.urljoin(link),
                    callback=self.parse_pdf,
                    errback=self.handle_error,
                    meta={'source_url': response.url}
                )
        
        # Follow pagination or section links
        for href in response.css('a.pagination::attr(href)').getall():
            yield response.follow(
                href,
                callback=self.parse,
                errback=self.handle_error
            )
    
    def parse_pdf(self, response: Response) -> Dict[str, Any]:
        """
        Process downloaded PDF file.
        
        Args:
            response: Response containing PDF data
            
        Returns:
            Dictionary containing extracted guidelines data
        """
        filename = f"aetna_guidelines_{datetime.now().strftime('%Y%m%d')}.pdf"
        pdf_path = self.save_pdf(response.body, filename)
        
        # Extract text and parse guidelines
        procedures = self.extract_procedures(pdf_path)
        
        if not procedures:
            logger.error(f"No procedures extracted from {filename}")
            return None
            
        guidelines_data = {
            'carrier': 'Aetna',
            'year': 2024,
            'source_url': response.meta['source_url'],
            'last_updated': datetime.now().date(),
            'procedures': procedures,
            'metadata': {
                'pdf_filename': filename,
                'pdf_size': len(response.body),
                'extraction_date': datetime.now().isoformat(),
                'quality_metrics': self.generate_quality_report(procedures)
            }
        }
        
        # Validate extracted data
        success, validated_data, errors = self.validator.validate_carrier_data(
            guidelines_data
        )
        
        if not success:
            logger.error(f"Validation failed for {filename}: {errors}")
            return None
        
        # Save metadata alongside PDF
        self.save_metadata(
            validated_data.dict(),
            filename.replace('.pdf', '.json')
        )
        
        return validated_data.dict()
    
    def extract_procedures(self, pdf_path: Path) -> List[Dict]:
        """
        Extract procedures and requirements from PDF.
        
        Args:
            pdf_path: Path to the saved PDF file
            
        Returns:
            List of procedure dictionaries
        """
        procedures = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                        
                    # Find CDT codes and their descriptions
                    cdt_matches = self.cdt_pattern.finditer(text)
                    for match in cdt_matches:
                        procedure = self.extract_procedure_data(
                            text[match.start():],
                            match.group()
                        )
                        if procedure:
                            procedures.append(procedure)
        except Exception as e:
            logger.error(f"Error extracting from PDF {pdf_path}: {str(e)}")
            return []
            
        return procedures
    
    def extract_procedure_data(self, text: str, cdt_code: str) -> Optional[Dict]:
        """Extract single procedure data from text."""
        try:
            # Find the end of the procedure section (next CDT code or end of text)
            next_cdt = self.cdt_pattern.search(text[5:])  # Skip current code
            proc_text = text[:next_cdt.start()] if next_cdt else text
            
            # Split into lines and clean
            lines = [l.strip() for l in proc_text.split('\n') if l.strip()]
            if len(lines) < 2:  # Need at least description and one requirement
                return None
                
            # First line after code is description
            description = lines[0].replace(cdt_code, '').strip()
            
            # Remaining lines are requirements and notes
            requirements = []
            notes = None
            
            for line in lines[1:]:
                if line.lower().startswith('note'):
                    notes = line
                elif line.strip():
                    requirements.append(line)
            
            if not requirements:  # Must have at least one requirement
                return None
                
            return {
                "code": cdt_code,
                "description": description,
                "requirements": self.validator.validate_requirements_format(requirements),
                "notes": notes,
                "effective_date": "2024-01-01"  # Default for 2024 guidelines
            }
        except Exception as e:
            logger.error(f"Error extracting procedure {cdt_code}: {str(e)}")
            return None
    
    def generate_quality_report(self, procedures: List[Dict]) -> Dict:
        """Generate quality metrics for extracted data."""
        total_procs = len(procedures)
        if not total_procs:
            return {"error": "No procedures found"}
            
        metrics = {
            "total_procedures": total_procs,
            "procedures_with_requirements": sum(
                1 for p in procedures if p.get('requirements')
            ),
            "procedures_with_notes": sum(
                1 for p in procedures if p.get('notes')
            ),
            "avg_requirements_per_procedure": sum(
                len(p.get('requirements', [])) for p in procedures
            ) / total_procs,
            "validation_rate": sum(
                1 for p in procedures 
                if self.validator.validate_procedure_data(p)[0]
            ) / total_procs
        }
        
        # Add quality warnings
        warnings = []
        if metrics["validation_rate"] < 0.95:
            warnings.append("High validation failure rate")
        if metrics["avg_requirements_per_procedure"] < 1:
            warnings.append("Low average requirements per procedure")
            
        metrics["warnings"] = warnings
        return metrics 