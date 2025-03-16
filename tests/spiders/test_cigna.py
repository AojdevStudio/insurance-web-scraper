import pytest
from unittest.mock import Mock, patch, AsyncMock
from scrapy.http import Response, Request, TextResponse, Headers
from loguru import logger
from dental_insurance_guidelines_web_scraper.spiders.cigna import CignaSpider

@pytest.fixture
def spider():
    logger.info("Creating CignaSpider instance for test")
    return CignaSpider()
    
@pytest.fixture
def mock_response():
    """Create a mock response with sample HTML content."""
    logger.info("Creating mock response with sample HTML content")
    url = 'https://www.cigna.com/test'
    html = """
    <html>
        <body>
            <a href="/guidelines.pdf">Dental Guidelines</a>
            <a href="/policy.pdf">Documentation Requirements</a>
            <a href="/other.pdf">Other Document</a>
            <a href="/dental/resources">Dental Resources</a>
        </body>
    </html>
    """
    
    request = Request(url=url)
    headers = Headers({
        'Content-Type': 'text/html',
        'Server': 'nginx'
    })
    
    # Create a mock response with the HTML content
    response = TextResponse(
        url=url,
        body=html.encode('utf-8'),
        encoding='utf-8',
        request=request,
        headers=headers
    )
    
    # Add CSS selector functionality
    def mock_css(selector):
        logger.debug(f"Mock CSS selector called with: {selector}")
        if selector == 'a':
            links = []
            for line in html.split('\n'):
                if '<a href=' in line:
                    href_start = line.find('href="') + 6
                    href_end = line.find('"', href_start)
                    href = line[href_start:href_end]
                    text_start = line.find('>') + 1
                    text_end = line.find('</a>')
                    text = line[text_start:text_end].strip()
                    logger.debug(f"Found link: href={href}, text={text}")
                    
                    class MockSelector:
                        def __init__(self, text):
                            self.text = text
                            
                        def getall(self):
                            return [self.text]
                            
                    class MockLink:
                        def __init__(self, href, text):
                            self.attrib = {'href': href}
                            self._text = text
                            
                        def css(self, selector):
                            if selector == '::text':
                                return MockSelector(self._text)
                            return []
                            
                    links.append(MockLink(href, text))
            return links
        return []
    
    response.css = mock_css
    return response
    
@pytest.fixture
def mock_pdf_response():
    """Create a mock PDF response."""
    logger.info("Creating mock PDF response")
    url = 'https://www.cigna.com/guidelines.pdf'
    body = b'%PDF-1.4\nTest PDF content'
    request = Request(url=url)
    headers = Headers({
        'Content-Type': 'application/pdf',
        'Content-Length': str(len(body)),
        'Server': 'nginx'
    })
    return Response(
        url=url,
        body=body,
        request=request,
        headers=headers
    )
    
def test_spider_initialization():
    logger.info("Testing spider initialization")
    spider = CignaSpider()
    assert spider.name == 'cigna'
    assert 'cigna.com' in spider.allowed_domains
    assert len(spider.start_urls) == 1
    assert spider.custom_settings['CONCURRENT_REQUESTS'] == 2
    logger.info("Spider initialization test passed")
    
def test_parse_finds_pdf_links(spider, mock_response):
    logger.info("Testing parse method for PDF links")
    results = list(spider.parse(mock_response))
    pdf_requests = [r for r in results if '.pdf' in r.url]
    logger.debug(f"Found {len(pdf_requests)} PDF requests")
    assert len(pdf_requests) == 2  # guidelines.pdf and policy.pdf
    logger.info("PDF links test passed")
    
def test_parse_follows_relevant_links(spider, mock_response):
    logger.info("Testing parse method for resource links")
    results = list(spider.parse(mock_response))
    resource_requests = [r for r in results if 'dental/resources' in r.url]
    logger.debug(f"Found {len(resource_requests)} resource requests")
    assert len(resource_requests) == 1
    logger.info("Resource links test passed")
    
@pytest.mark.asyncio
async def test_parse_pdf_link_success(spider, mock_pdf_response):
    logger.info("Testing successful PDF link parsing")
    # Mock the download handler
    mock_download = AsyncMock(return_value='/tmp/test.pdf')
    spider.download_handler.download_pdf = mock_download
    logger.debug("Mocked download handler")
    
    # Mock the PDF extractor
    mock_text = AsyncMock(return_value='Procedure: D0150 Test procedure')
    spider.pdf_extractor.extract_text = mock_text
    logger.debug("Mocked PDF text extractor")
    
    mock_tables = AsyncMock(return_value=[{'code': 'D0150', 'info': 'test'}])
    spider.pdf_extractor.extract_tables = mock_tables
    logger.debug("Mocked PDF table extractor")
    
    # Mock the pattern matcher
    mock_pattern_matcher = Mock()
    mock_pattern_matcher.extract_procedure_blocks = Mock(return_value=[{
        'code': 'D0150',
        'description': 'Test procedure',
        'requirements': ['Test requirement'],
        'notes': ['Test note']
    }])
    mock_pattern_matcher.validate_cdt_code = Mock(return_value=True)
    spider.pattern_matcher = mock_pattern_matcher
    logger.debug("Mocked pattern matcher")
    
    results = [r async for r in spider.parse_pdf_link(mock_pdf_response, 'test')]
    logger.debug(f"Got {len(results)} results from parse_pdf_link")
    assert len(results) == 1
    assert results[0]['code'] == 'D0150'
    assert results[0]['carrier'] == 'cigna'
    assert results[0]['description'] == 'Test procedure'
    assert results[0]['requirements'] == ['Test requirement']
    assert results[0]['notes'] == ['Test note']
    logger.info("PDF link success test passed")
    
@pytest.mark.asyncio
async def test_parse_pdf_link_download_failure(spider, mock_pdf_response):
    logger.info("Testing PDF link download failure")
    # Mock download failure
    mock_download = AsyncMock(return_value=None)
    spider.download_handler.download_pdf = mock_download
    logger.debug("Mocked download handler to return None")
    
    results = [r async for r in spider.parse_pdf_link(mock_pdf_response, 'test')]
    logger.debug(f"Got {len(results)} results from parse_pdf_link")
    assert len(results) == 0
    logger.info("PDF link failure test passed")
    
def test_process_procedure_block(spider):
    logger.info("Testing procedure block processing")
    block = {
        'code': 'D0150',
        'description': 'Test procedure',
        'requirements': ['Test requirement'],
        'notes': ['Test note']
    }
    tables = [{'code': 'D0150', 'frequency': 'Once per year'}]
    logger.debug(f"Processing block: {block}")
    
    # Mock pattern matcher for validation
    mock_pattern_matcher = Mock()
    mock_pattern_matcher.validate_cdt_code = Mock(return_value=True)
    spider.pattern_matcher = mock_pattern_matcher
    
    result = spider.process_procedure_block(block, tables)
    assert result['code'] == 'D0150'
    assert result['description'] == 'Test procedure'
    assert len(result['requirements']) == 1
    assert len(result['notes']) == 1
    assert result['additional_info']['frequency'] == 'Once per year'
    logger.info("Procedure block test passed")
    
def test_process_procedure_block_invalid_code(spider):
    logger.info("Testing procedure block with invalid code")
    block = {
        'code': 'invalid',
        'description': 'Test procedure',
        'requirements': ['Test requirement'],
        'notes': ['Test note']
    }
    tables = []
    logger.debug(f"Processing invalid block: {block}")
    
    # Mock pattern matcher for validation
    mock_pattern_matcher = Mock()
    mock_pattern_matcher.validate_cdt_code = Mock(return_value=False)
    spider.pattern_matcher = mock_pattern_matcher
    
    result = spider.process_procedure_block(block, tables)
    assert result is None
    logger.info("Invalid procedure block test passed")
    
def test_find_table_info(spider):
    logger.info("Testing table info extraction")
    tables = [
        {'code': 'D0150', 'frequency': 'Once per year'},
        {'code': 'D0150', 'requirements': 'Additional req'},
        {'code': 'D0220', 'frequency': 'As needed'}
    ]
    logger.debug(f"Processing tables for D0150: {tables}")
    
    result = spider.find_table_info('D0150', tables)
    assert result == {
        'frequency': 'Once per year',
        'requirements': 'Additional req'
    }
    logger.info("Table info test passed")
    
def test_spider_closed_with_guidelines(spider):
    logger.info("Testing spider closed with guidelines")
    spider.guidelines_found = True
    spider.closed(reason='finished')
    logger.info("Spider closed with guidelines test passed")
    
def test_spider_closed_without_guidelines(spider):
    logger.info("Testing spider closed without guidelines")
    spider.guidelines_found = False
    spider.closed(reason='finished')
    logger.info("Spider closed without guidelines test passed") 