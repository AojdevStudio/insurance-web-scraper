"""
Tests for the rate limiting middleware.
"""
import pytest
import time
from unittest.mock import patch, MagicMock

from scrapy import Request
from scrapy.exceptions import IgnoreRequest

from dental_scraper.middlewares.rate_limiter import RateLimitMiddleware
from dental_scraper.exceptions import RateLimitException

@pytest.fixture
def rate_limiter():
    """Create a RateLimitMiddleware instance."""
    return RateLimitMiddleware()

@pytest.fixture
def spider():
    """Create a mock spider."""
    spider = MagicMock()
    spider.name = "test_spider"
    return spider

@pytest.fixture
def test_request():
    """Create a test request."""
    return Request(url="https://example.com/test")

def test_init():
    """Test initialization of RateLimitMiddleware."""
    middleware = RateLimitMiddleware()
    assert middleware.default_delay == 2.0
    assert middleware.domain_delays == {}
    assert middleware.last_request_time is not None

def test_process_request_no_delay(rate_limiter, test_request, spider):
    """Test processing a request with no previous requests."""
    # Should return None to allow request to proceed
    result = rate_limiter.process_request(test_request, spider)
    assert result is None
    assert "example.com" in rate_limiter.last_request_time

def test_process_request_with_delay(rate_limiter, test_request, spider):
    """Test processing a request with a recent previous request."""
    # Set last request time to now
    domain = test_request.url.split('/')[2]
    rate_limiter.last_request_time[domain] = time.time()
    
    # Mock time.sleep to avoid actually waiting
    with patch('time.sleep') as mock_sleep:
        result = rate_limiter.process_request(test_request, spider)
        
        # Should still return None but should have called sleep
        assert result is None
        mock_sleep.assert_called_once()

def test_process_response_success(rate_limiter, test_request, spider):
    """Test processing a successful response."""
    response = MagicMock()
    response.status = 200
    
    result = rate_limiter.process_response(test_request, response, spider)
    assert result == response

def test_process_response_rate_limited(rate_limiter, test_request, spider):
    """Test processing a rate-limited response."""
    response = MagicMock()
    response.status = 429
    
    with pytest.raises(RateLimitException):
        rate_limiter.process_response(test_request, response, spider)
    
    # Verify delay was increased for the domain
    domain = test_request.url.split('/')[2]
    assert rate_limiter.domain_delays[domain] > rate_limiter.default_delay

def test_set_domain_delay(rate_limiter):
    """Test setting a custom delay for a domain."""
    rate_limiter.set_domain_delay("example.com", 5.0)
    assert rate_limiter.domain_delays["example.com"] == 5.0 