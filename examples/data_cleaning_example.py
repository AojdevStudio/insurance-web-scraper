#!/usr/bin/env python3
"""
Example of using the DataCleaningPipeline.

This script demonstrates how to use the DataCleaningPipeline to clean
and validate dental insurance guidelines data.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dental_scraper.utils.data_cleaner import DataCleaningPipeline
from dental_scraper.exceptions import DataCleaningException


def setup_logging():
    """Set up basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )


def load_sample_data():
    """
    Load sample data for demonstration.
    
    Returns:
        dict: Sample data
    """
    # Sample data representing extracted insurance guidelines
    return {
        "carrier": "  Aetna  ",
        "year": 2024,
        "source_url": "https://www.aetna.com/dental/guidelines-2024.pdf",
        "last_updated": "01/01/2024",
        "procedures": [
            {
                "code": "d 0150",
                "description": "  Comprehensive oral evaluation - new or established patient  ",
                "requirements": [
                    "• Complete charting of all teeth and existing restorations",
                    "• Documentation of patient's chief complaint",
                    "• Complete charting of all teeth and existing restorations",  # Duplicate
                    "- Medical and dental history"
                ],
                "notes": "  Limited to once per provider  ",
                "effective_date": "2024-01-01"
            },
            {
                "code": "D0220",
                "description": "Intraoral - periapical first radiographic image",
                "requirements": [
                    "• Radiographic image showing entire tooth and surrounding structures",
                    "• Date of service"
                ],
                "notes": "Maximum of 1 PA per day unless documentation supports necessity",
                "effective_date": "01/01/2024"
            },
            {
                # This one has some issues for validation to catch
                "code": "X0150",  # Invalid code
                "description": "",  # Empty description
                "requirements": [],  # Empty requirements
                "notes": "Some notes",
                "effective_date": "2024-01-01"
            }
        ]
    }


def main():
    """Run the example."""
    setup_logging()
    logger = logging.getLogger("data_cleaning_example")
    
    logger.info("Starting data cleaning example")
    
    # Load sample data
    data = load_sample_data()
    logger.info(f"Loaded sample data with {len(data['procedures'])} procedures")
    
    # Initialize the pipeline
    pipeline = DataCleaningPipeline()
    
    try:
        # Process the data
        logger.info("Processing data through the cleaning pipeline")
        cleaned_data = pipeline.process(data)
        
        # Check for validation errors
        if 'validation_errors' in cleaned_data:
            logger.warning("Validation errors found in the data:")
            for error_type, errors in cleaned_data['validation_errors'].items():
                logger.warning(f"  {error_type} errors: {errors}")
        
        # Output the cleaned data
        logger.info("Cleaned data:")
        for proc in cleaned_data['procedures']:
            if proc.get('code'):
                logger.info(f"  Procedure: {proc['code']} - {proc.get('description', '')}")
                if 'requirements' in proc:
                    logger.info(f"    Requirements: {len(proc['requirements'])}")
                    for req in proc['requirements']:
                        logger.info(f"      - {req}")
        
        # Save the cleaned data to a file
        output_file = "cleaned_data_example.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Cleaned data saved to {output_file}")
        
    except DataCleaningException as e:
        logger.error(f"Error during data cleaning: {e}")
        sys.exit(1)
    
    logger.info("Data cleaning example completed successfully")


if __name__ == "__main__":
    main() 