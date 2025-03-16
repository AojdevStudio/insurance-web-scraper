"""
Tests for the data cleaning module.
"""

import pytest
from datetime import date
from dental_scraper.utils.data_cleaner import (
    TextNormalizer,
    CDTCodeCleaner,
    RequirementsCleaner,
    DateNormalizer,
    DataValidator,
    DataCleaner,
    DataCleaningPipeline
)


def test_text_normalizer():
    """Test the TextNormalizer class."""
    normalizer = TextNormalizer()
    
    # Test basic normalization
    assert normalizer.normalize("  Hello  World  ") == "Hello World"
    
    # Test unicode replacement
    assert normalizer.normalize("Bullet •") == "Bullet *"
    assert normalizer.normalize("Quote \"test\"") == "Quote \"test\""
    assert normalizer.normalize("Dash –") == "Dash -"


def test_cdt_code_cleaner():
    """Test the CDTCodeCleaner class."""
    cleaner = CDTCodeCleaner()
    
    # Test valid codes
    assert cleaner.clean("D0150") == "D0150"
    assert cleaner.clean("d0150") == "D0150"
    
    # Test codes with spaces
    assert cleaner.clean("D 0150") == "D0150"
    
    # Test invalid codes
    assert cleaner.clean("X0150") == ""
    assert cleaner.clean("D01") == ""
    
    # Test validation
    assert cleaner.validate("D0150") is True
    assert cleaner.validate("X0150") is False


def test_requirements_cleaner():
    """Test the RequirementsCleaner class."""
    cleaner = RequirementsCleaner()
    
    # Test basic cleaning
    requirements = [
        "• First requirement",
        "- Second requirement",
        "• First requirement",  # Duplicate
        "* Third requirement"
    ]
    
    cleaned = cleaner.clean(requirements)
    
    assert len(cleaned) == 3
    assert cleaned[0] == "First requirement"
    assert cleaned[1] == "Second requirement"
    assert cleaned[2] == "Third requirement"
    
    # Test empty list
    assert cleaner.clean([]) == []
    
    # Test None
    assert cleaner.clean(None) == []


def test_date_normalizer():
    """Test the DateNormalizer class."""
    normalizer = DateNormalizer()
    
    # Test various date formats
    assert normalizer.normalize("2024-01-01") == "2024-01-01"
    assert normalizer.normalize("01/01/2024") == "2024-01-01"
    assert normalizer.normalize("Jan 01, 2024") == "2024-01-01"
    
    # Test invalid dates
    assert normalizer.normalize("not a date") == "not a date"
    
    # Test empty string
    assert normalizer.normalize("") == ""


def test_data_validator():
    """Test the DataValidator class."""
    validator = DataValidator()
    
    # Test valid data
    valid_data = {
        "procedures": [
            {
                "code": "D0150",
                "description": "Comprehensive oral evaluation",
                "requirements": ["First requirement"]
            }
        ]
    }
    
    assert validator.validate_structure(valid_data) == {}
    assert validator.validate_content(valid_data) == {}
    
    # Test invalid data
    invalid_data = {
        "procedures": [
            {
                "code": "X0150",  # Invalid code
                "description": "",  # Empty description
                "requirements": []  # Empty requirements
            }
        ]
    }
    
    structure_errors = validator.validate_structure(invalid_data)
    assert "procedures" in structure_errors
    
    content_errors = validator.validate_content(invalid_data)
    assert "procedures" in content_errors


def test_data_cleaner():
    """Test the DataCleaner class."""
    cleaner = DataCleaner()
    
    # Test procedure cleaning
    procedure = {
        "code": "d 0150",
        "description": "  Comprehensive oral evaluation  ",
        "requirements": ["• First requirement", "• First requirement", "- Second requirement"],
        "effective_date": "01/01/2024",
        "notes": "  Some notes  "
    }
    
    cleaned = cleaner.clean_procedure(procedure)
    
    assert cleaned["code"] == "D0150"
    assert cleaned["description"] == "Comprehensive oral evaluation"
    assert len(cleaned["requirements"]) == 2
    assert cleaned["effective_date"] == "2024-01-01"
    assert cleaned["notes"] == "Some notes"


def test_data_cleaning_pipeline():
    """Test the DataCleaningPipeline class."""
    pipeline = DataCleaningPipeline()
    
    # Test valid data
    valid_data = {
        "carrier": "  Aetna  ",
        "last_updated": "01/01/2024",
        "procedures": [
            {
                "code": "D0150",
                "description": "Comprehensive oral evaluation",
                "requirements": ["First requirement"]
            }
        ]
    }
    
    cleaned = pipeline.process(valid_data)
    
    assert cleaned["carrier"] == "Aetna"
    assert cleaned["last_updated"] == "2024-01-01"
    assert len(cleaned["procedures"]) == 1
    assert "validation_errors" not in cleaned
    
    # Test invalid data
    invalid_data = {
        "carrier": "Aetna",
        "last_updated": "01/01/2024",
        "procedures": [
            {
                "code": "X0150",  # Invalid code
                "description": "",  # Empty description
                "requirements": []  # Empty requirements
            }
        ]
    }
    
    cleaned_invalid = pipeline.process(invalid_data)
    
    assert "validation_errors" in cleaned_invalid 