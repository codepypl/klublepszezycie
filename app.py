"""
Refactored Flask application - main entry point
"""
import sys
import logging
from datetime import datetime
from app import create_app

# Configure logging to file
def setup_logging():
    """Setup logging to file"""
    # Create logs directory if it doesn't exist
    import os
    logs_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f'app_console_{timestamp}.log')
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)  # Also show in console
        ]
    )
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"🚀 Application starting - Console logs saved to: {log_file}")
    
    return log_file

# Setup logging
log_file = setup_logging()

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Log application startup
    logger = logging.getLogger(__name__)
    logger.info("🌐 Starting Flask application on http://0.0.0.0:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
