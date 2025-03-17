"""
Utility functions for authentication handling.
"""
import logging
import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

def extract_csrf_token(html: str, token_name: str = "csrf_token") -> Optional[str]:
    """
    Extract CSRF token from HTML content.
    
    Args:
        html: HTML content to parse
        token_name: Name of the CSRF token field
        
    Returns:
        Optional[str]: CSRF token if found
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Check meta tags
        meta_tag = soup.find('meta', {'name': re.compile(f'{token_name}', re.I)})
        if meta_tag and meta_tag.get('content'):
            return meta_tag['content']
        
        # Check input fields
        input_tag = soup.find('input', {'name': re.compile(f'{token_name}', re.I)})
        if input_tag and input_tag.get('value'):
            return input_tag['value']
        
        return None
    except Exception as e:
        logger.error(f"Failed to extract CSRF token: {e}")
        return None

def verify_ssl_cert(url: str) -> bool:
    """
    Verify SSL certificate of a URL.
    
    Args:
        url: URL to verify
        
    Returns:
        bool: True if certificate is valid
    """
    try:
        response = requests.get(url, verify=True)
        return True
    except RequestException:
        return False

def extract_form_fields(html: str, form_id: Optional[str] = None) -> Dict[str, str]:
    """
    Extract form fields and their default values from HTML.
    
    Args:
        html: HTML content to parse
        form_id: Optional ID of the form to target
        
    Returns:
        Dict[str, str]: Dictionary of field names and default values
    """
    try:
        soup = BeautifulSoup(html, 'html.parser')
        form = soup.find('form', {'id': form_id}) if form_id else soup.find('form')
        
        if not form:
            return {}
        
        fields = {}
        for input_tag in form.find_all(['input', 'select']):
            name = input_tag.get('name')
            if name:
                fields[name] = input_tag.get('value', '')
        
        return fields
    except Exception as e:
        logger.error(f"Failed to extract form fields: {e}")
        return {}

def parse_token_response(response: requests.Response, token_field: str = "token") -> Dict[str, Any]:
    """
    Parse token response and extract relevant fields.
    
    Args:
        response: Response from token request
        token_field: Name of the token field
        
    Returns:
        Dict[str, Any]: Dictionary containing token and related data
    """
    try:
        data = response.json()
        result = {
            'token': data.get(token_field),
            'expires_in': data.get('expires_in'),
            'token_type': data.get('token_type', 'Bearer'),
            'scope': data.get('scope'),
        }
        return {k: v for k, v in result.items() if v is not None}
    except Exception as e:
        logger.error(f"Failed to parse token response: {e}")
        return {}

def validate_auth_response(response: requests.Response, success_indicators: Dict[str, Any]) -> bool:
    """
    Validate authentication response against success indicators.
    
    Args:
        response: Response to validate
        success_indicators: Dictionary of indicators (status_code, headers, cookies, content)
        
    Returns:
        bool: True if response matches success indicators
    """
    try:
        # Check status code
        if 'status_code' in success_indicators:
            if response.status_code != success_indicators['status_code']:
                return False
        
        # Check headers
        headers = success_indicators.get('headers', {})
        for header, value in headers.items():
            if header not in response.headers or response.headers[header] != value:
                return False
        
        # Check cookies
        cookies = success_indicators.get('cookies', [])
        for cookie in cookies:
            if cookie not in response.cookies:
                return False
        
        # Check content
        content = success_indicators.get('content')
        if content:
            if isinstance(content, str) and content not in response.text:
                return False
            elif isinstance(content, dict):
                response_json = response.json()
                for key, value in content.items():
                    if key not in response_json or response_json[key] != value:
                        return False
        
        return True
    except Exception as e:
        logger.error(f"Failed to validate auth response: {e}")
        return False

def sanitize_auth_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize authentication data by removing sensitive information.
    
    Args:
        data: Dictionary containing authentication data
        
    Returns:
        Dict[str, Any]: Sanitized data dictionary
    """
    sensitive_fields = {'password', 'token', 'api_key', 'secret', 'private_key'}
    return {
        k: '***' if any(field in k.lower() for field in sensitive_fields) else v
        for k, v in data.items()
    }
