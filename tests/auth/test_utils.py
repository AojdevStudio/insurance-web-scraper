"""
Tests for authentication utility functions.
"""
import pytest
import requests
from auth.utils import (
    extract_csrf_token,
    verify_ssl_cert,
    extract_form_fields,
    parse_token_response,
    validate_auth_response,
    sanitize_auth_data
)

def test_extract_csrf_token():
    """Test CSRF token extraction from HTML."""
    # Test meta tag
    html = '<meta name="csrf_token" content="test_token">'
    assert extract_csrf_token(html) == "test_token"
    
    # Test input field
    html = '<input name="csrf_token" value="test_token">'
    assert extract_csrf_token(html) == "test_token"
    
    # Test custom token name
    html = '<input name="custom_token" value="test_token">'
    assert extract_csrf_token(html, "custom_token") == "test_token"
    
    # Test no token
    html = '<div>No token here</div>'
    assert extract_csrf_token(html) is None

def test_extract_form_fields():
    """Test form field extraction."""
    html = """
    <form id="login_form">
        <input name="username" value="default_user">
        <input name="password" type="password">
        <select name="language">
            <option value="en">English</option>
        </select>
    </form>
    """
    
    fields = extract_form_fields(html, "login_form")
    assert fields["username"] == "default_user"
    assert fields["password"] == ""
    assert fields["language"] == ""
    
    # Test no form
    assert extract_form_fields("<div>No form</div>") == {}
    
    # Test wrong form ID
    assert extract_form_fields(html, "wrong_id") == {}

def test_parse_token_response():
    """Test token response parsing."""
    class MockResponse:
        def json(self):
            return {
                "token": "test_token",
                "expires_in": 3600,
                "token_type": "Bearer",
                "scope": "read write"
            }
    
    response = MockResponse()
    result = parse_token_response(response)
    
    assert result["token"] == "test_token"
    assert result["expires_in"] == 3600
    assert result["token_type"] == "Bearer"
    assert result["scope"] == "read write"
    
    # Test custom token field
    result = parse_token_response(response, "access_token")
    assert "token" not in result

def test_validate_auth_response():
    """Test authentication response validation."""
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.headers = {"content-type": "application/json"}
            self.cookies = {"session": "test_session"}
            self.text = "Welcome User"
        
        def json(self):
            return {"status": "success"}
    
    response = MockResponse()
    
    # Test status code
    assert validate_auth_response(response, {"status_code": 200})
    assert not validate_auth_response(response, {"status_code": 401})
    
    # Test headers
    assert validate_auth_response(response, {
        "headers": {"content-type": "application/json"}
    })
    assert not validate_auth_response(response, {
        "headers": {"content-type": "text/html"}
    })
    
    # Test cookies
    assert validate_auth_response(response, {"cookies": ["session"]})
    assert not validate_auth_response(response, {"cookies": ["invalid"]})
    
    # Test content string
    assert validate_auth_response(response, {"content": "Welcome"})
    assert not validate_auth_response(response, {"content": "Invalid"})
    
    # Test content dict
    assert validate_auth_response(response, {
        "content": {"status": "success"}
    })
    assert not validate_auth_response(response, {
        "content": {"status": "error"}
    })

def test_sanitize_auth_data():
    """Test authentication data sanitization."""
    data = {
        "username": "test_user",
        "password": "secret",
        "api_key": "12345",
        "token": "abcdef",
        "private_key": "xyz",
        "public_info": "visible"
    }
    
    sanitized = sanitize_auth_data(data)
    
    assert sanitized["username"] == "test_user"
    assert sanitized["password"] == "***"
    assert sanitized["api_key"] == "***"
    assert sanitized["token"] == "***"
    assert sanitized["private_key"] == "***"
    assert sanitized["public_info"] == "visible" 