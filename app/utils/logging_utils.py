"""
Logging utilities for the application
"""
import logging
import sys
from datetime import datetime
from typing import Optional, Any, Dict

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_info(message: str, logger: Optional[logging.Logger] = None, extra_data: Optional[Dict[str, Any]] = None):
    """
    Log an info message
    
    Args:
        message: Log message
        logger: Logger instance (optional)
        extra_data: Additional data to log (optional)
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    if extra_data:
        logger.info(f"{message} | Data: {extra_data}")
    else:
        logger.info(message)

def log_error(message: str, logger: Optional[logging.Logger] = None, extra_data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
    """
    Log an error message
    
    Args:
        message: Log message
        logger: Logger instance (optional)
        extra_data: Additional data to log (optional)
        exc_info: Include exception info (optional)
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    if extra_data:
        logger.error(f"{message} | Data: {extra_data}", exc_info=exc_info)
    else:
        logger.error(message, exc_info=exc_info)

def log_warning(message: str, logger: Optional[logging.Logger] = None, extra_data: Optional[Dict[str, Any]] = None):
    """
    Log a warning message
    
    Args:
        message: Log message
        logger: Logger instance (optional)
        extra_data: Additional data to log (optional)
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    if extra_data:
        logger.warning(f"{message} | Data: {extra_data}")
    else:
        logger.warning(message)

def setup_basic_logging(level: int = logging.INFO) -> None:
    """
    Setup basic logging configuration
    
    Args:
        level: Logging level (default: INFO)
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )




