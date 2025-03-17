"""Main URL management interface for dental insurance web scraping."""

from typing import Dict, List, Optional, Set, Tuple
import logging
from pathlib import Path
from dataclasses import dataclass
from urllib.parse import urlparse

from .validator import URLValidator, ValidationResult
from .rules import RulesEngine, CarrierRule
from .store import URLStore, URLEntry

logger = logging.getLogger(__name__)

@dataclass
class URLValidationError:
    """Represents a URL validation error."""
    url: str
    error: str
    details: Optional[str] = None

class URLManager:
    """Main interface for URL management."""
    
    def __init__(
        self,
        storage_file: Optional[str] = None,
        rules_config: Optional[Dict] = None
    ):
        """Initialize the URL manager.
        
        Args:
            storage_file: Path to JSON file for URL storage
            rules_config: Optional carrier-specific rules configuration
        """
        self.validator = URLValidator()
        self.rules_engine = RulesEngine(rules_config)
        self.store = URLStore(storage_file)
        
    def add_url(
        self,
        url: str,
        carrier: str,
        category: str,
        tags: Optional[Set[str]] = None,
        validate: bool = True
    ) -> Tuple[bool, Optional[URLEntry], Optional[List[str]]]:
        """Add a URL to the system.
        
        Args:
            url: URL to add
            carrier: Associated carrier
            category: URL category
            tags: Optional set of tags
            validate: Whether to validate the URL before adding
            
        Returns:
            Tuple of (success, URLEntry if success else None, list of errors if any)
        """
        errors = []
        
        if validate:
            # Validate URL structure
            validation_result = self.validator.validate(url)
            if not validation_result.is_valid:
                errors.extend(validation_result.errors)
            
            # Check against carrier rules
            rule_violations = self.rules_engine.check_url_against_rules(url, carrier)
            if rule_violations:
                errors.extend(rule_violations)
                
        if errors and validate:
            return False, None, errors
            
        try:
            entry = self.store.add_url(url, carrier, category, tags)
            return True, entry, None
        except Exception as e:
            logger.error(f"Failed to add URL {url}: {str(e)}")
            return False, None, [str(e)]
            
    def remove_url(self, url: str) -> bool:
        """Remove a URL from the system.
        
        Args:
            url: URL to remove
            
        Returns:
            True if successful, False otherwise
        """
        return self.store.remove_url(url)
        
    def validate_url(self, url: str, carrier: str) -> Tuple[bool, List[str]]:
        """Validate a URL against all rules.
        
        Args:
            url: URL to validate
            carrier: Associated carrier
            
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        # Validate URL structure
        validation_result = self.validator.validate(url)
        if not validation_result.is_valid:
            errors.extend(validation_result.errors)
        
        # Check against carrier rules
        rule_violations = self.rules_engine.check_url_against_rules(url, carrier)
        if rule_violations:
            errors.extend(rule_violations)
            
        return not bool(errors), errors
        
    def get_urls_by_carrier(self, carrier: str) -> List[URLEntry]:
        """Get all URLs for a carrier.
        
        Args:
            carrier: Carrier name
            
        Returns:
            List of URLEntry objects
        """
        return self.store.get_urls_by_carrier(carrier)
        
    def get_urls_by_category(self, category: str) -> List[URLEntry]:
        """Get all URLs in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of URLEntry objects
        """
        return self.store.get_urls_by_category(category)
        
    def get_urls_by_tag(self, tag: str) -> List[URLEntry]:
        """Get all URLs with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of URLEntry objects
        """
        return self.store.get_urls_by_tag(tag)
        
    def can_request_url(self, url: str, carrier: str) -> Tuple[bool, Optional[float]]:
        """Check if a URL can be requested based on rate limits.
        
        Args:
            url: URL to check
            carrier: Associated carrier
            
        Returns:
            Tuple of (can_request, wait_time_seconds if needed)
        """
        return self.rules_engine.can_request(carrier), self.rules_engine.get_wait_time(carrier)
        
    def update_url_stats(self, url: str, success: bool) -> None:
        """Update success/failure statistics for a URL.
        
        Args:
            url: URL to update
            success: Whether the request was successful
        """
        self.store.update_stats(url, success)
        
    def add_tags(self, url: str, tags: Set[str]) -> bool:
        """Add tags to a URL.
        
        Args:
            url: URL to tag
            tags: Tags to add
            
        Returns:
            True if successful, False if URL not found
        """
        return self.store.add_tags(url, tags)
        
    def remove_tags(self, url: str, tags: Set[str]) -> bool:
        """Remove tags from a URL.
        
        Args:
            url: URL to update
            tags: Tags to remove
            
        Returns:
            True if successful, False if URL not found
        """
        return self.store.remove_tags(url, tags)
        
    def get_carrier_rule(self, carrier: str) -> Optional[CarrierRule]:
        """Get rules for a specific carrier.
        
        Args:
            carrier: Carrier name
            
        Returns:
            CarrierRule if found, None otherwise
        """
        return self.rules_engine.get_carrier_rule(carrier)
        
    def validate_urls_batch(
        self,
        urls: List[Tuple[str, str]]  # List of (url, carrier) tuples
    ) -> List[URLValidationError]:
        """Validate multiple URLs in batch.
        
        Args:
            urls: List of (url, carrier) tuples to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for url, carrier in urls:
            is_valid, validation_errors = self.validate_url(url, carrier)
            if not is_valid:
                errors.append(URLValidationError(
                    url=url,
                    error="Validation failed",
                    details="; ".join(validation_errors)
                ))
                
        return errors 