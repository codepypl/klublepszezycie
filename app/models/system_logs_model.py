"""
System Logs Model - logowanie operacji systemowych
"""
from datetime import datetime
from . import db

class SystemLog(db.Model):
    """System operation logs"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    operation_type = db.Column(db.String(50), nullable=False, index=True)  # 'email_processing', 'event_reminders', 'group_update', etc.
    operation_name = db.Column(db.String(100), nullable=False)  # Human readable operation name
    status = db.Column(db.String(20), nullable=False)  # 'success', 'error', 'warning'
    message = db.Column(db.Text, nullable=False)  # Detailed message
    details = db.Column(db.JSON, nullable=True)  # Additional details as JSON
    execution_time = db.Column(db.Float, nullable=True)  # Execution time in seconds
    created_at = db.Column(db.DateTime, default=lambda: __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now(), index=True)
    
    def __repr__(self):
        return f'<SystemLog {self.operation_type} - {self.status}>'
    
    @classmethod
    def log_email_processing(cls, processed_count, success_count, failed_count, execution_time=None):
        """Log email processing operation"""
        status = 'success' if failed_count == 0 else 'warning' if failed_count < processed_count else 'error'
        message = f"Przetworzono {processed_count} emaili. Sukces: {success_count}, Błędy: {failed_count}"
        
        log = cls(
            operation_type='email_processing',
            operation_name='Przetwarzanie kolejek emaili',
            status=status,
            message=message,
            details={
                'processed_count': processed_count,
                'success_count': success_count,
                'failed_count': failed_count
            },
            execution_time=execution_time
        )
        db.session.add(log)
        return log
    
    @classmethod
    def log_event_reminders(cls, processed_events, success, message, execution_time=None):
        """Log event reminders processing"""
        log = cls(
            operation_type='event_reminders',
            operation_name='Przetwarzanie przypomnień o wydarzeniach',
            status='success' if success else 'error',
            message=message,
            details={
                'processed_events': processed_events,
                'success': success
            },
            execution_time=execution_time
        )
        db.session.add(log)
        return log
    
    @classmethod
    def log_group_update(cls, updated_groups, success, message, execution_time=None):
        """Log group update operation"""
        log = cls(
            operation_type='group_update',
            operation_name='Aktualizacja grup użytkowników',
            status='success' if success else 'error',
            message=message,
            details={
                'updated_groups': updated_groups,
                'success': success
            },
            execution_time=execution_time
        )
        db.session.add(log)
        return log
    
    @classmethod
    def log_archive_events(cls, archived_events, success, message, execution_time=None):
        """Log event archiving operation"""
        log = cls(
            operation_type='archive_events',
            operation_name='Archiwizacja zakończonych wydarzeń',
            status='success' if success else 'error',
            message=message,
            details={
                'archived_events': archived_events,
                'success': success
            },
            execution_time=execution_time
        )
        db.session.add(log)
        return log
    
    @classmethod
    def log_cron_execution(cls, operation_type, success, message, details=None, execution_time=None):
        """Log general cron execution"""
        log = cls(
            operation_type=f'cron_{operation_type}',
            operation_name=f'Cron: {operation_type}',
            status='success' if success else 'error',
            message=message,
            details=details,
            execution_time=execution_time
        )
        db.session.add(log)
        return log

