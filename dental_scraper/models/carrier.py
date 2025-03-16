"""
Models for insurance carrier guidelines.
"""
from typing import Dict, List, Optional
from datetime import date
from pydantic import BaseModel, Field, HttpUrl

from .procedure import Procedure


class CarrierGuidelines(BaseModel):
    """
    Model representing insurance carrier guidelines.
    """
    carrier: str = Field(..., description="Insurance carrier name")
    year: int = Field(
        ...,
        ge=2024,
        le=2026,
        description="Year these guidelines are effective"
    )
    source_url: HttpUrl = Field(..., description="URL where guidelines were obtained")
    last_updated: date = Field(..., description="Last update date of the guidelines")
    procedures: List[Procedure] = Field(
        ...,
        description="List of procedures and their requirements",
        min_items=1
    )
    metadata: Dict = Field(
        default_factory=dict,
        description="Additional carrier-specific metadata"
    )
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "carrier": "Aetna",
                "year": 2024,
                "source_url": "https://www.aetna.com/dental/guidelines-2024.pdf",
                "last_updated": "2024-01-01",
                "procedures": [
                    {
                        "code": "D0150",
                        "description": "Comprehensive oral evaluation",
                        "requirements": [
                            "Complete charting",
                            "Medical history"
                        ],
                        "notes": "Once per provider",
                        "effective_date": "2024-01-01"
                    }
                ],
                "metadata": {
                    "version": "2024.1",
                    "region": "National",
                    "plan_types": ["PPO", "DMO"]
                }
            }
        } 