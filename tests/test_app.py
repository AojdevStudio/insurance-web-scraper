"""
Tests for the main application module.
"""
import pytest
from unittest.mock import patch, MagicMock

# Import the main function directly
from dental_scraper.app import main

def test_main_success():
    """Test the main function runs successfully."""
    with patch('dental_scraper.app.setup_logging') as mock_setup_logging, \
         patch('loguru.logger.info') as mock_logger_info:
        
        # Run the function
        main()
        
        # Verify logging was set up
        mock_setup_logging.assert_called_once()
        
        # Verify start and completion messages were logged
        assert mock_logger_info.call_count >= 2
        mock_logger_info.assert_any_call("Starting dental insurance scraper")
        mock_logger_info.assert_any_call("Scraper execution completed")

def test_main_exception_handling():
    """Test that exceptions in the main function are properly handled."""
    with patch('dental_scraper.app.setup_logging', 
               side_effect=RuntimeError("Test error")), \
         patch('loguru.logger.error') as mock_logger_error:
        
        # Run the function, which should catch and re-raise the exception
        with pytest.raises(RuntimeError):
            main()
        
        # Verify the error was logged
        mock_logger_error.assert_called_once()
        assert "Error during scraper execution" in mock_logger_error.call_args[0][0] 