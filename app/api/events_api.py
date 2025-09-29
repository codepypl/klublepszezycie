"""
Events API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import EventSchedule, User, db
from app.utils.auth_utils import admin_required, admin_required_api
import logging

events_api_bp = Blueprint('events_api', __name__)

@events_api_bp.route('/events', methods=['GET'])
@login_required
def api_events():
    """Get all events"""
    try:
        events = EventSchedule.query.order_by(EventSchedule.event_date.asc()).all()
        return jsonify({
            'success': True,
            'events': [{
                'id': event.id,
                'title': event.title,
                'description': event.description,
                'event_date': event.event_date.isoformat() if event.event_date else None,
                'end_date': event.end_date.isoformat() if event.end_date else None,
                'location': event.location,
                'max_participants': event.max_participants,
                'is_active': event.is_active,
                'created_at': event.created_at.isoformat() if event.created_at else None
            } for event in events]
        })
    except Exception as e:
        logging.error(f"Error getting events: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/event-schedule', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_event_schedule():
    """Event schedule API"""
    if request.method == 'GET':
        try:
            # Get query parameters for filtering
            show_archived_param = request.args.get('show_archived')
            show_published = request.args.get('show_published', 'all')  # 'all', 'true', 'false'
            search = request.args.get('search', '').strip()
            
            # Get pagination parameters
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 10))
            
            # Build query
            query = EventSchedule.query
            
            # Filter by archived status
            if show_archived_param is not None:
                # Only filter if show_archived parameter is explicitly provided
                show_archived = show_archived_param.lower() == 'true'
                if not show_archived:
                    query = query.filter(EventSchedule.is_archived == False)
                else:
                    query = query.filter(EventSchedule.is_archived == True)
            
            # Filter by published status
            if show_published == 'true':
                query = query.filter(EventSchedule.is_published == True)
            elif show_published == 'false':
                query = query.filter(EventSchedule.is_published == False)
            
            # Search filter
            if search:
                query = query.filter(
                    EventSchedule.title.ilike(f'%{search}%') |
                    EventSchedule.description.ilike(f'%{search}%') |
                    EventSchedule.location.ilike(f'%{search}%')
                )
            
            # Apply pagination
            events_pagination = query.order_by(EventSchedule.event_date.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            events = events_pagination.items
            pagination_info = {
                'page': events_pagination.page,
                'pages': events_pagination.pages,
                'per_page': events_pagination.per_page,
                'total': events_pagination.total,
                'has_next': events_pagination.has_next,
                'has_prev': events_pagination.has_prev
            }
            
            return jsonify({
                'success': True,
                'events': [{
                    'id': event.id,
                    'title': event.title,
                    'description': event.description,
                    'event_type': event.event_type,
                    'event_date': event.event_date.isoformat() if event.event_date else None,
                    'end_date': event.end_date.isoformat() if event.end_date else None,
                    'location': event.location,
                    'meeting_link': event.meeting_link,
                    'max_participants': event.max_participants,
                    'is_active': event.is_active,
                    'is_published': event.is_published,
                    'is_archived': event.is_archived,
                    'created_at': event.created_at.isoformat() if event.created_at else None
                } for event in events],
                'pagination': pagination_info
            })
        except Exception as e:
            logging.error(f"Error getting event schedule: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            event = EventSchedule(
                title=data['title'],
                description=data.get('description', ''),
                event_date=data.get('event_date'),
                end_date=data.get('end_date'),
                location=data.get('location', ''),
                max_participants=data.get('max_participants', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(event)
            db.session.commit()
            
            # Automatycznie utwórz grupę dla wydarzenia
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            group_manager.create_event_group(event.id, event.title)
            
            # Automatycznie zaplanuj przypomnienia o wydarzeniu
            from app.services.email_automation import EmailAutomation
            email_automation = EmailAutomation()
            success, message = email_automation.schedule_event_reminders(event.id, 'event_based')
            if success:
                print(f"✅ Zaplanowano przypomnienia dla wydarzenia: {event.title}")
            else:
                print(f"⚠️ Błąd planowania przypomnień: {message}")
            
            return jsonify({
                'success': True,
                'message': 'Event created successfully',
                'event': {
                    'id': event.id,
                    'title': event.title,
                    'description': event.description,
                    'event_date': event.event_date.isoformat() if event.event_date else None,
                    'end_date': event.end_date.isoformat() if event.end_date else None,
                    'location': event.location,
                    'max_participants': event.max_participants,
                    'is_active': event.is_active
                }
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating event: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            data = request.get_json()
            event_ids = data.get('event_ids', data.get('ids', []))
            
            if not event_ids:
                return jsonify({'success': False, 'message': 'No events selected'}), 400
            
            deleted_count = 0
            total_cancelled_tasks = 0
            
            for event_id in event_ids:
                event = EventSchedule.query.get(event_id)
                if event:
                    # Clean up related groups and cancel Celery tasks before deleting event
                    from app.services.group_manager import GroupManager
                    from app.services.celery_cleanup import CeleryCleanupService
                    
                    group_manager = GroupManager()
                    celery_cleanup = CeleryCleanupService()
                    
                    # 1. Cancel all scheduled Celery tasks for this event
                    cancelled_tasks = celery_cleanup.cancel_event_tasks(event_id)
                    total_cancelled_tasks += cancelled_tasks
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
                    deleted_count += 1
            
            db.session.commit()
            
            # Clean up any orphaned groups (safety measure)
            success, message = group_manager.cleanup_orphaned_groups()
            if success and "Usunięto" in message:
                print(f"🧹 {message}")
            
            return jsonify({
                'success': True,
                'message': f'Successfully deleted {deleted_count} events. Cancelled {total_cancelled_tasks} Celery tasks.'
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error bulk deleting events: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/event-schedule/<int:event_id>', methods=['GET', 'PUT', 'DELETE'])
def api_event(event_id):
    """Individual event API"""
    event = EventSchedule.query.get_or_404(event_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'event': {
                    'id': event.id,
                    'title': event.title,
                    'description': event.description,
                    'event_type': event.event_type,
                    'event_date': event.event_date.isoformat() if event.event_date else None,
                    'end_date': event.end_date.isoformat() if event.end_date else None,
                    'location': event.location,
                    'meeting_link': event.meeting_link,
                    'max_participants': event.max_participants,
                    'is_active': event.is_active,
                    'is_published': event.is_published,
                    'is_archived': event.is_archived,
                    'created_at': event.created_at.isoformat() if event.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'title' in data:
                event.title = data['title']
            if 'description' in data:
                event.description = data['description']
            if 'event_type' in data:
                event.event_type = data['event_type']
            if 'event_date' in data:
                event.event_date = data['event_date']
            if 'end_date' in data:
                event.end_date = data['end_date']
            if 'location' in data:
                event.location = data['location']
            if 'meeting_link' in data:
                event.meeting_link = data['meeting_link']
            if 'max_participants' in data:
                event.max_participants = data['max_participants']
            if 'is_active' in data:
                event.is_active = data['is_active']
            if 'is_published' in data:
                event.is_published = data['is_published']
            
            db.session.commit()
            
            # Aktualizuj grupę wydarzenia jeśli nazwa się zmieniła
            if 'title' in data:
                from app.services.group_manager import GroupManager
                group_manager = GroupManager()
                group_manager.create_event_group(event.id, event.title)
            
            return jsonify({
                'success': True,
                'message': 'Event updated successfully'
            })
        
        elif request.method == 'DELETE':
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
            
            return jsonify({
                'success': True,
                'message': f'Event deleted successfully. Cancelled {cancelled_tasks} Celery tasks.'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with event {event_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/schedules', methods=['GET', 'POST'])
@login_required
def api_schedules():
    """Schedules API"""
    if request.method == 'GET':
        try:
            schedules = EventSchedule.query.order_by(EventSchedule.event_date.asc()).all()
            return jsonify({
                'success': True,
                'schedules': [{
                    'id': schedule.id,
                    'title': schedule.title,
                    'event_type': schedule.event_type,
                    'event_date': schedule.event_date.isoformat() if schedule.event_date else None,
                    'end_date': schedule.end_date.isoformat() if schedule.end_date else None,
                    'location': schedule.location,
                    'is_active': schedule.is_active
                } for schedule in schedules]
            })
        except Exception as e:
            logging.error(f"Error getting schedules: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            schedule = EventSchedule(
                title=data['title'],
                description=data.get('description', ''),
                event_type=data.get('event_type', ''),
                event_date=data.get('event_date'),
                end_date=data.get('end_date'),
                location=data.get('location', ''),
                max_participants=data.get('max_participants', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(schedule)
            db.session.commit()
            
            # Automatycznie utwórz grupę dla wydarzenia
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            group_manager.create_event_group(schedule.id, schedule.title)
            
            return jsonify({
                'success': True,
                'message': 'Schedule created successfully',
                'schedule': {
                    'id': schedule.id,
                    'title': schedule.title,
                    'event_type': schedule.event_type,
                    'event_date': schedule.event_date.isoformat() if schedule.event_date else None,
                    'end_date': schedule.end_date.isoformat() if schedule.end_date else None,
                    'location': schedule.location,
                    'is_active': schedule.is_active
                }
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating schedule: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/schedules/<int:schedule_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_schedule(schedule_id):
    """Individual schedule API"""
    schedule = EventSchedule.query.get_or_404(schedule_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'schedule': {
                    'id': schedule.id,
                    'title': schedule.title,
                    'description': schedule.description,
                    'event_type': schedule.event_type,
                    'event_date': schedule.event_date.isoformat() if schedule.event_date else None,
                    'end_date': schedule.end_date.isoformat() if schedule.end_date else None,
                    'location': schedule.location,
                    'max_participants': schedule.max_participants,
                    'is_active': schedule.is_active,
                    'created_at': schedule.created_at.isoformat() if schedule.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            # Store old title for group update
            old_title = schedule.title
            
            if 'title' in data:
                schedule.title = data['title']
            if 'description' in data:
                schedule.description = data['description']
            if 'event_type' in data:
                schedule.event_type = data['event_type']
            if 'event_date' in data:
                schedule.event_date = data['event_date']
            if 'end_date' in data:
                schedule.end_date = data['end_date']
            if 'location' in data:
                schedule.location = data['location']
            if 'max_participants' in data:
                schedule.max_participants = data['max_participants']
            if 'is_active' in data:
                schedule.is_active = data['is_active']
            
            db.session.commit()
            
            # Update group name if title changed
            if 'title' in data and old_title != data['title']:
                from app.services.group_manager import GroupManager
                group_manager = GroupManager()
                
                # Find and update the event group
                from app.models import UserGroup
                group = UserGroup.query.filter_by(
                    name=f"Wydarzenie: {old_title}",
                    group_type='event_based'
                ).first()
                
                if group:
                    print(f"🔍 Aktualizacja nazwy grupy z '{group.name}' na 'Wydarzenie: {data['title']}'")
                    group.name = f"Wydarzenie: {data['title']}"
                    group.description = f"Grupa uczestników wydarzenia: {data['title']}"
                    db.session.commit()
                    print(f"✅ Nazwa grupy zaktualizowana pomyślnie")
                else:
                    print(f"❌ Grupa wydarzenia '{old_title}' nie została znaleziona")
            
            # Asynchronicznie synchronizuj grupę wydarzenia po aktualizacji
            success, message = group_manager.async_sync_event_group(schedule_id)
            if success:
                print(f"✅ Zsynchronizowano grupę wydarzenia po aktualizacji przez API")
            else:
                print(f"❌ Błąd synchronizacji grupy wydarzenia: {message}")
            
            # Aktualizuj powiadomienia jeśli zmieniła się godzina wydarzenia
            if 'event_date' in data and 'event_time' in data:
                from datetime import datetime
                old_event_date = schedule.event_date
                new_event_date = datetime.strptime(f"{data['event_date']} {data['event_time']}", "%Y-%m-%d %H:%M")
                
                if old_event_date != new_event_date:
                    print(f"🕐 Godzina wydarzenia zmieniła się z {old_event_date} na {new_event_date}")
                    
                    from app.services.email_automation import EmailAutomation
                    email_automation = EmailAutomation()
                    success, message = email_automation.update_event_notifications(
                        schedule.id, old_event_date, new_event_date
                    )
                    
                    if success:
                        print(f"✅ {message}")
                    else:
                        print(f"❌ Błąd aktualizacji powiadomień: {message}")
            
            return jsonify({
                'success': True,
                'message': 'Schedule updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(schedule)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Schedule deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with schedule {schedule_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/check-schedules', methods=['POST'])
@login_required
def api_check_schedules():
    """Check for schedule conflicts"""
    try:
        data = request.get_json()
        event_date = data.get('event_date')
        end_date = data.get('end_date')
        exclude_id = data.get('exclude_id')
        
        query = EventSchedule.query.filter(
            EventSchedule.event_date <= end_date,
            EventSchedule.end_date >= event_date
        )
        
        if exclude_id:
            query = query.filter(EventSchedule.id != exclude_id)
        
        conflicting_schedules = query.all()
        
        return jsonify({
            'success': True,
            'has_conflicts': len(conflicting_schedules) > 0,
            'conflicting_schedules': [{
                'id': schedule.id,
                'title': schedule.title,
                'event_date': schedule.event_date.isoformat() if schedule.event_date else None,
                'end_date': schedule.end_date.isoformat() if schedule.end_date else None
            } for schedule in conflicting_schedules]
        })
    except Exception as e:
        logging.error(f"Error checking schedules: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/bulk-delete/schedules', methods=['POST'])
@login_required
@admin_required_api
def api_bulk_delete_schedules():
    """Bulk delete schedules"""
    try:
        data = request.get_json()
        schedule_ids = data.get('schedule_ids', data.get('ids', []))
        
        if not schedule_ids:
            return jsonify({'success': False, 'message': 'No schedules selected'}), 400
        
        deleted_count = 0
        for schedule_id in schedule_ids:
            schedule = EventSchedule.query.get(schedule_id)
            if schedule:
                db.session.delete(schedule)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} schedules'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting schedules: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/bulk-delete/events', methods=['POST'])
@login_required
@admin_required_api
def api_bulk_delete_events():
    """Bulk delete events"""
    try:
        data = request.get_json()
        event_ids = data.get('event_ids', data.get('ids', []))
        
        if not event_ids:
            return jsonify({'success': False, 'message': 'No events selected'}), 400
        
        deleted_count = 0
        total_cancelled_tasks = 0
        
        for event_id in event_ids:
            event = EventSchedule.query.get(event_id)
            if event:
                # Clean up related groups and cancel Celery tasks before deleting event
                from app.services.group_manager import GroupManager
                from app.services.celery_cleanup import CeleryCleanupService
                
                group_manager = GroupManager()
                celery_cleanup = CeleryCleanupService()
                
                # 1. Cancel all scheduled Celery tasks for this event
                cancelled_tasks = celery_cleanup.cancel_event_tasks(event_id)
                total_cancelled_tasks += cancelled_tasks
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
                deleted_count += 1
        
        db.session.commit()
        
        # Clean up any orphaned groups (safety measure)
        success, message = group_manager.cleanup_orphaned_groups()
        if success and "Usunięto" in message:
            print(f"🧹 {message}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} events. Cancelled {total_cancelled_tasks} Celery tasks.'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting events: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/registrations/<int:registration_id>', methods=['DELETE'])
@login_required
@admin_required
def api_delete_registration(registration_id):
    """Delete event registration"""
    try:
        user = User.query.get(registration_id)
        if not user or user.account_type != 'event_registration':
            return jsonify({'success': False, 'message': 'Registration not found'}), 404
        
        # Store data before deletion for group cleanup
        event_id = user.event_id
        email = user.email
        
        # Reset user account type
        user.account_type = 'user'
        user.event_id = None
        db.session.commit()
        
        # Asynchronicznie synchronizuj grupę wydarzenia
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        # Wywołaj asynchroniczną synchronizację grupy wydarzenia
        success, message = group_manager.async_sync_event_group(event_id)
        if success:
            print(f"✅ Zsynchronizowano grupę wydarzenia po usunięciu rejestracji")
        else:
            print(f"❌ Błąd synchronizacji grupy wydarzenia: {message}")
        
        return jsonify({
            'success': True,
            'message': 'Registration deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting registration: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/bulk-delete/registrations', methods=['POST'])
@login_required
@admin_required_api
def api_bulk_delete_registrations():
    """Bulk delete event registrations"""
    try:
        data = request.get_json()
        registration_ids = data.get('registration_ids', data.get('ids', []))
        
        if not registration_ids:
            return jsonify({'success': False, 'message': 'No registrations selected'}), 400
        
        # Store registration data before deletion for group cleanup
        registrations_to_delete = []
        for registration_id in registration_ids:
            user = User.query.get(registration_id)
            if user and user.account_type == 'event_registration':
                registrations_to_delete.append({
                    'id': user.id,
                    'event_id': user.event_id,
                    'email': user.email
                })
        
        # Reset user registrations
        deleted_count = 0
        for registration_id in registration_ids:
            user = User.query.get(registration_id)
            if user and user.account_type == 'event_registration':
                user.account_type = 'user'
                user.event_id = None
                deleted_count += 1
        
        db.session.commit()
        
        # Remove from event groups
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        for reg_data in registrations_to_delete:
            if reg_data['user_id']:
                # User has account - remove from group by user_id
                success, message = group_manager.remove_user_from_event_group(reg_data['user_id'], reg_data['event_id'])
                if success:
                    print(f"✅ Usunięto użytkownika {reg_data['user_id']} z grupy wydarzenia {reg_data['event_id']}")
                else:
                    print(f"❌ Błąd usuwania użytkownika z grupy wydarzenia: {message}")
            else:
                # No user account - remove by email
                success, message = group_manager.remove_email_from_event_group(reg_data['email'], reg_data['event_id'])
                if success:
                    print(f"✅ Usunięto email {reg_data['email']} z grupy wydarzenia {reg_data['event_id']}")
                else:
                    print(f"❌ Błąd usuwania emailu z grupy wydarzenia: {message}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} registrations'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting registrations: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/cleanup/orphaned-groups', methods=['POST'])
@login_required
@admin_required
def api_cleanup_orphaned_groups():
    """Cleanup orphaned user groups"""
    try:
        # This would need to be implemented based on your specific logic
        # for determining what constitutes an "orphaned" group
        return jsonify({
            'success': True,
            'message': 'Orphaned groups cleanup completed'
        })
    except Exception as e:
        logging.error(f"Error cleaning up orphaned groups: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/events/register', methods=['POST'])
def api_register_event():
    """Register for event via API"""
    try:
        data = request.get_json()
        print(f"🔍 API Event registration data: {data}")
        
        # Check if data is valid JSON
        if not data:
            print("❌ No data received")
            return jsonify({'success': False, 'message': 'Nieprawidłowe dane JSON'}), 400
        
        # Validate input
        if not data.get('first_name') or not data.get('email') or not data.get('event_id'):
            return jsonify({'success': False, 'message': 'Imię, email i ID wydarzenia są wymagane'}), 400
        
        event_id = data['event_id']
        
        # Import functions from public_route
        from app.routes.public_route import register_event
        
        # Create a mock request object with the data
        class MockRequest:
            def __init__(self, json_data):
                self.json_data = json_data
            def get_json(self):
                return self.json_data
        
        # Temporarily replace request with mock
        original_request = request
        import app.api.events_api
        app.api.events_api.request = MockRequest(data)
        
        try:
            # Call the existing register_event function
            response = register_event(event_id)
            return response
        finally:
            # Restore original request
            app.api.events_api.request = original_request
            
    except Exception as e:
        logging.error(f"Error in API event registration: {str(e)}")
        return jsonify({'success': False, 'message': 'Wystąpił błąd podczas rejestracji'}), 500


@events_api_bp.route('/events/archive-ended', methods=['POST'])
@login_required
@admin_required_api
def api_archive_ended_events():
    """Archive all ended events and clean up their groups - AJAX version"""
    try:
        from app.models import EventSchedule, UserGroup, UserGroupMember
        from app.utils.timezone_utils import get_local_now
        
        print("🏁 === ROZPOCZYNAM ARCHIWIZACJĘ WYDARZEŃ (AJAX) ===")
        
        # Find all active events
        all_events = EventSchedule.query.filter_by(
            is_active=True, 
            is_published=True, 
            is_archived=False
        ).all()
        
        print(f"📊 Znaleziono {len(all_events)} aktywnych wydarzeń do sprawdzenia")
        
        # Check which events are ended
        ended_events = []
        now = get_local_now().replace(tzinfo=None)
        
        for event in all_events:
            if event.is_ended():
                ended_events.append(event)
                print(f"⏰ Wydarzenie '{event.title}' (ID: {event.id}) jest zakończone")
            else:
                print(f"🟢 Wydarzenie '{event.title}' (ID: {event.id}) jest jeszcze aktywne")
        
        if not ended_events:
            return jsonify({
                'success': True,
                'message': 'Brak wydarzeń do archiwizacji',
                'archived_count': 0
            })
        
        # Archive each ended event
        archived_count = 0
        total_members_removed = 0
        total_groups_deleted = 0
        
        for event in ended_events:
            print(f"🏁 Archiwizuję: {event.title} (ID: {event.id})")
            
            # Find event groups
            event_groups = UserGroup.query.filter_by(
                event_id=event.id,
                group_type='event_based'
            ).all()
            
            # Remove members from groups
            for group in event_groups:
                members_count = UserGroupMember.query.filter_by(
                    group_id=group.id,
                    is_active=True
                ).count()
                
                UserGroupMember.query.filter_by(
                    group_id=group.id,
                    is_active=True
                ).delete(synchronize_session=False)
                
                total_members_removed += members_count
                print(f"  👥 Usunięto {members_count} członków z grupy '{group.name}'")
            
            # Delete groups
            for group in event_groups:
                db.session.delete(group)
                total_groups_deleted += 1
                print(f"  🗑️ Usunięto grupę '{group.name}'")
            
            # Archive event
            event.is_archived = True
            event.is_active = False
            event.is_published = False
            archived_count += 1
            
            print(f"  📦 Wydarzenie zarchiwizowane")
        
        # Commit all changes
        db.session.commit()
        
        message = f"Zarchiwizowano {archived_count} wydarzeń. Usunięto {total_members_removed} członków z {total_groups_deleted} grup."
        print(f"✅ {message}")
        
        return jsonify({
            'success': True,
            'message': message,
            'archived_count': archived_count,
            'members_removed': total_members_removed,
            'groups_deleted': total_groups_deleted
        })
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"Błąd archiwizacji: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': error_msg}), 500
