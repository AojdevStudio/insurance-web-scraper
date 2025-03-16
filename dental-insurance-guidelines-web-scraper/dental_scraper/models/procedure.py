"""
Models for dental procedures and CDT codes.
"""
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field, validator


class Procedure(BaseModel):
    """
    Model representing a dental procedure with its CDT code and requirements.
    """
    code: str = Field(..., pattern=r'^D\d{4}$', description="CDT code (e.g., D0150)")
    description: str = Field(..., description="Official procedure description")
    requirements: List[str] = Field(
        ...,
        description="List of documentation requirements",
        min_items=1
    )
    notes: Optional[str] = Field(None, description="Additional notes or special considerations")
    effective_date: date = Field(..., description="When these requirements take effect")
    
    @validator('code')
    def validate_cdt_code(cls, v: str) -> str:
        """Validate CDT code format."""
        if not v.startswith('D') or not len(v) == 5:
            raise ValueError('Invalid CDT code format. Must be D followed by 4 digits.')
        try:
            int(v[1:])  # Validate digits after D
        except ValueError:
            raise ValueError('Invalid CDT code format. Must be D followed by 4 digits.')
        return v.upper()
    
    @validator('requirements')
    def validate_requirements(cls, v: List[str]) -> List[str]:
        """Validate requirements are not empty strings."""
        if not all(req.strip() for req in v):
            raise ValueError('Requirements cannot be empty strings')
        return [req.strip() for req in v]
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "code": "D0150",
                "description": "Comprehensive oral evaluation - new or established patient",
                "requirements": [
                    "Complete charting of all teeth and existing restorations",
                    "Documentation of patient's chief complaint",
                    "Medical and dental history"
                ],
                "notes": "Limited to once per provider",
                "effective_date": "2024-01-01"
            }
        } 