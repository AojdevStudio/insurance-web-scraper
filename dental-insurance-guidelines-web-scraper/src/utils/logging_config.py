"""
Logging configuration for the dental insurance guidelines web scraper.
"""
from loguru import logger
import sys
from pathlib import Path

def setup_logging(log_path: Path = None):
    """
    Configure logging for the application.
    
    Args:
        log_path (Path, optional): Path to store log files. Defaults to storage/logs.
    """
    if log_path is None:
        log_path = Path(__file__).parent.parent / "storage" / "logs"
    
    # Ensure log directory exists
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Remove default handler
    logger.remove()
    
    # Add console handler for INFO and above
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Add file handler for DEBUG and above
    logger.add(
        log_path / "debug_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # New file at midnight
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        compression="zip"
    )
    
    # Add file handler for ERROR and above
    logger.add(
        log_path / "error_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # New file at midnight
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        compression="zip"
    )
    
    logger.info("Logging configured successfully") 