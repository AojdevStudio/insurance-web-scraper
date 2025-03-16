"""
Tests for the download handler module.
"""
import os
import pytest
import aiohttp
import datetime
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from dental_scraper.utils.download_handler import DownloadHandler

@pytest.fixture
def download_handler():
    """Create a DownloadHandler instance for testing."""
    with patch('os.makedirs') as mock_makedirs:
        handler = DownloadHandler(download_dir="/tmp/test_downloads")
        return handler

def test_init():
    """Test initialization of DownloadHandler."""
    with patch('os.makedirs') as mock_makedirs:
        handler = DownloadHandler()
        assert 'downloads' in handler.download_dir
        mock_makedirs.assert_called_once()
        
        # Test with custom download dir
        handler = DownloadHandler(download_dir="/tmp/custom_dir")
        assert handler.download_dir == "/tmp/custom_dir"

def test_ensure_download_dir():
    """Test that _ensure_download_dir creates the directory."""
    with patch('os.makedirs') as mock_makedirs:
        handler = DownloadHandler(download_dir="/tmp/test_dir")
        mock_makedirs.assert_called_once_with("/tmp/test_dir", exist_ok=True)
        
        # Test with exception
        mock_makedirs.reset_mock()
        mock_makedirs.side_effect = PermissionError("Access denied")
        
        with pytest.raises(PermissionError):
            handler._ensure_download_dir()

def test_generate_filename(download_handler):
    """Test filename generation."""
    test_url = "https://example.com/test.pdf"
    test_carrier = "Test Carrier"
    
    filename = download_handler._generate_filename(test_url, test_carrier)
    
    # Check filename format using regex pattern instead of exact match
    assert filename.startswith("testcarrier_")
    assert filename.endswith(".pdf")
    
    # Split the filename by underscore
    parts = filename.split("_")
    assert len(parts) >= 3  # At least carrier_timestamp_hash.pdf
    
    # Verify the carrier part
    assert parts[0] == "testcarrier"
    
    # Verify the last part contains the hash and .pdf
    assert len(parts[-1]) > 5  # hash.pdf

@pytest.mark.asyncio
async def test_download_pdf_success(download_handler):
    """Test successful PDF download."""
    test_url = "https://example.com/test.pdf"
    test_carrier = "Test Carrier"
    expected_filename = "testcarrier_20240101_120000_0123456789.pdf"
    expected_filepath = f"/tmp/test_downloads/{expected_filename}"
    
    # Mock the response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.headers = {'Content-Type': 'application/pdf'}
    
    # Setup content reading - use a proper async iterator
    mock_content = MagicMock()
    
    # Create a proper async method for read
    async def mock_read(size):
        # Return content first time, empty string second time
        mock_read.call_count = getattr(mock_read, 'call_count', 0) + 1
        if mock_read.call_count == 1:
            return b'PDF content chunk 1'
        return b''
    
    mock_content.read = mock_read
    mock_response.content = mock_content
    
    # Mock the session
    mock_session = MagicMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    # Mock the file operations
    with patch('aiohttp.ClientSession', return_value=mock_session), \
         patch('builtins.open', mock_open()) as mock_file, \
         patch('os.path.getsize', return_value=10240), \
         patch.object(download_handler, '_generate_filename', return_value=expected_filename):
        
        result = await download_handler.download_pdf(test_url, test_carrier)
        
        # Verify result is the filepath
        assert result == expected_filepath
        mock_file.assert_called_once_with(expected_filepath, 'wb')

@pytest.mark.asyncio
async def test_download_pdf_failure_status(download_handler):
    """Test PDF download failure due to non-200 status."""
    test_url = "https://example.com/test.pdf"
    test_carrier = "Test Carrier"
    
    # Mock the response with error status
    mock_response = MagicMock()
    mock_response.status = 404
    
    # Mock the session
    mock_session = MagicMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await download_handler.download_pdf(test_url, test_carrier)
        
        # Should return None for failure
        assert result is None

@pytest.mark.asyncio
async def test_download_pdf_invalid_content_type(download_handler):
    """Test PDF download failure due to invalid content type."""
    test_url = "https://example.com/test.pdf"
    test_carrier = "Test Carrier"
    
    # Mock the response with wrong content type
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.headers = {'Content-Type': 'text/html'}
    
    # Mock the session
    mock_session = MagicMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await download_handler.download_pdf(test_url, test_carrier)
        
        # Should return None for failure
        assert result is None

@pytest.mark.asyncio
async def test_download_pdf_file_too_small(download_handler):
    """Test PDF download failure due to file being too small."""
    test_url = "https://example.com/test.pdf"
    test_carrier = "Test Carrier"
    
    # Mock the response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.headers = {'Content-Type': 'application/pdf'}
    
    # Setup content reading with async method
    mock_content = MagicMock()
    
    async def mock_read(size):
        # Return small content first time, empty string second time
        mock_read.call_count = getattr(mock_read, 'call_count', 0) + 1
        if mock_read.call_count == 1:
            return b'Small content'
        return b''
    
    mock_content.read = mock_read
    mock_response.content = mock_content
    
    # Mock the session
    mock_session = MagicMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    # Mock the file operations with small size
    with patch('aiohttp.ClientSession', return_value=mock_session), \
         patch('builtins.open', mock_open()), \
         patch('os.path.getsize', return_value=500), \
         patch('os.path.exists', return_value=True), \
         patch('os.remove'):
        
        result = await download_handler.download_pdf(test_url, test_carrier)
        
        # Should return None for failure
        assert result is None

@pytest.mark.asyncio
async def test_cleanup_old_files(download_handler):
    """Test cleanup of old downloaded files."""
    # Mock file listing and stats
    test_files = [
        "old_file.pdf",  # Will be old
        "new_file.pdf"   # Will be recent
    ]
    
    test_paths = [os.path.join(download_handler.download_dir, f) for f in test_files]
    
    # Create a now datetime and old/new file datetimes
    now = datetime.datetime.now()
    old_time = now - datetime.timedelta(days=10)
    new_time = now - datetime.timedelta(days=2)
    
    with patch('os.listdir', return_value=test_files), \
         patch('os.path.isfile', return_value=True), \
         patch('os.path.getctime') as mock_getctime, \
         patch('datetime.datetime') as mock_datetime, \
         patch('os.remove') as mock_remove:
        
        # Setup the datetime.now mock
        mock_datetime.now.return_value = now
        mock_datetime.fromtimestamp.side_effect = lambda x: old_time if x == os.path.getctime(test_paths[0]) else new_time
        
        # Set ctime based on file
        def mock_getctime_side_effect(path):
            if path == test_paths[0]:
                return old_time.timestamp()
            return new_time.timestamp()
            
        mock_getctime.side_effect = mock_getctime_side_effect
        
        # Run the cleanup
        await download_handler.cleanup_old_files(max_age_days=7)
        
        # Only the old file should be removed
        mock_remove.assert_called_once_with(test_paths[0])

def test_get_download_path(download_handler):
    """Test getting download path without downloading."""
    test_url = "https://example.com/test.pdf"
    test_carrier = "Test Carrier"
    
    with patch.object(download_handler, '_generate_filename', return_value="testcarrier_123.pdf"):
        path = download_handler.get_download_path(test_url, test_carrier)
        
        assert path == os.path.join("/tmp/test_downloads", "testcarrier_123.pdf") 