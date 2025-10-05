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
    Przetwarza przypomnienia o wydarzeniach - NOWY SYSTEM v2
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam przetwarzanie przypomnień o wydarzeniach v2")
            
            from app.services.email_v2 import EmailManager
            email_manager = EmailManager()
            
            # Pobierz wszystkie aktywne wydarzenia, które nie mają zaplanowanych przypomnień
            events = EventSchedule.query.filter(
                EventSchedule.is_active == True
            ).all()
            
            # Filter out events that already have reminders scheduled
            events = [event for event in events if not event.reminders_scheduled]
            
            # DODATKOWA KONTROLA: Sprawdź czy w kolejce już są emaile dla wydarzeń
            from app.models.email_model import EmailQueue
            events_with_emails = set()
            for event in events:
                existing_emails = EmailQueue.query.filter_by(
                    event_id=event.id,
                    status='pending'
                ).count()
                if existing_emails > 0:
                    events_with_emails.add(event.id)
                    logger.warning(f"⚠️ Wydarzenie {event.id} ({event.title}) już ma {existing_emails} emaili w kolejce")
            
            # Usuń wydarzenia które już mają emaile w kolejce
            events = [event for event in events if event.id not in events_with_emails]
            
            processed_count = 0
            success_count = 0
            failed_count = 0
            
            for event in events:
                try:
                    logger.info(f"📅 Przetwarzam wydarzenie: {event.title} (ID: {event.id})")
                    
                    # Wywołaj send_event_reminders dla każdego wydarzenia
                    success, message = email_manager.send_event_reminders(event.id)
                    
                    if success:
                        success_count += 1
                        logger.info(f"✅ Zaplanowano przypomnienia dla: {event.title}")
                    else:
                        failed_count += 1
                        logger.warning(f"⚠️ Błąd planowania przypomnień dla {event.title}: {message}")
                    
                    processed_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Błąd przetwarzania wydarzenia {event.id}: {e}")
            
            logger.info(f"✅ Przetworzono {processed_count} wydarzeń: {success_count} sukces, {failed_count} błąd")
            
            return {
                'success': True,
                'processed': processed_count,
                'success_count': success_count,
                'failed_count': failed_count
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd przetwarzania przypomnień v2: {exc}")
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