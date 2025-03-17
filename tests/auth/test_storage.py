"""
Tests for the credential storage system.
"""
import os
import pytest
from auth.storage import CredentialManager

@pytest.fixture
def credential_manager():
    """Create a CredentialManager instance for testing."""
    return CredentialManager("test_service")

def test_store_and_get_credential(credential_manager):
    """Test storing and retrieving a credential."""
    credential_manager.store_credential("test_key", "test_value")
    value = credential_manager.get_credential("test_key")
    assert value == "test_value"

def test_delete_credential(credential_manager):
    """Test deleting a credential."""
    credential_manager.store_credential("test_key", "test_value")
    credential_manager.delete_credential("test_key")
    value = credential_manager.get_credential("test_key")
    assert value is None

def test_list_credentials(credential_manager):
    """Test listing stored credentials."""
    credential_manager.store_credential("test_key1", "test_value1")
    credential_manager.store_credential("test_key2", "test_value2")
    credentials = credential_manager.list_credentials()
    assert len(credentials) >= 2
    assert "test_key1" in credentials
    assert "test_key2" in credentials

def test_nonexistent_credential(credential_manager):
    """Test retrieving a nonexistent credential."""
    value = credential_manager.get_credential("nonexistent")
    assert value is None

def test_update_credential(credential_manager):
    """Test updating an existing credential."""
    credential_manager.store_credential("test_key", "old_value")
    credential_manager.store_credential("test_key", "new_value")
    value = credential_manager.get_credential("test_key")
    assert value == "new_value"

def test_empty_key_value(credential_manager):
    """Test handling of empty key or value."""
    with pytest.raises(ValueError):
        credential_manager.store_credential("", "test_value")
    
    with pytest.raises(ValueError):
        credential_manager.store_credential("test_key", "") 