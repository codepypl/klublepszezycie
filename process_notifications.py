#!/usr/bin/env python3
"""
Nowoczesny system powiadomień - skrypt cron
Przetwarza kolejkę emaili i wysyła przez Mailgun
Uruchamiać co 2 minuty: */2 * * * *
"""
import sys
import os
import asyncio
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app import create_app
from app.services.notification_system import process_event_reminders, process_email_queue

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/notifications.log'),
        logging.StreamHandler()
    ]
)

async def main():
    """Główna funkcja przetwarzania powiadomień"""
    print("🚀 Rozpoczynam przetwarzanie powiadomień...")
    print(f"📅 Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # 1. Planuj nowe przypomnienia o wydarzeniach
            print("📋 Planowanie przypomnień o wydarzeniach...")
            success, message = process_event_reminders()
            
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
            
            print("-" * 40)
            
            # 2. Przetwarzaj kolejkę emaili
            print("📧 Przetwarzanie kolejki emaili...")
            success, message = await process_email_queue()
            
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
            
            print("-" * 40)
            print("✅ Przetwarzanie powiadomień zakończone!")
            
        except Exception as e:
            print(f"❌ Błąd krytyczny: {str(e)}")
            logging.error(f"Critical error in notification processing: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    # Uruchom asynchroniczną funkcję
    asyncio.run(main())
