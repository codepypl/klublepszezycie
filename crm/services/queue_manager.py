"""
Queue management service for CRM system
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from datetime import datetime, timedelta
from app.models import db
from crm.models import Contact, Call, BlacklistEntry
from crm.config import DEFAULT_MAX_CALL_ATTEMPTS

class QueueManager:
    """Service for managing call queue and contact assignment"""
    
    @staticmethod
    def get_next_contact_for_ankieter(ankieter_id):
        """Get next contact for ankieter based on priority"""
        # First try high priority (callbacks)
        high_priority = Call.query.filter_by(
            ankieter_id=ankieter_id,
            priority='high',
            queue_status='pending'
        ).order_by(Call.scheduled_date.asc()).first()
        
        if high_priority and high_priority.contact.can_be_called():
            return high_priority.contact
        
        # Then medium priority (leads)
        medium_priority = Call.query.filter_by(
            ankieter_id=ankieter_id,
            priority='medium',
            queue_status='pending'
        ).order_by(Call.created_at.asc()).first()
        
        if medium_priority and medium_priority.contact.can_be_called():
            return medium_priority.contact
        
        # Finally low priority (new contacts)
        low_priority = Call.query.filter_by(
            ankieter_id=ankieter_id,
            priority='low',
            queue_status='pending'
        ).order_by(Call.created_at.asc()).first()
        
        if low_priority and low_priority.contact.can_be_called():
            return low_priority.contact
        
        return None
    
    @staticmethod
    def assign_contact_to_ankieter(contact_id, ankieter_id, priority='low'):
        """Assign contact to ankieter"""
        # Check if already assigned
        existing = Call.query.filter_by(
            contact_id=contact_id,
            ankieter_id=ankieter_id,
            queue_status='pending'
        ).first()
        
        if existing:
            return existing
        
        # Create new call entry
        call_entry = Call(
            contact_id=contact_id,
            ankieter_id=ankieter_id,
            priority=priority,
            queue_status='pending',
            call_date=datetime.utcnow()
        )
        
        db.session.add(call_entry)
        db.session.commit()
        
        return call_entry
    
    @staticmethod
    def auto_assign_contacts_to_ankieter(ankieter_id, limit=10):
        """Automatically assign contacts to ankieter"""
        # Get unassigned contacts that can be called
        unassigned_contacts = Contact.query.filter(
            Contact.assigned_ankieter_id.is_(None),
            Contact.is_active == True,
            Contact.is_blacklisted == False,
            Contact.call_attempts < Contact.max_call_attempts
        ).limit(limit).all()
        
        assigned_count = 0
        for contact in unassigned_contacts:
            # Assign to ankieter
            contact.assigned_ankieter_id = ankieter_id
            
            # Create call entry
            call_entry = Call(
                contact_id=contact.id,
                ankieter_id=ankieter_id,
                priority='low',
                queue_status='pending',
                queue_type='new',
                call_date=datetime.utcnow()
            )
            
            db.session.add(call_entry)
            assigned_count += 1
        
        db.session.commit()
        return assigned_count
    
    @staticmethod
    def schedule_callback(contact_id, ankieter_id, callback_date, notes=None):
        """Schedule a callback for contact"""
        # Create high priority call entry
        call_entry = Call(
            contact_id=contact_id,
            ankieter_id=ankieter_id,
            priority='high',
            scheduled_date=callback_date,
            queue_status='pending',
            queue_type='callback',
            call_date=datetime.utcnow()
        )
        
        db.session.add(call_entry)
        
        # Update contact
        contact = Contact.query.get(contact_id)
        if contact:
            contact.assigned_ankieter_id = ankieter_id
        
        db.session.commit()
        
        return call_entry
    
    @staticmethod
    def process_call_result(contact_id, ankieter_id, call_status, notes=None, 
                          callback_date=None, event_id=None):
        """Process call result and update queue accordingly"""
        contact = Contact.query.get(contact_id)
        if not contact:
            return False
        
        # Update contact call attempts
        contact.call_attempts += 1
        contact.last_call_date = datetime.now()
        
        # Create call record
        call = Call(
            contact_id=contact_id,
            ankieter_id=ankieter_id,
            call_date=datetime.now(),
            status=call_status,
            notes=notes,
            event_id=event_id
        )
        
        if callback_date:
            call.next_call_date = callback_date
        
        db.session.add(call)
        
        # Process based on status
        if call_status == 'lead':
            # Lead - mark as completed
            QueueManager._mark_queue_completed(contact_id, ankieter_id)
            # TODO: Register for event and send email
            
        elif call_status == 'rejection':
            # Rejection - add to blacklist
            QueueManager._add_to_blacklist(contact_id, ankieter_id, 'rejection')
            QueueManager._mark_queue_completed(contact_id, ankieter_id)
            
        elif call_status == 'callback':
            # Callback - schedule for later
            if callback_date:
                QueueManager.schedule_callback(contact_id, ankieter_id, callback_date, notes)
            else:
                # Default callback in 1 hour
                default_callback = datetime.now() + timedelta(hours=1)
                QueueManager.schedule_callback(contact_id, ankieter_id, default_callback, notes)
        
        elif call_status in ['no_answer', 'busy']:
            # No answer or busy - check if max attempts reached
            if contact.call_attempts >= contact.max_call_attempts:
                QueueManager._add_to_blacklist(contact_id, ankieter_id, 'max_attempts')
                QueueManager._mark_queue_completed(contact_id, ankieter_id)
            else:
                # Schedule retry
                retry_time = datetime.now() + timedelta(minutes=30)  # Retry in 30 minutes
                QueueManager.schedule_callback(contact_id, ankieter_id, retry_time, notes)
        
        elif call_status == 'wrong_number':
            # Wrong number - add to blacklist
            QueueManager._add_to_blacklist(contact_id, ankieter_id, 'wrong_number')
            QueueManager._mark_queue_completed(contact_id, ankieter_id)
        
        db.session.commit()
        return True
    
    @staticmethod
    def _mark_queue_completed(contact_id, ankieter_id):
        """Mark queue entry as completed"""
        call_entry = Call.query.filter_by(
            contact_id=contact_id,
            ankieter_id=ankieter_id,
            queue_status='pending'
        ).first()
        
        if call_entry:
            call_entry.queue_status = 'completed'
    
    @staticmethod
    def _add_to_blacklist(contact_id, ankieter_id, reason):
        """Add contact to blacklist"""
        contact = Contact.query.get(contact_id)
        if not contact:
            return
        
        # Check if already blacklisted
        existing = BlacklistEntry.query.filter_by(phone=contact.phone).first()
        if existing:
            return existing
        
        # Create blacklist entry
        blacklist_entry = BlacklistEntry(
            phone=contact.phone,
            reason=reason,
            blacklisted_by=ankieter_id,
            contact_id=contact_id
        )
        
        db.session.add(blacklist_entry)
        
        # Mark contact as blacklisted
        contact.is_blacklisted = True
        
        return blacklist_entry
    
    @staticmethod
    def get_ankieter_queue_stats(ankieter_id):
        """Get queue statistics for ankieter"""
        stats = {
            'pending_high': Call.query.filter_by(
                ankieter_id=ankieter_id,
                priority='high',
                queue_status='pending'
            ).count(),
            'pending_medium': Call.query.filter_by(
                ankieter_id=ankieter_id,
                priority='medium',
                queue_status='pending'
            ).count(),
            'pending_low': Call.query.filter_by(
                ankieter_id=ankieter_id,
                priority='low',
                queue_status='pending'
            ).count(),
            'total_pending': Call.query.filter_by(
                ankieter_id=ankieter_id,
                queue_status='pending'
            ).count()
        }
        
        return stats
