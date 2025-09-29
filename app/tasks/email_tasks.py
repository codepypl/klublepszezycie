"""
Email tasks for Celery
"""
from celery import current_task
from celery.exceptions import Retry
from datetime import datetime, timedelta
import logging
import json
import time

from celery_app import celery
from app import create_app
from app.models import EmailQueue, EmailCampaign, UserGroupMember, User
from app.services.email_service import EmailService

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_app_context():
    """Pobiera kontekst aplikacji Flask dla Celery"""
    app = create_app()
    return app.app_context()

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.process_email_queue_task')
def process_email_queue_task(self, batch_size=50):
    """
    Przetwarza kolejkę emaili w batchach
    """
    with get_app_context():
        try:
            logger.info(f"🔄 Rozpoczynam przetwarzanie kolejki emaili (batch: {batch_size})")
            
            email_service = EmailService()
            stats = email_service.process_queue(batch_size)
            
            logger.info(f"✅ Przetworzono {stats['processed']} emaili: {stats['success']} sukces, {stats['failed']} błąd")
            
            return {
                'success': True,
                'processed': stats['processed'],
                'success_count': stats['success'],
                'failed_count': stats['failed']
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd przetwarzania kolejki: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.process_scheduled_campaigns_task')
def process_scheduled_campaigns_task(self):
    """
    Przetwarza zaplanowane kampanie
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam przetwarzanie zaplanowanych kampanii")
            
            email_service = EmailService()
            success, message = email_service.process_scheduled_campaigns()
            
            logger.info(f"✅ Przetwarzanie kampanii: {message}")
            
            return {
                'success': success,
                'message': message
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd przetwarzania kampanii: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.send_batch_emails_task')
def send_batch_emails_task(self, email_ids, batch_size=10):
    """
    Wysyła emaile w batchach
    """
    with get_app_context():
        try:
            logger.info(f"🔄 Rozpoczynam wysyłanie {len(email_ids)} emaili w batchach po {batch_size}")
            
            email_service = EmailService()
            stats = email_service.send_batch_emails(email_ids, batch_size)
            
            logger.info(f"✅ Wysłano {stats['sent']} emaili: {stats['success']} sukces, {stats['failed']} błąd")
            
            return {
                'success': True,
                'sent': stats['sent'],
                'success_count': stats['success'],
                'failed_count': stats['failed']
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd wysyłania emaili: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.test_email_sending_task')
def test_email_sending_task(self, to_email="test@example.com"):
    """
    Testuje wysyłanie emaili
    """
    with get_app_context():
        try:
            logger.info(f"🔄 Testuję wysyłanie emaila do {to_email}")
            
            email_service = EmailService()
            success, message = email_service.send_email(
                to_email=to_email,
                subject="Test email z Celery",
                html_content="<h1>Test email</h1><p>To jest test email z Celery.</p>",
                text_content="Test email\n\nTo jest test email z Celery.",
                use_queue=False
            )
            
            if success:
                logger.info(f"✅ Test email wysłany pomyślnie: {message}")
                return {'success': True, 'message': message}
            else:
                logger.error(f"❌ Błąd wysyłania test email: {message}")
                return {'success': False, 'message': message}
                
        except Exception as exc:
            logger.error(f"❌ Błąd testu email: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.send_event_reminder_task')
def send_event_reminder_task(self, event_id, user_id, reminder_type="24h"):
    """
    Wysyła przypomnienie o wydarzeniu
    """
    with get_app_context():
        try:
            logger.info(f"🔄 Wysyłam przypomnienie o wydarzeniu {event_id} dla użytkownika {user_id}")
            
            from app.services.mailgun_service import EnhancedNotificationProcessor
            email_processor = EnhancedNotificationProcessor()
            
            # Pobierz dane wydarzenia i użytkownika
            from app.models.events_model import EventSchedule
            event = EventSchedule.query.get(event_id)
            user = User.query.get(user_id)
            
            if not event or not user:
                logger.error(f"❌ Nie znaleziono wydarzenia {event_id} lub użytkownika {user_id}")
                return {'success': False, 'message': 'Event or user not found'}
            
            # Wyślij przypomnienie
            success, message = email_processor.send_template_email(
                template_name=f'event_reminder_{reminder_type}',
                to_email=user.email,
                to_name=user.first_name,
                context={
                    'event_title': event.title,
                    'event_date': event.event_date.strftime('%d.%m.%Y'),
                    'event_time': event.event_date.strftime('%H:%M'),
                    'event_location': event.location or 'Online',
                    'user_name': user.first_name,
                    'event_id': event_id,
                    'user_id': user_id
                },
                use_queue=True
            )
            
            if success:
                logger.info(f"✅ Przypomnienie wysłane: {message}")
                return {'success': True, 'message': message}
            else:
                logger.error(f"❌ Błąd wysyłania przypomnienia: {message}")
                return {'success': False, 'message': message}
                
        except Exception as exc:
            logger.error(f"❌ Błąd wysyłania przypomnienia: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.update_event_notifications_task')
def update_event_notifications_task(self, event_id):
    """
    Aktualizuje powiadomienia o wydarzeniu
    """
    with get_app_context():
        try:
            logger.info(f"🔄 Aktualizuję powiadomienia o wydarzeniu {event_id}")
            
            from app.models.events_model import EventSchedule
            event = EventSchedule.query.get(event_id)
            
            if not event:
                logger.error(f"❌ Nie znaleziono wydarzenia {event_id}")
                return {'success': False, 'message': 'Event not found'}
            
            # Tutaj można dodać logikę aktualizacji powiadomień
            # Na przykład: anulowanie starych przypomnień, planowanie nowych
            
            logger.info(f"✅ Powiadomienia o wydarzeniu {event_id} zaktualizowane")
            return {'success': True, 'message': 'Event notifications updated'}
            
        except Exception as exc:
            logger.error(f"❌ Błąd aktualizacji powiadomień: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.schedule_event_reminders_task')
def schedule_event_reminders_task(self, event_id):
    """
    Planuje przypomnienia o wydarzeniu
    """
    with get_app_context():
        try:
            logger.info(f"🔄 Planuję przypomnienia o wydarzeniu {event_id}")
            
            from app.models.events_model import EventSchedule
            event = EventSchedule.query.get(event_id)
            
            if not event:
                logger.error(f"❌ Nie znaleziono wydarzenia {event_id}")
                return {'success': False, 'message': 'Event not found'}
            
            # Pobierz wszystkich członków klubu (account_type='member') + osoby zapisane na wydarzenie
            from app.models.user_model import User
            club_members = User.query.filter_by(account_type='member').all()
            event_registrations = User.query.filter_by(
                event_id=event_id,
                account_type='event_registration'
            ).all()
            
            # Połącz listy i usuń duplikaty (po email)
            all_users = {}
            for user in club_members + event_registrations:
                all_users[user.email] = user
            
            users = list(all_users.values())
            
            # Zaplanuj przypomnienia dla każdego użytkownika
            for user in users:
                # Przypomnienie 24h przed
                if event.event_date:
                    reminder_time = event.event_date - timedelta(hours=24)
                    if reminder_time > datetime.now():
                        send_event_reminder_task.apply_async(
                            args=[event_id, user.id, "24h"],
                            eta=reminder_time
                        )
                
                # Przypomnienie 1h przed
                if event.event_date:
                    reminder_time = event.event_date - timedelta(hours=1)
                    if reminder_time > datetime.now():
                        send_event_reminder_task.apply_async(
                            args=[event_id, user.id, "1h"],
                            eta=reminder_time
                        )
                
                # Przypomnienie 5 minut przed
                if event.event_date:
                    reminder_time = event.event_date - timedelta(minutes=5)
                    if reminder_time > datetime.now():
                        send_event_reminder_task.apply_async(
                            args=[event_id, user.id, "5min"],
                            eta=reminder_time
                        )
            
            logger.info(f"✅ Zaplanowano przypomnienia dla {len(users)} użytkowników")
            return {'success': True, 'message': f'Scheduled reminders for {len(users)} users'}
            
        except Exception as exc:
            logger.error(f"❌ Błąd planowania przypomnień: {exc}")
            raise self.retry(exc=exc, countdown=60)