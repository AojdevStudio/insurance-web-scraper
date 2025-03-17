"""
PDF processing utilities.

This module contains functions to extract text from PDF files and convert it to JSON.
"""

import os
import json
import re
import PyPDF2
import pdfplumber
import hashlib
import asyncio
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path
from loguru import logger
from typing import Dict, List, Any, Optional, Tuple, Union
import time
import psutil


def extract_text_with_pypdf2(pdf_path):
    """
    Extract text from a PDF file using PyPDF2.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        dict: Dictionary containing the extracted text with page numbers as keys
    """
    result = {}
    
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        num_pages = len(reader.pages)
        
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            text = page.extract_text()
            result[f"page_{page_num + 1}"] = text
    
    return result


def extract_text_with_pdfplumber(pdf_path):
    """
    Extract text from a PDF file using pdfplumber.
    
    This function requires the pdfplumber package to be installed.
    It generally provides better text extraction than PyPDF2 for complex layouts.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        dict: Dictionary containing the extracted text with page numbers as keys
    """
    result = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            result[f"page_{page_num + 1}"] = text
    
    return result


def pdf_to_json(pdf_path, output_path=None, method="pypdf2"):
    """
    Convert a PDF file to a JSON file.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_path (str, optional): Path to save the JSON file. If None, the output is saved in the same directory as the PDF file.
        method (str, optional): Method to use for text extraction. Default is "pypdf2".
        
    Returns:
        str: Path to the saved JSON file
    """
    if method.lower() == "pypdf2":
        extracted_text = extract_text_with_pypdf2(pdf_path)
    elif method.lower() == "pdfplumber":
        extracted_text = extract_text_with_pdfplumber(pdf_path)
    else:
        raise ValueError("Method must be either 'pypdf2' or 'pdfplumber'")
    
    # If output_path is not provided, save the output in the same directory as the PDF file
    if output_path is None:
        output_path = pdf_path.replace(".pdf", ".json")
    
    with open(output_path, "w") as f:
        json.dump(extracted_text, f, indent=4)
    
    return output_path


def batch_process_pdfs(pdf_directory, output_directory=None, method="pypdf2"):
    """
    Process all PDF files in a directory.
    
    Args:
        pdf_directory (str): Directory containing PDF files
        output_directory (str, optional): Directory to save the output JSON files. If None, the output is saved in the same directory as the PDF files.
        method (str, optional): Method to use for text extraction. Default is "pypdf2".
        
    Returns:
        list: List of paths to the saved JSON files
    """
    pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith(".pdf")]
    output_files = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        
        if output_directory is not None:
            output_file = os.path.join(output_directory, pdf_file.replace(".pdf", ".json"))
        else:
            output_file = None
        
        output_path = pdf_to_json(pdf_path, output_file, method)
        output_files.append(output_path)
    
    return output_files


class PerformanceMonitor:
    """
    Utility class for monitoring performance metrics of PDF processing.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.metrics = {}
    
    def start(self):
        """Start monitoring performance."""
        self.start_time = time.time()
        self.start_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)  # MB
    
    def stop(self):
        """Stop monitoring performance and calculate metrics."""
        self.end_time = time.time()
        self.end_memory = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)  # MB
        
        self.metrics = {
            "execution_time": self.end_time - self.start_time,
            "memory_used": self.end_memory - self.start_memory,
            "peak_memory": self.end_memory,
        }
        
        return self.metrics
    
    def log_metrics(self, operation: str):
        """Log performance metrics."""
        logger.info(f"Performance metrics for {operation}:")
        logger.info(f"Execution time: {self.metrics['execution_time']:.2f} seconds")
        logger.info(f"Memory used: {self.metrics['memory_used']:.2f} MB")
        logger.info(f"Peak memory: {self.metrics['peak_memory']:.2f} MB")


class PDFProcessor:
    """
    Process PDF files for dental insurance guidelines extraction.
    """
    
    def __init__(self, cache_dir: Optional[str] = None, max_workers: int = None):
        """
        Initialize the PDF processor.
        
        Args:
            cache_dir: Directory to store cache files. If None, caching is disabled.
            max_workers: Maximum number of workers for parallel processing. 
                         If None, uses the number of processors on the machine.
        """
        logger.info("Initializing PDFProcessor")
        self.cache_dir = cache_dir
        self.max_workers = max_workers or os.cpu_count()
        
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
            logger.info(f"Using cache directory: {self.cache_dir}")
            
        self.monitor = PerformanceMonitor()
    
    def _get_cache_path(self, pdf_path: Union[str, Path], operation: str) -> Optional[Path]:
        """Generate a cache file path for a PDF."""
        if not self.cache_dir:
            return None
            
        pdf_hash = hashlib.md5(str(pdf_path).encode()).hexdigest()
        return Path(self.cache_dir) / f"{pdf_hash}_{operation}.json"
    
    def _determine_best_method(self, pdf_path: Union[str, Path]) -> str:
        """
        Determine the best extraction method based on PDF characteristics.
        
        Simple PDFs work well with PyPDF2 which is faster.
        Complex PDFs with tables and multiple columns need pdfplumber.
        """
        try:
            # Check file size - larger PDFs often have complex layouts
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # Size in MB
            
            # Check if the PDF has images or complex layouts
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                first_page = reader.pages[0]
                
                # Check for /XObject in resources, which often indicates images
                has_images = False
                if hasattr(first_page, 'resources') and '/XObject' in first_page.resources:
                    has_images = True
                
                # Try to determine if it has multiple columns using extracted text
                text = first_page.extract_text()
                has_multiple_columns = False
                if text:
                    lines = text.split('\n')
                    if len(lines) > 5:
                        # Check if there are short lines in a pattern that suggests columns
                        short_lines = [line for line in lines if len(line) < 30]
                        if len(short_lines) > len(lines) * 0.5:
                            has_multiple_columns = True
            
            # Decision logic
            if file_size > 10 or has_images or has_multiple_columns:
                return "pdfplumber"
            return "pypdf2"
        except Exception as e:
            logger.warning(f"Error determining extraction method: {e}, defaulting to pdfplumber")
            return "pdfplumber"
    
    async def extract_text(self, pdf_path: Union[str, Path], method: Optional[str] = None) -> Dict[str, str]:
        """
        Extract text from a PDF file with performance monitoring.
        
        Args:
            pdf_path: Path to the PDF file
            method: Method to use for extraction (pypdf2 or pdfplumber). 
                    If None, the best method is automatically determined.
            
        Returns:
            dict: Dictionary containing the extracted text with page numbers as keys
        """
        pdf_path = str(pdf_path)
        logger.info(f"Extracting text from {pdf_path}")
        
        # Check cache first
        cache_path = self._get_cache_path(pdf_path, "text")
        if cache_path and cache_path.exists():
            logger.info(f"Using cached text for {pdf_path}")
            try:
                with open(cache_path, 'r') as f:
                    return json.loads(f.read())
            except Exception as e:
                logger.warning(f"Failed to read cache: {e}")
        
        # Auto-select method if not specified
        if method is None:
            method = self._determine_best_method(pdf_path)
        
        logger.info(f"Using extraction method: {method}")
        
        self.monitor.start()
        
        try:
            if method.lower() == "pypdf2":
                result = extract_text_with_pypdf2(pdf_path)
            elif method.lower() == "pdfplumber":
                result = extract_text_with_pdfplumber(pdf_path)
            else:
                raise ValueError("Method must be either 'pypdf2' or 'pdfplumber'")
                
            # Save to cache
            if cache_path:
                try:
                    with open(cache_path, 'w') as f:
                        f.write(json.dumps(result))
                except Exception as e:
                    logger.warning(f"Failed to write cache: {e}")
                    
            return result
        finally:
            self.monitor.stop()
            self.monitor.log_metrics(f"text extraction with {method}")
    
    async def pdf_to_json(self, pdf_path: Union[str, Path], output_path: Optional[str] = None, 
                     method: Optional[str] = None) -> str:
        """
        Convert a PDF file to a JSON file with performance monitoring.
        
        Args:
            pdf_path: Path to the PDF file
            output_path: Path to save the JSON file
            method: Method to use for text extraction. If None, auto-selects.
            
        Returns:
            str: Path to the saved JSON file
        """
        pdf_path = str(pdf_path)
        logger.info(f"Converting {pdf_path} to JSON")
        
        self.monitor.start()
        
        try:
            # Extract text
            extracted_text = await self.extract_text(pdf_path, method)
            
            # If output_path is not provided, save the output in the same directory as the PDF file
            if output_path is None:
                output_path = pdf_path.replace(".pdf", ".json")
            
            with open(output_path, "w") as f:
                json.dump(extracted_text, f, indent=4)
            
            return output_path
        finally:
            self.monitor.stop()
            self.monitor.log_metrics("pdf to json conversion")
    
    async def batch_process(self, pdf_directory: Union[str, Path], 
                        output_directory: Optional[Union[str, Path]] = None,
                        method: Optional[str] = None) -> List[str]:
        """
        Process all PDF files in a directory in parallel.
        
        Args:
            pdf_directory: Directory containing PDF files
            output_directory: Directory to save JSON files
            method: Method to use for text extraction. If None, auto-selects.
            
        Returns:
            list: Paths to all processed JSON files
        """
        pdf_directory = str(pdf_directory)
        logger.info(f"Batch processing PDFs in {pdf_directory}")
        
        self.monitor.start()
        
        try:
            pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith(".pdf")]
            output_files = []
            
            # Process PDFs in parallel
            tasks = []
            for pdf_file in pdf_files:
                pdf_path = os.path.join(pdf_directory, pdf_file)
                
                if output_directory is not None:
                    output_file = os.path.join(str(output_directory), pdf_file.replace(".pdf", ".json"))
                else:
                    output_file = None
                
                task = self.pdf_to_json(pdf_path, output_file, method)
                tasks.append(task)
            
            # Wait for all tasks to complete
            output_files = await asyncio.gather(*tasks)
            
            return output_files
        finally:
            self.monitor.stop()
            self.monitor.log_metrics("batch processing")
    
    async def process_content(self, content: Dict[str, str]) -> str:
        """
        Process the extracted PDF content into a structured format.
        
        Args:
            content: The extracted PDF content with page numbers as keys
            
        Returns:
            str: The combined content as a single string
        """
        logger.debug("Processing extracted content")
        if not content:
            return ""
        
        combined_text = ""
        for page_num in sorted(content.keys()):
            combined_text += content[page_num] + "\n\n"
        
        return combined_text

    @lru_cache(maxsize=100)
    def extract_procedure_codes(self, text: str) -> List[str]:
        """
        Extract CDT procedure codes from text.
        
        Args:
            text: The text to extract codes from
            
        Returns:
            list: List of extracted procedure codes
        """
        logger.debug("Extracting procedure codes")
        
        # Define the pattern for CDT procedure codes (D followed by 4 digits)
        pattern = r'D\d{4}'
        
        # Find all matches in the text
        matches = re.findall(pattern, text)
        
        # Remove duplicates and sort
        unique_codes = sorted(list(set(matches)))
        
        return unique_codes

    async def extract_procedures(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract procedure information from text.
        
        Args:
            text: The text to extract procedures from
            
        Returns:
            list: List of procedure dictionaries
        """
        logger.debug("Extracting procedures")
        
        # Get procedure codes
        codes = self.extract_procedure_codes(text)
        
        procedures = []
        
        # Process each code
        for code in codes:
            # Find text sections containing the code
            pattern = fr'{code}[\s\S]{{10,1000}}?(?=D\d{{4}}|\Z)'
            matches = re.findall(pattern, text)
            
            if matches:
                description = ""
                requirements = []
                
                # Extract description and requirements from the matched text
                for match in matches:
                    lines = match.split('\n')
                    
                    # Assume the first line contains the description
                    if not description and len(lines) > 0:
                        description = lines[0].replace(code, '').strip()
                    
                    # Look for requirements
                    req_section = False
                    for line in lines[1:]:
                        line = line.strip()
                        if not line:
                            continue
                            
                        if 'requirement' in line.lower() or 'documentation' in line.lower():
                            req_section = True
                            continue
                            
                        if req_section and line and not line.startswith('D'):
                            requirements.append(line)
                
                procedures.append({
                    'code': code,
                    'description': description,
                    'requirements': requirements
                })
        
        return procedures


if __name__ == "__main__":
    # Example usage
    pdf_dir = os.path.join(os.getcwd(), "data", "pdfs")
    json_dir = os.path.join(os.getcwd(), "data", "json")
    
    # Check if there are any PDFs in the directory
    if any(f.lower().endswith(".pdf") for f in os.listdir(pdf_dir)):
        print(f"Processing PDFs in {pdf_dir}")
        processor = PDFProcessor()
        processed = processor.batch_process(pdf_dir, json_dir)
        print(f"Processed {len(processed)} PDF files")
    else:
        print(f"No PDF files found in {pdf_dir}")
        print("Please run the spider first to download some PDFs")
