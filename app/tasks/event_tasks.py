"""
Event tasks for Celery
"""
from celery import current_task
from celery.exceptions import Retry
from datetime import datetime, timedelta
import logging

from celery import current_app as celery
from app import create_app
from app.models.events_model import EventSchedule

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_app_context():
    """Pobiera kontekst aplikacji Flask dla Celery"""
    app = create_app()
    return app.app_context()

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.event_tasks.process_event_reminders_task')
def process_event_reminders_task(self):
    """
    Przetwarza przypomnienia o wydarzeniach - NOWY SYSTEM v3
    
    Uruchamiany co 5 minut.
    Dla każdego aktywnego wydarzenia sprawdza czy przypomnienia zostały zaplanowane.
    Jeśli nie, wywołuje scheduler.schedule_event_reminders()
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam przetwarzanie przypomnień o wydarzeniach v3")
            
            from app.services.email_v2.queue.scheduler import EmailScheduler
            from app.models.email_model import EmailQueue
            from app import db
            
            scheduler = EmailScheduler()
            
            # Pobierz wszystkie aktywne wydarzenia bez zaplanowanych przypomnień
            events = EventSchedule.query.filter(
                EventSchedule.is_active == True,
                EventSchedule.reminders_scheduled == False
            ).all()
            
            if not events:
                logger.info("ℹ️ Brak wydarzeń do zaplanowania")
                return {
                    'success': True,
                    'processed': 0,
                    'success_count': 0,
                    'failed_count': 0
                }
            
            processed_count = 0
            success_count = 0
            failed_count = 0
            
            for event in events:
                try:
                    logger.info(f"📅 Planuję przypomnienia dla: {event.title} (ID: {event.id})")
                    
                    # Użyj nowego schedulera
                    success, message = scheduler.schedule_event_reminders(event.id)
                    
                    if success:
                        success_count += 1
                        logger.info(f"✅ {message}")
                    else:
                        failed_count += 1
                        logger.warning(f"⚠️ {message}")
                    
                    processed_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Błąd planowania przypomnień dla wydarzenia {event.id}: {e}")
            
            logger.info(f"✅ Przetworzono {processed_count} wydarzeń: {success_count} sukces, {failed_count} błąd")
            
            return {
                'success': True,
                'processed': processed_count,
                'success_count': success_count,
                'failed_count': failed_count
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd przetwarzania przypomnień v3: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.event_tasks.archive_ended_events_task')
def archive_ended_events_task(self):
    """
    Archiwizuje zakończone wydarzenia
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam archiwizację zakończonych wydarzeń")
            
            from app.models.events_model import EventSchedule
            from app.utils.timezone_utils import get_local_now
            
            now = get_local_now()
            if now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            
            # Znajdź wydarzenia, które się zakończyły
            ended_events = EventSchedule.query.filter(
                EventSchedule.event_date < now,
                EventSchedule.is_active == True,
                EventSchedule.is_archived == False
            ).all()
            
            archived_count = 0
            
            for event in ended_events:
                try:
                    event.is_archived = True
                    event.is_active = False
                    event.is_published = False
                    archived_count += 1
                    logger.info(f"📦 Zarchiwizowano wydarzenie: {event.title}")
                    
                except Exception as e:
                    logger.error(f"❌ Błąd archiwizacji wydarzenia {event.id}: {e}")
            
            from app.models import db
            db.session.commit()
            
            logger.info(f"✅ Zarchiwizowano {archived_count} wydarzeń")
            
            return {
                'success': True,
                'archived_count': archived_count
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd archiwizacji wydarzeń: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.event_tasks.cleanup_old_reminders_task')
def cleanup_old_reminders_task(self):
    """
    Czyści stare przypomnienia
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam czyszczenie starych przypomnień")
            
            from app.models import db, EmailQueue
            from app.utils.timezone_utils import get_local_now
            
            now = get_local_now()
            if now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            
            # Usuń stare emaile z kolejki (starsze niż 7 dni)
            old_date = now - timedelta(days=7)
            old_emails = EmailQueue.query.filter(
                EmailQueue.created_at < old_date,
                EmailQueue.status.in_(['sent', 'failed'])
            ).all()
            
            deleted_count = 0
            for email in old_emails:
                try:
                    db.session.delete(email)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"❌ Błąd usuwania emaila {email.id}: {e}")
            
            db.session.commit()
            
            logger.info(f"✅ Usunięto {deleted_count} starych emaili")
            
            return {
                'success': True,
                'deleted_count': deleted_count
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd czyszczenia starych przypomnień: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, name='app.tasks.event_tasks.cleanup_duplicate_event_groups_task')
def cleanup_duplicate_event_groups_task(self):
    """
    Czyści duplikaty grup wydarzeń - zadanie Celery
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam czyszczenie duplikatów grup wydarzeń")
            
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            
            success, message = group_manager.cleanup_duplicate_event_groups()
            
            if success:
                logger.info(f"✅ Czyszczenie duplikatów zakończone: {message}")
            else:
                logger.error(f"❌ Błąd czyszczenia duplikatów: {message}")
            
            return {
                'success': success,
                'message': message
            }
            
        except Exception as e:
            logger.error(f"❌ Błąd zadania czyszczenia duplikatów grup: {e}")
            return {
                'success': False,
                'error': str(e)
            }

@celery.task(bind=True, name='app.tasks.event_tasks.cleanup_orphaned_groups_task')
def cleanup_orphaned_groups_task(self):
    """
    Czyści osierocone grupy wydarzeń (gdy wydarzenia nie istnieją lub są nieaktywne)
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam czyszczenie osieroconych grup wydarzeń")
            
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            
            success, message = group_manager.cleanup_orphaned_groups()
            
            if success:
                logger.info(f"✅ Czyszczenie osieroconych grup zakończone: {message}")
            else:
                logger.error(f"❌ Błąd czyszczenia osieroconych grup: {message}")
            
            return {
                'success': success,
                'message': message
            }
            
        except Exception as e:
            logger.error(f"❌ Błąd zadania czyszczenia osieroconych grup: {e}")
            return {
                'success': False,
                'error': str(e)
            }