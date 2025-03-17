"""PDF processor module for extracting CDT codes and requirements."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pdfplumber
from loguru import logger

class PDFProcessor:
    def __init__(self):
        """Initialize the PDF processor with regex patterns."""
        self.cdt_pattern = re.compile(r'CDT Code:\s*(D\d{4})')
        self.desc_pattern = re.compile(r'Description:\s*(.+)')
        self.req_pattern = re.compile(r'Requirements:\s*$')
        
    def process_pdf(self, pdf_path: str) -> List[Dict[str, str]]:
        """Process a PDF file to extract CDT codes and requirements.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing CDT codes, descriptions, and requirements
        """
        logger.info(f"Processing PDF: {pdf_path}")
        results = []
        current_code = None
        current_desc = None
        current_reqs = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if not text:
                        continue
                        
                    lines = text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        # Check for CDT code
                        cdt_match = self.cdt_pattern.search(line)
                        if cdt_match:
                            # Save previous code if exists
                            if current_code:
                                results.append({
                                    'cdt_code': current_code,
                                    'description': current_desc or '',
                                    'requirements': current_reqs
                                })
                            
                            current_code = cdt_match.group(1)
                            current_desc = None
                            current_reqs = []
                            continue
                            
                        # Check for description
                        desc_match = self.desc_pattern.search(line)
                        if desc_match:
                            current_desc = desc_match.group(1)
                            continue
                            
                        # Check for requirements
                        if line.startswith('- ') or line.startswith('• '):
                            current_reqs.append(line[2:].strip())
                            
                # Add the last code
                if current_code:
                    results.append({
                        'cdt_code': current_code,
                        'description': current_desc or '',
                        'requirements': current_reqs
                    })
                    
            logger.info(f"Successfully processed PDF. Found {len(results)} CDT codes.")
            return results
            
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return []
            
    def validate_cdt_code(self, code: str) -> bool:
        """Validate if a string matches CDT code format (D followed by 4 digits)."""
        return bool(re.match(r'^D\d{4}$', code)) 