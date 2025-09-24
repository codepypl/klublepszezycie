#!/usr/bin/env python3
"""
Event Reminders Scheduler
Planuje przypomnienia o wydarzeniach
Uruchamiany przez cron co godzinę
"""
import os
import sys
import logging
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.email_automation import EmailAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/event_reminders.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def schedule_reminders():
    """Schedule event reminders"""
    try:
        logger.info("🚀 Starting event reminders scheduling")
        
        # Create app context
        app = create_app()
        with app.app_context():
            automation = EmailAutomation()
            
            # Process event reminders
            success, message = automation.process_event_reminders()
            
            if success:
                logger.info(f"✅ Event reminders processed: {message}")
            else:
                logger.warning(f"⚠️ Event reminders processing completed with issues: {message}")
                
    except Exception as e:
        logger.error(f"❌ Error processing event reminders: {e}")
        sys.exit(1)

def main():
    """Main function"""
    logger.info(f"📅 Event reminders scheduler started at {datetime.now()}")
    schedule_reminders()
    logger.info(f"🏁 Event reminders scheduler finished at {datetime.now()}")

if __name__ == "__main__":
    main()
