"""
Queue management service for CRM system
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from datetime import datetime, timedelta
from app.models import db
from app.models.crm_model import Contact, Call, BlacklistEntry
from app.config.crm_config import DEFAULT_MAX_CALL_ATTEMPTS

class QueueManager:
    """Service for managing call queue and contact assignment"""
    
    @staticmethod
    def get_next_contact_for_ankieter(ankieter_id):
        """Get next contact for ankieter based on priority and scheduled time"""
        from app.utils.timezone_utils import get_local_now
        now = get_local_now()
        
        # First try high priority (scheduled callbacks) - only if scheduled time has passed
        high_priority = Call.query.filter_by(
            ankieter_id=ankieter_id,
            priority='high',
            queue_status='pending'
        ).filter(
            (Call.scheduled_date.is_(None)) | (Call.scheduled_date <= now)
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
            status='pending',  # Domyślny status dla nowego rekordu
            call_date=__import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
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
                status='pending',  # Domyślny status dla nowego rekordu
                call_date=__import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
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
            status='callback',  # Status dla callback
            call_date=__import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
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
                          callback_date=None, event_id=None, duration_minutes=0):
        """Process call result and update queue accordingly"""
        from app.utils.timezone_utils import get_local_now
        
        contact = Contact.query.get(contact_id)
        if not contact:
            return {'success': False, 'error': 'Contact not found'}
        
        # Update contact call attempts
        contact.call_attempts += 1
        contact.last_call_date = get_local_now()
        
        # Create call record
        call = Call(
            contact_id=contact_id,
            ankieter_id=ankieter_id,
            call_date=get_local_now(),
            status=call_status,
            notes=notes,
            duration_minutes=duration_minutes
        )
        
        db.session.add(call)
        db.session.commit()  # Commit call record first
        
        # Process based on status - implementation of business rules
        if call_status == 'lead':
            # LEAD - Sukces! Podbij liczniki, oznacz jako zakończony, nigdy więcej nie dzwoń
            contact.business_reason = 'lead'
            QueueManager._mark_queue_completed(contact_id, ankieter_id)
            
            # Update stats - increment lead counter
            from app.models.stats_model import Stats
            Stats.increment_lead_count(ankieter_id)
            
            print(f"✅ LEAD: Kontakt {contact.name} oznaczony jako sukces (lead)")
            
        elif call_status == 'blacklist':
            # CZARNA LISTA - Dodaj do blacklist, oznacz jako zakończony, nigdy więcej nie dzwoń
            contact.business_reason = 'blacklist'
            QueueManager._add_to_blacklist(contact_id, ankieter_id, 'blacklist')
            QueueManager._mark_queue_completed(contact_id, ankieter_id)
            
            print(f"✅ BLACKLIST: Kontakt {contact.name} dodany do czarnej listy")
            
        elif call_status == 'rejection':
            # ODMOWA - Oznacz jako zakończony, nigdy więcej nie dzwoń
            contact.business_reason = 'rejection'
            QueueManager._mark_queue_completed(contact_id, ankieter_id)
            
            print(f"✅ ODMOWA: Kontakt {contact.name} odrzucił ofertę")
            
        elif call_status == 'wrong_number':
            # BŁĘDNY NUMER - Oznacz jako zakończony, nigdy więcej nie dzwoń
            contact.business_reason = 'wrong_number'
            QueueManager._mark_queue_completed(contact_id, ankieter_id)
            
            print(f"✅ BŁĘDNY NUMER: Kontakt {contact.name} ma nieprawidłowy numer")
            
        elif call_status in ['no_answer', 'busy']:
            # NIE ODEBRAŁ / ZAJĘTE - Automatyczne przeplanowanie za 4h (tylko w godzinach 8-21)
            contact.business_reason = 'callback_auto'
            
            # Oblicz czas za 4 godziny
            retry_time = get_local_now() + timedelta(hours=4)
            
            # Sprawdź czy to będzie w godzinach pracy (8-21)
            retry_hour = retry_time.hour
            if retry_hour < 8:
                # Jeśli przed 8:00, ustaw na 8:00
                retry_time = retry_time.replace(hour=8, minute=0, second=0)
            elif retry_hour >= 21:
                # Jeśli po 21:00, ustaw na następny dzień o 8:00
                retry_time = retry_time + timedelta(days=1)
                retry_time = retry_time.replace(hour=8, minute=0, second=0)
            
            QueueManager.schedule_callback(contact_id, ankieter_id, retry_time, notes)
            
            print(f"✅ AUTO-PRZEPLANOWANIE: Kontakt {contact.name} przeplanowany na {retry_time}")
            
        elif call_status == 'callback':
            # RĘCZNE PRZEPLANOWANIE - użytkownik sam wybrał datę
            contact.business_reason = 'callback_manual'
            
            if callback_date:
                QueueManager.schedule_callback(contact_id, ankieter_id, callback_date, notes)
                print(f"✅ PRZEPLANOWANIE: Kontakt {contact.name} przeplanowany na {callback_date}")
            else:
                # Default callback in 1 hour if no date provided
                default_callback = get_local_now() + timedelta(hours=1)
                QueueManager.schedule_callback(contact_id, ankieter_id, default_callback, notes)
        
        db.session.commit()
        return {'success': True, 'message': 'Wynik połączenia zapisany pomyślnie'}
    
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
            db.session.commit()
    
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
