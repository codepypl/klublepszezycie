#!/usr/bin/env python3
"""
Cron job do automatycznego wysyłania emaili
Uruchamiaj co 5 minut: */5 * * * * /path/to/python /path/to/cron_email_sender.py
"""

import sys
import os
from datetime import datetime

# Dodaj ścieżkę do projektu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from services.email_automation_service import email_automation_service

def run_email_automation():
    """Uruchom automatyczne wysyłanie emaili"""
    try:
        print(f"🕐 {datetime.now()}: Uruchamianie automatyzacji emaili...")
        
        with app.app_context():
            # Przetwórz harmonogramy wydarzeń
            event_results = email_automation_service.process_scheduled_emails()
            print(f"📊 Harmonogramy wydarzeń: {event_results}")
            
            # Przetwórz harmonogramy EmailSchedule (jeśli są)
            from app import check_and_run_schedules
            check_and_run_schedules()
            
            print(f"✅ Automatyzacja zakończona: {datetime.now()}")
            
    except Exception as e:
        print(f"❌ Błąd automatyzacji: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = run_email_automation()
    sys.exit(0 if success else 1)
