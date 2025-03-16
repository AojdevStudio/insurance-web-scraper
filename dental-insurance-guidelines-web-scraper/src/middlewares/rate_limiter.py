"""
Rate limiting middleware for the dental insurance guidelines web scraper.
"""
from typing import Optional
import time
from collections import defaultdict

from scrapy import Spider, Request
from scrapy.exceptions import IgnoreRequest
from loguru import logger

from ..exceptions import RateLimitException

class RateLimitMiddleware:
    """
    Middleware to enforce rate limiting per domain.
    
    This middleware tracks requests per domain and enforces minimum delays
    between requests to prevent overloading servers.
    """
    
    def __init__(self):
        """Initialize the rate limiter."""
        # Track last request time per domain
        self.last_request_time = defaultdict(float)
        # Default delay between requests (in seconds)
        self.default_delay = 2.0
        # Custom delays per domain
        self.domain_delays = {}
        
    def process_request(self, request: Request, spider: Spider) -> Optional[Request]:
        """
        Process each request and enforce rate limiting.
        
        Args:
            request: The request being processed
            spider: The spider making the request
            
        Returns:
            None if request should proceed, raises IgnoreRequest if rate limit exceeded
            
        Raises:
            IgnoreRequest: If rate limit is exceeded
        """
        domain = request.url.split('/')[2]
        current_time = time.time()
        
        # Get delay for this domain (use default if not specified)
        delay = self.domain_delays.get(domain, self.default_delay)
        
        # Check if enough time has passed since last request
        time_since_last = current_time - self.last_request_time[domain]
        if time_since_last < delay:
            wait_time = delay - time_since_last
            logger.warning(f"Rate limit reached for {domain}. Waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
        
        # Update last request time
        self.last_request_time[domain] = time.time()
        
        return None
        
    def process_response(self, request: Request, response, spider: Spider):
        """
        Process the response and handle rate limit responses.
        
        Args:
            request: The request that was made
            response: The response received
            spider: The spider making the request
            
        Returns:
            Response object if ok, raises RateLimitException if rate limited
            
        Raises:
            RateLimitException: If server indicates rate limit was exceeded
        """
        # Check for rate limit response codes
        if response.status in [429, 503]:
            domain = request.url.split('/')[2]
            
            # Increase delay for this domain
            current_delay = self.domain_delays.get(domain, self.default_delay)
            new_delay = current_delay * 2
            self.domain_delays[domain] = new_delay
            
            logger.warning(f"Rate limit response from {domain}. Increasing delay to {new_delay} seconds")
            raise RateLimitException(f"Rate limit exceeded for {domain}")
            
        return response
        
    def set_domain_delay(self, domain: str, delay: float):
        """
        Set a custom delay for a specific domain.
        
        Args:
            domain: The domain to set delay for
            delay: Delay in seconds between requests
        """
        self.domain_delays[domain] = delay
        logger.info(f"Set rate limit delay for {domain} to {delay} seconds") 