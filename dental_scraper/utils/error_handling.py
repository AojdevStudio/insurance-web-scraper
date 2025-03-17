"""
Error handling utilities for the dental insurance guidelines web scraper.
Includes retry mechanisms, logging configuration, and monitoring.
"""
from functools import wraps
import time
from typing import Any, Callable, Dict, Optional, Type, Union
from loguru import logger
import psutil
from tenacity import (
    retry,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from ..exceptions import (
    ScraperException,
    RateLimitException,
    AuthenticationException,
    ParsingException,
    DownloadException,
)

# Configure loguru logger
logger.add(
    "logs/error.log",
    rotation="500 MB",
    retention="10 days",
    level="ERROR",
    backtrace=True,
    diagnose=True,
)
logger.add(
    "logs/info.log",
    rotation="100 MB",
    retention="7 days",
    level="INFO",
)

class CircuitBreaker:
    """Circuit breaker pattern implementation to prevent repeated failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 60,
        half_open_timeout: int = 30
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, or half-open
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if self.state == "open":
                if time.time() - self.last_failure_time >= self.reset_timeout:
                    self.state = "half-open"
                    logger.info(f"Circuit breaker for {func.__name__} entering half-open state")
                else:
                    raise ScraperException(f"Circuit breaker for {func.__name__} is open")
            
            try:
                result = func(*args, **kwargs)
                if self.state == "half-open":
                    self.state = "closed"
                    self.failures = 0
                    logger.info(f"Circuit breaker for {func.__name__} reset to closed state")
                return result
            except Exception as e:
                self.failures += 1
                self.last_failure_time = time.time()
                
                if self.failures >= self.failure_threshold:
                    self.state = "open"
                    logger.error(f"Circuit breaker for {func.__name__} opened after {self.failures} failures")
                raise e
        
        return wrapper

class ErrorMonitor:
    """Monitors error rates and system health."""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.start_time = time.time()
    
    def record_error(self, error_type: str) -> None:
        """Record an error occurrence."""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Log if error rate is high
        error_rate = self.get_error_rate(error_type)
        if error_rate > 0.1:  # More than 10% error rate
            logger.warning(f"High error rate for {error_type}: {error_rate:.2%}")
    
    def get_error_rate(self, error_type: str) -> float:
        """Calculate error rate for a specific error type."""
        total_time = time.time() - self.start_time
        return self.error_counts.get(error_type, 0) / total_time if total_time > 0 else 0
    
    def get_system_health(self) -> Dict[str, float]:
        """Get current system health metrics."""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage("/").percent,
        }

# Global error monitor instance
error_monitor = ErrorMonitor()

def retry_with_logging(
    retry_exceptions: Union[Type[Exception], tuple] = ScraperException,
    max_attempts: int = 3,
    max_delay: int = 60,
    exponential_base: int = 2,
) -> Callable:
    """
    Decorator that combines retry logic with logging and monitoring.
    
    Args:
        retry_exceptions: Exception type(s) to retry on
        max_attempts: Maximum number of retry attempts
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff
    """
    def decorator(func: Callable) -> Callable:
        @retry(
            retry=retry_if_exception_type(retry_exceptions),
            stop=(
                stop_after_attempt(max_attempts) |
                stop_after_delay(max_delay)
            ),
            wait=wait_exponential(multiplier=1, min=4, max=max_delay),
            before_sleep=before_sleep_log(logger, log_level="INFO"),
        )
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Record error in monitor
                error_monitor.record_error(e.__class__.__name__)
                raise
        
        return wrapper
    return decorator

def handle_rate_limit(func: Callable) -> Callable:
    """Specific handler for rate limit exceptions with appropriate backoff."""
    return retry_with_logging(
        retry_exceptions=RateLimitException,
        max_attempts=5,
        max_delay=120,
        exponential_base=4,
    )(func)

def handle_auth_error(func: Callable) -> Callable:
    """Specific handler for authentication errors with refresh attempt."""
    return retry_with_logging(
        retry_exceptions=AuthenticationException,
        max_attempts=2,
        max_delay=30,
    )(func)

def handle_parsing_error(func: Callable) -> Callable:
    """Specific handler for parsing errors with limited retries."""
    return retry_with_logging(
        retry_exceptions=ParsingException,
        max_attempts=2,
        max_delay=10,
    )(func)

def handle_download_error(func: Callable) -> Callable:
    """Specific handler for download errors with extended retries."""
    return retry_with_logging(
        retry_exceptions=DownloadException,
        max_attempts=5,
        max_delay=300,
    )(func) 