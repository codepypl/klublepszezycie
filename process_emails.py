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
from app.models.system_logs_model import SystemLog

def main():
    """Główna funkcja przetwarzania emaili"""
    start_time = datetime.now()
    print(f"[{start_time}] Rozpoczynanie przetwarzania emaili...")
    
    try:
        # Utwórz aplikację
        app = create_app()
        
        with app.app_context():
            from app.models import db
            
            # Przetwórz kolejkę emaili
            email_start = datetime.now()
            email_service = EmailService()
            stats = email_service.process_queue()
            email_time = (datetime.now() - email_start).total_seconds()
            
            # Zapisz log do bazy danych
            SystemLog.log_email_processing(
                processed_count=stats['processed'],
                success_count=stats['success'],
                failed_count=stats['failed'],
                execution_time=email_time
            )
            db.session.commit()
            
            if stats['processed'] > 0:
                print(f"[{datetime.now()}] ✅ Przetworzono {stats['processed']} emaili. Sukces: {stats['success']}, Błędy: {stats['failed']}")
            else:
                print(f"[{datetime.now()}] ℹ️ Brak emaili do przetworzenia")
            
            # Ponów nieudane emaile
            retry_start = datetime.now()
            retry_stats = email_service.retry_failed_emails()
            retry_time = (datetime.now() - retry_start).total_seconds()
            
            # Zapisz log do bazy danych
            SystemLog.log_email_processing(
                processed_count=retry_stats['retried'],
                success_count=retry_stats['success'],
                failed_count=retry_stats['failed'],
                execution_time=retry_time
            )
            db.session.commit()
            
            if retry_stats['retried'] > 0:
                print(f"[{datetime.now()}] ✅ Ponowiono {retry_stats['retried']} emaili. Sukces: {retry_stats['success']}, Błędy: {retry_stats['failed']}")
            else:
                print(f"[{datetime.now()}] ℹ️ Brak emaili do ponowienia")
            
            # Przetwórz przypomnienia o wydarzeniach (WYŁĄCZONE - powoduje dodawanie emaili do kolejki)
            print(f"[{datetime.now()}] ⏸️ Pominięto automatyczne przypomnienia - wyłączone aby nie dodawać emaili do kolejki")
            # automation = EmailAutomation()
            # success, message = automation.process_event_reminders()
            # reminders_time = (datetime.now() - reminders_start).total_seconds()
            
            # # Zapisz log do bazy danych
            # SystemLog.log_event_reminders(
            #     processed_events=1 if success else 0,
            #     success=success,
            #     message=message,
            #     execution_time=reminders_time
            # )
            # db.session.commit()
            
            # if success:
            #     print(f"[{datetime.now()}] ✅ {message}")
            # else:
            #     print(f"[{datetime.now()}] ❌ {message}")
            
            # Aktualizuj grupy
            groups_start = datetime.now()
            success, message = automation.update_all_groups()
            groups_time = (datetime.now() - groups_start).total_seconds()
            
            # Zapisz log do bazy danych
            SystemLog.log_group_update(
                updated_groups=2,  # Based on previous output
                success=success,
                message=message,
                execution_time=groups_time
            )
            db.session.commit()
            
            if success:
                print(f"[{datetime.now()}] ✅ {message}")
            else:
                print(f"[{datetime.now()}] ❌ {message}")
            
            # Archiwizuj zakończone wydarzenia
            archive_start = datetime.now()
            success, message = automation.archive_ended_events()
            archive_time = (datetime.now() - archive_start).total_seconds()
            
            # Zapisz log do bazy danych
            SystemLog.log_archive_events(
                archived_events=0,  # Will be updated based on actual results
                success=success,
                message=message,
                execution_time=archive_time
            )
            db.session.commit()
            
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
            
            # Zapisz ogólny log wykonania cron
            total_time = (datetime.now() - start_time).total_seconds()
            SystemLog.log_cron_execution(
                operation_type='email_processing',
                success=True,
                message=f"Przetwarzanie zakończone pomyślnie. Całkowity czas: {total_time:.2f}s",
                details={
                    'queue_stats': stats,
                    'total_execution_time': total_time
                },
                execution_time=total_time
            )
            db.session.commit()
            
            print(f"[{datetime.now()}] ✅ Przetwarzanie zakończone pomyślnie")
            
    except Exception as e:
        error_time = (datetime.now() - start_time).total_seconds()
        error_message = f"Błąd przetwarzania: {str(e)}"
        
        # Zapisz błąd do bazy danych
        try:
            app = create_app()
            with app.app_context():
                from app.models import db
                SystemLog.log_cron_execution(
                    operation_type='email_processing',
                    success=False,
                    message=error_message,
                    details={'error': str(e)},
                    execution_time=error_time
                )
                db.session.commit()
        except:
            pass  # Jeśli nie można zapisać do bazy, kontynuuj
        
        print(f"[{datetime.now()}] ❌ {error_message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
