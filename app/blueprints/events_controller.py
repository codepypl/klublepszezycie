"""
Events business logic controller
"""
from flask import request
from flask_login import login_required, current_user
from app.models import db, EventSchedule, User, Stats, UserLogs, UserHistory
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
            
            # Automatycznie utwórz grupę dla wydarzenia
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            group_manager.create_event_group(event.id, event.title)
            
            # Automatycznie zaplanuj przypomnienia o wydarzeniu przez Celery
            from app.tasks.email_tasks import schedule_event_reminders_task
            
            # Wywołaj zadanie Celery asynchronicznie
            task = schedule_event_reminders_task.delay(event.id)
            print(f"✅ Zadanie Celery zaplanowane (ID: {task.id}) dla wydarzenia: {event.title}")
            
            # Trigger auto-posting for new event
            if event.is_active and not event.is_archived:
                try:
                    from app.tasks.social_media_tasks import auto_post_event_task
                    social_task = auto_post_event_task.delay(event.id)
                    print(f"✅ Auto-posting zaplanowane dla wydarzenia {event.id} (Task ID: {social_task.id})")
                except Exception as e:
                    print(f"⚠️ Błąd planowania auto-posting dla wydarzenia {event.id}: {e}")
            
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
            
            # Ponownie zaplanuj przypomnienia po aktualizacji wydarzenia - NOWY SYSTEM v2
            # RESETUJ flagę i usuń stare emaile, aby zaplanować nowe
            event.reminders_scheduled = False
            
            # Usuń wszystkie stare emaile dla tego wydarzenia
            from app.models import EmailQueue
            old_emails = EmailQueue.query.filter_by(event_id=event_id).all()
            if old_emails:
                print(f"🗑️ Usuwam {len(old_emails)} starych emaili przed ponownym planowaniem")
                for email in old_emails:
                    db.session.delete(email)
                db.session.commit()
            
            # Teraz zaplanuj nowe przypomnienia
            from app.services.email_v2 import EmailManager
            email_manager = EmailManager()
            success, message = email_manager.send_event_reminders(event_id)
            if success:
                print(f"✅ Ponownie zaplanowano przypomnienia v2 dla wydarzenia: {title}")
            else:
                print(f"⚠️ Błąd ponownego planowania przypomnień v2: {message}")
            
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
            
            # Check if event is archived - prevent deletion
            if event.is_archived:
                return {
                    'success': False,
                    'error': f'Nie można usunąć zarchiwizowanego wydarzenia: {event.title}'
                }
            
            # Check if there are registrations
            registrations_count = User.query.filter_by(
                event_id=event_id,
                account_type='event_registration'
            ).count()
            if registrations_count > 0:
                return {
                    'success': False,
                    'error': f'Nie można usunąć wydarzenia z {registrations_count} rejestracjami'
                }
            
            # Clean up related groups and cancel Celery tasks before deleting event
            from app.services.group_manager import GroupManager
            from app.services.celery_cleanup import CeleryCleanupService
            
            group_manager = GroupManager()
            celery_cleanup = CeleryCleanupService()
            
            # 1. Cancel all scheduled Celery tasks for this event
            cancelled_tasks = celery_cleanup.cancel_event_tasks(event_id)
            print(f"🚫 Anulowano {cancelled_tasks} zadań Celery dla wydarzenia {event_id}")
            
            # 2. Clean up event groups
            success, message = group_manager.cleanup_event_groups(event_id)
            if success:
                print(f"🧹 {message}")
            else:
                print(f"❌ Błąd czyszczenia grup: {message}")
            
            # 3. Delete event groups
            success, message = group_manager.delete_event_groups(event_id)
            if success:
                print(f"🗑️ {message}")
            else:
                print(f"❌ Błąd usuwania grup: {message}")
            
            # 4. Delete the event
            db.session.delete(event)
            db.session.commit()
            
            # 5. Clean up any orphaned groups (safety measure)
            success, message = group_manager.cleanup_orphaned_groups()
            if success and "Usunięto" in message:
                print(f"🧹 {message}")
            
            return {
                'success': True,
                'message': f'Wydarzenie zostało usunięte pomyślnie. Anulowano {cancelled_tasks} zadań Celery.'
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
            query = User.query.filter_by(account_type='event_registration')
            
            if event_id:
                query = query.filter_by(event_id=event_id)
            
            # Note: status filtering removed as it's not applicable to users
            # Users are either registered (account_type='event_registration') or not
            
            if search:
                query = query.filter(
                    User.first_name.ilike(f'%{search}%') |
                    User.email.ilike(f'%{search}%')
                )
            
            registrations = query.order_by(User.created_at.desc()).paginate(
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
            existing_user = User.query.filter_by(
                event_id=event_id,
                account_type='event_registration',
                id=user_id
            ).first()
            
            if existing_user:
                return {
                    'success': False,
                    'error': 'Jesteś już zarejestrowany na to wydarzenie'
                }
            
            # Check if event is full
            current_registrations = User.query.filter_by(
                event_id=event_id,
                account_type='event_registration'
            ).count()
            if event.max_participants and current_registrations >= event.max_participants:
                return {
                    'success': False,
                    'error': 'Wydarzenie jest pełne'
                }
            
            # Update user to register for event
            user = User.query.get(user_id)
            user.account_type = 'event_registration'
            
            # Create EventRegistration entry
            from app.models import EventRegistration
            EventRegistration.register_user(
                user_id=user_id,
                event_id=event_id,
                registration_source='admin'
            )
            
            # Log the registration in UserHistory (event participation history)
            UserHistory.log_event_registration(
                user_id=user_id,
                event_id=event_id,
                was_club_member=user.club_member or False
            )
            
            # Log the action in UserLogs (user activity logs)
            UserLogs.log_event_registration(
                user_id=user_id,
                event_id=event_id,
                event_title=event.title
            )
            
            # Update stats
            Stats.increment('event_registrations', related_id=event_id, related_type='event')
            Stats.increment('total_registrations')
            
            db.session.commit()
            
            return {
                'success': True,
                'user': user,
                'message': 'Zostałeś zarejestrowany na wydarzenie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def cancel_registration(user_id, event_id):
        """Cancel event registration"""
        try:
            user = User.query.filter_by(
                id=user_id,
                event_id=event_id,
                account_type='event_registration'
            ).first()
            
            if not user:
                return {
                    'success': False,
                    'error': 'Rejestracja nie została znaleziona'
                }
            
            # Get event title for logging
            event = EventSchedule.query.get(event_id)
            event_title = event.title if event else f'Event {event_id}'
            
            # Unregister from event
            from app.models import EventRegistration
            EventRegistration.unregister_user(user_id, event_id)
            
            # Reset user account type
            user.account_type = 'user'
            
            # Log the cancellation in user history
            UserHistory.log_event_cancellation(
                user_id=user_id,
                event_id=event_id,
                event_title=event_title
            )
            
            # Update stats
            Stats.decrement('event_registrations', related_id=event_id, related_type='event')
            Stats.decrement('total_registrations')
            
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
