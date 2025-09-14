"""
Email logging utility functions
"""
import logging
import os
from datetime import datetime

def setup_email_logging():
    """Setup dedicated email logging"""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create email logger
    email_logger = logging.getLogger('email_system')
    email_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    for handler in email_logger.handlers[:]:
        email_logger.removeHandler(handler)
    
    # Create file handler for email logs
    email_log_file = os.path.join(logs_dir, 'mailer.log')
    file_handler = logging.FileHandler(email_log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    email_logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    email_logger.propagate = False
    
    return email_logger

def log_email_send(to_email, subject, status, message=""):
    """Log email sending attempt"""
    logger = setup_email_logging()
    
    if status == 'success':
        logger.info(f"✅ Email sent successfully to {to_email} - Subject: {subject}")
    elif status == 'error':
        logger.error(f"❌ Failed to send email to {to_email} - Subject: {subject} - Error: {message}")
    elif status == 'warning':
        logger.warning(f"⚠️ Email warning for {to_email} - Subject: {subject} - Message: {message}")
    else:
        logger.info(f"📧 Email attempt to {to_email} - Subject: {subject} - Status: {status} - Message: {message}")

def log_email_template_used(template_name, recipient_count):
    """Log email template usage"""
    logger = setup_email_logging()
    logger.info(f"📋 Template '{template_name}' used for {recipient_count} recipients")

def log_email_schedule_executed(schedule_name, success_count, error_count):
    """Log email schedule execution"""
    logger = setup_email_logging()
    if error_count > 0:
        logger.warning(f"📅 Schedule '{schedule_name}' executed - Success: {success_count}, Errors: {error_count}")
    else:
        logger.info(f"📅 Schedule '{schedule_name}' executed successfully for {success_count} recipients")

def log_email_system_status(status, message=""):
    """Log email system status"""
    logger = setup_email_logging()
    if status == 'started':
        logger.info(f"🚀 Email system started - {message}")
    elif status == 'stopped':
        logger.info(f"🛑 Email system stopped - {message}")
    elif status == 'error':
        logger.error(f"💥 Email system error - {message}")
    else:
        logger.info(f"📊 Email system status: {status} - {message}")

def log_smtp_connection(server, port, status, message=""):
    """Log SMTP connection attempts"""
    logger = setup_email_logging()
    if status == 'success':
        logger.info(f"🔗 SMTP connected to {server}:{port}")
    elif status == 'error':
        logger.error(f"❌ SMTP connection failed to {server}:{port} - {message}")
    else:
        logger.info(f"🔄 SMTP connection attempt to {server}:{port} - {message}")







