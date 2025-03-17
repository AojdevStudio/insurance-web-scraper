"""
Unit tests for the PDF processor.
"""
import pytest
import json
import os
import re
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock, call
from datetime import datetime
import io

from dental_scraper.utils.pdf_processor import PDFProcessor
from dental_scraper.exceptions import ParsingException

@pytest.fixture
def pdf_processor():
    """Create a PDF processor instance for testing."""
    return PDFProcessor()

@pytest.fixture
def mock_pdf_file():
    """Return a Path to a mock PDF file."""
    return Path("data/pdfs/test.pdf")

@pytest.fixture
def mock_pdf_content():
    """Return mock PDF content for testing."""
    return """
    D0150 Comprehensive oral evaluation
    
    Requirements:
    - Patient must be new
    - Complete examination required
    
    D0210 Intraoral - complete series
    
    Requirements:
    - Limited to once every 3 years
    """

@pytest.fixture
def sample_pdf_path():
    """Return a sample PDF path for testing."""
    return os.path.join('test_output', 'sample.pdf')

@pytest.fixture
def sample_text():
    """Return sample extracted text from a PDF."""
    return """
    Procedure Code: D0120
    Description: Periodic oral evaluation - established patient
    
    Patient Responsibility: $25.00
    Insurance Pays: 80%
    
    Procedure Code: D0274
    Description: Bitewings - four films
    
    Patient Responsibility: $35.00
    Insurance Pays: 70%
    """

def test_init_creates_directory():
    """Test that the __init__ method creates the base directory."""
    base_dir = 'test_output'
    with patch('os.makedirs') as mock_makedirs:
        processor = PDFProcessor(base_dir=base_dir)
        mock_makedirs.assert_called_once_with(base_dir, exist_ok=True)

@patch('dental_scraper.utils.pdf_processor.pdfplumber.open')
def test_extract_text(mock_open, pdf_processor, sample_pdf_path, sample_text):
    """Test text extraction from a PDF."""
    # Mock the PDF object
    mock_pdf = MagicMock()
    mock_pdf.__enter__.return_value.pages = [
        MagicMock(extract_text=MagicMock(return_value=sample_text))
    ]
    mock_open.return_value = mock_pdf
    
    # Extract text
    result = pdf_processor.extract_text(sample_pdf_path)
    
    # Verify the result
    assert result == sample_text
    mock_open.assert_called_once_with(sample_pdf_path)

@patch('dental_scraper.utils.pdf_processor.pdfplumber.open')
def test_extract_text_multiple_pages(mock_open, pdf_processor, sample_pdf_path):
    """Test text extraction from multiple pages."""
    # Mock PDF with multiple pages
    mock_pdf = MagicMock()
    mock_pdf.__enter__.return_value.pages = [
        MagicMock(extract_text=MagicMock(return_value="Page 1 content")),
        MagicMock(extract_text=MagicMock(return_value="Page 2 content")),
        MagicMock(extract_text=MagicMock(return_value="Page 3 content"))
    ]
    mock_open.return_value = mock_pdf
    
    # Extract text
    result = pdf_processor.extract_text(sample_pdf_path)
    
    # Verify all pages were extracted and concatenated
    assert "Page 1 content" in result
    assert "Page 2 content" in result
    assert "Page 3 content" in result

@patch('dental_scraper.utils.pdf_processor.pdfplumber.open', side_effect=Exception("PDF error"))
def test_extract_text_error(mock_open, pdf_processor, sample_pdf_path):
    """Test handling errors during text extraction."""
    # Attempt to extract text and expect exception
    with pytest.raises(ParsingException):
        pdf_processor.extract_text(sample_pdf_path)

@patch('os.path.exists', return_value=False)
def test_extract_text_file_not_found(mock_exists, pdf_processor, sample_pdf_path):
    """Test handling missing PDF files."""
    # Attempt to extract text and expect exception
    with pytest.raises(ParsingException):
        pdf_processor.extract_text(sample_pdf_path)

@patch('dental_scraper.utils.pdf_processor.pdfplumber.open')
def test_extract_table(mock_open, pdf_processor, sample_pdf_path):
    """Test table extraction from a PDF."""
    # Mock table data
    mock_table = [
        ['Header1', 'Header2', 'Header3'],
        ['Value1', 'Value2', 'Value3'],
        ['Value4', 'Value5', 'Value6'],
    ]
    
    # Mock the PDF object
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_tables.return_value = [mock_table]
    mock_pdf.__enter__.return_value.pages = [mock_page]
    mock_open.return_value = mock_pdf
    
    # Extract tables
    result = pdf_processor.extract_tables(sample_pdf_path)
    
    # Verify the result
    assert len(result) == 1
    assert result[0] == mock_table
    mock_open.assert_called_once_with(sample_pdf_path)

@patch('dental_scraper.utils.pdf_processor.pdfplumber.open')
def test_extract_tables_multiple_pages(mock_open, pdf_processor, sample_pdf_path):
    """Test table extraction from multiple pages."""
    # Mock tables for multiple pages
    mock_table1 = [['Table1Header', 'Table1Value']]
    mock_table2 = [['Table2Header', 'Table2Value']]
    
    # Mock the PDF object
    mock_pdf = MagicMock()
    mock_page1 = MagicMock()
    mock_page1.extract_tables.return_value = [mock_table1]
    
    mock_page2 = MagicMock()
    mock_page2.extract_tables.return_value = [mock_table2]
    
    mock_pdf.__enter__.return_value.pages = [mock_page1, mock_page2]
    mock_open.return_value = mock_pdf
    
    # Extract tables
    result = pdf_processor.extract_tables(sample_pdf_path)
    
    # Verify results
    assert len(result) == 2
    assert result[0] == mock_table1
    assert result[1] == mock_table2

@patch('dental_scraper.utils.pdf_processor.pdfplumber.open', side_effect=Exception("PDF error"))
def test_extract_tables_error(mock_open, pdf_processor, sample_pdf_path):
    """Test handling errors during table extraction."""
    # Attempt to extract tables and expect exception
    with pytest.raises(ParsingException):
        pdf_processor.extract_tables(sample_pdf_path)

@patch('dental_scraper.utils.pdf_processor.pdfplumber.open')
def test_extract_tables_no_tables(mock_open, pdf_processor, sample_pdf_path):
    """Test behavior when no tables are found."""
    # Mock empty table list
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_tables.return_value = []
    mock_pdf.__enter__.return_value.pages = [mock_page]
    mock_open.return_value = mock_pdf
    
    # Extract tables
    result = pdf_processor.extract_tables(sample_pdf_path)
    
    # Verify empty list is returned
    assert result == []

@patch('dental_scraper.utils.pdf_processor.PyPDF2.PdfReader')
def test_count_pages(mock_pdf_reader, pdf_processor, sample_pdf_path):
    """Test counting pages in a PDF."""
    # Mock PDF with 3 pages
    mock_pdf = MagicMock()
    mock_pdf.pages = [None, None, None]  # 3 pages
    mock_pdf_reader.return_value = mock_pdf
    
    # Count pages
    with patch('builtins.open', mock_open()):
        count = pdf_processor.count_pages(sample_pdf_path)
    
    # Verify count is correct
    assert count == 3

@patch('dental_scraper.utils.pdf_processor.PyPDF2.PdfReader')
def test_count_pages_empty_pdf(mock_pdf_reader, pdf_processor, sample_pdf_path):
    """Test counting pages in an empty PDF."""
    # Mock empty PDF
    mock_pdf = MagicMock()
    mock_pdf.pages = []  # 0 pages
    mock_pdf_reader.return_value = mock_pdf
    
    # Count pages
    with patch('builtins.open', mock_open()):
        count = pdf_processor.count_pages(sample_pdf_path)
    
    # Verify count is correct
    assert count == 0

@patch('dental_scraper.utils.pdf_processor.PyPDF2.PdfReader', side_effect=Exception("PDF error"))
def test_count_pages_error(mock_pdf_reader, pdf_processor, sample_pdf_path):
    """Test handling errors during page counting."""
    # Attempt to count pages and expect exception
    with patch('builtins.open', mock_open()):
        with pytest.raises(ParsingException):
            pdf_processor.count_pages(sample_pdf_path)

@patch('dental_scraper.utils.pdf_processor.re.findall')
@patch('dental_scraper.utils.pdf_processor.PDFProcessor.extract_text')
def test_extract_procedure_codes(mock_extract_text, mock_findall, pdf_processor, sample_pdf_path):
    """Test extracting procedure codes from PDF text."""
    # Mock text extraction and regex search
    mock_extract_text.return_value = "Text with D0120 and D0274 codes"
    mock_findall.return_value = ["D0120", "D0274"]
    
    # Extract procedure codes
    result = pdf_processor.extract_procedure_codes(sample_pdf_path)
    
    # Verify codes were extracted
    assert result == ["D0120", "D0274"]
    mock_extract_text.assert_called_once_with(sample_pdf_path)

@patch('dental_scraper.utils.pdf_processor.re.findall', return_value=[])
@patch('dental_scraper.utils.pdf_processor.PDFProcessor.extract_text')
def test_extract_procedure_codes_no_matches(mock_extract_text, mock_findall, pdf_processor, sample_pdf_path):
    """Test behavior when no procedure codes are found."""
    # Mock text extraction with no procedure codes
    mock_extract_text.return_value = "Text with no procedure codes"
    
    # Extract procedure codes
    result = pdf_processor.extract_procedure_codes(sample_pdf_path)
    
    # Verify empty list is returned
    assert result == []

@patch('dental_scraper.utils.pdf_processor.PDFProcessor.extract_text', side_effect=ParsingException("Error"))
def test_extract_procedure_codes_error(mock_extract_text, pdf_processor, sample_pdf_path):
    """Test handling errors during procedure code extraction."""
    # Attempt to extract procedure codes and expect exception
    with pytest.raises(ParsingException):
        pdf_processor.extract_procedure_codes(sample_pdf_path)

@patch('dental_scraper.utils.pdf_processor.pdfplumber.open')
def test_is_valid_pdf_valid(mock_open, pdf_processor, sample_pdf_path):
    """Test validation of a valid PDF."""
    # Mock successful PDF opening
    mock_pdf = MagicMock()
    mock_open.return_value = mock_pdf
    
    # Validate PDF
    result = pdf_processor.is_valid_pdf(sample_pdf_path)
    
    # Verify PDF is valid
    assert result is True

@patch('dental_scraper.utils.pdf_processor.pdfplumber.open', side_effect=Exception("PDF error"))
def test_is_valid_pdf_invalid(mock_open, pdf_processor, sample_pdf_path):
    """Test validation of an invalid PDF."""
    # Validate PDF
    result = pdf_processor.is_valid_pdf(sample_pdf_path)
    
    # Verify PDF is invalid
    assert result is False

@patch('os.path.exists', return_value=False)
def test_is_valid_pdf_not_found(mock_exists, pdf_processor, sample_pdf_path):
    """Test validation of a non-existent PDF."""
    # Validate PDF
    result = pdf_processor.is_valid_pdf(sample_pdf_path)
    
    # Verify PDF is invalid
    assert result is False 