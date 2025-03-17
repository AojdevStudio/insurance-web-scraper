"""Rules engine for managing carrier-specific URL rules and rate limiting."""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

@dataclass
class RateLimit:
    """Rate limit configuration."""
    requests_per_second: float
    burst_size: int = 1
    tokens: float = field(default=1.0)
    last_update: float = field(default_factory=time.time)

@dataclass
class CarrierRule:
    """Carrier-specific URL rules."""
    allowed_domains: List[str]
    required_paths: List[str]
    forbidden_paths: List[str]
    rate_limit: RateLimit
    auth_required: bool = False
    custom_headers: Dict[str, str] = field(default_factory=dict)

class RulesEngine:
    """Manages carrier-specific rules and rate limiting for URLs."""
    
    # Default rate limits per carrier
    DEFAULT_RATE_LIMITS = {
        'aetna': RateLimit(0.2, 2),     # 1 request per 5 seconds, burst of 2
        'cigna': RateLimit(0.33, 2),    # 1 request per 3 seconds, burst of 2
        'metlife': RateLimit(0.25, 2),  # 1 request per 4 seconds, burst of 2
        'uhc': RateLimit(0.2, 2),       # 1 request per 5 seconds, burst of 2
    }
    
    # Default carrier rules
    DEFAULT_CARRIER_RULES = {
        'aetna': CarrierRule(
            allowed_domains=['aetna.com', 'www.aetna.com'],
            required_paths=['/providers', '/health-care-professionals'],  # Added /providers
            forbidden_paths=['/about-us', '/careers'],
            rate_limit=DEFAULT_RATE_LIMITS['aetna'],
            auth_required=True,
            custom_headers={'User-Agent': 'DentalScraper/1.0'}
        ),
        'cigna': CarrierRule(
            allowed_domains=['cigna.com', 'www.cigna.com'],
            required_paths=['/healthcare-providers', '/providers'],  # Added /providers
            forbidden_paths=['/about-us'],
            rate_limit=DEFAULT_RATE_LIMITS['cigna'],
            auth_required=True
        ),
        'metlife': CarrierRule(
            allowed_domains=['metlife.com', 'www.metlife.com'],
            required_paths=['/dental-providers', '/providers'],  # Added /providers
            forbidden_paths=['/about-us'],
            rate_limit=DEFAULT_RATE_LIMITS['metlife'],
            auth_required=True
        ),
        'uhc': CarrierRule(
            allowed_domains=['uhc.com', 'www.uhc.com'],
            required_paths=['/dental-providers', '/providers'],  # Added /providers
            forbidden_paths=['/about-us'],
            rate_limit=DEFAULT_RATE_LIMITS['uhc'],
            auth_required=True
        )
    }
    
    def __init__(self, rules_config: Optional[Dict] = None):
        """Initialize the rules engine.
        
        Args:
            rules_config: Optional dictionary of carrier rules to override defaults
        """
        self.rate_limiters: Dict[str, RateLimit] = {}
        self.carrier_rules = self.DEFAULT_CARRIER_RULES.copy()
        
        if rules_config:
            for carrier, rule_config in rules_config.items():
                if carrier in self.carrier_rules:
                    # Update existing rule
                    current_rule = self.carrier_rules[carrier]
                    for key, value in rule_config.items():
                        if hasattr(current_rule, key):
                            setattr(current_rule, key, value)
                else:
                    # Create new rule if it has the required fields
                    if all(field in rule_config for field in ['allowed_domains', 'required_paths', 'forbidden_paths', 'rate_limit']):
                        self.carrier_rules[carrier] = CarrierRule(**rule_config)
                    else:
                        logger.warning(f"Incomplete rule configuration for carrier: {carrier}")
        
    def get_carrier_rule(self, carrier: str) -> Optional[CarrierRule]:
        """Get rules for a specific carrier.
        
        Args:
            carrier: Name of the carrier (e.g., 'aetna')
            
        Returns:
            CarrierRule object if carrier exists, None otherwise
        """
        return self.carrier_rules.get(carrier.lower())
        
    def check_url_against_rules(self, url: str, carrier: str) -> List[str]:
        """Check if a URL complies with carrier-specific rules.
        
        Args:
            url: URL to check
            carrier: Carrier name
            
        Returns:
            List of rule violations (empty if compliant)
        """
        violations = []
        rule = self.get_carrier_rule(carrier)
        
        if not rule:
            violations.append(f"No rules defined for carrier: {carrier}")
            return violations
            
        parsed = urlparse(url)
        
        # Check domain
        if parsed.netloc not in rule.allowed_domains:
            violations.append(
                f"Domain {parsed.netloc} not in allowed domains: {rule.allowed_domains}"
            )
            
        # Check required paths
        if not any(req_path in parsed.path for req_path in rule.required_paths):
            violations.append(
                f"URL path must contain one of: {rule.required_paths}"
            )
            
        # Check forbidden paths
        if any(forbidden in parsed.path for forbidden in rule.forbidden_paths):
            violations.append(
                f"URL contains forbidden path: {parsed.path}"
            )
            
        return violations
        
    def can_request(self, carrier: str) -> bool:
        """Check if a request is allowed based on rate limiting.
        
        Args:
            carrier: Carrier name
            
        Returns:
            True if request is allowed, False otherwise
        """
        rule = self.get_carrier_rule(carrier)
        if not rule:
            return False
            
        # Get or create rate limiter
        if carrier not in self.rate_limiters:
            self.rate_limiters[carrier] = rule.rate_limit
            
        rate_limit = self.rate_limiters[carrier]
        
        # Update tokens
        now = time.time()
        time_passed = now - rate_limit.last_update
        rate_limit.tokens = min(
            rate_limit.burst_size,
            rate_limit.tokens + time_passed * rate_limit.requests_per_second
        )
        rate_limit.last_update = now
        
        # Check if request is allowed
        if rate_limit.tokens >= 1.0:
            rate_limit.tokens -= 1.0
            return True
            
        return False
        
    def get_wait_time(self, carrier: str) -> float:
        """Get time to wait before next request is allowed.
        
        Args:
            carrier: Carrier name
            
        Returns:
            Time in seconds to wait (0 if request is allowed now)
        """
        if carrier not in self.rate_limiters:
            return 0.0
            
        rate_limit = self.rate_limiters[carrier]
        if rate_limit.tokens >= 1.0:
            return 0.0
            
        return (1.0 - rate_limit.tokens) / rate_limit.requests_per_second 