"""
Zadania Celery dla automatycznego wysyłania emaili
"""

import logging
from datetime import datetime
from celery import current_task
from celery_config import celery_app

# Konfiguracja logowania
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='tasks.email_tasks.process_email_schedules')
def process_email_schedules(self):
    """
    Główne zadanie do przetwarzania harmonogramów emaili
    Uruchamiane co 5 minut przez Celery Beat
    """
    try:
        logger.info(f"🕐 {datetime.now()}: Uruchamianie przetwarzania harmonogramów emaili...")
        
        # Import tutaj, żeby uniknąć problemów z kontekstem aplikacji
        from app import app, db
        from services.email_automation_service import email_automation_service
        
        with app.app_context():
            # Przetwórz harmonogramy wydarzeń (EventEmailSchedule)
            event_results = email_automation_service.process_scheduled_emails()
            logger.info(f"📊 Harmonogramy wydarzeń: {event_results}")
            
            # Przetwórz harmonogramy EmailSchedule (jeśli są)
            from app import check_and_run_schedules
            check_and_run_schedules()
            
            # Zwróć wyniki
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'event_results': event_results,
                'message': 'Harmonogramy przetworzone pomyślnie'
            }
            
    except Exception as e:
        logger.error(f"❌ Błąd podczas przetwarzania harmonogramów: {e}")
        
        # Retry po 5 minutach
        raise self.retry(countdown=300, exc=e)

@celery_app.task(bind=True, name='tasks.email_tasks.send_immediate_email')
def send_immediate_email(self, template_name, recipient_email, variables=None):
    """
    Zadanie do natychmiastowego wysłania emaila
    """
    try:
        logger.info(f"📧 Wysyłanie natychmiastowego emaila: {template_name} -> {recipient_email}")
        
        from app import app
        from services.email_service import EmailService
        
        with app.app_context():
            email_service = EmailService()
            email_service.init_app(app)
            
            result = email_service.send_template_email(
                to_email=recipient_email,
                template_name=template_name,
                variables=variables or {}
            )
            
            if result:
                logger.info(f"✅ Email wysłany pomyślnie: {recipient_email}")
                return {'success': True, 'recipient': recipient_email}
            else:
                logger.error(f"❌ Błąd wysyłania emaila: {recipient_email}")
                return {'success': False, 'recipient': recipient_email, 'error': 'Send failed'}
                
    except Exception as e:
        logger.error(f"❌ Błąd podczas wysyłania emaila: {e}")
        raise self.retry(countdown=60, exc=e)

@celery_app.task(bind=True, name='tasks.email_tasks.send_bulk_email')
def send_bulk_email(self, template_name, recipient_emails, variables=None):
    """
    Zadanie do wysyłania emaili do wielu odbiorców
    """
    try:
        logger.info(f"📧 Wysyłanie masowych emaili: {template_name} -> {len(recipient_emails)} odbiorców")
        
        from app import app
        from services.email_service import EmailService
        
        with app.app_context():
            email_service = EmailService()
            email_service.init_app(app)
            
            results = {
                'total': len(recipient_emails),
                'success': 0,
                'failed': 0,
                'errors': []
            }
            
            for email in recipient_emails:
                try:
                    result = email_service.send_template_email(
                        to_email=email,
                        template_name=template_name,
                        variables=variables or {}
                    )
                    
                    if result:
                        results['success'] += 1
                        logger.info(f"✅ Email wysłany: {email}")
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Failed to send to {email}")
                        logger.error(f"❌ Błąd wysyłania: {email}")
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Error sending to {email}: {str(e)}")
                    logger.error(f"❌ Błąd wysyłania do {email}: {e}")
            
            logger.info(f"📊 Wyniki masowego wysyłania: {results['success']}/{results['total']} sukces")
            return results
            
    except Exception as e:
        logger.error(f"❌ Błąd podczas masowego wysyłania: {e}")
        raise self.retry(countdown=300, exc=e)

@celery_app.task(bind=True, name='tasks.email_tasks.test_connection')
def test_connection(self):
    """
    Zadanie testowe do sprawdzenia połączenia z Celery
    """
    logger.info("🔍 Test połączenia Celery...")
    return {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'message': 'Połączenie z Celery działa poprawnie'
    }
