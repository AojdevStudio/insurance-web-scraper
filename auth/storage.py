"""
Secure credential storage management using keyring and environment variables.
Implements a layered approach to credential storage with fallback mechanisms.
"""
import os
import json
import logging
from typing import Optional, Dict, Any
import keyring
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

class CredentialManager:
    """Manages secure storage and retrieval of credentials."""
    
    def __init__(self, service_name: str = "insurance_scraper"):
        """
        Initialize the credential manager.
        
        Args:
            service_name: The name of the service for keyring storage
        """
        self.service_name = service_name
        load_dotenv()  # Load environment variables from .env file
        
        # Initialize encryption for file-based storage
        self._init_encryption()
    
    def _init_encryption(self) -> None:
        """Initialize encryption for file-based storage."""
        key_env = os.getenv('ENCRYPTION_KEY')
        if key_env:
            self.encryption_key = key_env.encode()
        else:
            self.encryption_key = Fernet.generate_key()
            logger.info("Generated new encryption key")
        
        self.cipher_suite = Fernet(self.encryption_key)
    
    def store_credential(self, key: str, value: str, use_keyring: bool = True) -> bool:
        """
        Store a credential securely.
        
        Args:
            key: The identifier for the credential
            value: The credential value to store
            use_keyring: Whether to attempt keyring storage first
            
        Returns:
            bool: True if storage was successful
        """
        try:
            if use_keyring:
                keyring.set_password(self.service_name, key, value)
                logger.info(f"Stored credential {key} in keyring")
                return True
        except Exception as e:
            logger.warning(f"Failed to store in keyring: {e}")
        
        # Fallback to encrypted file storage
        try:
            encrypted_value = self.cipher_suite.encrypt(value.encode())
            os.environ[f"{self.service_name.upper()}_{key.upper()}"] = encrypted_value.decode()
            logger.info(f"Stored encrypted credential {key} in environment")
            return True
        except Exception as e:
            logger.error(f"Failed to store credential: {e}")
            return False
    
    def get_credential(self, key: str, use_keyring: bool = True) -> Optional[str]:
        """
        Retrieve a stored credential.
        
        Args:
            key: The identifier for the credential
            use_keyring: Whether to attempt keyring retrieval first
            
        Returns:
            Optional[str]: The credential value if found, None otherwise
        """
        if use_keyring:
            try:
                value = keyring.get_password(self.service_name, key)
                if value:
                    return value
            except Exception as e:
                logger.warning(f"Failed to retrieve from keyring: {e}")
        
        # Try environment variable
        env_key = f"{self.service_name.upper()}_{key.upper()}"
        encrypted_value = os.getenv(env_key)
        if encrypted_value:
            try:
                decrypted_value = self.cipher_suite.decrypt(encrypted_value.encode())
                return decrypted_value.decode()
            except Exception as e:
                logger.error(f"Failed to decrypt credential: {e}")
        
        return None
    
    def delete_credential(self, key: str, use_keyring: bool = True) -> bool:
        """
        Delete a stored credential.
        
        Args:
            key: The identifier for the credential
            use_keyring: Whether to attempt keyring deletion first
            
        Returns:
            bool: True if deletion was successful
        """
        success = False
        
        if use_keyring:
            try:
                keyring.delete_password(self.service_name, key)
                success = True
                logger.info(f"Deleted credential {key} from keyring")
            except Exception as e:
                logger.warning(f"Failed to delete from keyring: {e}")
        
        # Also remove from environment if present
        env_key = f"{self.service_name.upper()}_{key.upper()}"
        if env_key in os.environ:
            del os.environ[env_key]
            success = True
            logger.info(f"Deleted credential {key} from environment")
        
        return success
    
    def list_credentials(self) -> Dict[str, Any]:
        """
        List all stored credentials (keys only, not values).
        
        Returns:
            Dict[str, Any]: Dictionary containing credential metadata
        """
        credentials = {}
        
        # List environment variables for this service
        prefix = f"{self.service_name.upper()}_"
        for key in os.environ:
            if key.startswith(prefix):
                clean_key = key[len(prefix):].lower()
                credentials[clean_key] = {"storage": "environment"}
        
        # Note: Keyring doesn't provide a native way to list all credentials
        # You would need to maintain a separate registry of keyring credentials
        
        return credentials
