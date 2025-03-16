"""
Validation utilities for insurance guidelines data.
"""
from typing import Dict, List, Optional, Tuple
from datetime import date

from pydantic import ValidationError
from loguru import logger

from .carrier import CarrierGuidelines
from .procedure import Procedure


class DataValidator:
    """
    Utility class for validating insurance guidelines data.
    """
    
    @staticmethod
    def validate_carrier_data(data: Dict) -> Tuple[bool, Optional[CarrierGuidelines], List[str]]:
        """
        Validate carrier guidelines data against the CarrierGuidelines model.
        
        Args:
            data: Dictionary containing carrier guidelines data
            
        Returns:
            Tuple containing:
            - Boolean indicating if validation passed
            - Validated CarrierGuidelines instance if successful, None if failed
            - List of validation error messages if any
        """
        try:
            validated_data = CarrierGuidelines(**data)
            return True, validated_data, []
        except ValidationError as e:
            errors = [f"{error['loc']}: {error['msg']}" for error in e.errors()]
            logger.error(f"Validation failed: {errors}")
            return False, None, errors
    
    @staticmethod
    def validate_procedure_data(data: Dict) -> Tuple[bool, Optional[Procedure], List[str]]:
        """
        Validate procedure data against the Procedure model.
        
        Args:
            data: Dictionary containing procedure data
            
        Returns:
            Tuple containing:
            - Boolean indicating if validation passed
            - Validated Procedure instance if successful, None if failed
            - List of validation error messages if any
        """
        try:
            validated_data = Procedure(**data)
            return True, validated_data, []
        except ValidationError as e:
            errors = [f"{error['loc']}: {error['msg']}" for error in e.errors()]
            logger.error(f"Validation failed: {errors}")
            return False, None, errors
    
    @staticmethod
    def validate_requirements_format(requirements: List[str]) -> List[str]:
        """
        Validate and standardize format of procedure requirements.
        
        Args:
            requirements: List of requirement strings
            
        Returns:
            List of formatted requirement strings
        """
        formatted = []
        for req in requirements:
            # Remove extra whitespace
            req = " ".join(req.split())
            # Ensure first letter is capitalized
            req = req[0].upper() + req[1:] if req else req
            # Ensure ends with period
            if req and not req.endswith('.'):
                req += '.'
            formatted.append(req)
        return formatted
    
    @staticmethod
    def validate_date_range(date_value: date) -> bool:
        """
        Validate if a date falls within the acceptable range (2024-2026).
        
        Args:
            date_value: Date to validate
            
        Returns:
            Boolean indicating if date is valid
        """
        min_date = date(2024, 1, 1)
        max_date = date(2026, 12, 31)
        return min_date <= date_value <= max_date 