#!/usr/bin/env python3
"""
Script to run the Aetna spider programmatically.
"""
import os
import sys
from pathlib import Path
import json
from datetime import datetime

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from loguru import logger

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the Aetna spider
from dental_scraper.spiders.aetna_spider import AetnaSpider
from dental_scraper.utils.logging_config import setup_logging


def run_aetna_spider(output_file=None):
    """
    Run the Aetna spider programmatically.
    
    Args:
        output_file (str, optional): Path to save the output JSON. 
                                    If None, a default path will be used.
    """
    try:
        # Set up logging
        setup_logging()
        
        logger.info("Starting Aetna spider")
        
        # Get credentials from environment variables
        username = os.getenv('AETNA_USERNAME')
        password = os.getenv('AETNA_PASSWORD')
        
        if not username or not password:
            logger.error("Missing credentials. Please set AETNA_USERNAME and AETNA_PASSWORD environment variables.")
            sys.exit(1)
        
        credentials = {
            'username': username,
            'password': password
        }
        
        # Create output directory if it doesn't exist
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set default output file if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f"aetna_guidelines_{timestamp}.json"
        
        logger.info(f"Spider will save results to {output_file}")
        
        # Configure the crawler process
        settings = get_project_settings()
        settings.update({
            'FEEDS': {
                str(output_file): {
                    'format': 'json',
                    'encoding': 'utf8',
                    'indent': 2,
                    'overwrite': True,
                },
            },
            'LOG_LEVEL': 'INFO',
        })
        
        # Create and start the crawler process
        process = CrawlerProcess(settings)
        process.crawl(AetnaSpider, credentials=credentials)
        
        # Start the crawling process (this will block until finished)
        process.start()
        
        logger.info("Aetna spider completed")
        return output_file

    except Exception as e:
        logger.error(f"Error running spider: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Run the Aetna spider')
    parser.add_argument('--output', '-o', type=str, help='Output file path')
    args = parser.parse_args()
    
    # Run the spider
    output_file = run_aetna_spider(args.output)
    
    if output_file:
        logger.info(f"Results saved to {output_file}") 