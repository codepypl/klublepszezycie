"""
Mailgun API Service for sending emails with detailed logging
"""
import os
import requests
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from app import db
from app.models.email_model import EmailQueue, EmailLog

class MailgunAPIService:
    """Service for sending emails via Mailgun API with detailed logging"""
    
    def __init__(self):
        """Initialize Mailgun API service"""
        self.api_key = os.getenv('MAILGUN_API_KEY', '')
        self.domain = os.getenv('MAILGUN_DOMAIN', 'klublepszezycie.pl')
        self.base_url = f"https://api.eu.mailgun.net/v3/{self.domain}"
        self.from_email = os.getenv('MAIL_DEFAULT_SENDER', f'noreply@{self.domain}')
        self.from_name = os.getenv('MAIL_DEFAULT_SENDER_NAME', 'Klub Lepsze Życie')
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Check if API key is available
        if not self.api_key:
            self.logger.warning("MAILGUN_API_KEY not set, falling back to SMTP")
            self.use_api = False
        else:
            self.use_api = True
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: str = None, template_id: int = None, 
                   context: Dict = None, event_id: int = None) -> Tuple[bool, str]:
        """
        Send single email via Mailgun API
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content
            template_id: Template ID for logging
            context: Additional context for logging
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            self.logger.info(f"📧 Sending email to {to_email} via Mailgun API")
            
            if not self.use_api:
                return self._fallback_to_smtp(to_email, subject, html_content, text_content, template_id)
            
            # Enrich template with unsubscribe/delete links
            try:
                from app.services.email_template_enricher import EmailTemplateEnricher
                enricher = EmailTemplateEnricher()
                enriched = enricher.enrich_template_content(
                    html_content=html_content or "",
                    text_content=text_content or "",
                    user_email=to_email
                )
                html_content = enriched.get('html_content') or html_content or ""
                text_content = enriched.get('text_content') or text_content or ""
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to enrich template: {e}")
                # Continue with original content
            
            # Prepare email data with proper encoding
            from_header = f"{self.from_name} <{self.from_email}>"
            email_data = {
                "from": from_header,
                "to": [to_email],
                "subject": subject,
                "html": html_content
            }
            
            if text_content:
                email_data["text"] = text_content
            
            # Add tracking parameters
            email_data["o:tracking"] = "yes"
            email_data["o:tracking-clicks"] = "yes"
            email_data["o:tracking-opens"] = "yes"
            
            # Send via Mailgun API
            response = requests.post(
                f"{self.base_url}/messages",
                auth=("api", self.api_key),
                data=email_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                message_id = result.get('id', 'unknown')
                
                self.logger.info(f"✅ Email sent successfully via Mailgun API")
                self.logger.info(f"   Message ID: {message_id}")
                self.logger.info(f"   Response: {result.get('message', 'No message')}")
                
                # Log successful email
                self._log_email(to_email, subject, 'sent', template_id, message_id, context, None, event_id)
                
                return True, f"Email sent via Mailgun API (ID: {message_id})"
            else:
                error_msg = f"Mailgun API error: {response.status_code} - {response.text}"
                self.logger.error(f"❌ {error_msg}")
                
                # Log failed email
                self._log_email(to_email, subject, 'failed', template_id, None, context, error_msg, event_id)
                
                # Try SMTP fallback
                return self._fallback_to_smtp(to_email, subject, html_content, text_content, template_id)
                
        except Exception as e:
            error_msg = f"Mailgun API exception: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            
            # Log failed email
            self._log_email(to_email, subject, 'failed', template_id, None, context, error_msg, event_id)
            
            # Try SMTP fallback
            return self._fallback_to_smtp(to_email, subject, html_content, text_content, template_id)
    
    def send_batch(self, emails: List[EmailQueue]) -> Tuple[bool, str]:
        """
        Send batch of emails via Mailgun API
        
        Args:
            emails: List of EmailQueue objects
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not emails:
            return True, "No emails to send"
        
        self.logger.info(f"📧 Sending batch of {len(emails)} emails via Mailgun API")
        
        if not self.use_api:
            return self._fallback_batch_to_smtp(emails)
        
        sent_count = 0
        failed_count = 0
        errors = []
        
        for email in emails:
            try:
                # Enrich template with unsubscribe/delete links
                html_content = email.html_content
                text_content = email.text_content
                
                try:
                    from app.services.email_template_enricher import EmailTemplateEnricher
                    enricher = EmailTemplateEnricher()
                    enriched = enricher.enrich_template_content(
                        html_content=html_content or "",
                        text_content=text_content or "",
                        user_email=email.recipient_email
                    )
                    html_content = enriched.get('html_content') or html_content or ""
                    text_content = enriched.get('text_content') or text_content or ""
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to enrich template for {email.recipient_email}: {e}")
                    # Continue with original content
                
                # Prepare email data with proper encoding
                from_header = f"{self.from_name} <{self.from_email}>"
                email_data = {
                    "from": from_header,
                    "to": [email.recipient_email],
                    "subject": email.subject,
                    "html": html_content
                }
                
                if text_content:
                    email_data["text"] = text_content
                
                # Add tracking parameters
                email_data["o:tracking"] = "yes"
                email_data["o:tracking-clicks"] = "yes"
                email_data["o:tracking-opens"] = "yes"
                
                # Send via Mailgun API
                response = requests.post(
                    f"{self.base_url}/messages",
                    auth=("api", self.api_key),
                    data=email_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    message_id = result.get('id', 'unknown')
                    
                    # Update email status
                    email.status = 'sent'
                    email.sent_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
                    email.message_id = message_id
                    
                    # Log successful email
                    self._log_email(
                        email.recipient_email, 
                        email.subject, 
                        'sent', 
                        email.template_id, 
                        message_id,
                        None,
                        None,
                        email.event_id
                    )
                    
                    sent_count += 1
                    self.logger.info(f"✅ Email sent to {email.recipient_email} (ID: {message_id})")
                else:
                    error_msg = f"API error {response.status_code}: {response.text}"
                    email.status = 'failed'
                    email.error_message = error_msg
                    
                    # Log failed email
                    self._log_email(
                        email.recipient_email, 
                        email.subject, 
                        'failed', 
                        email.template_id, 
                        None, 
                        None, 
                        error_msg,
                        email.event_id
                    )
                    
                    failed_count += 1
                    errors.append(f"{email.recipient_email}: {error_msg}")
                    self.logger.error(f"❌ Failed to send to {email.recipient_email}: {error_msg}")
                
            except Exception as e:
                error_msg = f"Exception: {str(e)}"
                email.status = 'failed'
                email.error_message = error_msg
                
                # Log failed email
                self._log_email(
                    email.recipient_email, 
                    email.subject, 
                    'failed', 
                    email.template_id, 
                    None, 
                    None, 
                    error_msg,
                    email.event_id
                )
                
                failed_count += 1
                errors.append(f"{email.recipient_email}: {error_msg}")
                self.logger.error(f"❌ Exception sending to {email.recipient_email}: {error_msg}")
        
        # Commit all changes
        try:
            db.session.commit()
            self.logger.info(f"✅ Batch processing completed: {sent_count} sent, {failed_count} failed")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"❌ Database commit failed: {e}")
            return False, f"Database error: {str(e)}"
        
        if sent_count > 0:
            message = f"Sent {sent_count} emails via Mailgun API"
            if failed_count > 0:
                message += f", {failed_count} failed"
            return True, message
        else:
            return False, f"Failed to send any emails: {'; '.join(errors)}"
    
    def get_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """
        Get delivery status for a message
        
        Args:
            message_id: Mailgun message ID
            
        Returns:
            Dict with delivery status information
        """
        if not self.use_api:
            return {"error": "API not available"}
        
        try:
            response = requests.get(
                f"{self.base_url}/events",
                auth=("api", self.api_key),
                params={"message-id": message_id},
                timeout=10
            )
            
            if response.status_code == 200:
                events = response.json()
                return {
                    "success": True,
                    "events": events.get('items', []),
                    "total": len(events.get('items', []))
                }
            else:
                return {
                    "success": False,
                    "error": f"API error {response.status_code}: {response.text}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception: {str(e)}"
            }
    
    def _fallback_to_smtp(self, to_email: str, subject: str, html_content: str, 
                         text_content: str, template_id: int) -> Tuple[bool, str]:
        """Fallback to SMTP when API is not available"""
        try:
            from app.services.email_service import EmailService
            email_service = EmailService()
            return email_service.send_email(to_email, subject, html_content, text_content, template_id, use_queue=True)
        except Exception as e:
            self.logger.error(f"❌ SMTP fallback failed: {e}")
            return False, f"Both Mailgun API and SMTP failed: {str(e)}"
    
    def _fallback_batch_to_smtp(self, emails: List[EmailQueue]) -> Tuple[bool, str]:
        """Fallback to SMTP for batch sending"""
        try:
            from app.services.email_fallback_sender import EmailFallbackSender
            import asyncio
            
            fallback_sender = EmailFallbackSender()
            return asyncio.run(fallback_sender.send_batch(emails))
        except Exception as e:
            self.logger.error(f"❌ SMTP batch fallback failed: {e}")
            return False, f"Both Mailgun API and SMTP batch failed: {str(e)}"
    
    def _log_email(self, email: str, subject: str, status: str, template_id: int = None, 
                   message_id: str = None, context: Dict = None, error_message: str = None, event_id: int = None):
        """Log email sending attempt using LogService"""
        try:
            from app.services.log_service import LogService
            
            success, message = LogService.log_email(
                to_email=email,
                subject=subject,
                status=status,
                template_id=template_id,
                event_id=event_id,
                context=context,
                error_message=error_message
            )
            
            if not success:
                self.logger.error(f"❌ Failed to log email: {message}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to log email: {e}")
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test Mailgun API connection"""
        if not self.use_api:
            return False, "Mailgun API not configured (no API key)"
        
        try:
            response = requests.get(
                f"https://api.eu.mailgun.net/v3/domains/{self.domain}",
                auth=("api", self.api_key),
                timeout=10
            )
            
            if response.status_code == 200:
                domain_data = response.json()
                return True, f"API connection successful. Domain status: {domain_data.get('domain', {}).get('state', 'unknown')}"
            else:
                return False, f"API connection failed: {response.status_code} - {response.text}"
                
        except Exception as e:
            return False, f"API connection error: {str(e)}"
