"""
Unit tests for the validation module.
"""
import pytest
from unittest.mock import MagicMock, patch

from dental_scraper.models.validation import (
    ValidationResult,
    DataValidator,
    InvalidProcedureCodeError,
    MissingRequiredFieldError
)
from dental_scraper.models.procedure import Procedure
from dental_scraper.models.carrier import Carrier


@pytest.fixture
def validator():
    """Create a DataValidator instance for testing."""
    return DataValidator()


@pytest.fixture
def valid_procedure():
    """Create a valid procedure for testing."""
    return Procedure(
        code="D0120",
        description="Periodic oral evaluation - established patient",
        patient_pays=25.0,
        insurance_pays=75.0,
        carrier=Carrier.AETNA
    )


@pytest.fixture
def invalid_procedure():
    """Create an invalid procedure for testing."""
    return Procedure(
        code="X9999",  # Invalid code format
        description="Invalid procedure",
        patient_pays=25.0,
        insurance_pays=75.0,
        carrier=Carrier.AETNA
    )


@pytest.fixture
def incomplete_procedure():
    """Create an incomplete procedure for testing."""
    return Procedure(
        code="D0120",
        description="",  # Missing description
        patient_pays=None,  # Missing patient pays
        insurance_pays=75.0,
        carrier=Carrier.AETNA
    )


def test_validation_result_init():
    """Test ValidationResult initialization."""
    # Valid result
    result = ValidationResult(is_valid=True)
    assert result.is_valid is True
    assert result.errors == []
    
    # Invalid result with errors
    errors = ["Error 1", "Error 2"]
    result = ValidationResult(is_valid=False, errors=errors)
    assert result.is_valid is False
    assert result.errors == errors


def test_validation_result_str():
    """Test ValidationResult string representation."""
    # Valid result
    result = ValidationResult(is_valid=True)
    assert str(result) == "ValidationResult(valid=True, errors=[])"
    
    # Invalid result with errors
    result = ValidationResult(is_valid=False, errors=["Error 1", "Error 2"])
    assert str(result) == "ValidationResult(valid=False, errors=['Error 1', 'Error 2'])"


def test_validate_procedure_code_valid(validator):
    """Test validation of valid procedure codes."""
    # Test with valid codes
    valid_codes = ["D0120", "D0150", "D0210", "D1110"]
    for code in valid_codes:
        result = validator.validate_procedure_code(code)
        assert result.is_valid is True
        assert len(result.errors) == 0


def test_validate_procedure_code_invalid(validator):
    """Test validation of invalid procedure codes."""
    # Test with invalid codes
    invalid_codes = ["X0120", "123456", "D01", "D01234", "", None]
    for code in invalid_codes:
        result = validator.validate_procedure_code(code)
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("procedure code" in str(err).lower() for err in result.errors)


def test_validate_required_fields_valid(validator, valid_procedure):
    """Test validation of required fields with valid data."""
    result = validator.validate_required_fields(valid_procedure)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_required_fields_invalid(validator, incomplete_procedure):
    """Test validation of required fields with missing data."""
    result = validator.validate_required_fields(incomplete_procedure)
    assert result.is_valid is False
    assert len(result.errors) > 0
    # Should mention missing fields
    error_str = ' '.join(str(err) for err in result.errors).lower()
    assert "description" in error_str
    assert "patient_pays" in error_str


def test_validate_procedure_valid(validator, valid_procedure):
    """Test validation of a valid procedure."""
    result = validator.validate_procedure(valid_procedure)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_procedure_invalid_code(validator, invalid_procedure):
    """Test validation of a procedure with invalid code."""
    result = validator.validate_procedure(invalid_procedure)
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert any("procedure code" in str(err).lower() for err in result.errors)


def test_validate_procedure_missing_fields(validator, incomplete_procedure):
    """Test validation of a procedure with missing fields."""
    result = validator.validate_procedure(incomplete_procedure)
    assert result.is_valid is False
    assert len(result.errors) > 0
    error_str = ' '.join(str(err) for err in result.errors).lower()
    assert "description" in error_str
    assert "patient_pays" in error_str


def test_validate_procedures_all_valid(validator, valid_procedure):
    """Test validation of multiple valid procedures."""
    procedures = [valid_procedure, valid_procedure.copy()]
    result = validator.validate_procedures(procedures)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_procedures_some_invalid(validator, valid_procedure, invalid_procedure, incomplete_procedure):
    """Test validation of a mix of valid and invalid procedures."""
    procedures = [valid_procedure, invalid_procedure, incomplete_procedure]
    result = validator.validate_procedures(procedures)
    assert result.is_valid is False
    assert len(result.errors) > 0
    
    # Should contain errors for invalid and incomplete procedures
    error_str = ' '.join(str(err) for err in result.errors).lower()
    assert "procedure code" in error_str
    assert "description" in error_str
    assert "patient_pays" in error_str


def test_validate_procedures_empty(validator):
    """Test validation of an empty procedure list."""
    result = validator.validate_procedures([])
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_data_consistency_valid(validator, valid_procedure):
    """Test data consistency validation with valid data."""
    procedures = [valid_procedure, valid_procedure.copy()]
    result = validator.validate_data_consistency(procedures)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_data_consistency_mixed_carriers(validator, valid_procedure):
    """Test data consistency validation with mixed carriers."""
    procedure1 = valid_procedure.copy()
    procedure1.carrier = Carrier.AETNA
    
    procedure2 = valid_procedure.copy()
    procedure2.carrier = Carrier.CIGNA
    
    procedures = [procedure1, procedure2]
    result = validator.validate_data_consistency(procedures)
    assert result.is_valid is False
    assert len(result.errors) > 0
    assert any("carrier" in str(err).lower() for err in result.errors)


def test_validate_data_consistency_duplicate_codes(validator, valid_procedure):
    """Test data consistency validation with duplicate codes."""
    # Two procedures with the same code
    procedure1 = valid_procedure.copy()
    procedure1.code = "D0120"
    
    procedure2 = valid_procedure.copy()
    procedure2.code = "D0120"
    
    procedures = [procedure1, procedure2]
    
    # This should still be valid in basic validation
    result = validator.validate_data_consistency(procedures)
    assert result.is_valid is True


def test_validate_data_consistency_mismatched_values(validator, valid_procedure):
    """Test data consistency validation with procedures with same code but different values."""
    # Two procedures with the same code but different values
    procedure1 = valid_procedure.copy()
    procedure1.code = "D0120"
    procedure1.patient_pays = 25.0
    
    procedure2 = valid_procedure.copy()
    procedure2.code = "D0120"
    procedure2.patient_pays = 30.0  # Different value
    
    procedures = [procedure1, procedure2]
    
    # Enable strict validation
    result = validator.validate_data_consistency(procedures, strict=True)
    assert result.is_valid is False
    assert len(result.errors) > 0
    error_str = ' '.join(str(err) for err in result.errors).lower()
    assert "d0120" in error_str
    assert "patient_pays" in error_str


def test_exception_classes():
    """Test exception classes behavior."""
    # Test InvalidProcedureCodeError
    error = InvalidProcedureCodeError("D9999")
    assert "D9999" in str(error)
    
    # Test MissingRequiredFieldError
    error = MissingRequiredFieldError("description")
    assert "description" in str(error) 