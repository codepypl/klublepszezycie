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
# from app.services.mailgun_service import EnhancedNotificationProcessor  # Nie używane

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_app_context():
    """Pobiera kontekst aplikacji Flask dla Celery"""
    app = create_app()
    return app.app_context()

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
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

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_scheduled_campaigns_task(self):
    """
    Przetwarza zaplanowane kampanie
    """
    with get_app_context():
        try:
            logger.info("🔄 Przetwarzam zaplanowane kampanie")
            
            email_service = EmailService()
            success, message = email_service.process_scheduled_campaigns()
            
            if success:
                logger.info(f"✅ {message}")
                return {'success': True, 'message': message}
            else:
                logger.error(f"❌ {message}")
                return {'success': False, 'message': message}
                
        except Exception as exc:
            logger.error(f"❌ Błąd przetwarzania kampanii: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=2, default_retry_delay=30)
def send_batch_emails_task(self, email_ids, batch_number=1, total_batches=1):
    """
    Wysyła paczkę emaili
    """
    with get_app_context():
        try:
            logger.info(f"📧 Wysyłam paczkę {batch_number}/{total_batches} ({len(email_ids)} emaili)")
            
            # Pobierz emaile z bazy
            emails = EmailQueue.query.filter(EmailQueue.id.in_(email_ids)).all()
            
            if not emails:
                logger.warning("⚠️ Brak emaili do wysłania")
                return {'success': True, 'sent': 0, 'failed': 0}
            
            # Użyj EmailService do wysyłki
            from app.services.email_service import EmailService
            from app import db
            from datetime import datetime
            email_service = EmailService()
            
            sent_count = 0
            failed_count = 0
            
            for email in emails:
                try:
                    success, message = email_service.send_email(
                        to_email=email.recipient_email,
                        subject=email.subject,
                        html_content=email.html_content,
                        text_content=email.text_content,
                        template_id=email.template_id
                    )
                    
                    if success:
                        # Oznacz jako wysłany
                        email.status = 'sent'
                        email.sent_at = datetime.utcnow()
                        sent_count += 1
                    else:
                        # Oznacz jako błąd
                        email.status = 'failed'
                        email.error_message = message
                        failed_count += 1
                        
                except Exception as e:
                    email.status = 'failed'
                    email.error_message = str(e)
                    failed_count += 1
                    logger.error(f"❌ Błąd wysyłki email {email.id}: {e}")
            
            # Zapisz zmiany
            db.session.commit()
            
            success = failed_count == 0
            message = f"Wysłano: {sent_count}, Błędy: {failed_count}"
            
            if success:
                logger.info(f"✅ Paczka {batch_number} wysłana: {message}")
                return {'success': True, 'sent': len(emails), 'failed': 0}
            else:
                logger.error(f"❌ Błąd wysyłki paczki {batch_number}: {message}")
                return {'success': False, 'sent': 0, 'failed': len(emails), 'error': message}
                
        except Exception as exc:
            logger.error(f"❌ Błąd wysyłki paczki {batch_number}: {exc}")
            raise self.retry(exc=exc, countdown=30)

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def schedule_event_reminders_task(self, event_id, group_type='event_based'):
    """
    Planuje przypomnienia o wydarzeniu z inteligentnym planowaniem
    """
    with get_app_context():
        try:
            from app.models import EventSchedule
            from app.services.email_automation import EmailAutomation
            
            logger.info(f"📅 Planuję przypomnienia dla wydarzenia {event_id}")
            
            event = EventSchedule.query.get(event_id)
            if not event:
                return {'success': False, 'message': 'Wydarzenie nie znalezione'}
            
            # Pobierz liczbę uczestników
            if group_type == 'event_based':
                group = UserGroup.query.filter_by(
                    name=f"Wydarzenie: {event.title}",
                    group_type='event_based'
                ).first()
            else:
                group = UserGroup.query.filter_by(
                    name="Członkowie klubu",
                    group_type='club_members'
                ).first()
            
            if not group:
                return {'success': False, 'message': 'Grupa nie znaleziona'}
            
            members_count = UserGroupMember.query.filter_by(
                group_id=group.id, 
                is_active=True
            ).count()
            
            logger.info(f"👥 Liczba uczestników: {members_count}")
            
            # Inteligentne planowanie czasu wysyłki
            email_automation = EmailAutomation()
            success, message = email_automation.schedule_event_reminders_smart(
                event_id, group_type, members_count
            )
            
            if success:
                logger.info(f"✅ {message}")
                return {'success': True, 'message': message, 'members_count': members_count}
            else:
                logger.error(f"❌ {message}")
                return {'success': False, 'message': message}
                
        except Exception as exc:
            logger.error(f"❌ Błąd planowania przypomnień: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=2, default_retry_delay=30)
def update_event_notifications_task(self, event_id, old_event_date, new_event_date):
    """
    Aktualizuje powiadomienia po zmianie godziny wydarzenia
    """
    with get_app_context():
        try:
            from app.models import EventSchedule, EmailReminder
            from app.services.email_automation import EmailAutomation
            
            logger.info(f"🔄 Aktualizuję powiadomienia dla wydarzenia {event_id}")
            
            # Anuluj stare powiadomienia
            old_reminders = EmailReminder.query.filter_by(event_id=event_id).all()
            for reminder in old_reminders:
                reminder.status = 'cancelled'
            
            # Usuń stare emaile z kolejki
            old_emails = EmailQueue.query.filter(
                EmailQueue.context.like(f'%event_id":{event_id}%'),
                EmailQueue.status.in_(['pending', 'scheduled'])
            ).all()
            
            for email in old_emails:
                email.status = 'cancelled'
            
            # Zaplanuj nowe powiadomienia
            email_automation = EmailAutomation()
            success, message = email_automation.schedule_event_reminders(event_id)
            
            if success:
                logger.info(f"✅ Powiadomienia zaktualizowane: {message}")
                return {
                    'success': True, 
                    'message': message,
                    'cancelled_reminders': len(old_reminders),
                    'cancelled_emails': len(old_emails)
                }
            else:
                logger.error(f"❌ Błąd aktualizacji: {message}")
                return {'success': False, 'message': message}
                
        except Exception as exc:
            logger.error(f"❌ Błąd aktualizacji powiadomień: {exc}")
            raise self.retry(exc=exc, countdown=30)

@celery.task(bind=True, max_retries=1, default_retry_delay=10)
def test_email_sending_task(self, test_email='codeitpy@gmail.com', count=100, batch_size=10):
    """
    Test wysyłania emaili - wysyła 100 emaili na testowy adres w paczkach po 10
    """
    with get_app_context():
        try:
            logger.info(f"🧪 Rozpoczynam test wysyłania {count} emaili na {test_email}")
            
            from app.services.email_service import EmailService
            from datetime import datetime, timedelta
            
            email_service = EmailService()
            total_batches = (count + batch_size - 1) // batch_size
            
            # Utwórz testowe emaile w kolejce
            created_emails = []
            for i in range(count):
                email_id = email_service.add_to_queue(
                    to_email=test_email,
                    subject=f"Test Email #{i+1} - Batch {((i // batch_size) + 1)}/{total_batches}",
                    html_content=f"""
                    <h2>Test Email #{i+1}</h2>
                    <p>To jest testowy email numer {i+1} z {count}.</p>
                    <p>Paczka: {((i // batch_size) + 1)}/{total_batches}</p>
                    <p>Wysłano: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>Celery Task ID: {self.request.id}</p>
                    """,
                    text_content=f"Test Email #{i+1} - To jest testowy email numer {i+1} z {count}.",
                    scheduled_at=datetime.utcnow() + timedelta(seconds=i*2)  # Rozłóż w czasie
                )
                if email_id[0]:  # Jeśli email został dodany
                    created_emails.append(i+1)
            
            logger.info(f"✅ Utworzono {len(created_emails)} testowych emaili w kolejce")
            
            # Zaplanuj wysyłkę w paczkach
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, count)
                
                # Pobierz ID emaili dla tej paczki
                batch_emails = EmailQueue.query.filter(
                    EmailQueue.recipient_email == test_email,
                    EmailQueue.subject.like(f'%Test Email #{start_idx+1}%')
                ).limit(batch_size).all()
                
                batch_ids = [email.id for email in batch_emails]
                
                if batch_ids:
                    # Zaplanuj wysyłkę paczki z opóźnieniem
                    send_batch_emails_task.apply_async(
                        args=[batch_ids, batch_num + 1, total_batches],
                        countdown=batch_num * 30  # 30 sekund między paczkami
                    )
                    logger.info(f"📦 Zaplanowano paczkę {batch_num + 1}/{total_batches} ({len(batch_ids)} emaili)")
            
            return {
                'success': True,
                'message': f'Utworzono {len(created_emails)} testowych emaili, zaplanowano {total_batches} paczek',
                'total_emails': len(created_emails),
                'total_batches': total_batches,
                'test_email': test_email
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd testu wysyłania: {exc}")
            return {'success': False, 'error': str(exc)}
