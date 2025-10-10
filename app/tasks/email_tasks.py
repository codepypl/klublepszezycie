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
    Przetwarza zaplanowane kampanie - NOWY SYSTEM v3
    
    Uruchamiany co 1 minutę.
    Znajduje kampanie ze statusem 'draft' lub 'scheduled' i dodaje je do kolejki.
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam przetwarzanie kampanii v3")
            
            from app.services.email_v2.queue.scheduler import EmailScheduler
            from app.utils.timezone_utils import get_local_now
            from app.models import db
            
            scheduler = EmailScheduler()
            
            now = get_local_now()
            if now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            
            # Znajdź kampanie do zaplanowania
            # 1. Kampanie natychmiastowe (draft + immediate)
            immediate_campaigns = EmailCampaign.query.filter(
                EmailCampaign.status == 'draft',
                EmailCampaign.send_type == 'immediate'
            ).all()
            
            # 2. Kampanie planowane (scheduled + scheduled_at <= now)
            scheduled_campaigns = EmailCampaign.query.filter(
                EmailCampaign.status.in_(['draft', 'scheduled']),
                EmailCampaign.send_type == 'scheduled',
                EmailCampaign.scheduled_at <= now
            ).all()
            
            campaigns = immediate_campaigns + scheduled_campaigns
            
            if not campaigns:
                logger.info("ℹ️ Brak kampanii do zaplanowania")
                return {
                    'success': True,
                    'processed': 0,
                    'success_count': 0,
                    'failed_count': 0
                }
            
            processed_count = 0
            success_count = 0
            failed_count = 0
            
            for campaign in campaigns:
                try:
                    logger.info(f"📧 Planuję kampanię: {campaign.name} (ID: {campaign.id}, typ: {campaign.send_type})")
                    
                    # Użyj nowego schedulera
                    success, message = scheduler.schedule_campaign(campaign.id)
                    
                    if success:
                        success_count += 1
                        logger.info(f"✅ {message}")
                    else:
                        failed_count += 1
                        logger.warning(f"⚠️ {message}")
                    
                    processed_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"❌ Błąd planowania kampanii {campaign.id}: {e}")
            
            logger.info(f"✅ Przetworzono {processed_count} kampanii: {success_count} sukces, {failed_count} błąd")
            
            return {
                'success': True,
                'processed': processed_count,
                'success_count': success_count,
                'failed_count': failed_count
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd przetwarzania kampanii v3: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.send_batch_emails_task')
def send_batch_emails_task(self, email_ids, batch_size=50):
    """
    Wysyła emaile w batchach - OPTIMIZED FOR PAID MAILGUN PLAN
    """
    with get_app_context():
        try:
            logger.info(f"🔄 Rozpoczynam wysyłanie {len(email_ids)} emaili w batchach po {batch_size}")
            
            # Use new EmailManager v2 for better performance
            from app.services.email_v2 import EmailManager
            email_manager = EmailManager()
            
            # Get emails from queue
            emails = EmailQueue.query.filter(EmailQueue.id.in_(email_ids)).all()
            
            if not emails:
                logger.warning("❌ Brak emaili do wysłania")
                return {'success': False, 'message': 'No emails to send'}
            
            # Send via EmailManager with intelligent batching
            stats = email_manager.process_queue(batch_size)
            
            if stats['processed'] > 0:
                logger.info(f"✅ Przetworzono {stats['processed']} emaili: {stats['success']} sukces, {stats['failed']} błąd")
                return {
                    'success': True,
                    'sent': stats['success'],
                    'failed': stats['failed'],
                    'processed': stats['processed']
                }
            else:
                logger.warning("⚠️ Brak emaili do przetworzenia")
                return {'success': False, 'message': 'No emails to process'}
            
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
            
            # Przygotuj kontekst z wszystkimi wymaganymi zmiennymi
            context = {
                'user_name': user.first_name or 'Użytkowniku',
                'event_title': event.title,
                'event_date': event.event_date.strftime('%d.%m.%Y'),
                'event_time': event.event_date.strftime('%H:%M'),
                'event_location': event.location or 'Online',
                'event_id': event_id,
                'user_id': user_id,
                'event_url': f"https://klublepszezycie.pl/events/{event.id}",
                'event_datetime': event.event_date.strftime('%d.%m.%Y %H:%M'),
                'event_description': event.description or ''
            }
            
            # Dodaj linki do wypisania i usunięcia konta
            try:
                from app.services.unsubscribe_manager import unsubscribe_manager
                context.update({
                    'unsubscribe_url': unsubscribe_manager.get_unsubscribe_url(user.email),
                    'delete_account_url': unsubscribe_manager.get_delete_account_url(user.email)
                })
            except Exception as e:
                logger.warning(f"⚠️ Błąd generowania linków unsubscribe dla {user.email}: {e}")
                context.update({
                    'unsubscribe_url': 'mailto:kontakt@klublepszezycie.pl',
                    'delete_account_url': 'mailto:kontakt@klublepszezycie.pl'
                })
            
            # Wyślij przypomnienie
            success, message = email_manager.send_template_email(
                template_name=f'event_reminder_{reminder_type}',
                to_email=user.email,
                context=context,
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
    Aktualizuje powiadomienia o wydarzeniu (reschedule przypomnień)
    
    Używane gdy:
    - Admin zmienia datę wydarzenia
    - System wykrywa niespójność w kolejce
    """
    with get_app_context():
        try:
            logger.info(f"🔄 Aktualizuję powiadomienia o wydarzeniu {event_id}")
            
            from app.models.events_model import EventSchedule
            from app.services.email_v2.queue.scheduler import EmailScheduler
            
            event = EventSchedule.query.get(event_id)
            
            if not event:
                logger.error(f"❌ Nie znaleziono wydarzenia {event_id}")
                return {'success': False, 'message': 'Event not found'}
            
            # Reschedule przypomnień
            scheduler = EmailScheduler()
            success, message = scheduler.reschedule_event_reminders(event_id)
            
            if success:
                logger.info(f"✅ Powiadomienia o wydarzeniu {event_id} zaktualizowane: {message}")
                return {'success': True, 'message': message}
            else:
                logger.error(f"❌ Błąd aktualizacji powiadomień: {message}")
                return {'success': False, 'message': message}
            
        except Exception as exc:
            logger.error(f"❌ Błąd aktualizacji powiadomień: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.monitor_event_changes_task')
def monitor_event_changes_task(self):
    """
    Monitoruje zmiany w wydarzeniach i automatycznie reschedule'uje przypomnienia
    
    Uruchamiany: co 15 minut
    
    Sprawdza:
    - Czy emaile w kolejce mają poprawne daty (zgodne z wydarzeniem)
    - Czy potrzebny jest reschedule
    """
    with get_app_context():
        try:
            logger.info("🔍 Rozpoczynam monitorowanie zmian w wydarzeniach")
            
            from app.models.events_model import EventSchedule
            from app.models.email_model import EmailQueue
            from app.services.email_v2.queue.scheduler import EmailScheduler
            from app.utils.timezone_utils import get_local_now
            from datetime import timedelta
            
            # Pobierz wszystkie aktywne wydarzenia z zaplanowanymi przypomnieniami
            events = EventSchedule.query.filter_by(
                is_active=True,
                reminders_scheduled=True
            ).all()
            
            if not events:
                logger.info("ℹ️ Brak wydarzeń do monitorowania")
                return {
                    'success': True,
                    'checked': 0,
                    'rescheduled': 0
                }
            
            rescheduled_count = 0
            scheduler = EmailScheduler()
            
            for event in events:
                try:
                    # Sprawdź czy są emaile dla tego wydarzenia w kolejce
                    queue_items = EmailQueue.query.filter_by(
                        event_id=event.id,
                        status='pending'
                    ).all()
                    
                    if not queue_items:
                        # Brak emaili w kolejce - może trzeba zaplanować?
                        logger.warning(f"⚠️ Wydarzenie {event.id} ma reminders_scheduled=True ale brak emaili w kolejce")
                        
                        # Zresetuj flagę i pozwól process_event_reminders_task zaplanować
                        event.reminders_scheduled = False
                        from app import db
                        db.session.commit()
                        continue
                    
                    # Sprawdź czy daty się zgadzają
                    # Oczekiwane scheduled_at: event.event_date - offset
                    needs_reschedule = False
                    
                    for queue_item in queue_items:
                        # Wyciągnij typ przypomnienia z template_name (np. "event_reminder_24h" -> "24h")
                        if queue_item.template_name and 'event_reminder_' in queue_item.template_name:
                            reminder_type = queue_item.template_name.replace('event_reminder_', '')
                            
                            # Wylicz oczekiwaną datę scheduled_at
                            offset_map = {
                                '24h': timedelta(hours=24),
                                '1h': timedelta(hours=1),
                                '5min': timedelta(minutes=5)
                            }
                            
                            if reminder_type in offset_map:
                                offset = offset_map[reminder_type]
                                expected_scheduled = event.event_date - offset
                                
                                # Normalizuj timezone
                                expected_naive = expected_scheduled.replace(tzinfo=None) if hasattr(expected_scheduled, 'tzinfo') and expected_scheduled.tzinfo else expected_scheduled
                                queue_naive = queue_item.scheduled_at.replace(tzinfo=None) if hasattr(queue_item.scheduled_at, 'tzinfo') and queue_item.scheduled_at.tzinfo else queue_item.scheduled_at
                                
                                # Sprawdź różnicę (tolerancja 5 minut)
                                time_diff = abs((expected_naive - queue_naive).total_seconds())
                                
                                if time_diff > 300:  # > 5 minut
                                    logger.warning(f"⚠️ Niespójność dla wydarzenia {event.id}: oczekiwano {expected_naive}, jest {queue_naive} (różnica: {time_diff}s)")
                                    needs_reschedule = True
                                    break
                    
                    # Jeśli potrzebny reschedule
                    if needs_reschedule:
                        logger.info(f"🔄 Reschedule przypomnień dla wydarzenia {event.id}: {event.title}")
                        success, message = scheduler.reschedule_event_reminders(event.id)
                        
                        if success:
                            rescheduled_count += 1
                            logger.info(f"✅ Zreschedule'owano: {message}")
                        else:
                            logger.error(f"❌ Błąd reschedulingu: {message}")
                    
                except Exception as e:
                    logger.error(f"❌ Błąd sprawdzania wydarzenia {event.id}: {e}")
            
            logger.info(f"✅ Monitorowanie zakończone: sprawdzono {len(events)} wydarzeń, zreschedule'owano {rescheduled_count}")
            
            return {
                'success': True,
                'checked': len(events),
                'rescheduled': rescheduled_count
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd monitorowania wydarzeń: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.email_tasks.schedule_event_reminders_task')
def schedule_event_reminders_task(self, event_id):
    """
    Planuje przypomnienia o wydarzeniu - WYŁĄCZONE (używamy process_event_reminders_task)
    """
    with get_app_context():
        try:
            logger.warning(f"⚠️ schedule_event_reminders_task wyłączone - używamy process_event_reminders_task")
            
            # Sprawdź czy wydarzenie już ma przypomnienia
            from app.models.events_model import EventSchedule
            from app.models.email_model import EmailQueue
            
            event = EventSchedule.query.get(event_id)
            if not event:
                return {'success': False, 'message': 'Wydarzenie nie zostało znalezione'}
            
            if event.reminders_scheduled:
                return {'success': True, 'message': 'Przypomnienia już zaplanowane'}
            
            # Sprawdź czy w kolejce już są emaile
            existing_emails = EmailQueue.query.filter_by(
                event_id=event_id,
                status='pending'
            ).count()
            
            if existing_emails > 0:
                return {'success': True, 'message': f'Wydarzenie już ma {existing_emails} emaili w kolejce'}
            
            return {'success': True, 'message': 'Zadanie wyłączone - używamy process_event_reminders_task'}
            
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
                        'user_name': recipient.first_name or 'Użytkowniku',
                        'user_email': recipient.email,
                        'campaign_name': campaign.name,
                        'message_subject': campaign.subject,
                        'message_content': campaign.html_content or campaign.text_content or 'Brak treści wiadomości',
                        'admin_message': campaign.html_content or campaign.text_content or 'Brak treści wiadomości',
                        'additional_info': '',
                        'contact_url': 'mailto:kontakt@klublepszezycie.pl'
                    })
                    
                    # Dodaj linki do wypisania i usunięcia konta
                    try:
                        from app.services.unsubscribe_manager import unsubscribe_manager
                        recipient_context.update({
                            'unsubscribe_url': unsubscribe_manager.get_unsubscribe_url(recipient.email),
                            'delete_account_url': unsubscribe_manager.get_delete_account_url(recipient.email)
                        })
                    except Exception as e:
                        logger.warning(f"⚠️ Błąd generowania linków unsubscribe dla {recipient.email}: {e}")
                        recipient_context.update({
                            'unsubscribe_url': 'mailto:kontakt@klublepszezycie.pl',
                            'delete_account_url': 'mailto:kontakt@klublepszezycie.pl'
                        })
                    
                    # Wyślij email (użyj szablonu jeśli istnieje)
                    template_name = campaign.template.name if campaign.template else 'default_campaign'
                    success, message = email_manager.send_template_email(
                        to_email=recipient.email,
                        template_name=template_name,
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