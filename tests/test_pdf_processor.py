"""
Tests for the PDF processor module.
"""
import pytest
import json
import os
import re
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock, call
from datetime import datetime

from dental_scraper.utils.pdf_processor import PDFProcessor
from dental_scraper.exceptions import ParsingException

@pytest.fixture
def pdf_processor():
    """Create a PDFProcessor instance for testing."""
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

def test_init_creates_directory():
    """Test that the __init__ method creates the base directory."""
    with patch('pathlib.Path.mkdir') as mock_mkdir:
        processor = PDFProcessor()
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

def test_extract_text_success(pdf_processor, mock_pdf_file, mock_pdf_content):
    """Test successful text extraction from PDF."""
    # Mock pdfplumber.open and the page extraction
    mock_page = MagicMock()
    mock_page.extract_text.return_value = mock_pdf_content
    
    mock_pdf = MagicMock()
    mock_pdf.__enter__.return_value.pages = [mock_page]
    
    with patch('pdfplumber.open', return_value=mock_pdf) as mock_open, \
         patch('pathlib.Path.exists', return_value=True):
        
        result = pdf_processor.extract_text(mock_pdf_file)
        
        # Verify pdfplumber was called with correct file
        mock_open.assert_called_once_with(mock_pdf_file)
        
        # Verify extract_text was called on page
        mock_page.extract_text.assert_called_once()
        
        # Verify result contains the mock content
        assert mock_pdf_content in result

def test_extract_text_failure(pdf_processor, mock_pdf_file):
    """Test handling of text extraction failure."""
    with patch('pdfplumber.open', side_effect=Exception("PDF error")):
        with pytest.raises(ParsingException):
            pdf_processor.extract_text(mock_pdf_file)

def test_extract_metadata_success(pdf_processor, mock_pdf_file):
    """Test successful metadata extraction from PDF."""
    mock_metadata = {
        'Title': 'Test PDF',
        'Author': 'Test Author',
        'Creator': 'Test Creator',
        'Producer': 'Test Producer',
        'CreationDate': 'D:20240101000000'
    }
    
    # Set up the mock PDF context manager
    mock_pdf_obj = MagicMock()
    mock_pdf_obj.metadata = mock_metadata
    mock_pdf_obj.pages = [MagicMock()]
    
    mock_pdf = MagicMock()
    mock_pdf.__enter__.return_value = mock_pdf_obj
    
    with patch('pdfplumber.open', return_value=mock_pdf) as mock_open, \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.stat') as mock_stat:
         
        # Mock the file stat result
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 12345
        mock_stat.return_value = mock_stat_result
        
        result = pdf_processor.extract_metadata(mock_pdf_file)
        
        # Verify pdfplumber was called with correct file
        mock_open.assert_called_once_with(mock_pdf_file)
        
        # Verify metadata was extracted correctly
        assert result['Title'] == 'Test PDF'
        assert result['Author'] == 'Test Author'
        assert result['num_pages'] == len(mock_pdf_obj.pages)
        assert result['file_size'] == 12345

def test_extract_metadata_failure(pdf_processor, mock_pdf_file):
    """Test handling of metadata extraction failure."""
    with patch('pdfplumber.open', side_effect=Exception("PDF error")):
        with pytest.raises(ParsingException):
            pdf_processor.extract_metadata(mock_pdf_file)

def test_organize_by_provider(pdf_processor, mock_pdf_file):
    """Test organizing PDFs by provider."""
    provider = "test_provider"
    metadata = {"Title": "Test PDF", "Date": "2024-01-01"}
    
    # Mock file operations
    with patch('pathlib.Path.mkdir') as mock_mkdir, \
         patch('shutil.copy2') as mock_copy, \
         patch('pathlib.Path.exists', return_value=False), \
         patch('pathlib.Path.with_suffix'), \
         patch('json.dump') as mock_json_dump:
        
        result = pdf_processor.organize_by_provider(
            mock_pdf_file, provider, metadata
        )
        
        # Verify provider directory was created
        mock_mkdir.assert_called()
        
        # Verify file was copied
        mock_copy.assert_called_once()
        
        # Verify metadata was saved
        mock_json_dump.assert_called_once()
        
        # Verify result contains expected keys
        assert 'pdf_path' in result
        assert 'metadata_path' in result

def test_process_pdf(pdf_processor, mock_pdf_file, mock_pdf_content):
    """Test the complete PDF processing workflow."""
    provider = "test_provider"
    metadata = {
        "Title": "Test PDF",
        "Producer": "Test Producer",
        "CreationDate": "D:20240101000000"
    }
    
    organized_result = {
        'pdf_path': Path('organized.pdf'),
        'metadata_path': Path('meta.json')
    }
    
    # Mock all the operations
    with patch.object(pdf_processor, 'extract_text', return_value=mock_pdf_content) as mock_extract_text, \
         patch.object(pdf_processor, 'extract_metadata', return_value=metadata) as mock_extract_metadata, \
         patch.object(pdf_processor, 'organize_by_provider', return_value=organized_result) as mock_organize:
        
        # Execute the method under test
        result = pdf_processor.process_pdf(mock_pdf_file, provider)
        
        # Verify all methods were called correctly
        mock_extract_text.assert_called_once_with(mock_pdf_file)
        mock_extract_metadata.assert_called_once_with(mock_pdf_file)
        mock_organize.assert_called_once_with(mock_pdf_file, provider, metadata)
        
        # Verify the result has the expected structure
        assert 'text_content' in result
        assert result['text_content'] == mock_pdf_content
        assert 'metadata' in result
        assert result['metadata'] == metadata
        assert 'organized_paths' in result
        assert result['organized_paths'] == organized_result

def test_get_provider_pdfs(pdf_processor):
    """Test retrieving PDFs for a specific provider."""
    provider = "test_provider"
    
    # Create mock PDF paths
    mock_paths = [
        Path(f"data/pdfs/{provider}/file1.pdf"),
        Path(f"data/pdfs/{provider}/file2.pdf")
    ]
    
    # Mock metadata
    mock_metadata = {
        "Title": "Test PDF",
        "Date": "2024-01-01"
    }
    
    # Mock directory and glob operations
    with patch('pathlib.Path.glob', return_value=mock_paths), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('pathlib.Path.is_file', return_value=True), \
         patch('json.loads', return_value=mock_metadata), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_metadata))):
        
        results = pdf_processor.get_provider_pdfs(provider)
        
        # Verify results
        assert len(results) == 2
        for result in results:
            assert 'pdf_path' in result
            assert 'metadata' in result
            assert result['metadata'] == mock_metadata

def test_process_content_with_data(pdf_processor):
    """Test processing content with valid data."""
    content = {
        "page_1": "This is page 1 content.",
        "page_2": "This is page 2 content."
    }
    
    result = pdf_processor.process_content(content)
    
    # Verify the result contains all page content
    assert "This is page 1 content." in result
    assert "This is page 2 content." in result
    assert result.endswith("\n\n")

def test_process_content_empty(pdf_processor):
    """Test processing content with empty data."""
    result = pdf_processor.process_content({})
    assert result == ""

def test_extract_procedure_codes(pdf_processor):
    """Test extracting procedure codes from text."""
    text = """
    This document contains procedure codes D0150 and D0210.
    It also has D1234 and D5678 codes.
    """
    
    result = pdf_processor.extract_procedure_codes(text)
    
    # Verify all codes were extracted
    assert len(result) == 4
    assert "D0150" in result
    assert "D0210" in result
    assert "D1234" in result
    assert "D5678" in result

def test_extract_procedure_codes_no_codes(pdf_processor):
    """Test extracting procedure codes from text with no codes."""
    text = "This document does not contain any procedure codes."
    
    result = pdf_processor.extract_procedure_codes(text)
    
    # Verify no codes were found
    assert len(result) == 0
    assert isinstance(result, list)

def test_extract_procedures(pdf_processor):
    """Test extracting full procedure information."""
    text = """
    D0150 Comprehensive oral evaluation
    
    Requirements:
    - Patient must be new
    - Complete examination required
    
    D0210 Intraoral - complete series
    
    Requirements:
    - Limited to once every 3 years
    """
    
    with patch.object(re, 'findall', return_value=["D0150 Comprehensive oral evaluation\n\nRequirements:\n- Patient must be new\n- Complete examination required", 
                                                  "D0210 Intraoral - complete series\n\nRequirements:\n- Limited to once every 3 years"]):
        result = pdf_processor.extract_procedures(text)
        
        # Verify procedures were extracted correctly
        assert len(result) == 2
        
        # Check first procedure
        assert result[0]['code'] == 'D0150'
        assert 'Comprehensive oral evaluation' in result[0]['description']
        assert len(result[0]['requirements']) == 2
        assert 'Patient must be new' in result[0]['requirements']
        
        # Check second procedure
        assert result[1]['code'] == 'D0210'
        assert 'Intraoral - complete series' in result[1]['description']
        assert len(result[1]['requirements']) == 1
        assert 'Limited to once every 3 years' in result[1]['requirements']

def test_extract_procedures_no_procedures(pdf_processor):
    """Test extracting procedures from text with no procedures."""
    text = "This document does not contain any procedure information."
    
    with patch.object(re, 'findall', return_value=[]):
        result = pdf_processor.extract_procedures(text)
        
        # Verify no procedures were found
        assert len(result) == 0
        assert isinstance(result, list)

def test_pdf_to_json(pdf_processor, mock_pdf_file):
    """Test converting PDF to JSON."""
    output_path = "data/json/test.json"
    extracted_data = {"page_1": "Test content"}
    
    with patch.object(pdf_processor, 'extract_text', return_value=extracted_data) as mock_extract, \
         patch('os.makedirs') as mock_makedirs, \
         patch('builtins.open', mock_open()) as mock_file, \
         patch('json.dump') as mock_json_dump:
        
        result = pdf_processor.pdf_to_json(mock_pdf_file, output_path)
        
        # Verify extract_text was called
        mock_extract.assert_called_once_with(mock_pdf_file)
        
        # Verify directory was created
        mock_makedirs.assert_called_once()
        
        # Verify file was opened
        mock_file.assert_called_once()
        
        # Verify JSON was written
        mock_json_dump.assert_called_once()
        
        # Verify result is the output path
        assert result == output_path

def test_pdf_to_json_default_output(pdf_processor, mock_pdf_file):
    """Test converting PDF to JSON with default output path."""
    extracted_data = {"page_1": "Test content"}
    
    with patch.object(pdf_processor, 'extract_text', return_value=extracted_data) as mock_extract, \
         patch('os.makedirs') as mock_makedirs, \
         patch('builtins.open', mock_open()) as mock_file, \
         patch('json.dump') as mock_json_dump, \
         patch('os.getcwd', return_value="/test"):
        
        result = pdf_processor.pdf_to_json(mock_pdf_file)
        
        # Verify extract_text was called
        mock_extract.assert_called_once_with(mock_pdf_file)
        
        # Verify directory was created
        mock_makedirs.assert_called_once()
        
        # Verify file was opened
        mock_file.assert_called_once()
        
        # Verify JSON was written
        mock_json_dump.assert_called_once()
        
        # Verify result contains the expected path
        assert "/test/data/json" in result

def test_batch_process(pdf_processor):
    """Test batch processing of PDFs."""
    pdf_directory = "data/pdfs"
    output_directory = "data/json"
    pdf_files = ["file1.pdf", "file2.pdf"]
    
    with patch('os.makedirs') as mock_makedirs, \
         patch('os.listdir', return_value=pdf_files + ["not_a_pdf.txt"]) as mock_listdir, \
         patch.object(pdf_processor, 'pdf_to_json', return_value="output_path") as mock_pdf_to_json:
        
        result = pdf_processor.batch_process(pdf_directory, output_directory)
        
        # Verify directory was created
        mock_makedirs.assert_called_once_with(output_directory, exist_ok=True)
        
        # Verify directory was listed
        mock_listdir.assert_called_once_with(pdf_directory)
        
        # Verify pdf_to_json was called for each PDF
        assert mock_pdf_to_json.call_count == 2
        mock_pdf_to_json.assert_has_calls([
            call(os.path.join(pdf_directory, "file1.pdf"), os.path.join(output_directory, "file1.json")),
            call(os.path.join(pdf_directory, "file2.pdf"), os.path.join(output_directory, "file2.json"))
        ])
        
        # Verify result contains all processed files
        assert len(result) == 2
        assert all(path == "output_path" for path in result)

def test_batch_process_no_pdfs(pdf_processor):
    """Test batch processing with no PDF files."""
    pdf_directory = "data/pdfs"
    output_directory = "data/json"
    
    with patch('os.makedirs') as mock_makedirs, \
         patch('os.listdir', return_value=["not_a_pdf.txt"]) as mock_listdir, \
         patch.object(pdf_processor, 'pdf_to_json') as mock_pdf_to_json:
        
        result = pdf_processor.batch_process(pdf_directory, output_directory)
        
        # Verify directory was created
        mock_makedirs.assert_called_once_with(output_directory, exist_ok=True)
        
        # Verify directory was listed
        mock_listdir.assert_called_once_with(pdf_directory)
        
        # Verify pdf_to_json was not called
        mock_pdf_to_json.assert_not_called()
        
        # Verify result is an empty list
        assert result == []

def test_batch_process_default_output(pdf_processor):
    """Test batch processing with default output directory."""
    pdf_directory = "data/pdfs"
    pdf_files = ["file1.pdf"]
    
    with patch('os.makedirs') as mock_makedirs, \
         patch('os.listdir', return_value=pdf_files) as mock_listdir, \
         patch.object(pdf_processor, 'pdf_to_json', return_value="output_path") as mock_pdf_to_json, \
         patch('os.getcwd', return_value="/test"):
        
        result = pdf_processor.batch_process(pdf_directory)
        
        # Verify directory was created with default path
        mock_makedirs.assert_called_once_with("/test/data/json", exist_ok=True)
        
        # Verify pdf_to_json was called with correct paths
        mock_pdf_to_json.assert_called_once()
        
        # Verify result contains the processed file
        assert len(result) == 1
        assert result[0] == "output_path" 