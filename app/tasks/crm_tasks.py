"""
CRM tasks for Celery
"""
import logging
from app import create_app
from app.models.crm_model import Call, Contact
from app.utils.timezone_utils import get_local_now
from app.services.crm_queue_manager import QueueManager

# Setup logging
logger = logging.getLogger(__name__)

# Import celery after other imports to avoid circular import
from celery import current_app as celery

def get_app_context():
    """Get Flask app context for Celery tasks"""
    app = create_app()
    return app.app_context()

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.crm_tasks.process_scheduled_calls_task')
def process_scheduled_calls_task(self):
    """
    Przetwarza zaplanowane połączenia CRM
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam przetwarzanie zaplanowanych połączeń CRM")
            
            from app import db
            from app.models import db as _db
            
            now = get_local_now()
            if now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            
            # Znajdź połączenia zaplanowane do wykonania
            scheduled_calls = Call.query.filter(
                Call.scheduled_date <= now,
                Call.queue_status == 'pending'
            ).all()
            
            processed_count = 0
            success_count = 0
            failed_count = 0
            
            for call in scheduled_calls:
                try:
                    logger.info(f"📞 Przetwarzam zaplanowane połączenie: {call.contact.name} (ID: {call.id})")
                    
                    # Sprawdź czy kontakt może być dzwoniony
                    if not call.contact.can_be_called():
                        logger.warning(f"⚠️ Kontakt {call.contact.name} nie może być dzwoniony (blacklisted lub max attempts)")
                        call.queue_status = 'cancelled'
                        _db.session.commit()
                        continue
                    
                    # Sprawdź czy ankieter jest dostępny
                    ankieter = call.ankieter
                    if not ankieter or not ankieter.is_active:
                        logger.warning(f"⚠️ Ankieter {call.ankieter_id} nie jest dostępny")
                        continue
                    
                    # Oznacz połączenie jako gotowe do wykonania
                    call.queue_status = 'in_progress'
                    call.call_start_time = now
                    _db.session.commit()
                    
                    success_count += 1
                    processed_count += 1
                    logger.info(f"✅ Połączenie {call.id} oznaczone jako gotowe do wykonania")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Błąd przetwarzania połączenia {call.id}: {e}")
            
            logger.info(f"✅ Przetworzono {processed_count} połączeń: {success_count} sukces, {failed_count} błąd")
            
            return {
                'success': True,
                'processed': processed_count,
                'success_count': success_count,
                'failed_count': failed_count
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd przetwarzania zaplanowanych połączeń: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.crm_tasks.process_callback_calls_task')
def process_callback_calls_task(self):
    """
    Przetwarza połączenia callback (oddzwonienia)
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam przetwarzanie połączeń callback")
            
            from app import db
            from app.models import db as _db
            
            now = get_local_now()
            if now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            
            # Znajdź połączenia callback gotowe do wykonania
            callback_calls = Call.query.filter(
                Call.next_call_date <= now,
                Call.status == 'callback',
                Call.queue_status == 'pending'
            ).all()
            
            processed_count = 0
            success_count = 0
            failed_count = 0
            
            for call in callback_calls:
                try:
                    logger.info(f"📞 Przetwarzam callback: {call.contact.name} (ID: {call.id})")
                    
                    # Sprawdź czy kontakt może być dzwoniony
                    if not call.contact.can_be_called():
                        logger.warning(f"⚠️ Kontakt {call.contact.name} nie może być dzwoniony")
                        call.queue_status = 'cancelled'
                        _db.session.commit()
                        continue
                    
                    # Oznacz jako gotowe do wykonania
                    call.queue_status = 'in_progress'
                    call.call_start_time = now
                    _db.session.commit()
                    
                    success_count += 1
                    processed_count += 1
                    logger.info(f"✅ Callback {call.id} oznaczone jako gotowe do wykonania")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Błąd przetwarzania callback {call.id}: {e}")
            
            logger.info(f"✅ Przetworzono {processed_count} callbacków: {success_count} sukces, {failed_count} błąd")
            
            return {
                'success': True,
                'processed': processed_count,
                'success_count': success_count,
                'failed_count': failed_count
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd przetwarzania callbacków: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.crm_tasks.cleanup_old_calls_task')
def cleanup_old_calls_task(self):
    """
    Czyści stare połączenia z systemu
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam czyszczenie starych połączeń")
            
            from app import db
            from app.models import db as _db
            from datetime import timedelta
            
            # Usuń połączenia starsze niż 30 dni
            cutoff_date = get_local_now() - timedelta(days=30)
            if cutoff_date.tzinfo is not None:
                cutoff_date = cutoff_date.replace(tzinfo=None)
            
            old_calls = Call.query.filter(
                Call.created_at < cutoff_date,
                Call.queue_status.in_(['completed', 'cancelled'])
            ).all()
            
            deleted_count = 0
            for call in old_calls:
                try:
                    _db.session.delete(call)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"❌ Błąd usuwania połączenia {call.id}: {e}")
            
            _db.session.commit()
            
            logger.info(f"✅ Usunięto {deleted_count} starych połączeń")
            
            return {
                'success': True,
                'deleted_count': deleted_count
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd czyszczenia starych połączeń: {exc}")
            raise self.retry(exc=exc, countdown=60)
