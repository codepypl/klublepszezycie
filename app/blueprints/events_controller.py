"""
Events business logic controller
"""
from flask import request
from flask_login import login_required, current_user
from app.models import db, EventSchedule, EventRegistration, User
from datetime import datetime, timedelta
from app.utils.timezone_utils import get_local_now

class EventsController:
    """Events business logic controller"""
    
    @staticmethod
    def get_events(page=1, per_page=10, status=None, search=None):
        """Get events with pagination and filters"""
        try:
            query = EventSchedule.query
            
            if status:
                query = query.filter_by(status=status)
            
            if search:
                query = query.filter(
                    EventSchedule.title.ilike(f'%{search}%') |
                    EventSchedule.description.ilike(f'%{search}%')
                )
            
            events = query.order_by(EventSchedule.event_date.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'success': True,
                'events': events
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'events': None
            }
    
    @staticmethod
    def get_event(event_id):
        """Get single event"""
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return {
                    'success': False,
                    'error': 'Wydarzenie nie zostało znalezione',
                    'event': None
                }
            
            return {
                'success': True,
                'event': event
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'event': None
            }
    
    @staticmethod
    def create_event(title, description, event_date, event_time, location, max_participants, status='active'):
        """Create new event"""
        try:
            if not all([title, description, event_date, event_time, location]):
                return {
                    'success': False,
                    'error': 'Wszystkie pola są wymagane'
                }
            
            # Parse datetime
            try:
                event_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                return {
                    'success': False,
                    'error': 'Nieprawidłowy format daty lub czasu'
                }
            
            event = EventSchedule(
                title=title,
                description=description,
                event_date=event_datetime,
                location=location,
                max_participants=max_participants,
                status=status,
                created_by=current_user.id
            )
            
            db.session.add(event)
            db.session.commit()
            
            return {
                'success': True,
                'event': event,
                'message': 'Wydarzenie zostało utworzone pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_event(event_id, title, description, event_date, event_time, location, max_participants, status):
        """Update event"""
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return {
                    'success': False,
                    'error': 'Wydarzenie nie zostało znalezione'
                }
            
            # Parse datetime
            try:
                event_datetime = datetime.strptime(f"{event_date} {event_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                return {
                    'success': False,
                    'error': 'Nieprawidłowy format daty lub czasu'
                }
            
            # Store old title for group update
            old_title = event.title
            
            event.title = title
            event.description = description
            event.event_date = event_datetime
            event.location = location
            event.max_participants = max_participants
            event.status = status
            
            db.session.commit()
            
            # Update group name if title changed
            if old_title != title:
                from app.services.group_manager import GroupManager
                group_manager = GroupManager()
                
                # Find and update the event group
                from app.models import UserGroup
                group = UserGroup.query.filter_by(
                    name=f"Wydarzenie: {old_title}",
                    group_type='event_based'
                ).first()
                
                if group:
                    print(f"🔍 Aktualizacja nazwy grupy z '{group.name}' na 'Wydarzenie: {title}'")
                    group.name = f"Wydarzenie: {title}"
                    group.description = f"Grupa uczestników wydarzenia: {title}"
                    db.session.commit()
                    print(f"✅ Nazwa grupy zaktualizowana pomyślnie")
                else:
                    print(f"❌ Grupa wydarzenia '{old_title}' nie została znaleziona")
            
            # Asynchronicznie synchronizuj grupę wydarzenia po aktualizacji
            success, message = group_manager.async_sync_event_group(event_id)
            if success:
                print(f"✅ Zsynchronizowano grupę wydarzenia po aktualizacji: {title}")
            else:
                print(f"❌ Błąd synchronizacji grupy wydarzenia: {message}")
            
            return {
                'success': True,
                'event': event,
                'message': 'Wydarzenie zostało zaktualizowane pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def delete_event(event_id):
        """Delete event"""
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return {
                    'success': False,
                    'error': 'Wydarzenie nie zostało znalezione'
                }
            
            # Check if there are registrations
            registrations_count = EventRegistration.query.filter_by(event_id=event_id).count()
            if registrations_count > 0:
                return {
                    'success': False,
                    'error': f'Nie można usunąć wydarzenia z {registrations_count} rejestracjami'
                }
            
            db.session.delete(event)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Wydarzenie zostało usunięte pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_registrations(event_id=None, page=1, per_page=10, status=None, search=None):
        """Get event registrations"""
        try:
            query = EventRegistration.query
            
            if event_id:
                query = query.filter_by(event_id=event_id)
            
            if status:
                query = query.filter_by(status=status)
            
            if search:
                query = query.join(User).filter(
                    User.first_name.ilike(f'%{search}%') |
                    User.email.ilike(f'%{search}%')
                )
            
            registrations = query.order_by(EventRegistration.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'success': True,
                'registrations': registrations.items,
                'pagination': {
                    'page': registrations.page,
                    'pages': registrations.pages,
                    'total': registrations.total,
                    'per_page': registrations.per_page
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'registrations': None
            }
    
    @staticmethod
    def register_for_event(event_id, user_id, notes=None):
        """Register user for event"""
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return {
                    'success': False,
                    'error': 'Wydarzenie nie zostało znalezione'
                }
            
            # Check if event is active
            if event.status != 'active':
                return {
                    'success': False,
                    'error': 'Wydarzenie nie jest aktywne'
                }
            
            # Check if user is already registered
            existing_registration = EventRegistration.query.filter_by(
                event_id=event_id, user_id=user_id
            ).first()
            
            if existing_registration:
                return {
                    'success': False,
                    'error': 'Jesteś już zarejestrowany na to wydarzenie'
                }
            
            # Check if event is full
            current_registrations = EventRegistration.query.filter_by(event_id=event_id).count()
            if event.max_participants and current_registrations >= event.max_participants:
                return {
                    'success': False,
                    'error': 'Wydarzenie jest pełne'
                }
            
            # Create registration
            user = User.query.get(user_id)
            registration = EventRegistration(
                event_id=event_id,
                user_id=user_id,
                first_name=user.first_name,
                email=user.email,
                phone=user.phone,
                notes=notes,
                status='confirmed'
            )
            
            db.session.add(registration)
            db.session.commit()
            
            return {
                'success': True,
                'registration': registration,
                'message': 'Zostałeś zarejestrowany na wydarzenie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def cancel_registration(registration_id):
        """Cancel event registration"""
        try:
            registration = EventRegistration.query.get(registration_id)
            if not registration:
                return {
                    'success': False,
                    'error': 'Rejestracja nie została znaleziona'
                }
            
            registration.status = 'cancelled'
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Rejestracja została anulowana'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_upcoming_events(limit=5):
        """Get upcoming events"""
        try:
            now = get_local_now()
            events = EventSchedule.query.filter(
                EventSchedule.event_date > now,
                EventSchedule.status == 'active'
            ).order_by(EventSchedule.event_date.asc()).limit(limit).all()
            
            return {
                'success': True,
                'events': events
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'events': []
            }
