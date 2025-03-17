import re
from typing import Dict, List, Union
from pathlib import Path
from ..base import PDFProcessor

class CDTExtractor(PDFProcessor):
    """Specialized extractor for CDT codes and related information."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cdt_pattern = re.compile(r'D\d{4}')
        self.requirement_patterns = [
            r'(?:Requirements|Documentation Required|Necessary Information):[\s\S]*?(?=\n\n|\Z)',
            r'Required:.*?(?=\n\n|\Z)',
            r'Documentation:.*?(?=\n\n|\Z)'
        ]
        
    def extract_cdt_codes(self, text: str) -> List[str]:
        """Extract CDT codes from text.
        
        Args:
            text: Text to extract codes from
            
        Returns:
            List[str]: List of unique CDT codes
        """
        codes = self.cdt_pattern.findall(text)
        return sorted(set(codes))
        
    def extract_requirements(self, text: str, code: str) -> List[str]:
        """Extract requirements for a specific CDT code.
        
        Args:
            text: Text to extract requirements from
            code: CDT code to find requirements for
            
        Returns:
            List[str]: List of requirements
        """
        # Find the section containing the code
        code_section = ""
        lines = text.split('\n')
        found_code = False
        
        for line in lines:
            if code in line:
                found_code = True
                code_section = line + '\n'
            elif found_code:
                if self.cdt_pattern.search(line):  # New code section
                    break
                code_section += line + '\n'
                
        requirements = []
        for pattern in self.requirement_patterns:
            matches = re.findall(pattern, code_section, re.IGNORECASE)
            requirements.extend(matches)
            
        # Clean and normalize requirements
        cleaned_reqs = []
        for req in requirements:
            # Split by common bullet points and clean
            items = re.split(r'[•●■◆\-]', req)
            items = [item.strip() for item in items if item.strip()]
            cleaned_reqs.extend(items)
            
        return cleaned_reqs
        
    def process_pdf(self, pdf_path: Union[str, Path]) -> Dict:
        """Process PDF and extract CDT codes with requirements.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict: Extracted CDT codes and their requirements
        """
        # Get base processing results
        base_results = super().process_pdf(pdf_path)
        text = base_results['text']
        
        # Extract CDT codes and requirements
        codes = self.extract_cdt_codes(text)
        results = {
            'cdt_codes': {},
            'metadata': base_results['metadata']
        }
        
        for code in codes:
            requirements = self.extract_requirements(text, code)
            if requirements:  # Only include codes with requirements
                results['cdt_codes'][code] = {
                    'requirements': requirements
                }
                
        return results 