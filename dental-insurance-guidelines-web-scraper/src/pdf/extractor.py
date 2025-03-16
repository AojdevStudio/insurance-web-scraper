"""
PDF text extraction utilities for the dental insurance guidelines web scraper.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from datetime import datetime

import pdfplumber
from loguru import logger

from ..exceptions import ParsingException

class PDFExtractor:
    """
    Utility class for extracting content from dental insurance guideline PDFs.
    """
    
    def __init__(self):
        """Initialize the PDF extractor."""
        logger.info("Initializing PDFExtractor")
        
    async def extract_text(self, pdf_path: Path) -> str:
        """
        Extract text content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
            
        Raises:
            ParsingException: If text extraction fails
        """
        try:
            text_content = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            
            return '\n'.join(text_content)
        except Exception as e:
            raise ParsingException(f"Failed to extract text from {pdf_path}: {e}")
            
    async def extract_tables(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """
        Extract tables from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing table data
            
        Raises:
            ParsingException: If table extraction fails
        """
        try:
            tables = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table in page_tables:
                            if table and len(table) > 1:  # Has headers and data
                                headers = [h.strip() for h in table[0] if h]
                                for row in table[1:]:
                                    if len(row) == len(headers):
                                        tables.append(dict(zip(headers, row)))
            
            return tables
        except Exception as e:
            raise ParsingException(f"Failed to extract tables from {pdf_path}: {e}") 