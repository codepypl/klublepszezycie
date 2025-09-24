#!/usr/bin/env python3
"""
Email Queue Processor
Przetwarza kolejkę zaplanowanych emaili
Uruchamiany przez cron co 5 minut
"""
import os
import sys
import asyncio
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.mailgun_service import EnhancedNotificationProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/email_queue.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def process_queue():
    """Process email queue"""
    try:
        logger.info("🚀 Starting email queue processing")
        
        # Create app context
        app = create_app()
        with app.app_context():
            processor = EnhancedNotificationProcessor()
            success, message = await processor.process_email_queue()
            
            if success:
                logger.info(f"✅ Queue processing completed: {message}")
            else:
                logger.warning(f"⚠️ Queue processing completed with issues: {message}")
                
    except Exception as e:
        logger.error(f"❌ Error processing email queue: {e}")
        sys.exit(1)

def main():
    """Main function"""
    logger.info(f"📧 Email queue processor started at {datetime.now()}")
    asyncio.run(process_queue())
    logger.info(f"🏁 Email queue processor finished at {datetime.now()}")

if __name__ == "__main__":
    main()
