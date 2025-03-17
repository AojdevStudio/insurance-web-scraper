"""
Configuration system for authentication settings.
Uses Pydantic for validation and type checking.
"""
from typing import Dict, Optional
from pydantic import BaseModel, Field, validator
from .storage import CredentialManager

class AuthConfig(BaseModel):
    """Base configuration for authentication."""
    auth_type: str = Field(..., description="Type of authentication (basic, form, token)")
    service_name: str = Field(..., description="Name of the service for credential storage")
    base_url: str = Field(..., description="Base URL of the service")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    verify_ssl: bool = Field(default=True, description="Whether to verify SSL certificates")

class BasicAuthConfig(AuthConfig):
    """Configuration for basic authentication."""
    auth_type: str = Field(default="basic", const=True)
    auth_url: str = Field(..., description="URL for basic auth")

class FormAuthConfig(AuthConfig):
    """Configuration for form-based authentication."""
    auth_type: str = Field(default="form", const=True)
    form_url: str = Field(..., description="URL of the login form")
    form_data: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional form fields"
    )
    success_url: Optional[str] = Field(
        None,
        description="URL to verify successful login"
    )

class TokenAuthConfig(AuthConfig):
    """Configuration for token-based authentication."""
    auth_type: str = Field(default="token", const=True)
    token_url: str = Field(..., description="URL to obtain token")
    token_field: str = Field(
        default="token",
        description="Field name containing token in response"
    )
    expiry_field: Optional[str] = Field(
        None,
        description="Field name containing token expiry in response"
    )

class AuthConfigManager:
    """Manager for authentication configurations."""
    
    def __init__(self, credential_manager: CredentialManager):
        """
        Initialize the config manager.
        
        Args:
            credential_manager: Instance of CredentialManager for credential storage
        """
        self.credential_manager = credential_manager
        self._configs: Dict[str, AuthConfig] = {}
    
    def add_config(self, service_name: str, config_dict: Dict) -> AuthConfig:
        """
        Add a new authentication configuration.
        
        Args:
            service_name: Name of the service
            config_dict: Configuration dictionary
            
        Returns:
            AuthConfig: Created configuration object
        """
        auth_type = config_dict.get('auth_type', '').lower()
        config_classes = {
            'basic': BasicAuthConfig,
            'form': FormAuthConfig,
            'token': TokenAuthConfig
        }
        
        config_class = config_classes.get(auth_type)
        if not config_class:
            raise ValueError(f"Unsupported auth type: {auth_type}")
        
        config = config_class(**config_dict)
        self._configs[service_name] = config
        return config
    
    def get_config(self, service_name: str) -> Optional[AuthConfig]:
        """
        Get configuration for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Optional[AuthConfig]: Configuration object if found
        """
        return self._configs.get(service_name)
    
    def remove_config(self, service_name: str) -> None:
        """
        Remove configuration for a service.
        
        Args:
            service_name: Name of the service
        """
        self._configs.pop(service_name, None)
    
    def list_configs(self) -> Dict[str, AuthConfig]:
        """
        List all configurations.
        
        Returns:
            Dict[str, AuthConfig]: Dictionary of service names to configurations
        """
        return self._configs.copy()
