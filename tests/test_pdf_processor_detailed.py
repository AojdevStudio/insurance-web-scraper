"""
Detailed unit tests for the PDF processor class.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

import pdfplumber

from dental_scraper.utils.pdf_processor import PDFProcessor
from dental_scraper.exceptions import ParsingException


@pytest.fixture
def pdf_processor():
    """Create a PDF processor instance for testing."""
    return PDFProcessor()


@pytest.fixture
def mock_pdf_path():
    """Create a mock PDF path for testing."""
    return Path('test_output/test.pdf')


@pytest.fixture
def mock_pdf_text():
    """Return mock text extracted from a PDF."""
    return """
    D0150 Comprehensive oral evaluation
    
    Requirements:
    - Patient must be new
    - Complete examination required
    
    D0210 Intraoral - complete series
    
    Requirements:
    - Limited to once every 3 years
    - Full mouth series
    """


@pytest.fixture
def mock_pdf_metadata():
    """Return mock PDF metadata."""
    return {
        'Title': 'Test PDF Document',
        'Author': 'Test Author',
        'Creator': 'Test Creator',
        'Producer': 'Test Producer',
        'CreationDate': 'D:20250101000000',
        'ModDate': 'D:20250101000000',
        'num_pages': 5,
        'file_name': 'test.pdf',
        'extraction_date': datetime.now().isoformat(),
        'file_size': 1024
    }


def test_init():
    """Test that the processor initializes correctly."""
    processor = PDFProcessor()
    assert processor is not None
    assert hasattr(processor, 'output_dir')
    assert processor.output_dir.exists()


@patch('pdfplumber.open')
def test_extract_text_success(mock_pdfplumber_open, pdf_processor, mock_pdf_path, mock_pdf_text):
    """Test successful text extraction from a PDF."""
    # Mock the PDF object
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = mock_pdf_text
    mock_pdf.pages = [mock_page]
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf
    
    # Extract text
    text = pdf_processor.extract_text(mock_pdf_path)
    
    # Verify extraction was successful
    assert text == mock_pdf_text
    mock_pdfplumber_open.assert_called_once_with(mock_pdf_path)
    mock_page.extract_text.assert_called_once()


@patch('pdfplumber.open')
def test_extract_text_empty_pdf(mock_pdfplumber_open, pdf_processor, mock_pdf_path):
    """Test handling of empty PDFs."""
    # Mock an empty PDF
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""
    mock_pdf.pages = [mock_page]
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf
    
    # Extract text
    text = pdf_processor.extract_text(mock_pdf_path)
    
    # Verify empty text was handled
    assert text == ""


@patch('pdfplumber.open')
def test_extract_text_exception(mock_pdfplumber_open, pdf_processor, mock_pdf_path):
    """Test error handling during text extraction."""
    # Make pdfplumber.open raise an exception
    mock_pdfplumber_open.side_effect = Exception("Test error")
    
    # Attempt to extract text and expect exception
    with pytest.raises(ParsingException):
        pdf_processor.extract_text(mock_pdf_path)


@patch('pdfplumber.open')
def test_extract_metadata_success(mock_pdfplumber_open, pdf_processor, mock_pdf_path, mock_pdf_metadata):
    """Test successful metadata extraction from a PDF."""
    # Mock the PDF object
    mock_pdf = MagicMock()
    mock_pdf.metadata = {
        'Title': 'Test PDF Document',
        'Author': 'Test Author',
        'Creator': 'Test Creator',
        'Producer': 'Test Producer',
        'CreationDate': 'D:20250101000000',
        'ModDate': 'D:20250101000000'
    }
    mock_pdf.pages = [MagicMock() for _ in range(5)]
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf
    
    # Mock the file_path.stat() call to return file size
    with patch.object(Path, 'stat', return_value=MagicMock(st_size=1024)):
        # Extract metadata
        metadata = pdf_processor.extract_metadata(mock_pdf_path)
    
    # Verify extraction was successful
    assert metadata['Title'] == 'Test PDF Document'
    assert metadata['Author'] == 'Test Author'
    assert metadata['num_pages'] == 5
    assert metadata['file_name'] == mock_pdf_path.name
    assert 'extraction_date' in metadata
    assert metadata['file_size'] == 1024


@patch('pdfplumber.open')
def test_extract_metadata_exception(mock_pdfplumber_open, pdf_processor, mock_pdf_path):
    """Test error handling during metadata extraction."""
    # Make pdfplumber.open raise an exception
    mock_pdfplumber_open.side_effect = Exception("Test error")
    
    # Attempt to extract metadata and expect exception
    with pytest.raises(ParsingException):
        pdf_processor.extract_metadata(mock_pdf_path)


@patch('os.path.join', return_value='organized/test/path.pdf')
@patch('os.makedirs')
@patch('shutil.copy2')
def test_organize_by_provider(mock_copy2, mock_makedirs, mock_join, pdf_processor, mock_pdf_path):
    """Test PDF organization by provider."""
    # Mock metadata
    metadata = {
        'Title': 'Test PDF Document',
        'extraction_date': datetime.now().isoformat()
    }
    
    # Organize PDF
    result = pdf_processor.organize_by_provider(mock_pdf_path, 'test_provider', metadata)
    
    # Verify directory was created and file was copied
    mock_makedirs.assert_called_once()
    mock_copy2.assert_called_once()
    
    # Verify result contains organized paths
    assert 'pdf_path' in result
    assert 'json_path' in result


@patch('pdfplumber.open')
@patch.object(PDFProcessor, 'extract_metadata')
@patch.object(PDFProcessor, 'organize_by_provider')
def test_process_pdf_success(mock_organize, mock_extract_metadata, mock_pdfplumber_open, pdf_processor, mock_pdf_path, mock_pdf_text, mock_pdf_metadata):
    """Test successful PDF processing."""
    # Mock extract_text
    mock_page = MagicMock()
    mock_page.extract_text.return_value = mock_pdf_text
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf
    
    # Mock extract_metadata
    mock_extract_metadata.return_value = mock_pdf_metadata
    
    # Mock organize_by_provider
    mock_organize.return_value = {
        'pdf_path': 'organized/test/path.pdf',
        'json_path': 'organized/test/path.json'
    }
    
    # Process PDF
    result = pdf_processor.process_pdf(mock_pdf_path, provider='test_provider')
    
    # Verify all steps were called
    mock_extract_metadata.assert_called_once_with(mock_pdf_path)
    mock_organize.assert_called_once()
    
    # Verify result structure
    assert result['text_content'] == mock_pdf_text
    assert result['metadata'] == mock_pdf_metadata
    assert result['organized_paths'] == mock_organize.return_value


@patch.object(PDFProcessor, 'extract_text')
def test_process_pdf_exception(mock_extract_text, pdf_processor, mock_pdf_path):
    """Test error handling during PDF processing."""
    # Make extract_text raise an exception
    mock_extract_text.side_effect = ParsingException("Test error")
    
    # Attempt to process PDF and expect exception
    with pytest.raises(ParsingException):
        pdf_processor.process_pdf(mock_pdf_path, provider='test_provider')


@patch('builtins.open', new_callable=mock_open)
@patch('json.dump')
def test_save_metadata(mock_json_dump, mock_file_open, pdf_processor):
    """Test saving metadata to JSON."""
    # Mock metadata
    metadata = {'key': 'value'}
    filename = 'test.json'
    
    # Save metadata
    result = pdf_processor.save_metadata(metadata, filename)
    
    # Verify file was opened and JSON was written
    mock_file_open.assert_called_once()
    mock_json_dump.assert_called_once_with(metadata, mock_file_open(), indent=2)
    
    # Verify result is the file path
    assert result.name == filename


def test_extract_cdt_codes(pdf_processor, mock_pdf_text):
    """Test CDT code extraction from text."""
    # Extract codes
    codes = pdf_processor.extract_cdt_codes(mock_pdf_text)
    
    # Verify codes were extracted
    assert len(codes) == 2
    assert 'D0150' in codes
    assert 'D0210' in codes


@patch('re.findall', return_value=['D0150', 'D0210'])
def test_extract_cdt_codes_with_pattern(mock_findall, pdf_processor):
    """Test CDT code extraction with a specific pattern."""
    # Extract codes
    codes = pdf_processor.extract_cdt_codes("Some text")
    
    # Verify codes were extracted using the pattern
    assert len(codes) == 2
    assert 'D0150' in codes
    assert 'D0210' in codes
    mock_findall.assert_called_once() 