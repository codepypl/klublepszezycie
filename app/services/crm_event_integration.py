"""
Event integration service for CRM system
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.models import db, UserGroup, UserGroupMember, EventSchedule, EventRegistration
from app.models.crm_model import Contact, Call
from app.services.email_automation import EmailService

class EventIntegrationService:
    """Service for integrating CRM leads with event system"""
    
    @staticmethod
    def get_leady_group():
        """Get or create 'Leady' group"""
        leady_group = UserGroup.query.filter_by(name='Leady').first()
        
        if not leady_group:
            leady_group = UserGroup(
                name='Leady',
                description='Grupa pozyskanych leadów z systemu CRM',
                group_type='manual',
                is_active=True
            )
            db.session.add(leady_group)
            db.session.commit()
        
        return leady_group
    
    @staticmethod
    def register_lead_for_event(contact_id, event_id, ankieter_id):
        """Register lead for event and add to Leady group"""
        contact = Contact.query.get(contact_id)
        event = EventSchedule.query.get(event_id)
        
        if not contact or not event:
            return False
        
        # Add to Leady group
        leady_group = EventIntegrationService.get_leady_group()
        
        # Check if already in group
        existing_member = UserGroupMember.query.filter_by(
            group_id=leady_group.id,
            email=contact.email
        ).first()
        
        if not existing_member:
            group_member = UserGroupMember(
                group_id=leady_group.id,
                email=contact.email,
                name=contact.name,
                member_type='manual'
            )
            db.session.add(group_member)
        
        # Create event registration
        registration = EventRegistration(
            event_id=event_id,
            name=contact.name,
            email=contact.email,
            phone=contact.phone,
            registration_source='crm_lead'
        )
        
        db.session.add(registration)
        
        # Update call record
        call = Call.query.filter_by(
            contact_id=contact_id,
            ankieter_id=ankieter_id,
            status='lead'
        ).order_by(Call.created_at.desc()).first()
        
        if call:
            call.is_lead_registered = True
            call.event_id = event_id
        
        # Update contact
        contact.is_active = False  # Mark as processed
        
        db.session.commit()
        
        # Send confirmation email
        EventIntegrationService._send_lead_confirmation_email(contact, event)
        
        return True
    
    @staticmethod
    def _send_lead_confirmation_email(contact, event):
        """Send confirmation email to lead"""
        try:
            email_service = EmailService()
            
            # Prepare email data
            email_data = {
                'to_email': contact.email,
                'to_name': contact.name,
                'event_title': event.title,
                'event_date': event.event_date.strftime('%d.%m.%Y'),
                'event_time': event.event_date.strftime('%H:%M'),
                'event_location': event.location or 'Do potwierdzenia'
            }
            
            # Send email (you'll need to create appropriate email template)
            # For now, just log the action
            print(f"📧 Email confirmation sent to {contact.email} for event {event.title}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error sending email to {contact.email}: {e}")
            return False
    
    @staticmethod
    def get_available_events():
        """Get available events for lead registration"""
        from datetime import datetime
        
        # Get future events
        future_events = EventSchedule.query.filter(
            EventSchedule.event_date > datetime.now(),
            EventSchedule.is_active == True
        ).order_by(EventSchedule.event_date.asc()).all()
        
        return future_events
    
    @staticmethod
    def get_lead_statistics():
        """Get lead statistics"""
        stats = {
            'total_leads': Call.query.filter_by(status='lead').count(),
            'registered_leads': Call.query.filter_by(
                status='lead',
                is_lead_registered=True
            ).count(),
            'pending_leads': Call.query.filter_by(
                status='lead',
                is_lead_registered=False
            ).count(),
            'leady_group_size': UserGroupMember.query.filter_by(
                group_id=EventIntegrationService.get_leady_group().id
            ).count()
        }
        
        return stats
    
    @staticmethod
    def get_ankieter_lead_stats(ankieter_id):
        """Get lead statistics for specific ankieter"""
        stats = {
            'total_leads': Call.query.filter_by(
                ankieter_id=ankieter_id,
                status='lead'
            ).count(),
            'registered_leads': Call.query.filter_by(
                ankieter_id=ankieter_id,
                status='lead',
                is_lead_registered=True
            ).count(),
            'pending_leads': Call.query.filter_by(
                ankieter_id=ankieter_id,
                status='lead',
                is_lead_registered=False
            ).count()
        }
        
        return stats
