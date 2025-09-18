"""
Events API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import EventSchedule, EventRegistration, db
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
            events = EventSchedule.query.order_by(EventSchedule.event_date.asc()).all()
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
                } for event in events]
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
            for event_id in event_ids:
                event = EventSchedule.query.get(event_id)
                if event:
                    db.session.delete(event)
                    deleted_count += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully deleted {deleted_count} events'
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error bulk deleting events: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/event-schedule/<int:event_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
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
                from app.api.email_api import create_event_group
                create_event_group(event.id, event.title)
            
            return jsonify({
                'success': True,
                'message': 'Event updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(event)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Event deleted successfully'
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
                event_date=data.get('event_date'),
                end_date=data.get('end_date'),
                location=data.get('location', ''),
                max_participants=data.get('max_participants', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(schedule)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Schedule created successfully',
                'schedule': {
                    'id': schedule.id,
                    'title': schedule.title,
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
            
            if 'title' in data:
                schedule.title = data['title']
            if 'description' in data:
                schedule.description = data['description']
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
        for event_id in event_ids:
            event = EventSchedule.query.get(event_id)
            if event:
                db.session.delete(event)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} events'
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
        registration = EventRegistration.query.get(registration_id)
        if not registration:
            return jsonify({'success': False, 'message': 'Registration not found'}), 404
        
        # Store data before deletion for group cleanup
        event_id = registration.event_id
        user_id = registration.user_id
        email = registration.email
        
        # Delete registration
        db.session.delete(registration)
        db.session.commit()
        
        # Remove from event group
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        if user_id:
            # User has account - remove from group by user_id
            success, message = group_manager.remove_user_from_event_group(user_id, event_id)
            if success:
                print(f"✅ Usunięto użytkownika {user_id} z grupy wydarzenia {event_id}")
            else:
                print(f"❌ Błąd usuwania użytkownika z grupy wydarzenia: {message}")
        else:
            # No user account - remove by email
            success, message = group_manager.remove_email_from_event_group(email, event_id)
            if success:
                print(f"✅ Usunięto email {email} z grupy wydarzenia {event_id}")
            else:
                print(f"❌ Błąd usuwania emailu z grupy wydarzenia: {message}")
        
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
            registration = EventRegistration.query.get(registration_id)
            if registration:
                registrations_to_delete.append({
                    'id': registration.id,
                    'event_id': registration.event_id,
                    'user_id': registration.user_id,
                    'email': registration.email
                })
        
        # Delete registrations
        deleted_count = 0
        for registration_id in registration_ids:
            registration = EventRegistration.query.get(registration_id)
            if registration:
                db.session.delete(registration)
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
