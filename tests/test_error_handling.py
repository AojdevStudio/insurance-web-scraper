"""Tests for error handling utilities."""
import time
import pytest
from unittest.mock import Mock, patch
from dental_scraper.utils.error_handling import (
    CircuitBreaker,
    ErrorMonitor,
    retry_with_logging,
    handle_rate_limit,
    handle_auth_error,
    handle_parsing_error,
    handle_download_error,
)
from dental_scraper.exceptions import (
    ScraperException,
    RateLimitException,
    AuthenticationException,
    ParsingException,
    DownloadException,
)

def test_circuit_breaker_normal_operation():
    """Test circuit breaker under normal operation."""
    circuit_breaker = CircuitBreaker(failure_threshold=2)
    
    @circuit_breaker
    def test_func():
        return "success"
    
    assert test_func() == "success"
    assert circuit_breaker.state == "closed"
    assert circuit_breaker.failures == 0

def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after threshold failures."""
    circuit_breaker = CircuitBreaker(failure_threshold=2)
    
    @circuit_breaker
    def failing_func():
        raise ValueError("test error")
    
    # First failure
    with pytest.raises(ValueError):
        failing_func()
    assert circuit_breaker.state == "closed"
    
    # Second failure should open the circuit
    with pytest.raises(ValueError):
        failing_func()
    assert circuit_breaker.state == "open"
    
    # Further calls should raise CircuitBreakerOpen
    with pytest.raises(ScraperException) as exc_info:
        failing_func()
    assert "Circuit breaker" in str(exc_info.value)

def test_circuit_breaker_half_open_recovery():
    """Test circuit breaker recovery through half-open state."""
    circuit_breaker = CircuitBreaker(
        failure_threshold=2,
        reset_timeout=0.1  # Short timeout for testing
    )
    
    @circuit_breaker
    def test_func():
        return "success"
    
    # Force circuit open
    circuit_breaker.failures = 2
    circuit_breaker.state = "open"
    circuit_breaker.last_failure_time = time.time()
    
    # Wait for reset timeout
    time.sleep(0.2)
    
    # Should enter half-open on next call
    result = test_func()
    assert result == "success"
    assert circuit_breaker.state == "closed"
    assert circuit_breaker.failures == 0

def test_error_monitor_error_tracking():
    """Test error monitor tracks error counts and rates."""
    monitor = ErrorMonitor()
    
    # Record some errors
    monitor.record_error("TestError")
    monitor.record_error("TestError")
    monitor.record_error("OtherError")
    
    assert monitor.error_counts["TestError"] == 2
    assert monitor.error_counts["OtherError"] == 1
    
    # Test error rate calculation
    rate = monitor.get_error_rate("TestError")
    assert rate > 0

@patch("psutil.cpu_percent")
@patch("psutil.virtual_memory")
@patch("psutil.disk_usage")
def test_error_monitor_system_health(mock_disk, mock_memory, mock_cpu):
    """Test system health monitoring."""
    # Setup mocks
    mock_cpu.return_value = 50.0
    mock_memory.return_value.percent = 60.0
    mock_disk.return_value.percent = 70.0
    
    monitor = ErrorMonitor()
    health = monitor.get_system_health()
    
    assert health["cpu_percent"] == 50.0
    assert health["memory_percent"] == 60.0
    assert health["disk_usage_percent"] == 70.0

def test_retry_with_logging():
    """Test retry decorator with logging."""
    mock_func = Mock(side_effect=[ValueError("test"), "success"])
    
    @retry_with_logging(retry_exceptions=ValueError, max_attempts=2)
    def test_func():
        return mock_func()
    
    result = test_func()
    assert result == "success"
    assert mock_func.call_count == 2

def test_handle_rate_limit():
    """Test rate limit handler."""
    mock_func = Mock(side_effect=[RateLimitException(), "success"])
    
    @handle_rate_limit
    def test_func():
        return mock_func()
    
    result = test_func()
    assert result == "success"
    assert mock_func.call_count == 2

def test_handle_auth_error():
    """Test authentication error handler."""
    mock_func = Mock(side_effect=[AuthenticationException(), "success"])
    
    @handle_auth_error
    def test_func():
        return mock_func()
    
    result = test_func()
    assert result == "success"
    assert mock_func.call_count == 2

def test_handle_parsing_error():
    """Test parsing error handler."""
    mock_func = Mock(side_effect=[ParsingException(), "success"])
    
    @handle_parsing_error
    def test_func():
        return mock_func()
    
    result = test_func()
    assert result == "success"
    assert mock_func.call_count == 2

def test_handle_download_error():
    """Test download error handler."""
    mock_func = Mock(side_effect=[DownloadException(), "success"])
    
    @handle_download_error
    def test_func():
        return mock_func()
    
    result = test_func()
    assert result == "success"
    assert mock_func.call_count == 2 