#!/usr/bin/env python3
"""
Skrypt do przetwarzania kolejek emaili - wywoływany przez cron
"""
import os
import sys
from datetime import datetime

# Dodaj ścieżkę do aplikacji
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.email_service import EmailService
from app.services.email_automation import EmailAutomation

def main():
    """Główna funkcja przetwarzania emaili"""
    print(f"[{datetime.now()}] Rozpoczynanie przetwarzania emaili...")
    
    try:
        # Utwórz aplikację
        app = create_app()
        
        with app.app_context():
            # Przetwórz kolejkę emaili
            email_service = EmailService()
            stats = email_service.process_queue()
            
            if stats['processed'] > 0:
                print(f"[{datetime.now()}] ✅ Przetworzono {stats['processed']} emaili. Sukces: {stats['success']}, Błędy: {stats['failed']}")
            else:
                print(f"[{datetime.now()}] ℹ️ Brak emaili do przetworzenia")
            
            # Ponów nieudane emaile
            stats = email_service.retry_failed_emails()
            
            if stats['retried'] > 0:
                print(f"[{datetime.now()}] ✅ Ponowiono {stats['retried']} emaili. Sukces: {stats['success']}, Błędy: {stats['failed']}")
            else:
                print(f"[{datetime.now()}] ℹ️ Brak emaili do ponowienia")
            
            # Przetwórz przypomnienia o wydarzeniach
            automation = EmailAutomation()
            success, message = automation.process_event_reminders()
            
            if success:
                print(f"[{datetime.now()}] ✅ {message}")
            else:
                print(f"[{datetime.now()}] ❌ {message}")
            
            # Aktualizuj grupy
            success, message = automation.update_all_groups()
            
            if success:
                print(f"[{datetime.now()}] ✅ {message}")
            else:
                print(f"[{datetime.now()}] ❌ {message}")
            
            # Archiwizuj zakończone wydarzenia
            success, message = automation.archive_ended_events()
            
            if success:
                print(f"[{datetime.now()}] ✅ {message}")
            else:
                print(f"[{datetime.now()}] ❌ {message}")
            
            # Pokaż statystyki
            stats = email_service.get_queue_stats()
            
            print(f"[{datetime.now()}] 📊 Statystyki kolejki:")
            print(f"  - Pending: {stats['pending']}")
            print(f"  - Sent: {stats['sent']}")
            print(f"  - Failed: {stats['failed']}")
            print(f"  - Total: {stats['total']}")
            
            print(f"[{datetime.now()}] ✅ Przetwarzanie zakończone pomyślnie")
            
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Błąd przetwarzania: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
