"""
Custom exceptions for the dental insurance guidelines web scraper.
"""

class ScraperException(Exception):
    """Base exception class for all scraper-related exceptions."""
    pass

class RateLimitException(ScraperException):
    """Raised when rate limits are exceeded."""
    pass

class AuthenticationException(ScraperException):
    """Raised when authentication fails."""
    pass

class ParsingException(ScraperException):
    """Raised when parsing of content fails."""
    pass

class DownloadException(ScraperException):
    """Raised when downloading content fails."""
    pass

class ConfigurationException(ScraperException):
    """Raised when there are configuration issues."""
    pass

class DataCleaningException(ScraperException):
    """Raised when data cleaning or validation fails."""
    pass 