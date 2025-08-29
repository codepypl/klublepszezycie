#!/usr/bin/env python3
"""
Email Automation Service for Lepsze Życie Club
Handles automatic email sending based on triggers and schedules
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy import and_, or_

from models import db, EmailAutomation, EmailAutomationLog, EventEmailSchedule, UserGroup, UserGroupMember, EmailTemplate, EventSchedule, EventRegistration
from .email_service import email_service
from .user_group_service import user_group_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailAutomationService:
    """Service for handling email automation"""
    
    def __init__(self):
        pass
    
    def create_automation(self, name: str, automation_type: str, template_id: int,
                         description: str = None, trigger_conditions: Dict = None) -> EmailAutomation:
        """
        Create a new email automation
        
        Args:
            name: Automation name
            automation_type: Type of automation
            template_id: Email template ID
            description: Automation description
            trigger_conditions: Trigger conditions
            
        Returns:
            EmailAutomation: Created automation
        """
        try:
            automation = EmailAutomation(
                name=name,
                description=description,
                automation_type=automation_type,
                template_id=template_id,
                trigger_conditions=json.dumps(trigger_conditions) if trigger_conditions else None
            )
            
            db.session.add(automation)
            db.session.commit()
            
            logger.info(f"Created email automation: {name}")
            return automation
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create automation {name}: {str(e)}")
            raise
    
    def create_welcome_automation(self) -> EmailAutomation:
        """Create welcome email automation"""
        template = EmailTemplate.query.filter_by(template_type='welcome').first()
        if not template:
            logger.error("Welcome template not found")
            raise ValueError("Welcome template not found")
        
        return self.create_automation(
            name="Automatyczny email powitalny",
            automation_type="welcome",
            template_id=template.id,
            description="Automatycznie wysyła email powitalny po rejestracji",
            trigger_conditions={'trigger': 'user_registration'}
        )
    
    def create_event_reminder_automation(self, reminder_type: str) -> EmailAutomation:
        """Create event reminder automation"""
        template_name = f'event_reminder_{reminder_type}'
        template = EmailTemplate.query.filter_by(template_type=template_name).first()
        if not template:
            logger.error(f"Event reminder template {template_name} not found")
            raise ValueError(f"Event reminder template {template_name} not found")
        
        return self.create_automation(
            name=f"Przypomnienie o wydarzeniu - {reminder_type}",
            automation_type="event_reminder",
            template_id=template.id,
            description=f"Automatycznie wysyła przypomnienie {reminder_type} przed wydarzeniem",
            trigger_conditions={'trigger': 'event_reminder', 'type': reminder_type}
        )
    
    def schedule_event_emails(self, event_id: int) -> List[EventEmailSchedule]:
        """
        Schedule automatic emails for an event
        
        Args:
            event_id: Event ID
            
        Returns:
            List[EventEmailSchedule]: Created schedules
        """
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                raise ValueError(f"Event {event_id} not found")
            
            # Get or create event group
            group = user_group_service.get_group_by_event(event_id)
            if not group:
                group = user_group_service.create_event_group(event_id, event.title)
            
            # Get reminder templates
            reminder_types = [
                ('24h_before', timedelta(hours=24)),
                ('1h_before', timedelta(hours=1)),
                ('5min_before', timedelta(minutes=5))
            ]
            
            schedules = []
            for reminder_type, time_offset in reminder_types:
                # Check if schedule already exists
                existing_schedule = EventEmailSchedule.query.filter_by(
                    event_id=event_id,
                    notification_type=reminder_type
                ).first()
                
                if existing_schedule:
                    continue
                
                # Calculate scheduled time
                scheduled_time = event.event_date - time_offset
                
                # Only schedule if it's in the future
                if scheduled_time > datetime.utcnow():
                    # Get template
                    template_name = f'event_reminder_{reminder_type}'
                    template = EmailTemplate.query.filter_by(template_type=template_name).first()
                    
                    if template:
                        schedule = EventEmailSchedule(
                            event_id=event_id,
                            notification_type=reminder_type,
                            scheduled_at=scheduled_time,
                            recipient_group_id=group.id,
                            template_id=template.id
                        )
                        
                        db.session.add(schedule)
                        schedules.append(schedule)
                        
                        logger.info(f"Scheduled {reminder_type} email for event {event_id} at {scheduled_time}")
            
            db.session.commit()
            return schedules
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to schedule event emails for event {event_id}: {str(e)}")
            raise
    
    def process_scheduled_emails(self) -> Dict:
        """
        Process all due scheduled emails
        
        Returns:
            Dict: Processing results
        """
        try:
            now = datetime.utcnow()
            
            # Get due schedules
            due_schedules = EventEmailSchedule.query.filter(
                and_(
                    EventEmailSchedule.status == 'pending',
                    EventEmailSchedule.scheduled_at <= now
                )
            ).all()
            
            results = {
                'total': len(due_schedules),
                'processed': 0,
                'success': 0,
                'failed': 0,
                'errors': []
            }
            
            for schedule in due_schedules:
                try:
                    results['processed'] += 1
                    
                    # Process the schedule
                    success = self._process_single_schedule(schedule)
                    
                    if success:
                        results['success'] += 1
                        schedule.status = 'sent'
                        schedule.sent_at = now
                    else:
                        results['failed'] += 1
                        schedule.status = 'failed'
                    
                    schedule.updated_at = now
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"Schedule {schedule.id}: {str(e)}")
                    schedule.status = 'failed'
                    schedule.updated_at = now
                    logger.error(f"Error processing schedule {schedule.id}: {str(e)}")
            
            db.session.commit()
            logger.info(f"Processed {results['processed']} scheduled emails: {results['success']} success, {results['failed']} failed")
            return results
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to process scheduled emails: {str(e)}")
            raise
    
    def _process_single_schedule(self, schedule: EventEmailSchedule) -> bool:
        """
        Process a single email schedule
        
        Args:
            schedule: Email schedule to process
            
        Returns:
            bool: True if successful
        """
        try:
            # Get recipient group
            if not schedule.recipient_group_id:
                logger.error(f"Schedule {schedule.id} has no recipient group")
                return False
            
            group = UserGroup.query.get(schedule.recipient_group_id)
            if not group:
                logger.error(f"Recipient group {schedule.recipient_group_id} not found")
                return False
            
            # Get group members
            members = user_group_service.get_group_members(group.id)
            if not members:
                logger.warning(f"Group {group.id} has no members")
                schedule.recipient_count = 0
                schedule.sent_count = 0
                schedule.failed_count = 0
                return True
            
            # Get template
            template = EmailTemplate.query.get(schedule.template_id)
            if not template:
                logger.error(f"Template {schedule.template_id} not found")
                return False
            
            # Send emails to all members
            schedule.recipient_count = len(members)
            sent_count = 0
            failed_count = 0
            
            for member in members:
                try:
                    # Prepare variables
                    variables = {
                        'name': member.name or 'Użytkowniku',
                        'email': member.email
                    }
                    
                    # Add event-specific variables if available
                    if schedule.event:
                        variables.update({
                            'event_title': schedule.event.title,
                            'event_date': schedule.event.event_date.strftime('%d.%m.%Y o %H:%M'),
                            'event_type': schedule.event.event_type,
                            'meeting_link': schedule.event.meeting_link or '',
                            'location': schedule.event.location or ''
                        })
                    
                    # Send email
                    success = email_service.send_template_email(
                        to_email=member.email,
                        template_name=template.template_type,
                        variables=variables
                    )
                    
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to send email to {member.email}: {str(e)}")
            
            # Update schedule statistics
            schedule.sent_count = sent_count
            schedule.failed_count = failed_count
            
            return failed_count == 0
            
        except Exception as e:
            logger.error(f"Error processing schedule {schedule.id}: {str(e)}")
            return False
    
    def trigger_welcome_email(self, email: str, name: str) -> bool:
        """
        Trigger welcome email for new user
        
        Args:
            email: User email
            name: User name
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Get welcome automation
            automation = EmailAutomation.query.filter_by(
                automation_type='welcome',
                is_active=True
            ).first()
            
            if not automation:
                logger.warning("No welcome automation found")
                return False
            
            # Send welcome email
            success = email_service.send_welcome_email(email, name)
            
            # Log automation execution
            if success:
                self._log_automation_execution(
                    automation.id,
                    'triggered',
                    1, 1, 0,
                    {'email': email, 'name': name}
                )
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to trigger welcome email for {email}: {str(e)}")
            return False
    
    def _log_automation_execution(self, automation_id: int, execution_type: str,
                                 recipient_count: int, success_count: int, error_count: int,
                                 details: Dict = None):
        """Log automation execution"""
        try:
            log_entry = EmailAutomationLog(
                automation_id=automation_id,
                execution_type=execution_type,
                recipient_count=recipient_count,
                success_count=success_count,
                error_count=error_count,
                details=json.dumps(details) if details else None,
                status='completed' if error_count == 0 else 'failed',
                completed_at=datetime.utcnow()
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to log automation execution: {str(e)}")
    
    def get_automation_statistics(self) -> Dict:
        """
        Get automation statistics
        
        Returns:
            Dict: Automation statistics
        """
        try:
            total_automations = EmailAutomation.query.filter_by(is_active=True).count()
            total_schedules = EventEmailSchedule.query.filter_by(status='pending').count()
            
            # Get recent logs
            recent_logs = EmailAutomationLog.query.order_by(
                EmailAutomationLog.started_at.desc()
            ).limit(10).all()
            
            # Calculate success rate
            total_executions = sum(log.recipient_count for log in recent_logs)
            total_success = sum(log.success_count for log in recent_logs)
            success_rate = (total_success / total_executions * 100) if total_executions > 0 else 0
            
            return {
                'total_automations': total_automations,
                'pending_schedules': total_schedules,
                'recent_executions': len(recent_logs),
                'success_rate': round(success_rate, 2),
                'recent_logs': [
                    {
                        'automation_name': log.automation.name,
                        'execution_type': log.execution_type,
                        'status': log.status,
                        'recipient_count': log.recipient_count,
                        'success_count': log.success_count,
                        'started_at': log.started_at.isoformat()
                    }
                    for log in recent_logs
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get automation statistics: {str(e)}")
            return {}


# Global service instance
email_automation_service = EmailAutomationService()

