"""
WSGI entry point for Gunicorn
"""
import sys
import logging
from datetime import datetime
from app import create_app

# Configure logging to file
def setup_logging():
    """Setup logging to file with daily rotation"""
    import os
    from logging.handlers import TimedRotatingFileHandler
    
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create log filename (without timestamp - rotation will handle it)
    log_file = os.path.join(logs_dir, 'wsgi.log')
    
    # Create rotating file handler (daily rotation)
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',  # Rotate at midnight
        interval=1,       # Every 1 day
        backupCount=30,   # Keep 30 days of logs
        encoding='utf-8',
        utc=False  # Use local time
    )
    
    # Set log format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            file_handler,
            logging.StreamHandler(sys.stdout)  # Also show in console
        ]
    )
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 WSGI Application starting - Logs saved to: {log_file} (daily rotation)")
    
    return log_file

# Setup logging
log_file = setup_logging()

# Create Flask application - this is what Gunicorn will use
application = create_app()

if __name__ == '__main__':
    # This block won't be executed when run by Gunicorn
    logger = logging.getLogger(__name__)
    logger.info("🌐 Starting Flask application directly on http://0.0.0.0:5000")
    application.run(debug=True, host='0.0.0.0', port=5000)

