#!/usr/bin/env python3
"""
Email Campaign Service for Lepsze Życie Club
Handles targeted email campaigns to specific user groups
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import and_, or_

from models import db, EmailCampaign, UserGroup, UserGroupMember, EmailTemplate, EmailLog
from .email_service import email_service
from .user_group_service import user_group_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailCampaignService:
    """Service for handling email campaigns"""
    
    def __init__(self):
        pass
    
    def create_campaign(self, name: str, subject: str, html_content: str = None,
                       text_content: str = None, recipient_groups: List[int] = None,
                       custom_emails: List[str] = None, send_type: str = 'immediate',
                       scheduled_at: datetime = None) -> EmailCampaign:
        """
        Create a new email campaign
        
        Args:
            name: Campaign name
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content
            recipient_groups: List of group IDs
            custom_emails: List of additional email addresses
            send_type: Send type (immediate, scheduled)
            scheduled_at: Scheduled send time
            
        Returns:
            EmailCampaign: Created campaign
        """
        try:
            campaign = EmailCampaign(
                name=name,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                recipient_groups=json.dumps(recipient_groups) if recipient_groups else None,
                custom_emails=json.dumps(custom_emails) if custom_emails else None,
                send_type=send_type,
                scheduled_at=scheduled_at
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            logger.info(f"Created email campaign: {name}")
            return campaign
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create campaign {name}: {str(e)}")
            raise
    
    def get_campaign_recipients(self, campaign_id: int) -> List[Dict]:
        """
        Get all recipients for a campaign
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            List[Dict]: List of recipients with their details
        """
        try:
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return []
            
            recipients = []
            
            # Add group members
            if campaign.recipient_groups:
                group_ids = json.loads(campaign.recipient_groups)
                for group_id in group_ids:
                    group = UserGroup.query.get(group_id)
                    if group and group.is_active:
                        members = user_group_service.get_group_members(group.id)
                        for member in members:
                            recipients.append({
                                'email': member.email,
                                'name': member.name,
                                'source': f'group:{group.name}',
                                'group_id': group_id
                            })
            
            # Add custom emails
            if campaign.custom_emails:
                custom_emails = json.loads(campaign.custom_emails)
                for email in custom_emails:
                    recipients.append({
                        'email': email,
                        'name': None,
                        'source': 'custom',
                        'group_id': None
                    })
            
            # Remove duplicates (keep first occurrence)
            seen_emails = set()
            unique_recipients = []
            for recipient in recipients:
                if recipient['email'] not in seen_emails:
                    seen_emails.add(recipient['email'])
                    unique_recipients.append(recipient)
            
            return unique_recipients
            
        except Exception as e:
            logger.error(f"Failed to get recipients for campaign {campaign_id}: {str(e)}")
            return []
    
    def send_campaign(self, campaign_id: int) -> Dict:
        """
        Send an email campaign
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Dict: Sending results
        """
        try:
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return {'success': False, 'error': 'Campaign not found'}
            
            if campaign.status != 'draft':
                return {'success': False, 'error': 'Campaign is not in draft status'}
            
            # Get recipients
            recipients = self.get_campaign_recipients(campaign_id)
            if not recipients:
                return {'success': False, 'error': 'No recipients found'}
            
            # Update campaign status
            campaign.status = 'sending'
            campaign.total_recipients = len(recipients)
            campaign.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Send emails
            results = {
                'total': len(recipients),
                'sent': 0,
                'failed': 0,
                'errors': []
            }
            
            for recipient in recipients:
                try:
                    # Prepare variables
                    variables = {
                        'name': recipient['name'] or 'Użytkowniku',
                        'email': recipient['email']
                    }
                    
                    # Send email
                    if campaign.html_content:
                        # Custom content campaign
                        success = email_service.send_custom_email(
                            to_email=recipient['email'],
                            subject=campaign.subject,
                            html_content=campaign.html_content,
                            text_content=campaign.text_content,
                            variables=variables
                        )
                    else:
                        # Template-based campaign (would need template_id)
                        success = False
                        results['errors'].append(f"No template specified for campaign")
                        break
                    
                    if success:
                        results['sent'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Failed to send to {recipient['email']}")
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Error sending to {recipient['email']}: {str(e)}")
                    logger.error(f"Error sending campaign email to {recipient['email']}: {str(e)}")
            
            # Update campaign status and statistics
            campaign.sent_count = results['sent']
            campaign.failed_count = results['failed']
            campaign.status = 'completed' if results['failed'] == 0 else 'completed_with_errors'
            campaign.sent_at = datetime.utcnow()
            campaign.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Campaign {campaign_id} completed: {results['sent']} sent, {results['failed']} failed")
            return results
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to send campaign {campaign_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def schedule_campaign(self, campaign_id: int, scheduled_at: datetime) -> bool:
        """
        Schedule a campaign for later sending
        
        Args:
            campaign_id: Campaign ID
            scheduled_at: Scheduled send time
            
        Returns:
            bool: True if scheduled successfully
        """
        try:
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return False
            
            campaign.send_type = 'scheduled'
            campaign.scheduled_at = scheduled_at
            campaign.status = 'scheduled'
            campaign.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Campaign {campaign_id} scheduled for {scheduled_at}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to schedule campaign {campaign_id}: {str(e)}")
            return False
    
    def cancel_campaign(self, campaign_id: int) -> bool:
        """
        Cancel a scheduled campaign
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            bool: True if cancelled successfully
        """
        try:
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return False
            
            if campaign.status not in ['draft', 'scheduled']:
                return False
            
            campaign.status = 'cancelled'
            campaign.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            logger.info(f"Campaign {campaign_id} cancelled")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to cancel campaign {campaign_id}: {str(e)}")
            return False
    
    def duplicate_campaign(self, campaign_id: int, new_name: str = None) -> EmailCampaign:
        """
        Duplicate an existing campaign
        
        Args:
            campaign_id: Campaign ID to duplicate
            new_name: New campaign name
            
        Returns:
            EmailCampaign: New campaign
        """
        try:
            original = EmailCampaign.query.get(campaign_id)
            if not original:
                raise ValueError("Original campaign not found")
            
            new_name = new_name or f"Kopia: {original.name}"
            
            new_campaign = EmailCampaign(
                name=new_name,
                subject=original.subject,
                html_content=original.html_content,
                text_content=original.text_content,
                recipient_groups=original.recipient_groups,
                custom_emails=original.custom_emails,
                send_type='immediate',
                status='draft'
            )
            
            db.session.add(new_campaign)
            db.session.commit()
            
            logger.info(f"Duplicated campaign {campaign_id} as {new_campaign.id}")
            return new_campaign
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to duplicate campaign {campaign_id}: {str(e)}")
            raise
    
    def get_campaign_statistics(self, campaign_id: int) -> Dict:
        """
        Get statistics for a campaign
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Dict: Campaign statistics
        """
        try:
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return {}
            
            # Get email logs for this campaign
            logs = EmailLog.query.filter_by(
                email=campaign.recipient_groups,  # This would need to be more specific
                subject=campaign.subject
            ).all()
            
            # Calculate delivery rate
            total_sent = campaign.sent_count + campaign.failed_count
            delivery_rate = (campaign.sent_count / total_sent * 100) if total_sent > 0 else 0
            
            return {
                'name': campaign.name,
                'status': campaign.status,
                'total_recipients': campaign.total_recipients,
                'sent_count': campaign.sent_count,
                'failed_count': campaign.failed_count,
                'delivery_rate': round(delivery_rate, 2),
                'created_at': campaign.created_at.isoformat(),
                'sent_at': campaign.sent_at.isoformat() if campaign.sent_at else None,
                'recipient_groups': json.loads(campaign.recipient_groups) if campaign.recipient_groups else [],
                'custom_emails': json.loads(campaign.custom_emails) if campaign.custom_emails else []
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics for campaign {campaign_id}: {str(e)}")
            return {}
    
    def search_campaigns(self, query: str = None, status: str = None) -> List[EmailCampaign]:
        """
        Search campaigns
        
        Args:
            query: Search query for name
            status: Filter by status
            
        Returns:
            List[EmailCampaign]: List of matching campaigns
        """
        try:
            campaigns_query = EmailCampaign.query
            
            if query:
                campaigns_query = campaigns_query.filter(
                    EmailCampaign.name.ilike(f'%{query}%')
                )
            
            if status:
                campaigns_query = campaigns_query.filter_by(status=status)
            
            return campaigns_query.order_by(EmailCampaign.created_at.desc()).all()
            
        except Exception as e:
            logger.error(f"Failed to search campaigns: {str(e)}")
            return []
    
    def process_scheduled_campaigns(self) -> Dict:
        """
        Process all scheduled campaigns that are due
        
        Returns:
            Dict: Processing results
        """
        try:
            now = datetime.utcnow()
            
            # Get due campaigns
            due_campaigns = EmailCampaign.query.filter(
                and_(
                    EmailCampaign.status == 'scheduled',
                    EmailCampaign.scheduled_at <= now
                )
            ).all()
            
            results = {
                'total': len(due_campaigns),
                'processed': 0,
                'success': 0,
                'failed': 0,
                'errors': []
            }
            
            for campaign in due_campaigns:
                try:
                    results['processed'] += 1
                    
                    # Send the campaign
                    send_results = self.send_campaign(campaign.id)
                    
                    if send_results.get('success', False):
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                        results['errors'].append(f"Campaign {campaign.id}: {send_results.get('error', 'Unknown error')}")
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Campaign {campaign.id}: {str(e)}")
                    logger.error(f"Error processing scheduled campaign {campaign.id}: {str(e)}")
            
            logger.info(f"Processed {results['processed']} scheduled campaigns: {results['success']} success, {results['failed']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Failed to process scheduled campaigns: {str(e)}")
            raise


# Global service instance
email_campaign_service = EmailCampaignService()

