"""
Tests for the logging configuration module.
"""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from dental_scraper.utils.logging_config import setup_logging

def test_setup_logging_default_path():
    """Test setup_logging with default path."""
    with patch('pathlib.Path.mkdir') as mock_mkdir, \
         patch('loguru.logger.remove') as mock_remove, \
         patch('loguru.logger.add') as mock_add, \
         patch('loguru.logger.info') as mock_info:
        
        # Call the function
        setup_logging()
        
        # Verify log directory was created
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        # Verify default logger was removed
        mock_remove.assert_called_once()
        
        # Verify loggers were added (3 calls: console, debug file, error file)
        assert mock_add.call_count == 3
        
        # Verify success message was logged
        mock_info.assert_called_once_with("Logging configured successfully")

def test_setup_logging_custom_path():
    """Test setup_logging with custom path."""
    custom_path = Path("/tmp/custom_logs")
    
    with patch('pathlib.Path.mkdir') as mock_mkdir, \
         patch('loguru.logger.remove') as mock_remove, \
         patch('loguru.logger.add') as mock_add, \
         patch('loguru.logger.info') as mock_info:
        
        # Call the function with custom path
        setup_logging(log_path=custom_path)
        
        # Verify custom log directory was created
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        # Verify default logger was removed
        mock_remove.assert_called_once()
        
        # Verify loggers were added (3 calls: console, debug file, error file)
        assert mock_add.call_count == 3
        
        # Verify debug and error log calls use the custom path
        call_args_list = mock_add.call_args_list
        assert str(custom_path) in str(call_args_list[1])  # Debug log
        assert str(custom_path) in str(call_args_list[2])  # Error log
        
        # Verify success message was logged
        mock_info.assert_called_once_with("Logging configured successfully")

def test_setup_logging_exception_handling():
    """Test exception handling in setup_logging."""
    with patch('pathlib.Path.mkdir', side_effect=PermissionError("Access denied")), \
         patch('loguru.logger.error') as mock_error:
        
        # The function should raise the exception
        with pytest.raises(PermissionError):
            setup_logging() 