"""URL validation utilities for dental insurance provider portals."""

import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from urllib import robotparser
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Container for URL validation results."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    parsed_url: Optional[Dict] = None

class URLValidator:
    """Validates URLs for dental insurance provider portals."""
    
    # URL pattern based on RFC 3986
    URL_PATTERN = re.compile(
        r'^(?:http|https)://'  # http:// or https:// (required)
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    def __init__(self):
        """Initialize the URL validator."""
        self.robots_parser = robotparser.RobotFileParser()
        
    def validate(self, url: str, check_robots: bool = True) -> ValidationResult:
        """Validate a URL and return detailed results.
        
        Args:
            url: The URL to validate
            check_robots: Whether to check robots.txt compliance
            
        Returns:
            ValidationResult object containing validation details
        """
        errors = []
        warnings = []
        parsed_url = None
        
        # Basic validation
        if not url:
            errors.append("URL cannot be empty")
            return ValidationResult(False, errors, warnings)
            
        if len(url) > 2048:
            errors.append(f"URL exceeds maximum length of 2048 characters (length={len(url)})")
            return ValidationResult(False, errors, warnings)
            
        # Parse URL
        try:
            parsed = urlparse(url)
            parsed_url = {
                'scheme': parsed.scheme,
                'netloc': parsed.netloc,
                'path': parsed.path,
                'params': parsed.params,
                'query': parsed.query,
                'fragment': parsed.fragment
            }
        except Exception as e:
            errors.append(f"Failed to parse URL: {str(e)}")
            return ValidationResult(False, errors, warnings)
            
        # Check scheme
        if not parsed.scheme:
            errors.append("No URL scheme specified")
        elif parsed.scheme not in ('http', 'https'):
            errors.append(f"URL scheme must be http or https (found: {parsed.scheme})")
            
        # Check domain
        if not parsed.netloc:
            errors.append("No domain specified")
        elif not self._is_valid_domain(parsed.netloc):
            errors.append(f"Invalid domain format: {parsed.netloc}")
            
        # Check path
        if parsed.path and not self._is_valid_path(parsed.path):
            warnings.append(f"Path contains potentially problematic characters: {parsed.path}")
            
        # Check robots.txt if requested
        if check_robots and not errors and parsed.scheme and parsed.netloc:
            try:
                robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
                self.robots_parser.set_url(robots_url)
                self.robots_parser.read()
                if not self.robots_parser.can_fetch("*", url):
                    warnings.append("URL is blocked by robots.txt")
            except Exception as e:
                warnings.append(f"Could not check robots.txt: {str(e)}")
                
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, parsed_url)
        
    def _is_valid_domain(self, domain: str) -> bool:
        """Check if a domain name is valid."""
        if not domain:
            return False
            
        # Handle IP addresses
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', domain):
            return all(0 <= int(i) <= 255 for i in domain.split('.'))
            
        # Handle localhost
        if domain.lower() == 'localhost':
            return True
            
        # Handle domain names
        if len(domain) > 255:
            return False
            
        if domain[-1] == ".":
            domain = domain[:-1]
            
        allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        return all(allowed.match(x) for x in domain.split("."))
        
    def _is_valid_path(self, path: str) -> bool:
        """Check if a URL path is valid."""
        if not path:
            return True
            
        # Check for common problematic characters
        problematic = re.compile(r'[<>{}|\^~`\[\]\\]')
        return not bool(problematic.search(path)) 