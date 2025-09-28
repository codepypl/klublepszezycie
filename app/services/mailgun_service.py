"""
Enhanced notification system with Mailgun API integration and detailed logging
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from app import db
from app.models.email_model import EmailQueue, EmailLog, EmailTemplate
from app.models.user_model import User
from app.services.mailgun_api_service import MailgunAPIService

class EnhancedNotificationProcessor:
    """Enhanced notification processor with Mailgun API and detailed logging"""
    
    def __init__(self):
        """Initialize enhanced notification processor"""
        self.mailgun_service = MailgunAPIService()
        self.logger = logging.getLogger(__name__)
        
        # Test API connection on initialization
        api_available, api_message = self.mailgun_service.test_connection()
        if api_available:
            self.logger.info(f"✅ Mailgun API available: {api_message}")
        else:
            self.logger.warning(f"⚠️ Mailgun API not available: {api_message}")
    
    async def process_email_queue(self) -> Tuple[bool, str]:
        """Process email queue with enhanced logging"""
        try:
            self.logger.info("🔄 Starting enhanced email queue processing")
            
            # Get pending emails
            now = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
            pending_emails = EmailQueue.query.filter(
                EmailQueue.status == 'pending',
                EmailQueue.scheduled_at <= now
            ).order_by(EmailQueue.priority.asc(), EmailQueue.scheduled_at.asc()).all()
            
            if not pending_emails:
                self.logger.info("ℹ️ No pending emails to process")
                return True, "No emails to process"
            
            self.logger.info(f"📧 Processing {len(pending_emails)} pending emails")
            
            # Process emails in batches
            batch_size = 10  # Smaller batches for better control
            total_sent = 0
            total_failed = 0
            
            for i in range(0, len(pending_emails), batch_size):
                batch = pending_emails[i:i + batch_size]
                self.logger.info(f"📦 Processing batch {i//batch_size + 1}: {len(batch)} emails")
                
                # Send batch via Mailgun API
                success, message = self.mailgun_service.send_batch(batch)
                
                if success:
                    sent_count = len([e for e in batch if e.status == 'sent'])
                    failed_count = len([e for e in batch if e.status == 'failed'])
                    total_sent += sent_count
                    total_failed += failed_count
                    
                    self.logger.info(f"✅ Batch {i//batch_size + 1} completed: {sent_count} sent, {failed_count} failed")
                else:
                    self.logger.error(f"❌ Batch {i//batch_size + 1} failed: {message}")
                    total_failed += len(batch)
                
                # Small delay between batches
                await asyncio.sleep(1)
            
            result_message = f"Processed {len(pending_emails)} emails: {total_sent} sent, {total_failed} failed"
            self.logger.info(f"✅ Email queue processing completed: {result_message}")
            
            return total_sent > 0, result_message
            
        except Exception as e:
            self.logger.error(f"❌ Error processing email queue: {e}")
            return False, f"Error: {str(e)}"
    
    def send_immediate_email(self, to_email: str, subject: str, html_content: str, 
                           text_content: str = None, template_id: int = None, 
                           context: Dict = None) -> Tuple[bool, str]:
        """Send immediate email with enhanced logging"""
        try:
            self.logger.info(f"📧 Sending immediate email to {to_email}")
            
            success, message = self.mailgun_service.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                template_id=template_id,
                context=context
            )
            
            if success:
                self.logger.info(f"✅ Immediate email sent successfully: {message}")
            else:
                self.logger.error(f"❌ Immediate email failed: {message}")
            
            return success, message
            
        except Exception as e:
            self.logger.error(f"❌ Error sending immediate email: {e}")
            return False, f"Error: {str(e)}"
    
    def send_template_email(self, to_email: str, template_name: str, 
                          context: Dict = None, to_name: str = None, use_queue: bool = True, event_id: int = None) -> Tuple[bool, str]:
        """Send template email with enhanced logging - through queue by default"""
        try:
            self.logger.info(f"📧 Sending template email '{template_name}' to {to_email} (queue: {use_queue})")
            
            # Get template
            template = EmailTemplate.query.filter_by(name=template_name, is_active=True).first()
            if not template:
                error_msg = f"Template '{template_name}' not found or inactive"
                self.logger.error(f"❌ {error_msg}")
                return False, error_msg
            
            # Prepare context
            if context is None:
                context = {}
            
            if to_name:
                context['recipient_name'] = to_name
            
            # Add unsubscribe URLs to context BEFORE Jinja2 rendering
            from app.services.email_template_enricher import email_template_enricher
            if email_template_enricher.should_add_links(template_name):
                # Check if user is club member
                from app.models.user_model import User
                user = User.query.filter_by(email=to_email).first()
                is_club_member = user.club_member if user else False
                
                # Generate URLs and add to context
                from app.services.unsubscribe_manager import unsubscribe_manager
                if is_club_member:
                    context['unsubscribe_url'] = unsubscribe_manager.get_unsubscribe_url(to_email)
                else:
                    context['unsubscribe_url'] = ''  # Empty for non-members
                context['delete_account_url'] = unsubscribe_manager.get_delete_account_url(to_email)
            
            # Render template content
            try:
                from jinja2 import Template
                
                # Render HTML content
                html_template = Template(template.html_content)
                html_content = html_template.render(**context)
                
                # Render text content
                text_content = None
                if template.text_content:
                    text_template = Template(template.text_content)
                    text_content = text_template.render(**context)
                
                # Enrich template with unsubscribe/delete links if needed (fallback)
                if email_template_enricher.should_add_links(template_name):
                    enriched = email_template_enricher.enrich_template_content(
                        html_content, text_content or '', to_email
                    )
                    html_content = enriched['html_content']
                    text_content = enriched['text_content']
                
            except Exception as e:
                error_msg = f"Template rendering error: {str(e)}"
                self.logger.error(f"❌ {error_msg}")
                return False, error_msg
            
            # Send through queue or directly
            if use_queue:
                # Add to email queue for Celery processing
                from app.services.email_service import EmailService
                email_service = EmailService()
                
                # Generate duplicate check key for event reminders
                duplicate_check_key = None
                if template_name.startswith('event_reminder_'):
                    # Extract event info from context for duplicate checking
                    event_id = context.get('event_id')
                    reminder_type = template_name.replace('event_reminder_', '')
                    
                    # Get user ID from email
                    from app.models.user_model import User
                    user = User.query.filter_by(email=to_email).first()
                    user_id = user.id if user else None
                    
                    if event_id and user_id and template.id:
                        duplicate_check_key = f"event_reminder_{event_id}_{user_id}_{template.id}_{reminder_type}"
                
                email_id = email_service.add_to_queue(
                    to_email=to_email,
                    subject=template.subject,
                    html_content=html_content,
                    text_content=text_content,
                    template_id=template.id,
                    event_id=event_id,
                    to_name=to_name,
                    context=context,
                    duplicate_check_key=duplicate_check_key
                )
                
                if email_id[0]:
                    self.logger.info(f"✅ Template email added to queue (ID: {email_id[1]})")
                    return True, f"Email added to queue (ID: {email_id[1]})"
                else:
                    self.logger.error(f"❌ Failed to add template email to queue: {email_id[1]}")
                    return False, f"Failed to add to queue: {email_id[1]}"
            else:
                # Send directly (old behavior)
                success, message = self.mailgun_service.send_email(
                    to_email=to_email,
                    subject=template.subject,
                    html_content=html_content,
                    text_content=text_content,
                    template_id=template.id,
                    context=context,
                    event_id=event_id
                )
                
                if success:
                    self.logger.info(f"✅ Template email sent directly: {message}")
                else:
                    self.logger.error(f"❌ Template email failed: {message}")
                
                return success, message
            
        except Exception as e:
            self.logger.error(f"❌ Error sending template email: {e}")
            return False, f"Error: {str(e)}"
    
    def get_delivery_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get delivery statistics for the last N hours"""
        try:
            since = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now() - timedelta(hours=hours)
            
            # Get email logs
            logs = EmailLog.query.filter(EmailLog.sent_at >= since).all()
            
            stats = {
                'total_emails': len(logs),
                'sent': len([l for l in logs if l.status == 'sent']),
                'failed': len([l for l in logs if l.status == 'failed']),
                'bounced': len([l for l in logs if l.status == 'bounced']),
                'opened': len([l for l in logs if l.status == 'opened']),
                'clicked': len([l for l in logs if l.status == 'clicked']),
                'success_rate': 0,
                'recent_emails': []
            }
            
            if stats['total_emails'] > 0:
                stats['success_rate'] = (stats['sent'] / stats['total_emails']) * 100
            
            # Get recent emails
            recent_logs = EmailLog.query.filter(
                EmailLog.sent_at >= since
            ).order_by(EmailLog.sent_at.desc()).limit(10).all()
            
            stats['recent_emails'] = [
                {
                    'email': log.email,
                    'subject': log.subject,
                    'status': log.status,
                    'sent_at': log.sent_at.isoformat(),
                    'error': log.error_message
                }
                for log in recent_logs
            ]
            
            self.logger.info(f"📊 Delivery statistics: {stats['sent']}/{stats['total_emails']} sent ({stats['success_rate']:.1f}%)")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Error getting delivery statistics: {e}")
            return {'error': str(e)}
    
    def check_gmail_delivery_issues(self) -> Dict[str, Any]:
        """Check for Gmail-specific delivery issues"""
        try:
            # Get recent emails to Gmail
            gmail_logs = EmailLog.query.filter(
                EmailLog.email.like('%@gmail.com'),
                EmailLog.sent_at >= __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now() - timedelta(hours=24)
            ).all()
            
            gmail_stats = {
                'total_gmail_emails': len(gmail_logs),
                'sent': len([l for l in gmail_logs if l.status == 'sent']),
                'failed': len([l for l in gmail_logs if l.status == 'failed']),
                'bounced': len([l for l in gmail_logs if l.status == 'bounced']),
                'success_rate': 0,
                'recent_gmail_emails': []
            }
            
            if gmail_stats['total_gmail_emails'] > 0:
                gmail_stats['success_rate'] = (gmail_stats['sent'] / gmail_stats['total_gmail_emails']) * 100
            
            # Get recent Gmail emails
            recent_gmail = EmailLog.query.filter(
                EmailLog.email.like('%@gmail.com'),
                EmailLog.sent_at >= __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now() - timedelta(hours=24)
            ).order_by(EmailLog.sent_at.desc()).limit(5).all()
            
            gmail_stats['recent_gmail_emails'] = [
                {
                    'email': log.email,
                    'subject': log.subject,
                    'status': log.status,
                    'sent_at': log.sent_at.isoformat(),
                    'error': log.error_message
                }
                for log in recent_gmail
            ]
            
            self.logger.info(f"📧 Gmail delivery stats: {gmail_stats['sent']}/{gmail_stats['total_gmail_emails']} sent ({gmail_stats['success_rate']:.1f}%)")
            
            return gmail_stats
            
        except Exception as e:
            self.logger.error(f"❌ Error checking Gmail delivery: {e}")
            return {'error': str(e)}
    
    def retry_failed_emails(self, limit: int = 10) -> Dict[str, int]:
        """
        Ponawia wysyłanie nieudanych emaili
        
        Args:
            limit: Maksymalna liczba emaili do ponowienia
            
        Returns:
            Dict[str, int]: Statystyki ponowienia
        """
        stats = {'retried': 0, 'success': 0, 'failed': 0}
        
        try:
            self.logger.info(f"🔄 Retrying up to {limit} failed emails")
            
            failed_items = EmailQueue.query.filter_by(status='failed').limit(limit).all()
            
            for item in failed_items:
                try:
                    # Oznacz jako przetwarzany
                    item.status = 'processing'
                    item.error_message = None
                    db.session.commit()
                    
                    # Wyślij email przez Mailgun API
                    success, message = self.mailgun_service.send_email(
                        to_email=item.recipient_email,
                        subject=item.subject,
                        html_content=item.html_content,
                        text_content=item.text_content
                    )
                    
                    if success:
                        item.status = 'sent'
                        item.sent_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
                        stats['success'] += 1
                        self.logger.info(f"✅ Retry successful: {item.recipient_email}")
                    else:
                        item.status = 'failed'
                        item.error_message = message
                        stats['failed'] += 1
                        self.logger.error(f"❌ Retry failed: {item.recipient_email} - {message}")
                    
                    stats['retried'] += 1
                    db.session.commit()
                    
                except Exception as e:
                    item.status = 'failed'
                    item.error_message = str(e)
                    stats['failed'] += 1
                    stats['retried'] += 1
                    self.logger.error(f"❌ Retry error for {item.recipient_email}: {e}")
                    db.session.commit()
            
            self.logger.info(f"📊 Retry stats: {stats['success']}/{stats['retried']} successful")
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Error retrying failed emails: {e}")
            db.session.rollback()
            return stats
    
    def send_campaign_to_group(self, campaign_id: int, group_id: int) -> Tuple[bool, str, int]:
        """
        Wysyła kampanię do grupy użytkowników
        
        Args:
            campaign_id: ID kampanii
            group_id: ID grupy
            
        Returns:
            Tuple[bool, str, int]: (sukces, komunikat, liczba wysłanych)
        """
        try:
            from app.models import EmailCampaign, UserGroup, UserGroupMember
            
            # Pobierz kampanię
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return False, "Kampania nie istnieje", 0
            
            # Pobierz grupę
            group = UserGroup.query.get(group_id)
            if not group:
                return False, "Grupa nie istnieje", 0
            
            # Pobierz członków grupy
            members = UserGroupMember.query.filter_by(group_id=group_id).all()
            if not members:
                return False, "Grupa nie ma członków", 0
            
            self.logger.info(f"📧 Sending campaign '{campaign.name}' to group '{group.name}' ({len(members)} members)")
            
            sent_count = 0
            failed_count = 0
            
            for member in members:
                try:
                    # Wyślij email przez Mailgun API
                    success, message = self.mailgun_service.send_email(
                        to_email=member.user.email,
                        subject=campaign.subject,
                        html_content=campaign.html_content,
                        text_content=campaign.text_content
                    )
                    
                    if success:
                        sent_count += 1
                        self.logger.info(f"✅ Campaign email sent to {member.user.email}")
                    else:
                        failed_count += 1
                        self.logger.error(f"❌ Campaign email failed to {member.user.email}: {message}")
                        
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"❌ Campaign email error for {member.user.email}: {e}")
            
            if sent_count > 0:
                return True, f"Wysłano {sent_count} emaili, {failed_count} błędów", sent_count
            else:
                return False, f"Nie udało się wysłać żadnego emaila ({failed_count} błędów)", 0
                
        except Exception as e:
            self.logger.error(f"❌ Error sending campaign to group: {e}")
            return False, f"Błąd: {str(e)}", 0
    
    def update_campaign_stats(self, campaign_id: int) -> bool:
        """
        Aktualizuje statystyki kampanii
        
        Args:
            campaign_id: ID kampanii
            
        Returns:
            bool: Sukces operacji
        """
        try:
            from app.models import EmailCampaign, EmailQueue
            
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return False
            
            # Policz emaile w kolejce dla tej kampanii
            total_emails = EmailQueue.query.filter_by(campaign_id=campaign_id).count()
            sent_emails = EmailQueue.query.filter_by(campaign_id=campaign_id, status='sent').count()
            failed_emails = EmailQueue.query.filter_by(campaign_id=campaign_id, status='failed').count()
            
            # Aktualizuj statystyki
            campaign.total_emails = total_emails
            campaign.sent_emails = sent_emails
            campaign.failed_emails = failed_emails
            campaign.success_rate = (sent_emails / total_emails * 100) if total_emails > 0 else 0
            
            db.session.commit()
            
            self.logger.info(f"📊 Updated campaign stats: {sent_emails}/{total_emails} sent ({campaign.success_rate:.1f}%)")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error updating campaign stats: {e}")
            db.session.rollback()
            return False
    
    def get_queue_stats(self) -> Dict[str, int]:
        """
        Zwraca statystyki kolejki emaili
        
        Returns:
            Dict[str, int]: Statystyki kolejki
        """
        try:
            from app.models import EmailQueue
            
            stats = {
                'pending': EmailQueue.query.filter_by(status='pending').count(),
                'processing': EmailQueue.query.filter_by(status='processing').count(),
                'sent': EmailQueue.query.filter_by(status='sent').count(),
                'failed': EmailQueue.query.filter_by(status='failed').count(),
                'total': EmailQueue.query.count()
            }
            
            self.logger.info(f"📊 Queue stats: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Error getting queue stats: {e}")
            return {}
