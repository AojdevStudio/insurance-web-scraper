"""
Unit tests for the data cleaner module.
"""
import pytest
from unittest.mock import patch, MagicMock

from dental_scraper.utils.data_cleaner import (
    DataCleaner,
    clean_amount,
    clean_procedure_code,
    clean_percentage,
    normalize_text,
    remove_currency,
    extract_percentage
)


@pytest.fixture
def data_cleaner():
    """Create a DataCleaner instance for testing."""
    return DataCleaner()


def test_clean_amount():
    """Test cleaning of monetary amounts."""
    # Test with currency symbols
    assert clean_amount("$123.45") == 123.45
    assert clean_amount("$1,234.56") == 1234.56
    
    # Test with text and currency
    assert clean_amount("Patient pays $50.00") == 50.0
    assert clean_amount("Fee: $ 75.25") == 75.25
    
    # Test with negative amounts
    assert clean_amount("-$25.00") == -25.0
    assert clean_amount("($100.00)") == -100.0
    
    # Test with no numeric content
    assert clean_amount("No fee") is None
    assert clean_amount("N/A") is None
    assert clean_amount("") is None
    
    # Test with None value
    assert clean_amount(None) is None


def test_clean_procedure_code():
    """Test cleaning of procedure codes."""
    # Test with valid codes
    assert clean_procedure_code("D0120") == "D0120"
    assert clean_procedure_code("d0120") == "D0120"  # Should capitalize
    
    # Test with spaces and special characters
    assert clean_procedure_code("D 0120") == "D0120"
    assert clean_procedure_code("D-0120") == "D0120"
    assert clean_procedure_code("Code: D0120") == "D0120"
    
    # Test with invalid formats
    assert clean_procedure_code("12345") is None
    assert clean_procedure_code("X0120") is None
    assert clean_procedure_code("D01") is None  # Too short
    assert clean_procedure_code("D01234") is None  # Too long
    
    # Test with None value
    assert clean_procedure_code(None) is None


def test_clean_percentage():
    """Test cleaning of percentage values."""
    # Test with percent symbol
    assert clean_percentage("80%") == 80.0
    assert clean_percentage("100 %") == 100.0
    
    # Test with decimal percentages
    assert clean_percentage("75.5%") == 75.5
    assert clean_percentage("0.8") == 80.0  # Should convert to percentage
    assert clean_percentage("0.75") == 75.0
    
    # Test with text and percentages
    assert clean_percentage("Insurance pays 80%") == 80.0
    assert clean_percentage("Coverage: 50 percent") == 50.0
    
    # Test with no numeric content
    assert clean_percentage("Not covered") is None
    assert clean_percentage("N/A") is None
    assert clean_percentage("") is None
    
    # Test with None value
    assert clean_percentage(None) is None


def test_normalize_text():
    """Test text normalization."""
    # Test with spaces and capitalization
    assert normalize_text("  Sample Text  ") == "sample text"
    assert normalize_text("UPPER CASE") == "upper case"
    
    # Test with special characters
    assert normalize_text("Text with special-characters!") == "text with special-characters!"
    
    # Test with multiple spaces
    assert normalize_text("Multiple   spaces") == "multiple spaces"
    
    # Test with newlines and tabs
    assert normalize_text("Text with\nnewlines\tand tabs") == "text with newlines and tabs"
    
    # Test with None value
    assert normalize_text(None) == ""


def test_remove_currency():
    """Test removal of currency symbols."""
    # Test with dollar signs
    assert remove_currency("$123.45") == "123.45"
    assert remove_currency("$ 123.45") == "123.45"
    
    # Test with other currency symbols
    assert remove_currency("€100.00") == "100.00"
    assert remove_currency("£75.50") == "75.50"
    
    # Test with text
    assert remove_currency("Payment: $50") == "Payment: 50"
    
    # Test with no currency symbols
    assert remove_currency("123.45") == "123.45"
    
    # Test with None value
    assert remove_currency(None) == ""


def test_extract_percentage():
    """Test extraction of percentage values."""
    # Test with percent symbol
    assert extract_percentage("80%") == 80.0
    assert extract_percentage("100 %") == 100.0
    
    # Test with text and percentages
    assert extract_percentage("Insurance covers 75% of the cost") == 75.0
    assert extract_percentage("Coverage at fifty percent (50%)") == 50.0
    
    # Test with decimal values
    assert extract_percentage("0.8 or 80%") == 80.0
    
    # Test with no percentage content
    assert extract_percentage("No percentage here") is None
    assert extract_percentage("") is None
    
    # Test with None value
    assert extract_percentage(None) is None


def test_data_cleaner_clean_procedure_data(data_cleaner):
    """Test cleaning of procedure data."""
    # Create sample raw procedure data
    raw_data = {
        "code": "d0120",
        "description": "  PERIODIC ORAL EVALUATION  ",
        "patient_pays": "$25.00",
        "insurance_pays": "75%"
    }
    
    # Clean the data
    cleaned = data_cleaner.clean_procedure_data(raw_data)
    
    # Verify cleaned data
    assert cleaned["code"] == "D0120"
    assert cleaned["description"] == "periodic oral evaluation"
    assert cleaned["patient_pays"] == 25.0
    assert cleaned["insurance_pays"] == 75.0


def test_data_cleaner_clean_procedure_data_invalid(data_cleaner):
    """Test cleaning with invalid procedure data."""
    # Invalid code
    invalid_data = {
        "code": "x0120",
        "description": "Test procedure",
        "patient_pays": "$25.00",
        "insurance_pays": "75%"
    }
    
    cleaned = data_cleaner.clean_procedure_data(invalid_data)
    assert cleaned["code"] is None
    
    # Missing fields
    incomplete_data = {
        "code": "D0120",
        "description": "Test procedure"
    }
    
    cleaned = data_cleaner.clean_procedure_data(incomplete_data)
    assert cleaned["code"] == "D0120"
    assert cleaned["description"] == "test procedure"
    assert "patient_pays" not in cleaned or cleaned["patient_pays"] is None
    assert "insurance_pays" not in cleaned or cleaned["insurance_pays"] is None


def test_data_cleaner_clean_procedures_list(data_cleaner):
    """Test cleaning a list of procedures."""
    # Create sample raw procedure data list
    raw_data_list = [
        {
            "code": "d0120",
            "description": "  PERIODIC ORAL EVALUATION  ",
            "patient_pays": "$25.00",
            "insurance_pays": "75%"
        },
        {
            "code": "d0150",
            "description": "COMPREHENSIVE ORAL EVALUATION",
            "patient_pays": "$45.00",
            "insurance_pays": "60%"
        }
    ]
    
    # Clean the data list
    cleaned_list = data_cleaner.clean_procedures_list(raw_data_list)
    
    # Verify the list was properly cleaned
    assert len(cleaned_list) == 2
    assert cleaned_list[0]["code"] == "D0120"
    assert cleaned_list[0]["patient_pays"] == 25.0
    assert cleaned_list[1]["code"] == "D0150"
    assert cleaned_list[1]["insurance_pays"] == 60.0


def test_data_cleaner_clean_procedures_list_with_invalid(data_cleaner):
    """Test cleaning a list of procedures that includes invalid data."""
    # Create sample raw procedure data list with one invalid entry
    raw_data_list = [
        {
            "code": "d0120",
            "description": "  PERIODIC ORAL EVALUATION  ",
            "patient_pays": "$25.00",
            "insurance_pays": "75%"
        },
        {
            "code": "x9999",  # Invalid code
            "description": "INVALID PROCEDURE",
            "patient_pays": "$45.00",
            "insurance_pays": "60%"
        }
    ]
    
    # Clean the data list
    cleaned_list = data_cleaner.clean_procedures_list(raw_data_list)
    
    # Verify the list was properly cleaned and invalid entry was skipped
    assert len(cleaned_list) == 1
    assert cleaned_list[0]["code"] == "D0120"
    
    # Test with remove_invalid=False
    cleaned_list = data_cleaner.clean_procedures_list(raw_data_list, remove_invalid=False)
    
    # Verify the list includes both entries, with code=None for the invalid one
    assert len(cleaned_list) == 2
    assert cleaned_list[1]["code"] is None 