"""
Tests for authentication handlers.
"""
import pytest
import responses
from auth.storage import CredentialManager
from auth.handlers import (
    BasicAuthHandler,
    FormAuthHandler,
    TokenAuthHandler,
    create_auth_handler
)

@pytest.fixture
def credential_manager():
    """Create a CredentialManager instance for testing."""
    return CredentialManager("test_service")

@pytest.fixture
def basic_auth_handler(credential_manager):
    """Create a BasicAuthHandler instance for testing."""
    return BasicAuthHandler(credential_manager)

@pytest.fixture
def form_auth_handler(credential_manager):
    """Create a FormAuthHandler instance for testing."""
    return FormAuthHandler(credential_manager)

@pytest.fixture
def token_auth_handler(credential_manager):
    """Create a TokenAuthHandler instance for testing."""
    return TokenAuthHandler(credential_manager)

@responses.activate
def test_basic_auth_success(basic_auth_handler):
    """Test successful basic authentication."""
    responses.add(
        responses.GET,
        'https://example.com/auth',
        status=200
    )
    
    success = basic_auth_handler.authenticate(
        username="test_user",
        password="test_pass",
        url="https://example.com/auth"
    )
    assert success
    assert basic_auth_handler.is_authenticated()

@responses.activate
def test_basic_auth_failure(basic_auth_handler):
    """Test failed basic authentication."""
    responses.add(
        responses.GET,
        'https://example.com/auth',
        status=401
    )
    
    success = basic_auth_handler.authenticate(
        username="test_user",
        password="wrong_pass",
        url="https://example.com/auth"
    )
    assert not success
    assert not basic_auth_handler.is_authenticated()

@responses.activate
def test_form_auth_success(form_auth_handler):
    """Test successful form authentication."""
    # Mock login form page
    responses.add(
        responses.GET,
        'https://example.com/login',
        body='<form><input name="csrf_token" value="test_token"></form>',
        status=200
    )
    
    # Mock form submission
    responses.add(
        responses.POST,
        'https://example.com/login',
        status=200,
        headers={'Location': 'https://example.com/dashboard'}
    )
    
    success = form_auth_handler.authenticate(
        username="test_user",
        password="test_pass",
        form_url="https://example.com/login"
    )
    assert success
    assert form_auth_handler.is_authenticated()

@responses.activate
def test_token_auth_success(token_auth_handler):
    """Test successful token authentication."""
    responses.add(
        responses.POST,
        'https://example.com/token',
        json={
            'token': 'test_token',
            'expires_in': 3600
        },
        status=200
    )
    
    success = token_auth_handler.authenticate(
        username="test_user",
        password="test_pass",
        token_url="https://example.com/token"
    )
    assert success
    assert token_auth_handler.is_authenticated()

def test_create_auth_handler(credential_manager):
    """Test auth handler factory function."""
    basic_handler = create_auth_handler('basic', credential_manager)
    assert isinstance(basic_handler, BasicAuthHandler)
    
    form_handler = create_auth_handler('form', credential_manager)
    assert isinstance(form_handler, FormAuthHandler)
    
    token_handler = create_auth_handler('token', credential_manager)
    assert isinstance(token_handler, TokenAuthHandler)
    
    with pytest.raises(ValueError):
        create_auth_handler('invalid', credential_manager)

def test_clear_auth(basic_auth_handler):
    """Test clearing authentication data."""
    basic_auth_handler.session.auth = ('test_user', 'test_pass')
    basic_auth_handler._token = 'test_token'
    basic_auth_handler._token_expiry = 12345
    
    basic_auth_handler.clear_auth()
    
    assert basic_auth_handler._token is None
    assert basic_auth_handler._token_expiry is None
    assert len(basic_auth_handler.session.cookies) == 0 