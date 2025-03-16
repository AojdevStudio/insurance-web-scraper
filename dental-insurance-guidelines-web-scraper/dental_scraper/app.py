"""
Main entry point for the dental scraper.
"""
from loguru import logger
from utils.logging_config import setup_logging

def main():
    """
    Main entry point for the scraper application.
    """
    try:
        # Set up logging
        setup_logging()
        
        logger.info("Starting dental insurance scraper")
        
        # TODO: Initialize and run scrapers
        pass
    except Exception as e:
        # Log the error before re-raising
        logger.error(f"Error during scraper execution: {e}")
        raise
    finally:
        logger.info("Scraper execution completed")

if __name__ == "__main__":
    main()
