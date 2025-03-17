"""
PDF text extraction utilities for the dental insurance guidelines web scraper.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
from datetime import datetime
import os
import asyncio
from concurrent.futures import ProcessPoolExecutor
import functools
import hashlib

import pdfplumber
from loguru import logger

from ..exceptions import ParsingException

class PDFExtractor:
    """
    Utility class for extracting content from dental insurance guideline PDFs.
    """
    
    def __init__(self, chunk_size: int = 5, cache_dir: Optional[str] = None):
        """
        Initialize the PDF extractor.
        
        Args:
            chunk_size: Number of pages to process at once
            cache_dir: Directory to store cache files. If None, caching is disabled.
        """
        logger.info("Initializing PDFExtractor")
        self.chunk_size = chunk_size
        self.cache_dir = cache_dir
        
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
            logger.info(f"Using cache directory: {self.cache_dir}")
    
    def _get_cache_path(self, pdf_path: Path, operation: str) -> Optional[Path]:
        """Generate a cache file path for a PDF."""
        if not self.cache_dir:
            return None
            
        pdf_hash = hashlib.md5(str(pdf_path).encode()).hexdigest()
        return Path(self.cache_dir) / f"{pdf_hash}_{operation}.json"
    
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
        # Check cache first
        cache_path = self._get_cache_path(pdf_path, "text")
        if cache_path and cache_path.exists():
            logger.info(f"Using cached text for {pdf_path}")
            try:
                with open(cache_path, 'r') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")
        
        try:
            text_content = []
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                chunks = [range(i, min(i + self.chunk_size, total_pages)) 
                         for i in range(0, total_pages, self.chunk_size)]
                
                # Process chunks in parallel
                loop = asyncio.get_event_loop()
                with ProcessPoolExecutor() as executor:
                    tasks = []
                    for chunk in chunks:
                        task = loop.run_in_executor(
                            executor,
                            self._process_page_chunk,
                            pdf_path,
                            chunk
                        )
                        tasks.append(task)
                    
                    chunk_results = await asyncio.gather(*tasks)
                    for result in chunk_results:
                        text_content.extend(result)
            
            full_text = '\n'.join(text_content)
            
            # Save to cache
            if cache_path:
                try:
                    with open(cache_path, 'w') as f:
                        f.write(full_text)
                except Exception as e:
                    logger.warning(f"Failed to write cache: {e}")
            
            return full_text
        except Exception as e:
            raise ParsingException(f"Failed to extract text from {pdf_path}: {e}")
    
    def _process_page_chunk(self, pdf_path: Path, page_range: range) -> List[str]:
        """Process a chunk of pages and extract text."""
        result = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i in page_range:
                    page = pdf.pages[i]
                    text = page.extract_text()
                    if text:
                        result.append(text)
            return result
        except Exception as e:
            logger.error(f"Error processing page chunk {page_range}: {e}")
            return []
            
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
        # Check cache first
        cache_path = self._get_cache_path(pdf_path, "tables")
        if cache_path and cache_path.exists():
            logger.info(f"Using cached tables for {pdf_path}")
            try:
                with open(cache_path, 'r') as f:
                    return json.loads(f.read())
            except Exception as e:
                logger.warning(f"Failed to read table cache: {e}")
        
        try:
            tables = []
            
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                chunks = [range(i, min(i + self.chunk_size, total_pages)) 
                         for i in range(0, total_pages, self.chunk_size)]
                
                # Process chunks in parallel
                loop = asyncio.get_event_loop()
                with ProcessPoolExecutor() as executor:
                    tasks = []
                    for chunk in chunks:
                        task = loop.run_in_executor(
                            executor,
                            self._process_table_chunk,
                            pdf_path,
                            chunk
                        )
                        tasks.append(task)
                    
                    chunk_results = await asyncio.gather(*tasks)
                    for result in chunk_results:
                        tables.extend(result)
            
            # Save to cache
            if cache_path:
                try:
                    with open(cache_path, 'w') as f:
                        f.write(json.dumps(tables))
                except Exception as e:
                    logger.warning(f"Failed to write table cache: {e}")
            
            return tables
        except Exception as e:
            raise ParsingException(f"Failed to extract tables from {pdf_path}: {e}")
    
    def _process_table_chunk(self, pdf_path: Path, page_range: range) -> List[Dict[str, Any]]:
        """Process a chunk of pages and extract tables."""
        tables = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i in page_range:
                    page = pdf.pages[i]
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
            logger.error(f"Error processing table chunk {page_range}: {e}")
            return [] 