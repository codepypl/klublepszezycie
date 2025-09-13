"""
Logging utility functions - simplified version
"""
import logging

def get_logger(name):
    """Get a logger instance"""
    return logging.getLogger(name)

def log_info(message):
    """Log info message"""
    logger = logging.getLogger(__name__)
    logger.info(message)

def log_error(message):
    """Log error message"""
    logger = logging.getLogger(__name__)
    logger.error(message)

def log_warning(message):
    """Log warning message"""
    logger = logging.getLogger(__name__)
    logger.warning(message)
