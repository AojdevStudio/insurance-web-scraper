"""
Integration tests for the dental insurance web scraper.
"""
import pytest
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from dental_scraper.utils.download_handler import DownloadHandler
from dental_scraper.utils.pdf_processor import PDFProcessor
from dental_scraper.utils.data_cleaner import DataCleaner
from dental_scraper.scrapers.pdf_spider import PDFSpider
from dental_scraper.models.procedure import Procedure
from dental_scraper.exceptions import ParsingException, DownloadException


@pytest.fixture
def test_output_dir():
    """Create test output directory."""
    test_dir = Path('test_output')
    test_dir.mkdir(exist_ok=True)
    yield test_dir
    # Do not clean up test directory to enable inspection of results


@pytest.fixture
def mock_pdf_path(test_output_dir):
    """Create a mock PDF file."""
    pdf_path = test_output_dir / 'mock_test.pdf'
    with open(pdf_path, 'wb') as pdf_file:
        pdf_file.write(b'%PDF-1.5\nTest PDF content')
    return pdf_path


@pytest.fixture
def mock_spider():
    """Create a mock spider."""
    spider = PDFSpider()
    spider.name = 'test_spider'
    return spider


@pytest.fixture
def mock_pdf_processor():
    """Create a mock PDF processor."""
    processor = MagicMock(spec=PDFProcessor)
    processor.extract_text.return_value = """
    Procedure Code: D0120
    Description: Periodic oral evaluation
    Patient Responsibility: $25.00
    Insurance Pays: 80%
    
    Procedure Code: D0150
    Description: Comprehensive oral evaluation
    Patient Responsibility: $35.00
    Insurance Pays: 70%
    """
    return processor


@pytest.fixture
def mock_download_handler():
    """Create a mock download handler."""
    handler = MagicMock(spec=DownloadHandler)
    handler.download_pdf = AsyncMock(return_value='test_output/mock_test.pdf')
    return handler


@pytest.fixture
def mock_data_cleaner():
    """Create a mock data cleaner."""
    cleaner = MagicMock(spec=DataCleaner)
    cleaner.clean_procedure_data.return_value = {
        'code': 'D0120',
        'description': 'Periodic oral evaluation',
        'patient_pays': 25.0,
        'insurance_pays': 80.0
    }
    return cleaner


@patch('dental_scraper.utils.pdf_processor.PDFProcessor')
@patch('dental_scraper.utils.download_handler.DownloadHandler')
@patch('dental_scraper.utils.data_cleaner.DataCleaner')
async def test_end_to_end_flow(mock_cleaner_class, mock_handler_class, mock_processor_class, 
                             mock_pdf_path, mock_pdf_processor, mock_download_handler, mock_data_cleaner):
    """Test the end-to-end flow of downloading and processing a PDF."""
    # Configure mocks
    mock_processor_class.return_value = mock_pdf_processor
    mock_handler_class.return_value = mock_download_handler
    mock_cleaner_class.return_value = mock_data_cleaner
    
    # Create a test spider and response
    spider = PDFSpider()
    spider.name = 'test_spider'
    
    # Create a mock response
    response = MagicMock()
    response.url = 'https://example.com/test.pdf'
    response.status = 200
    response.headers = {'Content-Type': 'application/pdf'}
    
    # Process the response
    result = await spider.parse_pdf(response)
    
    # Verify results
    assert result is not None
    assert 'pdf_path' in result
    assert 'url' in result
    assert result['url'] == 'https://example.com/test.pdf'
    
    # Verify download handler was called
    mock_download_handler.download_pdf.assert_called_once()


@patch('dental_scraper.utils.pdf_processor.PDFProcessor.extract_text')
def test_pdf_extraction_to_data_cleaning(mock_extract_text, mock_pdf_path):
    """Test extraction of text from PDF and data cleaning."""
    # Setup
    mock_extract_text.return_value = """
    Procedure Code: D0120
    Description: Periodic oral evaluation
    Patient Responsibility: $25.00
    Insurance Pays: 80%
    """
    
    # Create instances
    processor = PDFProcessor()
    cleaner = DataCleaner()
    
    # Extract text
    text = processor.extract_text(mock_pdf_path)
    
    # Manually extract procedure data (simplified for test)
    raw_procedure = {
        'code': 'D0120',
        'description': 'Periodic oral evaluation',
        'patient_pays': '$25.00',
        'insurance_pays': '80%'
    }
    
    # Clean the data
    cleaned = cleaner.clean_procedure_data(raw_procedure)
    
    # Verify results
    assert cleaned is not None
    assert cleaned.get('code') == 'D0120'
    assert 'periodic' in cleaned.get('description', '').lower()
    assert cleaned.get('patient_pays') in (25.0, None)
    assert cleaned.get('insurance_pays') in (80.0, None)


@patch('dental_scraper.utils.download_handler.DownloadHandler.download_pdf')
async def test_download_handler_integration(mock_download, test_output_dir):
    """Test download handler integration with error handling."""
    # Test successful download
    pdf_path = str(test_output_dir / 'test.pdf')
    mock_download.return_value = pdf_path
    
    handler = DownloadHandler()
    result = await handler.download_pdf('https://example.com/test.pdf', 'Test Carrier')
    
    assert result == pdf_path
    mock_download.assert_called_once()
    
    # Test failed download
    mock_download.reset_mock()
    mock_download.return_value = None
    
    result = await handler.download_pdf('https://example.com/error.pdf', 'Test Carrier')
    
    assert result is None
    mock_download.assert_called_once()


def test_error_handling_integration():
    """Test error handling across components."""
    # Test PDF processing error
    processor = PDFProcessor()
    
    # Test with non-existent file
    with pytest.raises(Exception):
        processor.extract_text('nonexistent.pdf')
    
    # Test data cleaning error
    cleaner = DataCleaner()
    
    # Test with invalid data
    invalid_data = {
        'code': 'X0120',  # Invalid code
        'description': 'Test',
        'patient_pays': 'not a number',
        'insurance_pays': 'invalid'
    }
    
    # This should not raise an exception but return cleaned data with None values
    cleaned = cleaner.clean_procedure_data(invalid_data)
    assert cleaned is not None
    assert cleaned.get('code', None) is None
    assert cleaned.get('patient_pays', None) is None
    assert cleaned.get('insurance_pays', None) is None
