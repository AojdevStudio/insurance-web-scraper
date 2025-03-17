"""
Unit tests for the download handler module.
"""
import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from dental_scraper.utils.download_handler import DownloadHandler


@pytest.fixture
def download_handler():
    """Create a download handler instance for testing."""
    return DownloadHandler(download_dir='test_output')


@pytest.fixture
def sample_url():
    """Return a sample URL for testing."""
    return 'https://example.com/document.pdf'


def test_init():
    """Test that the handler initializes correctly."""
    handler = DownloadHandler()
    assert handler is not None
    assert hasattr(handler, 'download_dir')
    
    # Test with custom output directory
    custom_dir = 'custom_dir'
    with patch('os.makedirs') as mock_makedirs:
        handler = DownloadHandler(download_dir=custom_dir)
        assert handler.download_dir == custom_dir
        mock_makedirs.assert_called_once_with(custom_dir, exist_ok=True)


def test_ensure_download_dir(download_handler):
    """Test that download directory is created."""
    with patch('os.makedirs') as mock_makedirs:
        # Call the method directly
        download_handler._ensure_download_dir()
        
        # Verify directory was created
        mock_makedirs.assert_called_once_with(download_handler.download_dir, exist_ok=True)


def test_generate_filename(download_handler, sample_url):
    """Test filename generation."""
    # Generate filename
    filename = download_handler._generate_filename(sample_url, 'Test Carrier')
    
    # Verify filename format
    assert filename.endswith('.pdf')
    assert 'testcarrier' in filename.lower()
    assert '_' in filename  # Should contain timestamp


@patch('aiohttp.ClientSession')
async def test_download_pdf_success(mock_session, download_handler, sample_url):
    """Test successful PDF download."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.headers = {'Content-Type': 'application/pdf'}
    mock_response.content.read.side_effect = [b'PDF content', b'']
    
    mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
    
    # Use a mock open to avoid actual file I/O
    with patch('builtins.open', mock_open()) as mock_file, \
         patch('os.path.getsize', return_value=1024):
        # Download PDF
        result = await download_handler.download_pdf(sample_url, 'Test Carrier')
    
    # Verify file was downloaded and saved
    assert mock_file.call_count > 0
    assert result is not None
    assert result.endswith('.pdf')


@patch('aiohttp.ClientSession')
async def test_download_pdf_http_error(mock_session, download_handler, sample_url):
    """Test handling of HTTP errors during download."""
    # Mock error response
    mock_response = MagicMock()
    mock_response.status = 404
    
    mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
    
    # Attempt to download
    result = await download_handler.download_pdf(sample_url, 'Test Carrier')
    
    # Verify download failed
    assert result is None


@patch('aiohttp.ClientSession')
async def test_download_pdf_invalid_content_type(mock_session, download_handler, sample_url):
    """Test handling of invalid content types."""
    # Mock response with invalid content type
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.headers = {'Content-Type': 'text/html'}
    
    mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
    
    # Attempt to download
    result = await download_handler.download_pdf(sample_url, 'Test Carrier')
    
    # Verify download failed
    assert result is None


@patch('aiohttp.ClientSession')
async def test_download_pdf_small_file(mock_session, download_handler, sample_url):
    """Test handling of suspiciously small files."""
    # Mock successful response but with small file
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.headers = {'Content-Type': 'application/pdf'}
    mock_response.content.read.side_effect = [b'PDF', b'']
    
    mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
    
    # Use a mock open to avoid actual file I/O
    with patch('builtins.open', mock_open()) as mock_file, \
         patch('os.path.getsize', return_value=3), \
         patch('os.remove'):  # Mock remove to avoid actual file deletion
        # Download PDF
        result = await download_handler.download_pdf(sample_url, 'Test Carrier')
    
    # Verify download failed due to small file size
    assert result is None


@patch('os.listdir')
@patch('os.path.isfile', return_value=True)
@patch('os.path.getctime')
@patch('datetime.datetime')
@patch('os.remove')
async def test_cleanup_old_files(mock_remove, mock_datetime, mock_getctime, mock_isfile, mock_listdir, download_handler):
    """Test cleaning up old files."""
    # Mock file listing
    mock_listdir.return_value = ['old_file.pdf', 'new_file.pdf']
    
    # Set up file creation times
    from datetime import datetime, timedelta
    now = datetime(2025, 1, 1)
    mock_datetime.now.return_value = now
    
    # Old file was created 10 days ago
    old_file_time = (now - timedelta(days=10)).timestamp()
    # New file was created 1 day ago
    new_file_time = (now - timedelta(days=1)).timestamp()
    
    mock_getctime.side_effect = lambda path: old_file_time if 'old_file' in path else new_file_time
    
    # Clean up old files
    await download_handler.cleanup_old_files(max_age_days=7)
    
    # Verify old file was removed but not new file
    assert mock_remove.call_count == 1
    file_removed = mock_remove.call_args[0][0]
    assert 'old_file' in file_removed
    assert 'new_file' not in file_removed


def test_get_download_path(download_handler, sample_url):
    """Test getting download path without downloading."""
    # Mock _generate_filename
    expected_filename = 'test_carrier_filename.pdf'
    with patch.object(download_handler, '_generate_filename', return_value=expected_filename):
        # Get download path
        path = download_handler.get_download_path(sample_url, 'Test Carrier')
    
    # Verify path is correct
    assert path == os.path.join(download_handler.download_dir, expected_filename) 