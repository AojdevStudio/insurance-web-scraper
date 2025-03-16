"""
Tests for the PDF spider module.
"""
import os
import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from scrapy.http import Request, Response, TextResponse, HtmlResponse
from dental_scraper.scrapers.pdf_spider import PDFSpider

@pytest.fixture
def spider():
    """Create a PDFSpider instance for testing."""
    with patch('pathlib.Path.mkdir'):
        return PDFSpider()

@pytest.fixture
def html_response():
    """Create a mock HTML response with PDF links."""
    html = """
    <html>
        <body>
            <a href="/document1.pdf">Document 1</a>
            <a href="https://example.com/document2.pdf">Document 2</a>
            <a href="/document3.doc">Document 3</a>
            <a href="/subpage">Subpage</a>
            <a class="next-page" href="/page2">Next Page</a>
        </body>
    </html>
    """
    
    return HtmlResponse(
        url="https://example.com/documents/",
        body=html.encode('utf-8'),
        encoding='utf-8',
        request=Request(url="https://example.com/documents/")
    )

@pytest.fixture
def pdf_response():
    """Create a mock PDF response."""
    pdf_content = b'%PDF-1.5\nTest PDF content'
    
    return Response(
        url="https://example.com/document1.pdf",
        body=pdf_content,
        request=Request(
            url="https://example.com/document1.pdf",
            meta={"filename": "document1.pdf"}
        )
    )

def test_init(spider):
    """Test initialization of PDFSpider."""
    # Verify attributes are set
    assert spider.name == "pdf_spider"
    assert isinstance(spider.pdf_dir, str)
    assert "data/pdfs" in spider.pdf_dir

def test_parse_finds_pdf_links(spider, html_response):
    """Test that parse method finds PDF links."""
    requests = list(spider.parse(html_response))
    
    # Should find 2 PDF links and 1 pagination link
    assert len(requests) == 3
    
    # Verify PDF requests
    pdf_requests = [r for r in requests if r.url.endswith(".pdf")]
    assert len(pdf_requests) == 2
    assert any(r.url == "https://example.com/document1.pdf" for r in pdf_requests)
    assert any(r.url == "https://example.com/document2.pdf" for r in pdf_requests)
    
    # Verify callback for PDF requests
    for request in pdf_requests:
        assert request.callback == spider.save_pdf
    
    # Verify pagination link was followed
    pagination_requests = [r for r in requests if not r.url.endswith(".pdf")]
    assert len(pagination_requests) == 1
    assert pagination_requests[0].url == "https://example.com/page2"

def test_save_pdf(spider, pdf_response):
    """Test saving a PDF file."""
    # Mock the open function and file operations
    with patch('builtins.open', mock_open()) as mock_file, \
         patch('os.makedirs') as mock_makedirs:
        
        result = spider.save_pdf(pdf_response)
        
        # Verify file was opened for writing
        mock_file.assert_called_once()
        handle = mock_file()
        handle.write.assert_called_once_with(pdf_response.body)
        
        # Verify parent directories were created
        mock_makedirs.assert_called_once()
        
        # Verify the result contains expected information
        assert result["url"] == "https://example.com/document1.pdf"
        assert result["filename"] == "document1.pdf"
        assert os.path.join(spider.pdf_dir, "document1.pdf") in result["path"]
        assert result["size"] == len(pdf_response.body) 