"""
Tests for the data validation module.
"""
import pytest
from datetime import date
from unittest.mock import patch

from dental_scraper.models.validation import DataValidator
from dental_scraper.models.procedure import Procedure
from dental_scraper.models.carrier import CarrierGuidelines

@pytest.fixture
def validator():
    """Create a DataValidator instance for testing."""
    return DataValidator()

@pytest.fixture
def valid_procedure_data():
    """Return valid procedure data for testing."""
    return {
        'code': 'D0150',
        'description': 'Comprehensive oral evaluation',
        'requirements': [
            'Patient must be new to the practice',
            'Complete examination required'
        ],
        'notes': 'Limited to once every 3 years',
        'effective_date': '2024-01-01'
    }

@pytest.fixture
def valid_carrier_data():
    """Return valid carrier guidelines data for testing."""
    return {
        'carrier': 'Test Carrier',
        'year': 2024,
        'source_url': 'https://example.com/guidelines',
        'last_updated': date.today(),
        'procedures': [
            {
                'code': 'D0150',
                'description': 'Comprehensive oral evaluation',
                'requirements': [
                    'Patient must be new to the practice',
                    'Complete examination required'
                ],
                'notes': 'Limited to once every 3 years',
                'effective_date': '2024-01-01'
            }
        ],
        'metadata': {
            'pdf_filename': 'test.pdf',
            'extraction_date': '2024-01-01T00:00:00'
        }
    }

def test_validate_requirements_format(validator):
    """Test validation and formatting of requirements."""
    requirements = [
        "- Patient must be new to the practice.",
        "• Complete examination required.",
        "* Documentation of medical history.",
        "  Some other requirement with leading spaces."
    ]
    
    result = validator.validate_requirements_format(requirements)
    
    # Check all requirements were properly formatted
    assert len(result) == 4
    assert result[0] == "- Patient must be new to the practice."
    assert "Complete examination required." in result[1]
    assert "Documentation of medical history." in result[2]
    assert "Some other requirement with leading spaces." in result[3]
    
    # Test with empty requirements
    assert validator.validate_requirements_format([]) == []
    
    # Test with None
    with pytest.raises(TypeError):
        validator.validate_requirements_format(None)

def test_validate_procedure_data_success(validator, valid_procedure_data):
    """Test successful validation of procedure data."""
    success, validated_data, errors = validator.validate_procedure_data(valid_procedure_data)
    
    assert success is True
    assert validated_data is not None
    assert isinstance(validated_data, Procedure)
    assert validated_data.code == valid_procedure_data['code']
    assert validated_data.description == valid_procedure_data['description']
    assert list(validated_data.requirements) == valid_procedure_data['requirements']
    assert validated_data.notes == valid_procedure_data['notes']
    assert not errors  # Empty list is falsy

def test_validate_procedure_data_invalid_code(validator, valid_procedure_data):
    """Test validation of procedure data with invalid code."""
    # Test with invalid code format
    invalid_data = valid_procedure_data.copy()
    invalid_data['code'] = '150'  # Missing D prefix
    
    success, validated_data, errors = validator.validate_procedure_data(invalid_data)
    
    assert success is False
    assert validated_data is None
    assert errors is not None
    assert len(errors) > 0

def test_validate_procedure_data_missing_fields(validator, valid_procedure_data):
    """Test validation of procedure data with missing required fields."""
    # Test with missing description
    invalid_data = valid_procedure_data.copy()
    del invalid_data['description']
    
    success, validated_data, errors = validator.validate_procedure_data(invalid_data)
    
    assert success is False
    assert validated_data is None
    assert errors is not None
    assert len(errors) > 0

def test_validate_carrier_data_success(validator, valid_carrier_data):
    """Test successful validation of carrier guidelines data."""
    success, validated_data, errors = validator.validate_carrier_data(valid_carrier_data)
    
    assert success is True
    assert validated_data is not None
    assert isinstance(validated_data, CarrierGuidelines)
    assert validated_data.carrier == valid_carrier_data['carrier']
    assert validated_data.year == valid_carrier_data['year']
    assert str(validated_data.source_url) == valid_carrier_data['source_url']
    assert len(validated_data.procedures) == 1
    assert not errors  # Empty list is falsy

def test_validate_carrier_data_invalid(validator, valid_carrier_data):
    """Test validation of carrier data with invalid fields."""
    # Test with invalid year
    invalid_data = valid_carrier_data.copy()
    invalid_data['year'] = 1900  # Year too old
    
    success, validated_data, errors = validator.validate_carrier_data(invalid_data)
    
    assert success is False
    assert validated_data is None
    assert errors is not None
    assert len(errors) > 0
    
    # Test with invalid URL
    invalid_data = valid_carrier_data.copy()
    invalid_data['source_url'] = 'not-a-url'
    
    success, validated_data, errors = validator.validate_carrier_data(invalid_data)
    
    assert success is False
    assert validated_data is None
    assert errors is not None
    assert len(errors) > 0

def test_validate_carrier_data_invalid_procedures(validator, valid_carrier_data):
    """Test validation of carrier data with invalid procedures."""
    # Test with invalid procedure
    invalid_data = valid_carrier_data.copy()
    invalid_data['procedures'][0]['code'] = '150'  # Invalid code
    
    with patch.object(validator, 'validate_procedure_data', 
                      return_value=(False, None, ["Invalid procedure code"])):
        success, validated_data, errors = validator.validate_carrier_data(invalid_data)
        
        assert success is False
        assert validated_data is None
        assert errors is not None
        assert len(errors) > 0

def test_is_valid_cdt_code(validator):
    """Test validation of CDT codes."""
    # The method is likely private or implemented differently
    # Let's use the validate_procedure_data method to test CDT code validation
    
    # Test with valid code
    valid_data = {
        'code': 'D0150',
        'description': 'Test procedure',
        'requirements': ['Test requirement'],
        'effective_date': '2024-01-01',
        'notes': 'Test notes'
    }
    success, _, _ = validator.validate_procedure_data(valid_data)
    assert success is True
    
    # Test with invalid code
    invalid_data = {
        'code': 'X0150',  # Invalid prefix
        'description': 'Test procedure',
        'requirements': ['Test requirement'],
        'effective_date': '2024-01-01',
        'notes': 'Test notes'
    }
    success, _, errors = validator.validate_procedure_data(invalid_data)
    assert success is False
    # The error message uses a regex pattern match, not "Invalid CDT code"
    assert any("String should match pattern" in str(err) for err in errors) 