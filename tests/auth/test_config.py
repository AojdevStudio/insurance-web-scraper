"""
Tests for authentication configuration system.
"""
import pytest
from pydantic import ValidationError
from auth.storage import CredentialManager
from auth.config import (
    AuthConfig,
    BasicAuthConfig,
    FormAuthConfig,
    TokenAuthConfig,
    AuthConfigManager
)

@pytest.fixture
def credential_manager():
    """Create a CredentialManager instance for testing."""
    return CredentialManager("test_service")

@pytest.fixture
def config_manager(credential_manager):
    """Create an AuthConfigManager instance for testing."""
    return AuthConfigManager(credential_manager)

def test_basic_auth_config():
    """Test basic auth configuration validation."""
    config = BasicAuthConfig(
        service_name="test_service",
        base_url="https://example.com",
        auth_url="https://example.com/auth"
    )
    assert config.auth_type == "basic"
    assert config.service_name == "test_service"
    assert config.base_url == "https://example.com"
    assert config.auth_url == "https://example.com/auth"
    assert config.timeout == 30
    assert config.verify_ssl is True

def test_form_auth_config():
    """Test form auth configuration validation."""
    config = FormAuthConfig(
        service_name="test_service",
        base_url="https://example.com",
        form_url="https://example.com/login",
        form_data={"extra_field": "value"}
    )
    assert config.auth_type == "form"
    assert config.form_url == "https://example.com/login"
    assert config.form_data == {"extra_field": "value"}
    assert config.success_url is None

def test_token_auth_config():
    """Test token auth configuration validation."""
    config = TokenAuthConfig(
        service_name="test_service",
        base_url="https://example.com",
        token_url="https://example.com/token"
    )
    assert config.auth_type == "token"
    assert config.token_url == "https://example.com/token"
    assert config.token_field == "token"
    assert config.expiry_field is None

def test_invalid_config():
    """Test invalid configuration handling."""
    with pytest.raises(ValidationError):
        BasicAuthConfig(
            service_name="test_service",
            base_url="not_a_url",
            auth_url="not_a_url"
        )

def test_config_manager_add_config(config_manager):
    """Test adding configurations to manager."""
    config = config_manager.add_config("test_service", {
        "auth_type": "basic",
        "service_name": "test_service",
        "base_url": "https://example.com",
        "auth_url": "https://example.com/auth"
    })
    assert isinstance(config, BasicAuthConfig)
    assert config.auth_type == "basic"

def test_config_manager_get_config(config_manager):
    """Test retrieving configurations from manager."""
    config_manager.add_config("test_service", {
        "auth_type": "basic",
        "service_name": "test_service",
        "base_url": "https://example.com",
        "auth_url": "https://example.com/auth"
    })
    
    config = config_manager.get_config("test_service")
    assert isinstance(config, BasicAuthConfig)
    assert config.service_name == "test_service"

def test_config_manager_remove_config(config_manager):
    """Test removing configurations from manager."""
    config_manager.add_config("test_service", {
        "auth_type": "basic",
        "service_name": "test_service",
        "base_url": "https://example.com",
        "auth_url": "https://example.com/auth"
    })
    
    config_manager.remove_config("test_service")
    assert config_manager.get_config("test_service") is None

def test_config_manager_list_configs(config_manager):
    """Test listing all configurations."""
    config_manager.add_config("service1", {
        "auth_type": "basic",
        "service_name": "service1",
        "base_url": "https://example1.com",
        "auth_url": "https://example1.com/auth"
    })
    
    config_manager.add_config("service2", {
        "auth_type": "form",
        "service_name": "service2",
        "base_url": "https://example2.com",
        "form_url": "https://example2.com/login"
    })
    
    configs = config_manager.list_configs()
    assert len(configs) == 2
    assert isinstance(configs["service1"], BasicAuthConfig)
    assert isinstance(configs["service2"], FormAuthConfig)

def test_invalid_auth_type(config_manager):
    """Test handling of invalid auth type."""
    with pytest.raises(ValueError):
        config_manager.add_config("test_service", {
            "auth_type": "invalid",
            "service_name": "test_service",
            "base_url": "https://example.com"
        }) 