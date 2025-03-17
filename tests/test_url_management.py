"""Tests for the URL Management System."""

import os
import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

from dental_scraper.url_management.manager import URLManager
from dental_scraper.url_management.validator import URLValidator
from dental_scraper.url_management.rules import RulesEngine
from dental_scraper.url_management.store import URLStore, URLEntry
from dental_scraper.url_management.config import (
    get_carrier_rule,
    get_rate_limit,
    get_burst_size,
    is_valid_category,
    is_valid_tag
)

@pytest.fixture
def temp_storage_file():
    """Create a temporary file for URL storage."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def url_manager(temp_storage_file):
    """Create a URL manager instance with temporary storage."""
    return URLManager(storage_file=temp_storage_file)

def test_url_validator():
    """Test URL validation functionality."""
    validator = URLValidator()
    
    # Test valid URLs
    valid_urls = [
        'https://www.aetna.com/providers',
        'https://provider.cigna.com/claims',
        'https://www.metlife.com/dental'
    ]
    for url in valid_urls:
        result = validator.validate(url)
        assert result.is_valid
        assert not result.errors
        
    # Test invalid URLs
    invalid_urls = [
        'not-a-url',
        'ftp://invalid-scheme.com',
        'http:/missing-slash.com'
    ]
    for url in invalid_urls:
        result = validator.validate(url)
        assert not result.is_valid
        assert result.errors

def test_rules_engine():
    """Test rules engine functionality."""
    rules_engine = RulesEngine()
    
    # Test carrier rules
    aetna_rule = rules_engine.get_carrier_rule('aetna')
    assert aetna_rule is not None
    assert 'www.aetna.com' in aetna_rule.allowed_domains
    
    # Test URL validation against rules
    valid_url = 'https://www.aetna.com/providers'
    violations = rules_engine.check_url_against_rules(valid_url, 'aetna')
    assert not violations
    
    invalid_url = 'https://invalid-domain.com'
    violations = rules_engine.check_url_against_rules(invalid_url, 'aetna')
    assert violations
    
    # Test rate limiting
    assert rules_engine.can_request('aetna')
    wait_time = rules_engine.get_wait_time('aetna')
    assert wait_time is not None

def test_url_store(temp_storage_file):
    """Test URL storage functionality."""
    store = URLStore(temp_storage_file)
    
    # Test adding URLs
    entry = store.add_url(
        'https://www.aetna.com/providers',
        'aetna',
        'provider-portal',
        {'high-priority'}
    )
    assert entry is not None
    assert entry.url == 'https://www.aetna.com/providers'
    assert entry.carrier == 'aetna'
    assert entry.category == 'provider-portal'
    assert 'high-priority' in entry.tags
    
    # Test retrieving URLs
    retrieved = store.get_url('https://www.aetna.com/providers')
    assert retrieved is not None
    assert retrieved.url == entry.url
    
    # Test carrier indexing
    carrier_urls = store.get_urls_by_carrier('aetna')
    assert len(carrier_urls) == 1
    assert carrier_urls[0].url == entry.url
    
    # Test category indexing
    category_urls = store.get_urls_by_category('provider-portal')
    assert len(category_urls) == 1
    assert category_urls[0].url == entry.url
    
    # Test tag indexing
    tagged_urls = store.get_urls_by_tag('high-priority')
    assert len(tagged_urls) == 1
    assert tagged_urls[0].url == entry.url
    
    # Test persistence
    store.save()
    new_store = URLStore(temp_storage_file)
    new_store.load()
    assert len(new_store.urls) == 1
    assert new_store.get_url(entry.url) is not None

def test_url_manager(url_manager):
    """Test URL manager integration."""
    # Test adding a valid URL
    success, entry, errors = url_manager.add_url(
        'https://www.aetna.com/providers',
        'aetna',
        'provider-portal',
        {'high-priority'}
    )
    assert success
    assert entry is not None
    assert not errors
    
    # Test adding an invalid URL
    success, entry, errors = url_manager.add_url(
        'not-a-url',
        'aetna',
        'provider-portal'
    )
    assert not success
    assert entry is None
    assert errors
    
    # Test URL validation
    is_valid, errors = url_manager.validate_url(
        'https://www.aetna.com/providers',
        'aetna'
    )
    assert is_valid
    assert not errors
    
    # Test rate limiting
    can_request, wait_time = url_manager.can_request_url(
        'https://www.aetna.com/providers',
        'aetna'
    )
    assert isinstance(can_request, bool)
    assert isinstance(wait_time, (float, type(None)))
    
    # Test URL grouping
    carrier_urls = url_manager.get_urls_by_carrier('aetna')
    assert len(carrier_urls) == 1
    
    category_urls = url_manager.get_urls_by_category('provider-portal')
    assert len(category_urls) == 1
    
    tagged_urls = url_manager.get_urls_by_tag('high-priority')
    assert len(tagged_urls) == 1

def test_config_functions():
    """Test configuration utility functions."""
    # Test carrier rule retrieval
    aetna_rule = get_carrier_rule('aetna')
    assert aetna_rule is not None
    assert 'allowed_domains' in aetna_rule
    
    # Test rate limit retrieval
    aetna_rate = get_rate_limit('aetna')
    assert aetna_rate > 0
    
    # Test burst size retrieval
    aetna_burst = get_burst_size('aetna')
    assert aetna_burst > 0
    
    # Test category validation
    assert is_valid_category('provider-portal')
    assert not is_valid_category('invalid-category')
    
    # Test tag validation
    assert is_valid_tag('high-priority')
    assert not is_valid_tag('invalid-tag')

def test_batch_validation(url_manager):
    """Test batch URL validation."""
    urls = [
        ('https://www.aetna.com/providers', 'aetna'),  # Valid URL
        ('https://www.cigna.com/providers', 'cigna'),  # Valid URL
        ('not-a-url', 'aetna'),  # Invalid URL format
        ('https://invalid-domain.com', 'aetna')  # Invalid domain
    ]
    
    errors = url_manager.validate_urls_batch(urls)
    assert len(errors) == 2  # Should have errors for the last two invalid URLs
    
    # Verify specific error cases
    invalid_urls = {error.url for error in errors}
    assert 'not-a-url' in invalid_urls
    assert 'https://invalid-domain.com' in invalid_urls

def test_url_stats(url_manager):
    """Test URL statistics tracking."""
    # Add a URL
    success, entry, _ = url_manager.add_url(
        'https://www.aetna.com/providers',
        'aetna',
        'provider-portal'
    )
    assert success
    
    # Update stats
    url_manager.update_url_stats('https://www.aetna.com/providers', True)
    url_manager.update_url_stats('https://www.aetna.com/providers', False)
    
    # Check stats
    entry = url_manager.store.get_url('https://www.aetna.com/providers')
    assert entry.success_count == 1
    assert entry.failure_count == 1

def test_tag_management(url_manager):
    """Test URL tag management."""
    # Add a URL
    success, _, _ = url_manager.add_url(
        'https://www.aetna.com/providers',
        'aetna',
        'provider-portal'
    )
    assert success
    
    # Add tags
    success = url_manager.add_tags(
        'https://www.aetna.com/providers',
        {'high-priority', 'login-required'}
    )
    assert success
    
    # Check tags
    entry = url_manager.store.get_url('https://www.aetna.com/providers')
    assert 'high-priority' in entry.tags
    assert 'login-required' in entry.tags
    
    # Remove tags
    success = url_manager.remove_tags(
        'https://www.aetna.com/providers',
        {'high-priority'}
    )
    assert success
    
    # Check tags again
    entry = url_manager.store.get_url('https://www.aetna.com/providers')
    assert 'high-priority' not in entry.tags
    assert 'login-required' in entry.tags 