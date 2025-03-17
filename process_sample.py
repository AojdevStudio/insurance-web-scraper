"""Script to process a sample dental guidelines PDF."""

import json
from pathlib import Path
from loguru import logger
from pdf_processor import PDFProcessor

def main():
    """Process the sample PDF and display results."""
    processor = PDFProcessor()
    pdf_path = "sample_dental_guidelines.pdf"
    
    try:
        results = processor.process_pdf(pdf_path)
        
        print("\nExtracted CDT Codes:")
        print("=" * 80)
        
        if not results:
            print("No CDT codes found in the PDF.")
            return
            
        for item in results:
            print(f"\nCDT Code: {item['cdt_code']}")
            print(f"Description: {item['description']}")
            print("Requirements:")
            for req in item['requirements']:
                print(f"  • {req}")
            print("-" * 80)
            
        # Save results to JSON
        output_path = Path("extracted_data.json")
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise

if __name__ == "__main__":
    main() 