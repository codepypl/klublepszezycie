#!/usr/bin/env python3
"""
Skrypt cron do przetwarzania kolejki emaili
Uruchamiany przez cron co 1 minutę
"""
import sys
import os
import argparse
import logging
from datetime import datetime

# Dodaj katalog główny projektu do ścieżki PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app
from app.services.email_v2 import EmailManager

def setup_logging():
    """Konfiguracja logowania"""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'email_cron.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def process_queue(limit=50):
    """Przetwarza kolejkę emaili"""
    logger = logging.getLogger(__name__)
    
    try:
        app = create_app()
        with app.app_context():
            logger.info("🚀 Uruchamiam procesor kolejki emaili przez cron...")
            
            email_manager = EmailManager()
            stats = email_manager.process_queue(limit=limit)
            
            logger.info(f"✅ Zakończono przetwarzanie kolejki emaili:")
            logger.info(f"   Przetworzonych: {stats.get('processed', 0)}")
            logger.info(f"   Sukces: {stats.get('success', 0)}")
            logger.info(f"   Błędy: {stats.get('failed', 0)}")
            
            if 'error' in stats:
                logger.error(f"   Błąd: {stats['error']}")
            
            return stats
            
    except Exception as e:
        logger.error(f"❌ Błąd podczas przetwarzania kolejki: {e}")
        return {'processed': 0, 'success': 0, 'failed': 0, 'error': str(e)}

def show_stats():
    """Pokazuje statystyki kolejki"""
    logger = logging.getLogger(__name__)
    
    try:
        app = create_app()
        with app.app_context():
            email_manager = EmailManager()
            stats = email_manager.get_stats()
            
            print("📊 Statystyki kolejki emaili:")
            print(f"   Wszystkich: {stats.get('total', 0)}")
            print(f"   Oczekujących: {stats.get('pending', 0)}")
            print(f"   Przetwarzanych: {stats.get('processing', 0)}")
            print(f"   Wysłanych: {stats.get('sent', 0)}")
            print(f"   Nieudanych: {stats.get('failed', 0)}")
            
            return stats
            
    except Exception as e:
        logger.error(f"❌ Błąd podczas pobierania statystyk: {e}")
        return {}

def cleanup_old_emails(days=30):
    """Czyści stare emaile z kolejki"""
    logger = logging.getLogger(__name__)
    
    try:
        app = create_app()
        with app.app_context():
            from app.services.email_v2.queue.processor import EmailQueueProcessor
            
            logger.info(f"🗑️ Czyszczę emaile starsze niż {days} dni...")
            
            processor = EmailQueueProcessor()
            stats = processor.cleanup_old_emails(days=days)
            
            logger.info(f"✅ Czyszczenie zakończone:")
            logger.info(f"   Usunięto wysłane: {stats.get('deleted_sent', 0)}")
            logger.info(f"   Usunięto nieudane: {stats.get('deleted_failed', 0)}")
            logger.info(f"   Razem: {stats.get('total_deleted', 0)}")
            
            return stats
            
    except Exception as e:
        logger.error(f"❌ Błąd podczas czyszczenia: {e}")
        return {'deleted_sent': 0, 'deleted_failed': 0, 'total_deleted': 0, 'error': str(e)}

def retry_failed_emails(limit=10):
    """Ponawia wysyłanie nieudanych emaili"""
    logger = logging.getLogger(__name__)
    
    try:
        app = create_app()
        with app.app_context():
            from app.services.email_v2.queue.processor import EmailQueueProcessor
            
            logger.info(f"🔄 Ponawiam wysyłanie {limit} nieudanych emaili...")
            
            processor = EmailQueueProcessor()
            stats = processor.retry_failed_emails(limit=limit)
            
            logger.info(f"✅ Ponawianie zakończone:")
            logger.info(f"   Ponowionych: {stats.get('retried', 0)}")
            logger.info(f"   Sukces: {stats.get('success', 0)}")
            logger.info(f"   Błędy: {stats.get('failed', 0)}")
            
            return stats
            
    except Exception as e:
        logger.error(f"❌ Błąd podczas ponawiania: {e}")
        return {'retried': 0, 'success': 0, 'failed': 0, 'error': str(e)}

def schedule_event_reminders():
    """Planuje przypomnienia o wydarzeniach"""
    logger = logging.getLogger(__name__)
    
    try:
        app = create_app()
        with app.app_context():
            from app.services.email_v2 import EmailManager
            from app.models import EventSchedule
            from app.utils.timezone_utils import get_local_now
            from datetime import timedelta
            
            logger.info("📅 Planuję przypomnienia o wydarzeniach...")
            
            # Znajdź wydarzenia, które potrzebują przypomnień
            now = get_local_now()
            events = EventSchedule.query.filter(
                EventSchedule.is_active == True,
                EventSchedule.is_archived == False,
                EventSchedule.reminders_scheduled == False,
                EventSchedule.event_date > now,
                EventSchedule.event_date <= now + timedelta(days=7)  # Tylko najbliższe 7 dni
            ).all()
            
            email_manager = EmailManager()
            scheduled_count = 0
            
            for event in events:
                try:
                    success, message = email_manager.send_event_reminders(event.id)
                    if success:
                        scheduled_count += 1
                        logger.info(f"✅ Zaplanowano przypomnienia dla: {event.title}")
                    else:
                        logger.warning(f"⚠️ Błąd planowania dla {event.title}: {message}")
                except Exception as e:
                    logger.error(f"❌ Błąd planowania przypomnień dla {event.id}: {e}")
            
            logger.info(f"📅 Zaplanowano przypomnienia dla {scheduled_count} wydarzeń")
            return {'scheduled': scheduled_count, 'total': len(events)}
            
    except Exception as e:
        logger.error(f"❌ Błąd planowania przypomnień: {e}")
        return {'scheduled': 0, 'total': 0, 'error': str(e)}

def main():
    """Główna funkcja skryptu"""
    parser = argparse.ArgumentParser(description='Procesor kolejki emaili')
    parser.add_argument('--limit', type=int, default=50, help='Maksymalna liczba emaili do przetworzenia')
    parser.add_argument('--stats', action='store_true', help='Pokaż statystyki kolejki')
    parser.add_argument('--cleanup', action='store_true', help='Wyczyść stare emaile')
    parser.add_argument('--retry', type=int, metavar='N', help='Ponów wysyłanie N nieudanych emaili')
    parser.add_argument('--days', type=int, default=30, help='Liczba dni dla czyszczenia (domyślnie 30)')
    parser.add_argument('--schedule-reminders', action='store_true', help='Zaplanuj przypomnienia o wydarzeniach')
    
    args = parser.parse_args()
    
    # Konfiguracja logowania
    logger = setup_logging()
    
    logger.info(f"🕐 Uruchomiono skrypt cron: {datetime.now()}")
    logger.info(f"   Argumenty: {vars(args)}")
    
    try:
        if args.stats:
            show_stats()
        elif args.cleanup:
            cleanup_old_emails(days=args.days)
        elif args.retry is not None:
            retry_failed_emails(limit=args.retry)
        elif args.schedule_reminders:
            schedule_event_reminders()
        else:
            process_queue(limit=args.limit)
            
    except Exception as e:
        logger.error(f"❌ Nieoczekiwany błąd: {e}")
        sys.exit(1)
    
    logger.info("✅ Skrypt zakończony pomyślnie")

if __name__ == "__main__":
    main()
