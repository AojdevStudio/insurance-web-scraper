"""Configuration settings for URL Management System."""

from typing import Dict, List, Set

# Default rate limits (requests per second) for carriers
DEFAULT_RATE_LIMITS = {
    'aetna': 2.0,
    'cigna': 1.0,
    'metlife': 1.5,
    'uhc': 1.0,
    'delta_dental': 1.0,
    'guardian': 1.0,
    'humana': 1.0,
    'default': 0.5  # Default rate limit for unspecified carriers
}

# Default burst sizes for rate limiting
DEFAULT_BURST_SIZES = {
    'aetna': 5,
    'cigna': 3,
    'metlife': 4,
    'uhc': 3,
    'delta_dental': 3,
    'guardian': 3,
    'humana': 3,
    'default': 2
}

# Carrier-specific URL rules
CARRIER_RULES = {
    'aetna': {
        'allowed_domains': {
            'www.aetna.com',
            'provider.aetna.com',
            'connect.aetna.com',
            'navinet.aetna.com'
        },
        'required_paths': set(),  # No specific path requirements
        'forbidden_paths': {
            '/login',  # Don't store login URLs
            '/logout',
            '/password-reset'
        },
        'auth_required': True,
        'custom_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    },
    'cigna': {
        'allowed_domains': {
            'www.cigna.com',
            'cignaforhcp.cigna.com',
            'provider.cigna.com'
        },
        'required_paths': set(),
        'forbidden_paths': {
            '/login',
            '/logout',
            '/reset-password'
        },
        'auth_required': True,
        'custom_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    },
    'metlife': {
        'allowed_domains': {
            'www.metlife.com',
            'online.metlife.com',
            'provider.metlife.com'
        },
        'required_paths': set(),
        'forbidden_paths': {
            '/login',
            '/logout',
            '/password-reset'
        },
        'auth_required': True,
        'custom_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    },
    'uhc': {
        'allowed_domains': {
            'www.uhc.com',
            'provider.uhc.com',
            'www.unitedhealthcareonline.com'
        },
        'required_paths': set(),
        'forbidden_paths': {
            '/login',
            '/logout',
            '/password-reset'
        },
        'auth_required': True,
        'custom_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    },
    'delta_dental': {
        'allowed_domains': {
            'www.deltadental.com',
            'provider.deltadental.com'
        },
        'required_paths': set(),
        'forbidden_paths': {
            '/login',
            '/logout',
            '/password-reset'
        },
        'auth_required': True,
        'custom_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    }
}

# URL categories
URL_CATEGORIES = {
    'provider-portal',
    'documentation',
    'claims',
    'eligibility',
    'benefits',
    'preauthorization',
    'fee-schedule',
    'forms',
    'resources',
    'contact'
}

# Common URL tags
COMMON_TAGS = {
    'login-required',
    'high-priority',
    'rate-limited',
    'pdf',
    'form',
    'api',
    'deprecated',
    'maintenance',
    'beta'
}

# Validation settings
VALIDATION_SETTINGS = {
    'check_robots_txt': True,
    'verify_ssl': True,
    'timeout_seconds': 10,
    'max_redirects': 5,
    'allowed_schemes': {'http', 'https'},
    'blocked_extensions': {
        '.exe', '.dll', '.bat', '.sh', '.jar',
        '.mp3', '.mp4', '.avi', '.mov',
        '.zip', '.tar', '.gz', '.rar'
    }
}

# Storage settings
STORAGE_SETTINGS = {
    'default_storage_file': 'url_store.json',
    'backup_enabled': True,
    'backup_count': 5,
    'compress_backups': True
}

def get_carrier_rule(carrier: str) -> Dict:
    """Get carrier-specific rules, falling back to defaults if not found.
    
    Args:
        carrier: Carrier name
        
    Returns:
        Dictionary of rules for the carrier
    """
    carrier = carrier.lower()
    if carrier in CARRIER_RULES:
        return CARRIER_RULES[carrier]
    
    # Return a default rule set
    return {
        'allowed_domains': set(),
        'required_paths': set(),
        'forbidden_paths': {'/login', '/logout', '/password-reset'},
        'auth_required': True,
        'custom_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    }

def get_rate_limit(carrier: str) -> float:
    """Get rate limit for a carrier.
    
    Args:
        carrier: Carrier name
        
    Returns:
        Rate limit in requests per second
    """
    carrier = carrier.lower()
    return DEFAULT_RATE_LIMITS.get(carrier, DEFAULT_RATE_LIMITS['default'])

def get_burst_size(carrier: str) -> int:
    """Get burst size for a carrier.
    
    Args:
        carrier: Carrier name
        
    Returns:
        Burst size for rate limiting
    """
    carrier = carrier.lower()
    return DEFAULT_BURST_SIZES.get(carrier, DEFAULT_BURST_SIZES['default'])

def is_valid_category(category: str) -> bool:
    """Check if a category is valid.
    
    Args:
        category: Category to check
        
    Returns:
        True if valid, False otherwise
    """
    return category.lower() in URL_CATEGORIES

def is_valid_tag(tag: str) -> bool:
    """Check if a tag is valid.
    
    Args:
        tag: Tag to check
        
    Returns:
        True if valid, False otherwise
    """
    return tag.lower() in COMMON_TAGS 