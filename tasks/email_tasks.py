"""
Zadania Celery dla automatycznego wysyłania emaili
"""

import logging
import os
from datetime import datetime
from celery import current_task
from celery_config import celery_app

# Setup logging for Celery tasks
def setup_celery_logging():
    """Setup logging for Celery tasks"""
    logs_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger('celery_tasks')
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create file handler
    log_file = os.path.join(logs_dir, 'celery_tasks.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler
    logger.addHandler(file_handler)
    logger.propagate = False
    
    return logger

# Get logger
logger = setup_celery_logging()

@celery_app.task(bind=True, name='tasks.email_tasks.process_email_schedules')
def process_email_schedules(self):
    """
    Główne zadanie do przetwarzania harmonogramów emaili
    Uruchamiane co 5 minut przez Celery Beat
    """
    try:
        logger.info(f"🕐 {datetime.now()}: Starting email schedules processing...")
        
        # Import here to avoid context issues
        from app import app
        from app.services.email_service import EmailService
        
        with app.app_context():
            # Use new EmailService
            email_service = EmailService()
            success, message = email_service.process_scheduled_emails()
            
            if success:
                logger.info(f"✅ Email schedules processed successfully: {message}")
                return {
                    'success': True,
                    'timestamp': datetime.now().isoformat(),
                    'message': message
                }
            else:
                logger.error(f"❌ Failed to process email schedules: {message}")
                return {
                    'success': False,
                    'timestamp': datetime.now().isoformat(),
                    'error': message
                }
            
    except Exception as e:
        logger.error(f"❌ Error processing email schedules: {e}")
        
        # Retry after 5 minutes
        raise self.retry(countdown=300, exc=e)

@celery_app.task(bind=True, name='tasks.email_tasks.send_immediate_email')
def send_immediate_email(self, template_name, recipient_email, variables=None):
    """
    Zadanie do natychmiastowego wysłania emaila
    """
    try:
        logger.info(f"📧 Sending immediate email: {template_name} -> {recipient_email}")
        
        from app import app
        from app.services.email_service import EmailService
        
        with app.app_context():
            email_service = EmailService()
            
            success, message = email_service.send_template_email(
                to_email=recipient_email,
                template_name=template_name,
                context=variables or {}
            )
            
            if success:
                logger.info(f"✅ Email sent successfully: {recipient_email}")
                return {'success': True, 'recipient': recipient_email, 'message': message}
            else:
                logger.error(f"❌ Failed to send email: {recipient_email} - {message}")
                return {'success': False, 'recipient': recipient_email, 'error': message}
                
    except Exception as e:
        logger.error(f"❌ Error sending email: {e}")
        raise self.retry(countdown=60, exc=e)

@celery_app.task(bind=True, name='tasks.email_tasks.send_bulk_email')
def send_bulk_email(self, template_name, recipient_emails, variables=None):
    """
    Zadanie do wysyłania emaili do wielu odbiorców
    """
    try:
        logger.info(f"📧 Sending bulk emails: {template_name} -> {len(recipient_emails)} recipients")
        
        from app import app
        from app.services.email_service import EmailService
        
        with app.app_context():
            email_service = EmailService()
            
            results = {
                'total': len(recipient_emails),
                'success': 0,
                'failed': 0,
                'errors': []
            }
            
            for email in recipient_emails:
                try:
                    success, message = email_service.send_template_email(
                        to_email=email,
                        template_name=template_name,
                        context=variables or {}
                    )
                    
                    if success:
                        results['success'] += 1
                        logger.info(f"✅ Email sent: {email}")
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Failed to send to {email}: {message}")
                        logger.error(f"❌ Failed to send: {email} - {message}")
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Error sending to {email}: {str(e)}")
                    logger.error(f"❌ Error sending to {email}: {e}")
            
            logger.info(f"📊 Bulk email results: {results['success']}/{results['total']} success")
            return results
            
    except Exception as e:
        logger.error(f"❌ Error during bulk email sending: {e}")
        raise self.retry(countdown=300, exc=e)

@celery_app.task(bind=True, name='tasks.email_tasks.test_connection')
def test_connection(self):
    """
    Zadanie testowe do sprawdzenia połączenia z Celery
    """
    logger.info("🔍 Testing Celery connection...")
    return {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'message': 'Celery connection working correctly'
    }
