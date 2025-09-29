"""
Event tasks for Celery
"""
from celery import current_task
from celery.exceptions import Retry
from datetime import datetime, timedelta
import logging

from celery_app import celery
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
    Przetwarza przypomnienia o wydarzeniach
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam przetwarzanie przypomnień o wydarzeniach")
            
            from app.services.mailgun_service import EnhancedNotificationProcessor
            email_processor = EnhancedNotificationProcessor()
            
            # Pobierz wydarzenia, które wymagają przypomnień
            now = datetime.now()
            tomorrow = now + timedelta(days=1)
            in_one_hour = now + timedelta(hours=1)
            in_five_minutes = now + timedelta(minutes=5)
            
            # Wydarzenia za 24h
            events_24h = EventSchedule.query.filter(
                EventSchedule.event_date >= now,
                EventSchedule.event_date <= tomorrow,
                EventSchedule.is_active == True
            ).all()
            
            # Wydarzenia za 1h
            events_1h = EventSchedule.query.filter(
                EventSchedule.event_date >= now,
                EventSchedule.event_date <= in_one_hour,
                EventSchedule.is_active == True
            ).all()
            
            # Wydarzenia za 5 minut
            events_5min = EventSchedule.query.filter(
                EventSchedule.event_date >= now,
                EventSchedule.event_date <= in_five_minutes,
                EventSchedule.is_active == True
            ).all()
            
            stats = {'processed': 0, 'success': 0, 'failed': 0}
            
            # Przetwórz wydarzenia za 24h
            for event in events_24h:
                try:
                    from app.models.user_model import User
                    
                    # Pobierz wszystkich członków klubu (club_member=True) + osoby zapisane na wydarzenie
                    club_members = User.query.filter_by(club_member=True, is_active=True).all()
                    event_registrations = User.query.filter_by(
                        event_id=event.id,
                        account_type='event_registration'
                    ).all()
                    
                    # Połącz listy i usuń duplikaty (po email)
                    all_users = {}
                    for user in club_members + event_registrations:
                        all_users[user.email] = user
                    
                    users = list(all_users.values())
                    logger.info(f"📧 Wysyłam przypomnienia 24h dla wydarzenia '{event.title}' do {len(users)} użytkowników")
                    
                    for user in users:
                        success, message = email_processor.send_template_email(
                            template_name='event_reminder_24h',
                            to_email=user.email,
                            to_name=user.first_name,
                            context={
                                'event_title': event.title,
                                'event_date': event.event_date.strftime('%d.%m.%Y'),
                                'event_time': event.event_date.strftime('%H:%M'),
                                'event_location': event.location or 'Online',
                                'user_name': user.first_name,
                                'event_id': event.id,
                                'user_id': user.id
                            },
                            use_queue=True
                        )
                        
                        stats['processed'] += 1
                        if success:
                            stats['success'] += 1
                        else:
                            stats['failed'] += 1
                            
                except Exception as exc:
                    logger.error(f"❌ Błąd przetwarzania wydarzenia {event.id}: {exc}")
                    stats['failed'] += 1
            
            # Przetwórz wydarzenia za 1h
            for event in events_1h:
                try:
                    from app.models.user_model import User
                    
                    # Pobierz wszystkich członków klubu (club_member=True) + osoby zapisane na wydarzenie
                    club_members = User.query.filter_by(club_member=True, is_active=True).all()
                    event_registrations = User.query.filter_by(
                        event_id=event.id,
                        account_type='event_registration'
                    ).all()
                    
                    # Połącz listy i usuń duplikaty (po email)
                    all_users = {}
                    for user in club_members + event_registrations:
                        all_users[user.email] = user
                    
                    users = list(all_users.values())
                    logger.info(f"📧 Wysyłam przypomnienia 1h dla wydarzenia '{event.title}' do {len(users)} użytkowników")
                    
                    for user in users:
                        success, message = email_processor.send_template_email(
                            template_name='event_reminder_1h',
                            to_email=user.email,
                            to_name=user.first_name,
                            context={
                                'event_title': event.title,
                                'event_date': event.event_date.strftime('%d.%m.%Y'),
                                'event_time': event.event_date.strftime('%H:%M'),
                                'event_location': event.location or 'Online',
                                'user_name': user.first_name,
                                'event_id': event.id,
                                'user_id': user.id
                            },
                            use_queue=True
                        )
                        
                        stats['processed'] += 1
                        if success:
                            stats['success'] += 1
                        else:
                            stats['failed'] += 1
                            
                except Exception as exc:
                    logger.error(f"❌ Błąd przetwarzania wydarzenia {event.id}: {exc}")
                    stats['failed'] += 1
            
            # Przetwórz wydarzenia za 5 minut
            for event in events_5min:
                try:
                    from app.models.user_model import User
                    
                    # Pobierz wszystkich członków klubu (club_member=True) + osoby zapisane na wydarzenie
                    club_members = User.query.filter_by(club_member=True, is_active=True).all()
                    event_registrations = User.query.filter_by(
                        event_id=event.id,
                        account_type='event_registration'
                    ).all()
                    
                    # Połącz listy i usuń duplikaty (po email)
                    all_users = {}
                    for user in club_members + event_registrations:
                        all_users[user.email] = user
                    
                    users = list(all_users.values())
                    logger.info(f"📧 Wysyłam przypomnienia 5min dla wydarzenia '{event.title}' do {len(users)} użytkowników")
                    
                    for user in users:
                        success, message = email_processor.send_template_email(
                            template_name='event_reminder_5min',
                            to_email=user.email,
                            to_name=user.first_name,
                            context={
                                'event_title': event.title,
                                'event_date': event.event_date.strftime('%d.%m.%Y'),
                                'event_time': event.event_date.strftime('%H:%M'),
                                'event_location': event.location or 'Online',
                                'user_name': user.first_name,
                                'event_id': event.id,
                                'user_id': user.id
                            },
                            use_queue=True
                        )
                        
                        stats['processed'] += 1
                        if success:
                            stats['success'] += 1
                        else:
                            stats['failed'] += 1
                            
                except Exception as exc:
                    logger.error(f"❌ Błąd przetwarzania wydarzenia {event.id}: {exc}")
                    stats['failed'] += 1
            
            logger.info(f"✅ Przetworzono {stats['processed']} przypomnień: {stats['success']} sukces, {stats['failed']} błąd")
            
            return {
                'success': True,
                'processed': stats['processed'],
                'success_count': stats['success'],
                'failed_count': stats['failed']
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd przetwarzania przypomnień: {exc}")
            raise self.retry(exc=exc, countdown=60)

@celery.task(bind=True, max_retries=3, default_retry_delay=60, name='app.tasks.event_tasks.archive_ended_events_task')
def archive_ended_events_task(self):
    """
    Archiwizuje zakończone wydarzenia
    """
    with get_app_context():
        try:
            logger.info("🔄 Rozpoczynam archiwizację zakończonych wydarzeń")
            
            from app import db
            
            # Znajdź wydarzenia zakończone więcej niż 24h temu
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            ended_events = EventSchedule.query.filter(
                EventSchedule.event_date < cutoff_time,
                EventSchedule.is_active == True
            ).all()
            
            stats = {'processed': 0, 'archived': 0, 'failed': 0}
            
            for event in ended_events:
                try:
                    # Oznacz jako nieaktywne
                    event.is_active = False
                    stats['processed'] += 1
                    stats['archived'] += 1
                    
                except Exception as exc:
                    logger.error(f"❌ Błąd archiwizacji wydarzenia {event.id}: {exc}")
                    stats['failed'] += 1
            
            # Zapisz zmiany
            db.session.commit()
            
            logger.info(f"✅ Zarchiwizowano {stats['archived']} wydarzeń: {stats['processed']} przetworzonych, {stats['failed']} błędów")
            
            return {
                'success': True,
                'processed': stats['processed'],
                'archived': stats['archived'],
                'failed': stats['failed']
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
            
            from app.models.email_model import EmailQueue
            from app import db
            
            # Usuń e-maile starsze niż 30 dni
            cutoff_time = datetime.now() - timedelta(days=30)
            
            old_emails = EmailQueue.query.filter(
                EmailQueue.created_at < cutoff_time,
                EmailQueue.status.in_(['sent', 'failed'])
            ).all()
            
            stats = {'processed': 0, 'deleted': 0, 'failed': 0}
            
            for email in old_emails:
                try:
                    db.session.delete(email)
                    stats['processed'] += 1
                    stats['deleted'] += 1
                    
                except Exception as exc:
                    logger.error(f"❌ Błąd usuwania e-maila {email.id}: {exc}")
                    stats['failed'] += 1
            
            # Zapisz zmiany
            db.session.commit()
            
            logger.info(f"✅ Usunięto {stats['deleted']} starych e-maili: {stats['processed']} przetworzonych, {stats['failed']} błędów")
            
            return {
                'success': True,
                'processed': stats['processed'],
                'deleted': stats['deleted'],
                'failed': stats['failed']
            }
            
        except Exception as exc:
            logger.error(f"❌ Błąd czyszczenia starych przypomnień: {exc}")
            raise self.retry(exc=exc, countdown=60)