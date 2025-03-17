"""
Unit tests for the app module.
"""
import pytest
from unittest.mock import patch, MagicMock

from dental_scraper.app import main


@patch('dental_scraper.app.setup_logging')
@patch('dental_scraper.app.logger')
def test_main_success(mock_logger, mock_setup_logging):
    """Test that the main function runs successfully and logs correctly."""
    # Call the main function
    main()
    
    # Verify logging was set up
    mock_setup_logging.assert_called_once()
    
    # Verify correct log messages were generated
    mock_logger.info.assert_called()


@patch('dental_scraper.app.setup_logging')
@patch('dental_scraper.app.logger')
def test_main_exception_handling(mock_logger, mock_setup_logging):
    """Test that exceptions are properly handled and logged."""
    # Setup the mock to raise an exception
    mock_setup_logging.side_effect = Exception("Test exception")
    
    # Call the main function
    main()
    
    # Verify exception was logged
    mock_logger.exception.assert_called_once()
    assert "Failed to run the scraper" in mock_logger.exception.call_args[0][0] 