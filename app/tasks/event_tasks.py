"""
Event tasks for Celery
"""
import logging
from datetime import datetime, timedelta

from celery_app import celery
from app import create_app
from app.models import EventSchedule, EmailReminder, UserGroup, UserGroupMember
from app.services.email_automation import EmailAutomation

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_app_context():
    """Pobiera kontekst aplikacji Flask dla Celery"""
    app = create_app()
    return app.app_context()

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_event_reminders_task(self):
    """
    Przetwarza przypomnienia o wydarzeniach (wywoływane przez beat scheduler)
    """
    with get_app_context():
        try:
            logger.info("📅 Przetwarzam przypomnienia o wydarzeniach")
            
            email_automation = EmailAutomation()
            success, message = email_automation.process_event_reminders()
            
            if success:
                logger.info(f"✅ {message}")
                return {'success': True, 'message': message}
            else:
                logger.error(f"❌ {message}")
                return {'success': False, 'message': message}
                
        except Exception as exc:
            logger.error(f"❌ Błąd przetwarzania przypomnień: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=2, default_retry_delay=30)
def cleanup_old_reminders_task(self, days_old=7):
    """
    Czyści stare przypomnienia z bazy danych
    """
    with get_app_context():
        try:
            from app import db
            
            cutoff_date = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now() - timedelta(days=days_old)
            
            # Usuń stare przypomnienia
            old_reminders = EmailReminder.query.filter(
                EmailReminder.created_at < cutoff_date
            ).all()
            
            count = len(old_reminders)
            for reminder in old_reminders:
                db.session.delete(reminder)
            
            db.session.commit()
            
            logger.info(f"🧹 Usunięto {count} starych przypomnień")
            return {'success': True, 'cleaned': count}
            
        except Exception as exc:
            logger.error(f"❌ Błąd czyszczenia przypomnień: {exc}")
            return {'success': False, 'error': str(exc)}

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def archive_ended_events_task(self):
    """
    Archiwizuje zakończone wydarzenia i czyści grupy (wywoływane przez beat scheduler)
    """
    with get_app_context():
        try:
            logger.info("📦 Przetwarzam archiwizację zakończonych wydarzeń")
            
            email_automation = EmailAutomation()
            success, message = email_automation.archive_ended_events()
            
            if success:
                logger.info(f"✅ {message}")
                return {'success': True, 'message': message}
            else:
                logger.error(f"❌ {message}")
                return {'success': False, 'message': message}
                
        except Exception as exc:
            logger.error(f"❌ Błąd archiwizacji wydarzeń: {exc}")
            raise self.retry(exc=exc, countdown=60)
