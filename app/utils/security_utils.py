"""
Security utilities for monitoring and alerting
"""
import logging
import os
from datetime import datetime
from flask import request
from app.services.email_service import EmailService

class SecurityMonitor:
    """Monitor security events and send alerts"""
    
    def __init__(self):
        self.email_service = EmailService()
    
    def log_security_event(self, event_type, details, severity='WARNING'):
        """Log security event and send alert if necessary"""
        try:
            # Get request context if available
            client_ip = 'unknown'
            user_agent = 'unknown'
            try:
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                              request.environ.get('REMOTE_ADDR', 'unknown'))
                user_agent = request.headers.get('User-Agent', 'unknown')
            except RuntimeError:
                pass  # No request context
            
            # Create log message
            log_message = f"SECURITY_{event_type}: {details} | IP: {client_ip} | UA: {user_agent[:100]}"
            
            # Log based on severity
            if severity == 'CRITICAL':
                logging.critical(log_message)
            elif severity == 'ERROR':
                logging.error(log_message)
            else:
                logging.warning(log_message)
            
            # Send alert to admin for critical events
            if severity in ['CRITICAL', 'ERROR']:
                self._send_admin_alert(event_type, details, client_ip, user_agent)
                
        except Exception as e:
            logging.error(f"Failed to log security event: {str(e)}")
    
    def _send_admin_alert(self, event_type, details, client_ip, user_agent):
        """Send email alert to administrator using database template"""
        try:
            admin_email = os.getenv('ADMIN_EMAIL', 'admin@klublepszezycie.pl')
            
            context = {
                'event_type': event_type,
                'details': details,
                'client_ip': client_ip,
                'user_agent': user_agent[:200],  # Limit length
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'server_name': os.getenv('SERVER_NAME', 'klublepszezycie.pl')
            }
            
            # Send alert email using template from database
            success, message = self.email_service.send_template_email(
                to_email=admin_email,
                template_name='security_alert',
                context=context,
                to_name='Administrator',
                use_queue=False  # Send immediately for security alerts
            )
            
            if success:
                logging.info(f"Security alert sent to {admin_email} for {event_type}")
            else:
                logging.error(f"Failed to send security alert: {message}")
            
        except Exception as e:
            logging.error(f"Failed to send security alert: {str(e)}")
    
    def check_suspicious_activity(self, email, action, token, result):
        """Check if activity is suspicious and log accordingly"""
        try:
            # Define suspicious patterns
            suspicious_patterns = [
                'INVALID_TOKEN',   # Invalid token attempts
                'ADMIN_PROTECTED'  # Attempts to delete admin accounts
            ]
            
            # Check if result indicates suspicious activity
            error_code = result.get('error_code', '')
            if error_code in suspicious_patterns:
                severity = 'ERROR'
                
                details = f"Email: {email}, Action: {action}, Error: {error_code}, Result: {result.get('error', 'Unknown')}"
                self.log_security_event(
                    event_type='SUSPICIOUS_ACTIVITY',
                    details=details,
                    severity=severity
                )
                
        except Exception as e:
            logging.error(f"Failed to check suspicious activity: {str(e)}")

# Global instance
security_monitor = SecurityMonitor()
