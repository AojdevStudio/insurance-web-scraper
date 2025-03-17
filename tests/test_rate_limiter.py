"""
Unit tests for the rate limiting middleware.
"""
import pytest
from unittest.mock import patch, MagicMock
import time

from dental_scraper.middlewares.rate_limiter import RateLimitMiddleware
from dental_scraper.exceptions import RateLimitException


@pytest.fixture
def rate_limiter():
    """Create a RateLimitMiddleware instance for testing."""
    return RateLimitMiddleware()


def test_init_default_values(rate_limiter):
    """Test initialization with default values."""
    assert rate_limiter.default_delay == 1.0
    assert isinstance(rate_limiter.last_request_time, dict)
    assert isinstance(rate_limiter.domain_delays, dict)


@patch('time.sleep')
def test_process_request(mock_sleep, rate_limiter):
    """Test processing a request and enforcing delay."""
    # Create request with domain
    request = MagicMock()
    request.url = 'https://example.com/path'
    
    # Process request
    rate_limiter.process_request(request, None)
    
    # Verify delay was applied
    mock_sleep.assert_called_once()
    assert 'example.com' in rate_limiter.last_request_time


@patch('time.sleep')
def test_process_request_no_delay_needed(mock_sleep, rate_limiter):
    """Test processing a request when no delay is needed."""
    # Set up a recent request time in the future
    request = MagicMock()
    request.url = 'https://example.com/path'
    future_time = time.time() + 10  # 10 seconds in the future
    rate_limiter.last_request_time['example.com'] = future_time
    
    # Process request
    rate_limiter.process_request(request, None)
    
    # Verify no delay was applied
    mock_sleep.assert_not_called()


def test_process_response_normal(rate_limiter):
    """Test processing a normal response."""
    # Create response
    response = MagicMock()
    response.status = 200
    
    # Process response
    result = rate_limiter.process_response(None, response, None)
    
    # Verify response was returned unchanged
    assert result == response


def test_process_response_rate_limited(rate_limiter):
    """Test processing a rate-limited response."""
    # Create response
    response = MagicMock()
    response.status = 429  # Too Many Requests
    request = MagicMock()
    request.url = 'https://example.com/path'
    
    # Process response and expect exception
    with pytest.raises(RateLimitException):
        rate_limiter.process_response(request, response, None)
    
    # Verify delay was increased
    assert rate_limiter.domain_delays['example.com'] > rate_limiter.default_delay


def test_set_domain_delay(rate_limiter):
    """Test setting a custom delay for a domain."""
    # Set custom delay
    domain = 'example.com'
    custom_delay = 5.0
    rate_limiter.set_domain_delay(domain, custom_delay)
    
    # Verify delay was set
    assert rate_limiter.domain_delays[domain] == custom_delay 