"""
Email logging utilities for the application
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from app import db
from app.models.email_model import EmailLog
from app.models.system_logs_model import SystemLog

def setup_email_logging() -> None:
    """
    Setup email logging configuration
    """
    logger = logging.getLogger(__name__)
    logger.info("Email logging setup completed")

def log_email_send(to_email: str, subject: str, status: str, 
                  template_id: Optional[int] = None, campaign_id: Optional[int] = None, 
                  event_id: Optional[int] = None, context: Optional[Dict[str, Any]] = None, 
                  error_message: Optional[str] = None, message_id: Optional[str] = None) -> bool:
    """
    Log email sending attempt
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        status: Email status (sent, failed, bounced, opened, clicked)
        template_id: Template ID (optional)
        campaign_id: Campaign ID (optional)
        event_id: Event ID (optional)
        context: Additional context data (optional)
        error_message: Error message if failed (optional)
        message_id: Message ID for tracking (optional)
        
    Returns:
        True if logged successfully, False otherwise
    """
    try:
        # Convert context to JSON string if it's a dict
        context_str = None
        if context:
            if isinstance(context, dict):
                import json
                context_str = json.dumps(context, ensure_ascii=False)
            else:
                context_str = str(context)
        
        log_entry = EmailLog(
            email=to_email,
            subject=subject,
            status=status,
            template_id=template_id,
            campaign_id=campaign_id,
            event_id=event_id,
            recipient_data=context_str,
            error_message=error_message,
            message_id=message_id,
            sent_at=datetime.now() if status == 'sent' else None
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error logging email send: {str(e)}")
        return False

def log_email_template_used(template_id: int, template_name: str, 
                           usage_context: Optional[str] = None) -> bool:
    """
    Log email template usage
    
    Args:
        template_id: Template ID
        template_name: Template name
        usage_context: Context of usage (optional)
        
    Returns:
        True if logged successfully, False otherwise
    """
    try:
        # Log to system logs
        log_entry = SystemLog(
            operation_type='email_template_used',
            operation_name=f'Template used: {template_name}',
            status='success',
            message=f'Template {template_name} (ID: {template_id}) was used',
            details={
                'template_id': template_id,
                'template_name': template_name,
                'usage_context': usage_context
            }
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error logging template usage: {str(e)}")
        return False

def log_email_schedule_executed(schedule_id: int, schedule_name: str, 
                               emails_processed: int, success_count: int, 
                               failed_count: int, execution_time: Optional[float] = None) -> bool:
    """
    Log email schedule execution
    
    Args:
        schedule_id: Schedule ID
        schedule_name: Schedule name
        emails_processed: Number of emails processed
        success_count: Number of successful sends
        failed_count: Number of failed sends
        execution_time: Execution time in seconds (optional)
        
    Returns:
        True if logged successfully, False otherwise
    """
    try:
        status = 'success' if failed_count == 0 else 'warning' if failed_count < emails_processed else 'error'
        message = f"Schedule '{schedule_name}' executed: {emails_processed} emails processed, {success_count} success, {failed_count} failed"
        
        log_entry = SystemLog(
            operation_type='email_schedule_executed',
            operation_name=f'Schedule executed: {schedule_name}',
            status=status,
            message=message,
            details={
                'schedule_id': schedule_id,
                'schedule_name': schedule_name,
                'emails_processed': emails_processed,
                'success_count': success_count,
                'failed_count': failed_count
            },
            execution_time=execution_time
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error logging schedule execution: {str(e)}")
        return False

def log_email_system_status(status: str, message: str, 
                           details: Optional[Dict[str, Any]] = None) -> bool:
    """
    Log email system status
    
    Args:
        status: System status (success, warning, error)
        message: Status message
        details: Additional details (optional)
        
    Returns:
        True if logged successfully, False otherwise
    """
    try:
        log_entry = SystemLog(
            operation_type='email_system_status',
            operation_name='Email system status check',
            status=status,
            message=message,
            details=details
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error logging system status: {str(e)}")
        return False

def log_smtp_connection(provider: str, status: str, message: str, 
                       details: Optional[Dict[str, Any]] = None) -> bool:
    """
    Log SMTP connection status
    
    Args:
        provider: Email provider (mailgun, smtp, etc.)
        status: Connection status (success, error)
        message: Status message
        details: Additional details (optional)
        
    Returns:
        True if logged successfully, False otherwise
    """
    try:
        log_entry = SystemLog(
            operation_type='smtp_connection',
            operation_name=f'SMTP connection: {provider}',
            status=status,
            message=message,
            details={
                'provider': provider,
                **(details or {})
            }
        )
        
        db.session.add(log_entry)
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        logger = logging.getLogger(__name__)
        logger.error(f"Error logging SMTP connection: {str(e)}")
        return False


