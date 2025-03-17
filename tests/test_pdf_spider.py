"""
Unit tests for the PDF spider module.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from scrapy.http import Request, Response
from scrapy.exceptions import CloseSpider

from dental_scraper.scrapers.pdf_spider import PDFSpider
from dental_scraper.exceptions import DownloadException


@pytest.fixture
def pdf_spider():
    """Create a PDF spider instance for testing."""
    class TestPDFSpider(PDFSpider):
        name = 'test_pdf_spider'
        allowed_domains = ['example.com']
        start_urls = ['https://example.com/documents']
        pdf_urls = ['https://example.com/document.pdf']
        
    return TestPDFSpider()


@pytest.fixture
def mock_response():
    """Create a mock response for testing."""
    mock_request = Request(url='https://example.com/documents')
    return Response(
        url='https://example.com/documents',
        status=200,
        request=mock_request,
        body=b'<html><body><a href="document.pdf">Document</a></body></html>'
    )


@pytest.fixture
def mock_pdf_response():
    """Create a mock PDF response for testing."""
    mock_request = Request(url='https://example.com/document.pdf')
    return Response(
        url='https://example.com/document.pdf',
        status=200,
        request=mock_request,
        body=b'%PDF-1.5\nTest PDF content'
    )


def test_init():
    """Test that the spider initializes correctly."""
    spider = PDFSpider(
        name='test_spider',
        allowed_domains=['example.com'],
        start_urls=['https://example.com'],
        pdf_urls=['https://example.com/doc.pdf'],
        output_dir=Path('test_output')
    )
    assert spider.name == 'test_spider'
    assert spider.allowed_domains == ['example.com']
    assert spider.start_urls == ['https://example.com']
    assert spider.pdf_urls == ['https://example.com/doc.pdf']
    assert spider.output_dir == Path('test_output')


def test_init_defaults():
    """Test default initialization values."""
    spider = PDFSpider(
        name='test_spider',
        allowed_domains=['example.com'],
        start_urls=['https://example.com']
    )
    assert spider.pdf_urls == []
    assert spider.output_dir == Path('data/pdfs')


def test_start_requests(pdf_spider):
    """Test start_requests method generates requests for start_urls and pdf_urls."""
    requests = list(pdf_spider.start_requests())
    assert len(requests) == 2  # One for start_url, one for pdf_url
    
    urls = [req.url for req in requests]
    callbacks = [req.callback.__name__ for req in requests]
    
    assert 'https://example.com/documents' in urls
    assert 'https://example.com/document.pdf' in urls
    
    # The callback for start_urls should be parse
    # The callback for pdf_urls should be parse_pdf
    assert callbacks.count('parse') == 1
    assert callbacks.count('parse_pdf') == 1


def test_parse(pdf_spider, mock_response):
    """Test parse method extracts PDF links."""
    requests = list(pdf_spider.parse(mock_response))
    assert len(requests) == 1
    
    request = requests[0]
    assert request.url == 'https://example.com/document.pdf'
    assert request.callback.__name__ == 'parse_pdf'


@patch('dental_scraper.scrapers.pdf_spider.download_file')
def test_parse_pdf(mock_download, pdf_spider, mock_pdf_response):
    """Test parse_pdf method downloads and processes PDFs."""
    # Mock successful download
    mock_download.return_value = Path('test_output/document.pdf')
    
    # Process PDF response
    results = list(pdf_spider.parse_pdf(mock_pdf_response))
    
    # Verify download was called and results are generated
    mock_download.assert_called_once()
    assert len(results) == 1
    assert isinstance(results[0], dict)
    assert 'url' in results[0]
    assert 'file_path' in results[0]
    assert results[0]['url'] == 'https://example.com/document.pdf'
    assert results[0]['file_path'] == Path('test_output/document.pdf')


@patch('dental_scraper.scrapers.pdf_spider.download_file', side_effect=DownloadException("Download failed"))
def test_parse_pdf_download_failure(mock_download, pdf_spider, mock_pdf_response):
    """Test error handling when PDF download fails."""
    # Process PDF response with simulated download failure
    with pytest.raises(DownloadException):
        list(pdf_spider.parse_pdf(mock_pdf_response))
    
    # Verify download was attempted
    mock_download.assert_called_once()


@patch('dental_scraper.scrapers.pdf_spider.validate_pdf', return_value=False)
def test_parse_pdf_invalid_pdf(mock_validate, pdf_spider, mock_pdf_response):
    """Test handling of invalid PDF content."""
    # Process invalid PDF response
    with pytest.raises(DownloadException):
        list(pdf_spider.parse_pdf(mock_pdf_response))
    
    # Verify PDF was validated
    mock_validate.assert_called_once()


def test_extract_pdf_links(pdf_spider, mock_response):
    """Test extraction of PDF links from HTML."""
    links = pdf_spider.extract_pdf_links(mock_response)
    assert len(links) == 1
    assert links[0] == 'https://example.com/document.pdf'


def test_extract_pdf_links_with_base_url(pdf_spider):
    """Test extraction of PDF links with base URL handling."""
    response = Response(
        url='https://example.com/subfolder/',
        status=200,
        body=b'<html><body><a href="../documents/document.pdf">Document</a></body></html>'
    )
    
    links = pdf_spider.extract_pdf_links(response)
    assert len(links) == 1
    assert links[0] == 'https://example.com/documents/document.pdf'


def test_extract_pdf_links_no_links(pdf_spider):
    """Test handling when no PDF links are found."""
    response = Response(
        url='https://example.com',
        status=200,
        body=b'<html><body>No PDF links here</body></html>'
    )
    
    links = pdf_spider.extract_pdf_links(response)
    assert len(links) == 0


def test_should_follow_link(pdf_spider):
    """Test link filtering logic."""
    # PDF link should be followed
    assert pdf_spider.should_follow_link('https://example.com/document.pdf') is True
    
    # Non-PDF link should not be followed
    assert pdf_spider.should_follow_link('https://example.com/page.html') is False
    
    # PDF link with allowed domain should be followed
    assert pdf_spider.should_follow_link('https://example.com/subfolder/document.pdf') is True
    
    # PDF link with disallowed domain should not be followed
    assert pdf_spider.should_follow_link('https://other-domain.com/document.pdf') is False


def test_handle_error(pdf_spider):
    """Test error handling."""
    class MockError:
        def __str__(self):
            return "Test error"
    
    # Spider should log the error and not crash
    pdf_spider.handle_error(MockError())


@patch('dental_scraper.scrapers.pdf_spider.logger')
def test_log_stats(mock_logger, pdf_spider):
    """Test statistics logging."""
    # Set some statistics
    pdf_spider.stats = {'downloaded': 5, 'failed': 2}
    
    # Log stats
    pdf_spider.log_stats()
    
    # Verify logger was called
    mock_logger.info.assert_called() 