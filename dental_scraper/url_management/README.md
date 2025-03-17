# URL Management System

A comprehensive system for managing, validating, and organizing URLs for dental insurance web scraping.

## Overview

The URL Management System provides a robust solution for handling URLs in the dental insurance web scraping project. It includes features for:

- URL validation and verification
- Carrier-specific rules management
- Rate limiting and request throttling
- URL storage and organization
- URL grouping and tagging

## Components

### URLManager

The main interface for interacting with the URL Management System. It integrates all other components and provides a unified API.

```python
from dental_scraper.url_management import URLManager

# Initialize the manager
manager = URLManager(storage_file='urls.json')

# Add a URL
success, entry, errors = manager.add_url(
    url='https://www.aetna.com/providers',
    carrier='aetna',
    category='provider-portal',
    tags={'high-priority'}
)

# Validate a URL
is_valid, errors = manager.validate_url(
    url='https://www.cigna.com/providers',
    carrier='cigna'
)

# Check rate limits
can_request, wait_time = manager.can_request_url(
    url='https://www.metlife.com/dental',
    carrier='metlife'
)
```

### URLValidator

Handles URL validation, checking for:
- Valid URL structure
- Allowed schemes (http/https)
- Domain validation
- Path validation
- robots.txt compliance

### RulesEngine

Manages carrier-specific rules including:
- Allowed domains
- Required/forbidden paths
- Rate limiting
- Authentication requirements
- Custom headers

### URLStore

Provides persistent storage and organization of URLs with:
- JSON-based storage
- URL grouping by carrier
- URL categorization
- URL tagging
- Success/failure tracking

## Configuration

The system is configured through the `config.py` file, which includes:

- Default rate limits for carriers
- Carrier-specific URL rules
- URL categories
- Common tags
- Validation settings
- Storage settings

## Usage Examples

### Adding and Validating URLs

```python
# Initialize the manager
manager = URLManager()

# Add a URL with validation
success, entry, errors = manager.add_url(
    url='https://www.aetna.com/providers',
    carrier='aetna',
    category='provider-portal',
    tags={'high-priority', 'login-required'}
)

if success:
    print(f"Added URL: {entry.url}")
else:
    print(f"Failed to add URL: {errors}")
```

### URL Grouping and Filtering

```python
# Get URLs by carrier
aetna_urls = manager.get_urls_by_carrier('aetna')

# Get URLs by category
portal_urls = manager.get_urls_by_category('provider-portal')

# Get URLs by tag
priority_urls = manager.get_urls_by_tag('high-priority')
```

### Rate Limiting

```python
# Check if a URL can be requested
can_request, wait_time = manager.can_request_url(
    url='https://www.cigna.com/providers',
    carrier='cigna'
)

if can_request:
    # Make the request
    pass
else:
    print(f"Need to wait {wait_time} seconds")
```

### Batch Operations

```python
# Validate multiple URLs
urls_to_validate = [
    ('https://www.aetna.com/providers', 'aetna'),
    ('https://provider.cigna.com/claims', 'cigna')
]

errors = manager.validate_urls_batch(urls_to_validate)
```

## Testing

The system includes comprehensive tests covering all components. Run the tests using pytest:

```bash
pytest tests/test_url_management.py
```

## Dependencies

- validators>=0.22.0
- urllib3>=2.2.0
- python-dateutil>=2.8.2
- robotexclusionrulesparser>=1.7.1

## Contributing

When contributing to this module:

1. Follow the existing code style and documentation patterns
2. Add tests for any new functionality
3. Update the README.md with any new features or changes
4. Run the test suite before submitting changes

## License

This module is part of the dental insurance web scraper project and is subject to its licensing terms. 