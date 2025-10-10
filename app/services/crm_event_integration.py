"""
CRM Event Integration Service - Integrates CRM with event management
"""
from app.models import db
from app.models.events_model import EventSchedule
from app.utils.timezone_utils import get_local_now


class EventIntegrationService:
    """Service for integrating CRM contacts with events"""
    
    @staticmethod
    def get_available_events():
        """
        Get list of available events for lead registration
        Returns active, published, non-archived events that haven't ended yet
        """
        try:
            now = get_local_now().replace(tzinfo=None)
            
            # Get all active, published, non-archived events
            events = EventSchedule.query.filter(
                EventSchedule.is_active == True,
                EventSchedule.is_published == True,
                EventSchedule.is_archived == False
            ).order_by(EventSchedule.event_date.asc()).all()
            
            # Filter out ended events
            available_events = [
                event for event in events 
                if not event.is_ended()
            ]
            
            return available_events
            
        except Exception as e:
            print(f"Error getting available events: {str(e)}")
            return []
    
    @staticmethod
    def register_contact_for_event(contact_id, event_id, user_id=None):
        """
        Register a CRM contact for an event
        
        Args:
            contact_id: ID of the contact to register
            event_id: ID of the event
            user_id: Optional user ID if contact is linked to a user account
            
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            from app.models.crm_model import Contact
            from app.models.event_registration_model import EventRegistration
            
            # Verify contact exists
            contact = Contact.query.get(contact_id)
            if not contact:
                return False, "Kontakt nie istnieje"
            
            # Verify event exists
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, "Wydarzenie nie istnieje"
            
            # Check if event is full
            if event.is_full:
                return False, f"Wydarzenie '{event.title}' jest już pełne"
            
            # Check if contact is already registered
            existing_registration = EventRegistration.query.filter_by(
                event_id=event_id,
                contact_id=contact_id,
                is_active=True
            ).first()
            
            if existing_registration:
                return False, f"Kontakt jest już zarejestrowany na wydarzenie '{event.title}'"
            
            # Create registration
            registration = EventRegistration(
                event_id=event_id,
                user_id=user_id,
                contact_id=contact_id,
                is_active=True
            )
            
            db.session.add(registration)
            db.session.commit()
            
            return True, f"Kontakt został pomyślnie zarejestrowany na wydarzenie '{event.title}'"
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Błąd podczas rejestracji kontaktu na wydarzenie: {str(e)}"
            print(error_msg)
            return False, error_msg
    
    @staticmethod
    def get_contact_events(contact_id):
        """
        Get all events a contact is registered for
        
        Args:
            contact_id: ID of the contact
            
        Returns:
            List of EventSchedule objects
        """
        try:
            from app.models.event_registration_model import EventRegistration
            
            # Get all active registrations for this contact
            registrations = EventRegistration.query.filter_by(
                contact_id=contact_id,
                is_active=True
            ).all()
            
            # Get the events
            event_ids = [reg.event_id for reg in registrations]
            events = EventSchedule.query.filter(
                EventSchedule.id.in_(event_ids)
            ).order_by(EventSchedule.event_date.asc()).all()
            
            return events
            
        except Exception as e:
            print(f"Error getting contact events: {str(e)}")
            return []


