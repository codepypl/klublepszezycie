"""
Email tasks for Celery
"""
from celery import current_task
from celery.exceptions import Retry
from datetime import datetime, timedelta
import logging
import json
import time

from celery import current_app as celery
from app import create_app
from app.models import EmailQueue, EmailCampaign, UserGroupMember, User
# from app.services.email_service import EmailService  # Usunięte - nie istnieje

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
    Przetwarza kolejkę emaili w batchach - NOWY SYSTEM v2
    """
    with get_app_context():
        try:
            logger.info(f"🔄 Rozpoczynam przetwarzanie kolejki emaili v2 (batch: {batch_size})")
            
            # Użyj nowego systemu mailingu v2
            from app.services.email_v2 import EmailManager
            email_manager = EmailManager()
            stats = email_manager.process_queue(batch_size)
            
            logger.info(f"✅ Przetworzono v2 {stats['processed']} emaili: {stats['success']} sukces, {stats['failed']} błąd")
            
            return {
                'success': True,
                'processed': stats['processed'],
                'success_count': stats['success'],
                'failed_count': stats['failed']
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd przetwarzania kolejki v2: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.process_scheduled_campaigns_task')
def process_scheduled_campaigns_task(self):
    """
    Przetwarza zaplanowane kampanie - NOWY SYSTEM v2
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam przetwarzanie zaplanowanych kampanii v2")
            
            from app.utils.timezone_utils import get_local_now
            from app.models import db
            
            now = get_local_now()
            if now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            
            # Znajdź kampanie zaplanowane do wysłania
            scheduled_campaigns = EmailCampaign.query.filter(
                EmailCampaign.status == 'scheduled',
                EmailCampaign.send_type == 'scheduled',
                EmailCampaign.scheduled_at <= now
            ).all()
            
            processed_count = 0
            success_count = 0
            failed_count = 0
            
            for campaign in scheduled_campaigns:
                try:
                    logger.info(f"📧 Przetwarzam kampanię: {campaign.name} (ID: {campaign.id})")
                    
                    # Wywołaj zadanie wysyłania kampanii
                    from app.tasks.email_tasks import send_campaign_task
                    task = send_campaign_task.delay(campaign.id)
                    
                    # Aktualizuj status kampanii
                    campaign.status = 'sending'
                    db.session.commit()
                    
                    success_count += 1
                    processed_count += 1
                    logger.info(f"✅ Kampania {campaign.name} zaplanowana do wysłania (Task ID: {task.id})")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Błąd przetwarzania kampanii {campaign.id}: {e}")
            
            logger.info(f"✅ Przetworzono {processed_count} kampanii: {success_count} sukces, {failed_count} błąd")
            
            return {
                'success': True,
                'processed': processed_count,
                'success_count': success_count,
                'failed_count': failed_count
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd przetwarzania kampanii v2: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.send_batch_emails_task')
def send_batch_emails_task(self, email_ids, batch_size=50):
    """
    Wysyła emaile w batchach - OPTIMIZED FOR PAID MAILGUN PLAN
    """
    with get_app_context():
        try:
            logger.info(f"🔄 Rozpoczynam wysyłanie {len(email_ids)} emaili w batchach po {batch_size}")
            
            # Use Mailgun API service directly for better performance
            from app.services.mailgun_api_service import MailgunAPIService
            mailgun_service = MailgunAPIService()
            
            # Get emails from queue
            emails = EmailQueue.query.filter(EmailQueue.id.in_(email_ids)).all()
            
            if not emails:
                logger.warning("❌ Brak emaili do wysłania")
                return {'success': False, 'message': 'No emails to send'}
            
            # Send via Mailgun API with intelligent batching
            success, message = mailgun_service.send_batch(emails, batch_size)
            
            if success:
                logger.info(f"✅ Wysłano {len(emails)} emaili: {message}")
                return {
                    'success': True,
                    'sent': len(emails),
                    'message': message
                }
            else:
                logger.error(f"❌ Błąd wysyłania emaili: {message}")
                return {'success': False, 'message': message}
            
        except Exception as exc:
            logger.error(f"❌ Błąd wysyłania emaili: {exc}")
            raise self.retry(exc=exc, countdown=60)


@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.send_event_reminder_task')
def send_event_reminder_task(self, event_id, user_id, reminder_type="24h"):
    """
    Wysyła przypomnienie o wydarzeniu
    """
    with get_app_context():
        try:
            logger.info(f"🔄 Wysyłam przypomnienie o wydarzeniu {event_id} dla użytkownika {user_id}")
            
            from app.services.email_v2 import EmailManager
            email_manager = EmailManager()
            
            # Pobierz dane wydarzenia i użytkownika
            from app.models.events_model import EventSchedule
            event = EventSchedule.query.get(event_id)
            user = User.query.get(user_id)
            
            if not event or not user:
                logger.error(f"❌ Nie znaleziono wydarzenia {event_id} lub użytkownika {user_id}")
                return {'success': False, 'message': 'Event or user not found'}
            
            # Wyślij przypomnienie
            success, message = email_manager.send_template_email(
                template_name=f'event_reminder_{reminder_type}',
                to_email=user.email,
                context={
                    'user_name': user.first_name,
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
    Planuje przypomnienia o wydarzeniu - OPTIMIZED VERSION
    """
    with get_app_context():
        try:
            logger.info(f"🔄 Planuję przypomnienia o wydarzeniu {event_id} (inteligentne planowanie)")
            
            from app.services.smart_reminder_scheduler import SmartReminderScheduler
            scheduler = SmartReminderScheduler()
            
            # Użyj inteligentnego planowania
            success, message = scheduler.schedule_event_reminders_smart(event_id)
            
            if success:
                logger.info(f"✅ {message}")
                return {'success': True, 'message': message}
            else:
                logger.error(f"❌ {message}")
                return {'success': False, 'message': message}
            
        except Exception as exc:
            logger.error(f"❌ Błąd planowania przypomnień: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.send_campaign_task')
def send_campaign_task(self, campaign_id):
    """
    Wysyła kampanię email - NOWY SYSTEM v2
    """
    with get_app_context():
        try:
            logger.info(f"📧 Rozpoczynam wysyłanie kampanii {campaign_id}")
            
            from app.services.email_v2 import EmailManager
            from app.models import db, UserGroupMember, User
            from app.utils.timezone_utils import get_local_now
            import json
            
            # Pobierz kampanię
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                logger.error(f"❌ Nie znaleziono kampanii {campaign_id}")
                return {'success': False, 'message': 'Campaign not found'}
            
            # Sprawdź czy kampania nie jest już wysłana
            if campaign.status == 'sent':
                logger.warning(f"⚠️ Kampania {campaign_id} już została wysłana")
                return {'success': False, 'message': 'Campaign already sent'}
            
            # Pobierz odbiorców
            recipients = []
            
            if campaign.recipient_type == 'groups' and campaign.recipient_groups:
                try:
                    group_ids = json.loads(campaign.recipient_groups)
                    for group_id in group_ids:
                        group_members = UserGroupMember.query.filter_by(
                            group_id=group_id, 
                            is_active=True
                        ).all()
                        for member in group_members:
                            user = User.query.get(member.user_id)
                            if user and user.is_active:
                                recipients.append(user)
                except json.JSONDecodeError:
                    logger.error(f"❌ Błąd parsowania grup odbiorców dla kampanii {campaign_id}")
            
            elif campaign.recipient_type == 'users' and campaign.recipient_users:
                try:
                    user_ids = json.loads(campaign.recipient_users)
                    for user_id in user_ids:
                        user = User.query.get(user_id)
                        if user and user.is_active:
                            recipients.append(user)
                except json.JSONDecodeError:
                    logger.error(f"❌ Błąd parsowania użytkowników dla kampanii {campaign_id}")
            
            elif campaign.recipient_type == 'custom' and campaign.custom_emails:
                try:
                    custom_emails = json.loads(campaign.custom_emails)
                    for email in custom_emails:
                        # Utwórz tymczasowy obiekt użytkownika
                        temp_user = type('User', (), {
                            'email': email,
                            'first_name': email.split('@')[0],
                            'id': None
                        })()
                        recipients.append(temp_user)
                except json.JSONDecodeError:
                    logger.error(f"❌ Błąd parsowania niestandardowych emaili dla kampanii {campaign_id}")
            
            if not recipients:
                logger.warning(f"⚠️ Brak odbiorców dla kampanii {campaign_id}")
                campaign.status = 'cancelled'
                db.session.commit()
                return {'success': False, 'message': 'No recipients found'}
            
            # Przygotuj kontekst
            context = {}
            if campaign.content_variables:
                try:
                    context = json.loads(campaign.content_variables)
                except json.JSONDecodeError:
                    logger.warning(f"⚠️ Błąd parsowania zmiennych treści dla kampanii {campaign_id}")
            
            # Wyślij emaile
            email_manager = EmailManager()
            sent_count = 0
            failed_count = 0
            
            for recipient in recipients:
                try:
                    # Przygotuj kontekst dla odbiorcy
                    recipient_context = context.copy()
                    recipient_context.update({
                        'user_name': recipient.first_name,
                        'user_email': recipient.email,
                        'campaign_name': campaign.name
                    })
                    
                    # Wyślij email
                    success, message = email_manager.send_template_email(
                        to_email=recipient.email,
                        template_name=campaign.template.name if campaign.template else None,
                        context=recipient_context,
                        priority=2,
                        campaign_id=campaign_id
                    )
                    
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                        logger.warning(f"⚠️ Błąd wysyłania do {recipient.email}: {message}")
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Błąd wysyłania do {recipient.email}: {e}")
            
            # Aktualizuj statystyki kampanii
            campaign.sent_count = sent_count
            campaign.failed_count = failed_count
            campaign.status = 'sent'
            campaign.sent_at = get_local_now()
            db.session.commit()
            
            logger.info(f"✅ Kampania {campaign_id} wysłana: {sent_count} sukces, {failed_count} błąd")
            
            return {
                'success': True,
                'sent_count': sent_count,
                'failed_count': failed_count,
                'total_recipients': len(recipients)
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd wysyłania kampanii {campaign_id}: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.schedule_campaign_task')
def schedule_campaign_task(self, campaign_id):
    """
    Planuje kampanię do wysłania w określonym czasie - NOWY SYSTEM v2
    """
    with get_app_context():
        try:
            logger.info(f"📅 Planuję kampanię {campaign_id}")
            
            from app.models import db
            from app.utils.timezone_utils import get_local_now
            
            # Pobierz kampanię
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                logger.error(f"❌ Nie znaleziono kampanii {campaign_id}")
                return {'success': False, 'message': 'Campaign not found'}
            
            # Sprawdź czy kampania ma ustawiony czas wysłania
            if not campaign.scheduled_at:
                logger.error(f"❌ Kampania {campaign_id} nie ma ustawionego czasu wysłania")
                return {'success': False, 'message': 'No scheduled time set'}
            
            # Sprawdź czy czas wysłania nie jest w przeszłości
            now = get_local_now()
            if now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            if campaign.scheduled_at.tzinfo is not None:
                scheduled_at = campaign.scheduled_at.replace(tzinfo=None)
            else:
                scheduled_at = campaign.scheduled_at
                
            if scheduled_at <= now:
                logger.warning(f"⚠️ Czas wysłania kampanii {campaign_id} jest w przeszłości")
                # Wyślij natychmiast
                return send_campaign_task(campaign_id)
            
            # Zaplanuj wysłanie kampanii
            campaign.status = 'scheduled'
            db.session.commit()
            
            logger.info(f"✅ Kampania {campaign_id} zaplanowana na {scheduled_at}")
            
            return {
                'success': True,
                'message': f'Campaign scheduled for {scheduled_at}',
                'scheduled_at': scheduled_at.isoformat()
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd planowania kampanii {campaign_id}: {exc}")
            raise self.retry(exc=exc, countdown=60)