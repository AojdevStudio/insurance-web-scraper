from pathlib import Path
from typing import Dict, List, Optional, Union
import pdfplumber
from pypdf import PdfReader
import pandas as pd
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

class PDFProcessor:
    """Base class for processing PDF documents with flexible extraction strategies."""
    
    def __init__(
        self,
        max_file_size: int = 50 * 1024 * 1024,  # 50MB limit
        enable_ocr: bool = False,
        table_settings: Optional[Dict] = None
    ):
        """Initialize the PDF processor.
        
        Args:
            max_file_size: Maximum file size in bytes
            enable_ocr: Whether to enable OCR for scanned documents
            table_settings: Custom settings for table extraction
        """
        self.max_file_size = max_file_size
        self.enable_ocr = enable_ocr
        self.table_settings = table_settings or {
            'vertical_strategy': 'text',
            'horizontal_strategy': 'lines',
            'intersection_x_tolerance': 3,
            'intersection_y_tolerance': 3,
            'snap_x_tolerance': 3,
            'snap_y_tolerance': 3,
            'edge_min_length': 3,
            'min_words_vertical': 3,
            'min_words_horizontal': 1
        }
        
    def validate_pdf(self, pdf_path: Union[str, Path]) -> bool:
        """Validate PDF file before processing.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            bool: Whether the PDF is valid
            
        Raises:
            ValueError: If file is too large or invalid
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise ValueError(f"PDF file not found: {pdf_path}")
            
        if pdf_path.stat().st_size > self.max_file_size:
            raise ValueError(f"PDF file too large: {pdf_path.stat().st_size} bytes")
            
        try:
            with pdfplumber.open(pdf_path) as pdf:
                return bool(pdf.pages)
        except Exception as e:
            logger.error(f"Failed to validate PDF {pdf_path}: {str(e)}")
            return False
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def extract_text(self, pdf_path: Union[str, Path]) -> str:
        """Extract text from PDF with fallback mechanisms.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            str: Extracted text content
        """
        pdf_path = Path(pdf_path)
        text = ""
        
        try:
            # Try pdfplumber first
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            logger.warning(f"pdfplumber failed, trying pypdf: {str(e)}")
            # Fallback to pypdf
            try:
                with open(pdf_path, 'rb') as f:
                    reader = PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
            except Exception as e2:
                logger.error(f"All text extraction methods failed: {str(e2)}")
                raise
                
        return text.strip()
        
    def extract_tables(self, pdf_path: Union[str, Path]) -> List[pd.DataFrame]:
        """Extract tables from PDF.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List[pd.DataFrame]: List of extracted tables
        """
        pdf_path = Path(pdf_path)
        tables = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables(table_settings=self.table_settings)
                for table in page_tables:
                    if table:  # Skip empty tables
                        df = pd.DataFrame(table[1:], columns=table[0])
                        tables.append(df)
                        
        return tables
        
    def process_pdf(self, pdf_path: Union[str, Path]) -> Dict:
        """Process PDF file and extract all relevant information.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict: Extracted information including text and tables
        """
        if not self.validate_pdf(pdf_path):
            raise ValueError(f"Invalid PDF file: {pdf_path}")
            
        result = {
            'text': self.extract_text(pdf_path),
            'tables': self.extract_tables(pdf_path),
            'metadata': self._extract_metadata(pdf_path)
        }
        
        return result
        
    def _extract_metadata(self, pdf_path: Union[str, Path]) -> Dict:
        """Extract PDF metadata.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict: PDF metadata
        """
        with open(pdf_path, 'rb') as f:
            reader = PdfReader(f)
            return reader.metadata 