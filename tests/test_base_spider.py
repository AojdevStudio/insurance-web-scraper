"""
Tests for the BaseInsuranceSpider class.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import io

from scrapy.http import Request, Response
from scrapy.exceptions import CloseSpider

from dental_scraper.spiders.base_spider import BaseInsuranceSpider
from dental_scraper.exceptions import ScraperException, DownloadException

class TestSpider(BaseInsuranceSpider):
    """Test implementation of BaseInsuranceSpider."""
    
    def parse(self, response):
        """Test parse implementation."""
        yield Request(url="https://example.com/test", callback=self.parse_detail)
    
    def parse_detail(self, response):
        """Test detail page parser."""
        return {'test': 'data'}
        
@pytest.fixture
def spider():
    """Create a TestSpider instance for testing."""
    return TestSpider(
        name='test_spider',
        allowed_domains=['example.com'],
        start_urls=['https://example.com'],
        credentials={'username': 'test', 'password': 'test'},
        output_dir=Path('test_output')
    )

@pytest.fixture
def response():
    """Create a mock response for testing."""
    return Response(
        url='https://example.com',
        body=b'<html><body>Test</body></html>',
        request=Request(url='https://example.com')
    )

def test_init(spider):
    """Test initialization of BaseInsuranceSpider."""
    assert spider.name == 'test_spider'
    assert spider.allowed_domains == ['example.com']
    assert spider.start_urls == ['https://example.com']
    assert spider.credentials == {'username': 'test', 'password': 'test'}
    assert isinstance(spider.output_dir, Path)
    assert str(spider.output_dir) == 'test_output'

def test_start_requests(spider):
    """Test start_requests method yields requests for start URLs."""
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert requests[0].url == 'https://example.com'
    assert requests[0].callback == spider.parse

def test_handle_error(spider):
    """Test error handling for failed requests."""
    # Create a mock failure
    failure = MagicMock()
    failure.value = Exception("Test error")
    failure.value.response = MagicMock()
    failure.value.response.status = 404
    failure.value.response.headers = {'Content-Type': 'text/html'}
    
    # Test that the error handler logs and re-raises
    with patch('loguru.logger.error') as mock_logger:
        with pytest.raises(ScraperException):
            spider.handle_error(failure)
        
        # Verify logger was called
        assert mock_logger.call_count >= 1

def test_save_pdf_success(spider):
    """Test successful saving of PDF content."""
    # Test data
    content = b'%PDF-1.5\nTest PDF content'
    filename = 'test.pdf'
    
    # Mock the file operations
    with patch('pathlib.Path.write_bytes') as mock_write:
        with patch('loguru.logger.info') as mock_logger:
            result = spider.save_pdf(content, filename)
            
            # Verify the write operation was called
            mock_write.assert_called_once_with(content)
            
            # Verify the logger was called
            mock_logger.assert_called_once()
            
            # Verify the result is a Path
            assert isinstance(result, Path)
            assert result.name == filename

def test_save_pdf_failure(spider):
    """Test error handling when saving PDF fails."""
    # Test data
    content = b'%PDF-1.5\nTest PDF content'
    filename = 'test.pdf'
    
    # Mock the file operations to fail
    with patch('pathlib.Path.write_bytes', side_effect=IOError("Write error")):
        with pytest.raises(DownloadException):
            spider.save_pdf(content, filename)

def test_save_metadata_success(spider):
    """Test successful saving of metadata."""
    # Test data
    metadata = {'test': 'data', 'nested': {'key': 'value'}}
    filename = 'test.json'
    
    # Mock the file operations
    with patch('builtins.open', MagicMock(return_value=io.StringIO())) as mock_open:
        with patch('json.dump') as mock_json_dump:
            with patch('loguru.logger.info') as mock_logger:
                result = spider.save_metadata(metadata, filename)
                
                # Verify the open operation was called
                mock_open.assert_called_once()
                
                # Verify the json dump was called
                mock_json_dump.assert_called_once()
                
                # Verify the logger was called
                mock_logger.assert_called_once()
                
                # Verify the result is a Path
                assert isinstance(result, Path)
                assert result.name == filename

def test_save_metadata_failure(spider):
    """Test error handling when saving metadata fails."""
    # Test data
    metadata = {'test': 'data'}
    filename = 'test.json'
    
    # Mock the file operations to fail
    with patch('builtins.open', side_effect=IOError("Open error")):
        with pytest.raises(ScraperException):
            spider.save_metadata(metadata, filename) 