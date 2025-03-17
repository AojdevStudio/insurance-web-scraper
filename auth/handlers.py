"""
Authentication handlers for different authentication methods.
Provides a flexible system for handling various authentication types.
"""
import abc
import logging
import time
from typing import Dict, Optional, Any
import requests
from requests.auth import HTTPBasicAuth
from .storage import CredentialManager

# Configure logging
logger = logging.getLogger(__name__)

class AuthHandler(abc.ABC):
    """Base class for authentication handlers."""
    
    def __init__(self, credential_manager: CredentialManager):
        """
        Initialize the auth handler.
        
        Args:
            credential_manager: Instance of CredentialManager for credential storage
        """
        self.credential_manager = credential_manager
        self.session = requests.Session()
        self._token = None
        self._token_expiry = None
    
    @abc.abstractmethod
    def authenticate(self, **kwargs) -> bool:
        """
        Authenticate with the service.
        
        Args:
            **kwargs: Authentication parameters
            
        Returns:
            bool: True if authentication was successful
        """
        pass
    
    @abc.abstractmethod
    def is_authenticated(self) -> bool:
        """
        Check if the current session is authenticated.
        
        Returns:
            bool: True if authenticated
        """
        pass
    
    def clear_auth(self) -> None:
        """Clear any stored authentication data."""
        self._token = None
        self._token_expiry = None
        self.session.cookies.clear()

class BasicAuthHandler(AuthHandler):
    """Handler for basic authentication."""
    
    def authenticate(self, username: str, password: str, **kwargs) -> bool:
        """
        Authenticate using basic auth.
        
        Args:
            username: Username for authentication
            password: Password for authentication
            **kwargs: Additional parameters
            
        Returns:
            bool: True if authentication was successful
        """
        try:
            auth = HTTPBasicAuth(username, password)
            response = self.session.get(kwargs.get('url', ''), auth=auth)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Basic auth failed: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if basic auth session is valid."""
        return self.session.auth is not None

class FormAuthHandler(AuthHandler):
    """Handler for form-based authentication."""
    
    def authenticate(self, username: str, password: str, **kwargs) -> bool:
        """
        Authenticate using form submission.
        
        Args:
            username: Username for authentication
            password: Password for authentication
            **kwargs: Additional parameters including form_url and form_data
            
        Returns:
            bool: True if authentication was successful
        """
        try:
            form_url = kwargs.get('form_url')
            if not form_url:
                raise ValueError("form_url is required")
            
            # Get CSRF token if needed
            response = self.session.get(form_url)
            csrf_token = self._extract_csrf_token(response.text)
            
            # Prepare form data
            form_data = kwargs.get('form_data', {})
            form_data.update({
                'username': username,
                'password': password
            })
            if csrf_token:
                form_data['csrf_token'] = csrf_token
            
            # Submit form
            response = self.session.post(form_url, data=form_data)
            return self._verify_auth_success(response)
        except Exception as e:
            logger.error(f"Form auth failed: {e}")
            return False
    
    def _extract_csrf_token(self, html: str) -> Optional[str]:
        """Extract CSRF token from HTML."""
        # Implement CSRF token extraction based on the site's structure
        return None
    
    def _verify_auth_success(self, response: requests.Response) -> bool:
        """Verify if authentication was successful."""
        return response.status_code == 200 and 'login' not in response.url.lower()
    
    def is_authenticated(self) -> bool:
        """Check if form auth session is valid."""
        return bool(self.session.cookies)

class TokenAuthHandler(AuthHandler):
    """Handler for token-based authentication."""
    
    def authenticate(self, username: str, password: str, **kwargs) -> bool:
        """
        Authenticate and obtain token.
        
        Args:
            username: Username for authentication
            password: Password for authentication
            **kwargs: Additional parameters including token_url
            
        Returns:
            bool: True if authentication was successful
        """
        try:
            token_url = kwargs.get('token_url')
            if not token_url:
                raise ValueError("token_url is required")
            
            # Request token
            response = self.session.post(token_url, json={
                'username': username,
                'password': password
            })
            
            if response.status_code == 200:
                token_data = response.json()
                self._token = token_data.get('token')
                expiry = token_data.get('expires_in')
                if expiry:
                    self._token_expiry = time.time() + expiry
                
                # Add token to session headers
                self.session.headers.update({
                    'Authorization': f'Bearer {self._token}'
                })
                return True
            return False
        except Exception as e:
            logger.error(f"Token auth failed: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if token is valid and not expired."""
        if not self._token:
            return False
        if self._token_expiry and time.time() > self._token_expiry:
            return False
        return True

def create_auth_handler(auth_type: str, credential_manager: CredentialManager) -> AuthHandler:
    """
    Factory function to create appropriate auth handler.
    
    Args:
        auth_type: Type of authentication ('basic', 'form', or 'token')
        credential_manager: Instance of CredentialManager
        
    Returns:
        AuthHandler: Instance of appropriate auth handler
    """
    handlers = {
        'basic': BasicAuthHandler,
        'form': FormAuthHandler,
        'token': TokenAuthHandler
    }
    
    handler_class = handlers.get(auth_type.lower())
    if not handler_class:
        raise ValueError(f"Unsupported auth type: {auth_type}")
    
    return handler_class(credential_manager)
