from pathlib import Path
from extractors.cdt_extractor import CDTExtractor
from validators.data_validator import DataValidator
from loguru import logger

def process_insurance_pdf(pdf_path: str):
    """Process an insurance PDF file and extract CDT codes with requirements.
    
    Args:
        pdf_path: Path to the PDF file
    """
    # Initialize extractor and validator
    extractor = CDTExtractor(
        max_file_size=100 * 1024 * 1024,  # 100MB limit
        enable_ocr=True  # Enable OCR for scanned documents
    )
    validator = DataValidator()
    
    try:
        # Process the PDF
        logger.info(f"Processing PDF: {pdf_path}")
        results = extractor.process_pdf(pdf_path)
        
        # Validate results
        validation_report = validator.validate_extraction_results(results)
        summary = validator.get_validation_summary(validation_report)
        
        # Log results
        logger.info("Extraction completed successfully")
        logger.info(f"\n{summary}")
        
        # Save results if valid codes were found
        if validation_report['valid_codes'] > 0:
            output_path = Path(pdf_path).with_suffix('.json')
            import json
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to: {output_path}")
            
    except Exception as e:
        logger.error(f"Failed to process PDF: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    pdf_path = "sample.pdf"  # Replace with actual PDF path
    process_insurance_pdf(pdf_path) 