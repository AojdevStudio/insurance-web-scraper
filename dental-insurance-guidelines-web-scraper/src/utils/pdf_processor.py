"""
PDF processing utilities for the dental insurance guidelines web scraper.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import shutil
from datetime import datetime

import pdfplumber
from loguru import logger

from ..exceptions import ParsingException

class PDFProcessor:
    """
    Utility class for processing dental insurance guideline PDFs.
    
    This class provides functionality for:
    - Extracting text from PDFs
    - Extracting metadata
    - Organizing PDFs by provider
    - Saving and managing PDF files
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize the PDF processor.
        
        Args:
            base_dir: Base directory for PDF storage. Defaults to data/pdfs
        """
        self.base_dir = base_dir or Path('data/pdfs')
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_text(self, pdf_path: Path) -> str:
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
                    text_content.append(page.extract_text())
            
            return '\n'.join(text_content)
        except Exception as e:
            raise ParsingException(f"Failed to extract text from {pdf_path}: {e}")
    
    def extract_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing metadata
            
        Raises:
            ParsingException: If metadata extraction fails
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Get PDF metadata
                metadata = pdf.metadata
                
                # Add additional metadata
                metadata.update({
                    'num_pages': len(pdf.pages),
                    'file_name': pdf_path.name,
                    'extraction_date': datetime.now().isoformat(),
                    'file_size': pdf_path.stat().st_size
                })
                
                return metadata
        except Exception as e:
            raise ParsingException(f"Failed to extract metadata from {pdf_path}: {e}")
    
    def organize_by_provider(self, pdf_path: Path, provider: str, 
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Path]:
        """
        Organize a PDF file into provider-specific directory with metadata.
        
        Args:
            pdf_path: Path to the PDF file
            provider: Name of the insurance provider
            metadata: Optional metadata to save with the PDF
            
        Returns:
            Dictionary with paths to organized files
            
        Raises:
            ParsingException: If organization fails
        """
        try:
            # Create provider directory
            provider_dir = self.base_dir / provider
            provider_dir.mkdir(exist_ok=True)
            
            # Generate organized paths
            organized_pdf = provider_dir / pdf_path.name
            metadata_path = organized_pdf.with_suffix('.json')
            
            # Copy PDF to organized location
            shutil.copy2(pdf_path, organized_pdf)
            
            # Save metadata if provided
            if metadata:
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            return {
                'pdf_path': organized_pdf,
                'metadata_path': metadata_path if metadata else None
            }
        except Exception as e:
            raise ParsingException(f"Failed to organize PDF {pdf_path}: {e}")
    
    def process_pdf(self, pdf_path: Path, provider: str) -> Dict[str, Any]:
        """
        Process a PDF file completely - extract text and metadata, and organize.
        
        Args:
            pdf_path: Path to the PDF file
            provider: Name of the insurance provider
            
        Returns:
            Dictionary containing processing results
            
        Raises:
            ParsingException: If processing fails
        """
        try:
            # Extract text and metadata
            text_content = self.extract_text(pdf_path)
            metadata = self.extract_metadata(pdf_path)
            
            # Add extracted text to metadata
            metadata['extracted_text'] = text_content
            
            # Organize the PDF
            organized_paths = self.organize_by_provider(pdf_path, provider, metadata)
            
            return {
                'text_content': text_content,
                'metadata': metadata,
                'organized_paths': organized_paths
            }
        except Exception as e:
            raise ParsingException(f"Failed to process PDF {pdf_path}: {e}")
    
    def get_provider_pdfs(self, provider: str) -> List[Dict[str, Any]]:
        """
        Get all PDFs for a specific provider.
        
        Args:
            provider: Name of the insurance provider
            
        Returns:
            List of dictionaries containing PDF info
        """
        provider_dir = self.base_dir / provider
        if not provider_dir.exists():
            return []
        
        pdf_files = []
        for pdf_path in provider_dir.glob('*.pdf'):
            metadata_path = pdf_path.with_suffix('.json')
            pdf_info = {
                'pdf_path': pdf_path,
                'metadata_path': metadata_path if metadata_path.exists() else None
            }
            
            # Load metadata if available
            if pdf_info['metadata_path']:
                with open(metadata_path) as f:
                    pdf_info['metadata'] = json.load(f)
            
            pdf_files.append(pdf_info)
        
        return pdf_files 