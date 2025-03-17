"""
Unit tests for PDF spiders.
"""
import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock

from scrapy.http import Response, Request
from scrapy.exceptions import DropItem

from dental_scraper.scrapers.pdf_spider import PDFSpider
from dental_scraper.utils.download_handler import DownloadHandler
from dental_scraper.models.carrier import Carrier


@pytest.fixture
def pdf_spider():
    """Create a PDF spider instance for testing."""
    spider = PDFSpider()
    spider.name = 'test_pdf_spider'
    spider.carrier = Carrier.AETNA
    return spider


@pytest.fixture
def sample_response():
    """Create a sample response for testing."""
    request = Request(url='https://example.com/document.pdf')
    return Response(
        url='https://example.com/document.pdf',
        status=200,
        headers={'Content-Type': 'application/pdf'},
        body=b'%PDF-1.5\nSample PDF content',
        request=request
    )


@pytest.fixture
def sample_download_path():
    """Return a sample download path for testing."""
    return os.path.join('test_output', 'sample.pdf')


def test_init():
    """Test spider initialization."""
    spider = PDFSpider()
    assert spider is not None
    assert hasattr(spider, 'name')
    assert hasattr(spider, 'allowed_domains')
    assert hasattr(spider, 'start_urls')
    assert hasattr(spider, 'carrier')


def test_from_crawler():
    """Test the from_crawler class method."""
    mock_crawler = MagicMock()
    mock_crawler.settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2
    }
    
    spider = PDFSpider.from_crawler(mock_crawler)
    
    assert spider is not None
    assert spider.concurrent_requests == 1
    assert spider.download_delay == 2


@patch('dental_scraper.scrapers.pdf_spider.DownloadHandler')
async def test_parse_pdf_valid(mock_handler_class, pdf_spider, sample_response, sample_download_path):
    """Test parsing a valid PDF response."""
    # Mock the download handler
    mock_handler = MagicMock()
    mock_handler.download_pdf = AsyncMock(return_value=sample_download_path)
    mock_handler_class.return_value = mock_handler
    
    # Parse the response
    result = await pdf_spider.parse_pdf(sample_response)
    
    # Verify result
    assert result is not None
    assert 'pdf_path' in result
    assert result['pdf_path'] == sample_download_path
    assert 'url' in result
    assert result['url'] == 'https://example.com/document.pdf'
    assert 'carrier' in result
    assert result['carrier'] == Carrier.AETNA
    
    # Verify download was called
    mock_handler.download_pdf.assert_called_once()


@patch('dental_scraper.scrapers.pdf_spider.DownloadHandler')
async def test_parse_pdf_download_failed(mock_handler_class, pdf_spider, sample_response):
    """Test handling failed PDF downloads."""
    # Mock the download handler to return None (download failed)
    mock_handler = MagicMock()
    mock_handler.download_pdf = AsyncMock(return_value=None)
    mock_handler_class.return_value = mock_handler
    
    # Parse the response and expect exception
    with pytest.raises(DropItem):
        await pdf_spider.parse_pdf(sample_response)
    
    # Verify download was called
    mock_handler.download_pdf.assert_called_once()


@patch('dental_scraper.scrapers.pdf_spider.DownloadHandler')
async def test_parse_pdf_non_pdf_response(mock_handler_class, pdf_spider):
    """Test handling non-PDF responses."""
    # Create a non-PDF response
    request = Request(url='https://example.com/page.html')
    response = Response(
        url='https://example.com/page.html',
        status=200,
        headers={'Content-Type': 'text/html'},
        body=b'<html><body>Not a PDF</body></html>',
        request=request
    )
    
    # Parse the response and expect exception
    with pytest.raises(DropItem):
        await pdf_spider.parse_pdf(response)
    
    # Verify download was not called
    mock_handler_class.assert_not_called()


def test_is_pdf_content_type_valid():
    """Test PDF content type detection with valid types."""
    pdf_spider_instance = PDFSpider()
    
    # Test with application/pdf
    assert pdf_spider_instance.is_pdf_content_type('application/pdf') is True
    
    # Test with uppercase
    assert pdf_spider_instance.is_pdf_content_type('APPLICATION/PDF') is True
    
    # Test with mixed case
    assert pdf_spider_instance.is_pdf_content_type('Application/Pdf') is True
    
    # Test with parameters
    assert pdf_spider_instance.is_pdf_content_type('application/pdf; charset=utf-8') is True


def test_is_pdf_content_type_invalid():
    """Test PDF content type detection with invalid types."""
    pdf_spider_instance = PDFSpider()
    
    # Test with HTML
    assert pdf_spider_instance.is_pdf_content_type('text/html') is False
    
    # Test with empty string
    assert pdf_spider_instance.is_pdf_content_type('') is False
    
    # Test with None
    assert pdf_spider_instance.is_pdf_content_type(None) is False


@patch('dental_scraper.scrapers.pdf_spider.PDFSpider.parse_pdf')
async def test_parse(mock_parse_pdf, pdf_spider, sample_response):
    """Test the main parse method."""
    # Set up mock to return a valid result
    mock_result = {'pdf_path': 'path/to/pdf', 'url': 'https://example.com/document.pdf', 'carrier': Carrier.AETNA}
    mock_parse_pdf.return_value = mock_result
    
    # Parse the response
    results = [r async for r in pdf_spider.parse(sample_response)]
    
    # Verify parse_pdf was called
    mock_parse_pdf.assert_called_once_with(sample_response)
    
    # Verify result
    assert len(results) == 1
    assert results[0] == mock_result


@patch('dental_scraper.scrapers.pdf_spider.PDFSpider.parse_pdf', side_effect=DropItem("Test error"))
async def test_parse_with_error(mock_parse_pdf, pdf_spider, sample_response):
    """Test the main parse method with an error."""
    # Parse the response
    results = [r async for r in pdf_spider.parse(sample_response)]
    
    # Verify parse_pdf was called
    mock_parse_pdf.assert_called_once_with(sample_response)
    
    # Verify no results
    assert len(results) == 0


@patch('os.path.exists', return_value=False)
@patch('os.makedirs')
def test_setup_output_dir(mock_makedirs, mock_exists, pdf_spider):
    """Test setting up the output directory."""
    # Call the method
    pdf_spider.setup_output_dir('test_output')
    
    # Verify directory was created
    mock_makedirs.assert_called_once_with('test_output', exist_ok=True)


async def test_start_requests(pdf_spider):
    """Test the start_requests method."""
    # Setup start_urls
    pdf_spider.start_urls = ['https://example.com/doc1.pdf', 'https://example.com/doc2.pdf']
    
    # Get requests
    requests = [r async for r in pdf_spider.start_requests()]
    
    # Verify requests
    assert len(requests) == 2
    assert all(isinstance(r, Request) for r in requests)
    assert requests[0].url == 'https://example.com/doc1.pdf'
    assert requests[1].url == 'https://example.com/doc2.pdf'
    assert all('dont_filter' in r.meta and r.meta['dont_filter'] is True for r in requests) 