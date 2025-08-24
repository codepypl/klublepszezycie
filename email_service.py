#!/usr/bin/env python3
"""
Email service for Lepsze Życie Club
Handles email templates, sending, and subscription management
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import uuid
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from flask import current_app, render_template_string, url_for
from models import db, EmailTemplate, EmailSubscription, EmailLog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailService:
    """Service for handling email operations"""
    
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize email service with Flask app"""
        self.app = app
        self.config = app.config
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: str = None, template_id: int = None) -> bool:
        """
        Send email using configured SMTP settings
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML version of email
            text_content: Plain text version (optional)
            template_id: ID of email template used
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config['MAIL_DEFAULT_SENDER_NAME']} <{self.config['MAIL_DEFAULT_SENDER']}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Connect to SMTP server
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.config['MAIL_SERVER'], self.config['MAIL_PORT']) as server:
                if self.config['MAIL_USE_TLS']:
                    server.starttls(context=context)
                elif self.config['MAIL_USE_SSL']:
                    server = smtplib.SMTP_SSL(self.config['MAIL_SERVER'], self.config['MAIL_PORT'], context=context)
                
                # Login
                server.login(self.config['MAIL_USERNAME'], self.config['MAIL_PASSWORD'])
                
                # Send email
                server.send_message(msg)
                
                logger.info(f"Email sent successfully to {to_email}")
                
                # Log email
                self._log_email(to_email, template_id, subject, 'sent')
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            self._log_email(to_email, template_id, subject, 'failed', str(e))
            return False
    
    def _is_user_approved(self, email: str) -> bool:
        """
        Check if user has approved registration status
        
        Args:
            email: User email address
            
        Returns:
            bool: True if user is approved, False otherwise
        """
        try:
            from models import Registration
            registration = Registration.query.filter_by(email=email).first()
            if registration and registration.status == 'approved':
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking user approval status for {email}: {str(e)}")
            return False
    
    def get_approved_subscribers(self) -> List[EmailSubscription]:
        """
        Get only approved subscribers
        
        Returns:
            List[EmailSubscription]: List of approved subscribers
        """
        try:
            from models import Registration
            # Get all active subscriptions
            all_subscriptions = EmailSubscription.query.filter_by(is_active=True).all()
            approved_subscriptions = []
            
            for subscription in all_subscriptions:
                if self._is_user_approved(subscription.email):
                    approved_subscriptions.append(subscription)
            
            return approved_subscriptions
            
        except Exception as e:
            logger.error(f"Error getting approved subscribers: {str(e)}")
            return []
    
    def send_template_email(self, to_email: str, template_name: str, 
                           variables: Dict = None) -> bool:
        """
        Send email using a template
        
        Args:
            to_email: Recipient email address
            template_name: Name of email template
            variables: Dictionary of variables to replace in template
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Check if user is approved (except for admin notifications)
            if template_name != 'admin_notification' and not self._is_user_approved(to_email):
                logger.info(f"Email not sent to {to_email} - user not approved")
                return False
            
            # Get template by name first, then by type if not found
            template = EmailTemplate.query.filter_by(name=template_name, is_active=True).first()
            if not template:
                # Try to find by template type
                template = EmailTemplate.query.filter_by(template_type=template_name, is_active=True).first()
            
            if not template:
                logger.error(f"Template '{template_name}' not found or inactive")
                return False
            
            # Replace variables in content
            html_content = self._replace_variables(template.html_content, variables or {})
            text_content = self._replace_variables(template.text_content, variables or {}) if template.text_content else None
            subject = self._replace_variables(template.subject, variables or {})
            
            # Send email
            return self.send_email(to_email, subject, html_content, text_content, template.id)
            
        except Exception as e:
            logger.error(f"Failed to send template email '{template_name}' to {to_email}: {str(e)}")
            return False
    
    def send_welcome_email(self, email: str, name: str) -> bool:
        """Send welcome email to new subscriber"""
        variables = {
            'name': name,
            'email': email,
            'unsubscribe_url': self._generate_unsubscribe_url(email),
            'delete_account_url': self._generate_delete_account_url(email)
        }
        return self.send_template_email(email, 'Email Powitalny', variables)
    
    def send_reminder_email(self, email: str, name: str, event_type: str, 
                           event_date: datetime, event_details: str = None) -> bool:
        """Send reminder email about upcoming events"""
        variables = {
            'name': name,
            'email': email,
            'event_type': event_type,
            'event_date': event_date.strftime('%d.%m.%Y %H:%M'),
            'event_details': event_details or '',
            'unsubscribe_url': self._generate_unsubscribe_url(email),
            'delete_account_url': self._generate_delete_account_url(email)
        }
        return self.send_template_email(email, 'Przypomnienie o Wydarzeniu', variables)
    
    def send_newsletter_email(self, email: str, name: str, newsletter_content: str) -> bool:
        """Send newsletter email"""
        variables = {
            'name': name,
            'email': email,
            'newsletter_content': newsletter_content,
            'unsubscribe_url': self._generate_unsubscribe_url(email),
            'delete_account_url': self._generate_delete_account_url(email)
        }
        return self.send_template_email(email, 'Newsletter Klubu', variables)
    
    def _replace_variables(self, content: str, variables: Dict) -> str:
        """Replace variables in template content"""
        if not content:
            return content
        
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            content = content.replace(placeholder, str(value))
        
        return content
    
    def _generate_unsubscribe_url(self, email: str) -> str:
        """Generate unsubscribe URL for email"""
        subscription = EmailSubscription.query.filter_by(email=email).first()
        if not subscription:
            # Create new subscription if doesn't exist
            subscription = EmailSubscription(
                email=email,
                unsubscribe_token=str(uuid.uuid4())
            )
            db.session.add(subscription)
            db.session.commit()
        
        # Use url_for in app context
        with self.app.app_context():
            return url_for('unsubscribe_email', token=subscription.unsubscribe_token, _external=True)
    
    def _generate_delete_account_url(self, email: str) -> str:
        """Generate delete account URL for email"""
        subscription = EmailSubscription.query.filter_by(email=email).first()
        if not subscription:
            return ""
        
        # Use url_for in app context
        with self.app.app_context():
            return url_for('delete_account', token=subscription.unsubscribe_token, _external=True)
    
    def _log_email(self, email: str, template_id: int, subject: str, 
                   status: str, error_message: str = None):
        """Log email operation"""
        try:
            log_entry = EmailLog(
                email=email,
                template_id=template_id,
                subject=subject,
                status=status,
                error_message=error_message
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to log email: {str(e)}")
    
    def add_subscriber(self, email: str, name: str = None, 
                      subscription_type: str = 'all') -> bool:
        """
        Add new email subscriber
        
        Args:
            email: Email address
            name: Subscriber name (optional)
            subscription_type: Type of subscription (all, reminders, newsletter)
            
        Returns:
            bool: True if added successfully, False otherwise
        """
        try:
            # Check if already exists
            existing = EmailSubscription.query.filter_by(email=email).first()
            if existing:
                existing.name = name or existing.name
                existing.subscription_type = subscription_type
                existing.is_active = True
            else:
                # Create new subscription
                subscription = EmailSubscription(
                    email=email,
                    name=name,
                    subscription_type=subscription_type,
                    unsubscribe_token=str(uuid.uuid4())
                )
                db.session.add(subscription)
            
            db.session.commit()
            logger.info(f"Subscriber added/updated: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add subscriber {email}: {str(e)}")
            db.session.rollback()
            return False
    
    def unsubscribe_email(self, token: str) -> bool:
        """
        Unsubscribe email using token
        
        Args:
            token: Unsubscribe token
            
        Returns:
            bool: True if unsubscribed successfully, False otherwise
        """
        try:
            subscription = EmailSubscription.query.filter_by(unsubscribe_token=token).first()
            if subscription:
                subscription.is_active = False
                db.session.commit()
                logger.info(f"Email unsubscribed: {subscription.email}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe email with token {token}: {str(e)}")
            return False
    
    def delete_account(self, token: str) -> bool:
        """
        Delete account using token
        
        Args:
            token: Unsubscribe token
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            subscription = EmailSubscription.query.filter_by(unsubscribe_token=token).first()
            if subscription:
                # Also remove from registrations if exists
                from models import Registration
                registration = Registration.query.filter_by(email=subscription.email).first()
                if registration:
                    db.session.delete(registration)
                
                db.session.delete(subscription)
                db.session.commit()
                logger.info(f"Account deleted: {subscription.email}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete account with token {token}: {str(e)}")
            return False
    
    def send_bulk_emails(self, template_name: str, variables: Dict = None, 
                        subscription_type: str = 'all') -> Dict:
        """
        Send bulk emails to subscribers
        
        Args:
            template_name: Name of email template
            variables: Variables to replace in template
            subscription_type: Type of subscribers to target
            
        Returns:
            Dict: Results of bulk sending
        """
        try:
            # Get subscribers
            query = EmailSubscription.query.filter_by(is_active=True)
            if subscription_type != 'all':
                query = query.filter_by(subscription_type=subscription_type)
            
            subscribers = query.all()
            
            if not subscribers:
                return {'success': False, 'message': 'No active subscribers found'}
            
            # Send emails in batches
            batch_size = self.config.get('EMAIL_BATCH_SIZE', 50)
            delay = self.config.get('EMAIL_DELAY', 1)
            
            results = {
                'total': len(subscribers),
                'sent': 0,
                'failed': 0,
                'errors': []
            }
            
            for i, subscriber in enumerate(subscribers):
                # Add subscriber-specific variables
                subscriber_vars = variables or {}
                subscriber_vars.update({
                    'name': subscriber.name or 'Użytkowniku',
                    'email': subscriber.email
                })
                
                # Send email
                success = self.send_template_email(
                    subscriber.email, template_name, subscriber_vars
                )
                
                if success:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to send to {subscriber.email}")
                
                # Add delay between emails (except for last one)
                if i < len(subscribers) - 1 and delay > 0:
                    import time
                    time.sleep(delay)
                
                # Log progress
                if (i + 1) % batch_size == 0:
                    logger.info(f"Bulk email progress: {i + 1}/{len(subscribers)}")
            
            logger.info(f"Bulk email completed: {results['sent']} sent, {results['failed']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Bulk email failed: {str(e)}")
            return {'success': False, 'message': str(e)}

# Global email service instance
email_service = EmailService()
