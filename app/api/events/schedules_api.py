"""
Events Schedules API - schedule management
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import EventSchedule, User, db
from app.utils.auth_utils import admin_required, admin_required_api
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create Schedules API blueprint
schedules_api_bp = Blueprint('events_schedules_main_api', __name__)

@schedules_api_bp.route('/schedules', methods=['GET'])
@login_required
def get_schedules():
    """Get all schedules"""
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
        logger.error(f"❌ Błąd pobierania harmonogramów: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@schedules_api_bp.route('/schedules', methods=['POST'])
@login_required
@admin_required_api
def create_schedule():
    """Create new schedule"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({
                'success': False,
                'message': 'Tytuł wydarzenia jest wymagany'
            }), 400
        
        schedule = EventSchedule(
            title=data['title'],
            description=data.get('description', ''),
            event_type=data.get('event_type', 'workshop'),
            event_date=datetime.fromisoformat(data['event_date'].replace('Z', '+00:00')) if data.get('event_date') else None,
            end_date=datetime.fromisoformat(data['end_date'].replace('Z', '+00:00')) if data.get('end_date') else None,
            location=data.get('location', ''),
            max_participants=data.get('max_participants', 0),
            is_active=data.get('is_active', True),
            is_published=data.get('is_published', False)
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        # Automatycznie utwórz grupę dla wydarzenia
        try:
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            group_manager.create_event_group(schedule.id, schedule.title)
            logger.info(f"✅ Utworzono grupę dla wydarzenia {schedule.id}")
        except Exception as e:
            logger.warning(f"⚠️ Błąd tworzenia grupy dla wydarzenia: {e}")
        
        # Automatycznie zaplanuj przypomnienia o wydarzeniu
        try:
            from app.services.email_v2 import EmailManager
            email_manager = EmailManager()
            success, message = email_manager.send_event_reminders(schedule.id)
            if success:
                logger.info(f"✅ Zaplanowano przypomnienia dla wydarzenia: {schedule.title}")
            else:
                logger.warning(f"⚠️ Błąd planowania przypomnień: {message}")
        except Exception as e:
            logger.warning(f"⚠️ Błąd planowania przypomnień: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Harmonogram został utworzony pomyślnie',
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
        logger.error(f"❌ Błąd tworzenia harmonogramu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@schedules_api_bp.route('/schedules/<int:schedule_id>', methods=['GET'])
@login_required
def get_schedule(schedule_id):
    """Get single schedule"""
    try:
        schedule = EventSchedule.query.get_or_404(schedule_id)
        
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
                'meeting_link': schedule.meeting_link,
                'max_participants': schedule.max_participants,
                'is_active': schedule.is_active,
                'is_published': schedule.is_published,
                'is_archived': schedule.is_archived,
                'created_at': schedule.created_at.isoformat() if schedule.created_at else None,
                'updated_at': schedule.updated_at.isoformat() if schedule.updated_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania harmonogramu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@schedules_api_bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
@login_required
@admin_required_api
def update_schedule(schedule_id):
    """Update schedule"""
    try:
        schedule = EventSchedule.query.get_or_404(schedule_id)
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            schedule.title = data['title']
        if 'description' in data:
            schedule.description = data['description']
        if 'event_type' in data:
            schedule.event_type = data['event_type']
        if 'event_date' in data:
            schedule.event_date = datetime.fromisoformat(data['event_date'].replace('Z', '+00:00'))
        if 'end_date' in data and data['end_date']:
            schedule.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        if 'location' in data:
            schedule.location = data['location']
        if 'meeting_link' in data:
            schedule.meeting_link = data['meeting_link']
        if 'max_participants' in data:
            schedule.max_participants = data['max_participants']
        if 'is_active' in data:
            schedule.is_active = data['is_active']
        if 'is_published' in data:
            schedule.is_published = data['is_published']
        if 'is_archived' in data:
            schedule.is_archived = data['is_archived']
        
        schedule.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Harmonogram został zaktualizowany'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd aktualizacji harmonogramu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@schedules_api_bp.route('/schedules/<int:schedule_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_schedule(schedule_id):
    """Delete schedule"""
    try:
        schedule = EventSchedule.query.get_or_404(schedule_id)
        
        # Delete associated group if exists
        try:
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            group_manager.delete_event_group(schedule_id)
            logger.info(f"✅ Usunięto grupę dla wydarzenia {schedule_id}")
        except Exception as e:
            logger.warning(f"⚠️ Błąd usuwania grupy dla wydarzenia: {e}")
        
        db.session.delete(schedule)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Harmonogram został usunięty'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania harmonogramu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@schedules_api_bp.route('/check-schedules', methods=['POST'])
@login_required
@admin_required_api
def check_schedules():
    """Check for schedule conflicts"""
    try:
        data = request.get_json()
        event_date = datetime.fromisoformat(data['event_date'].replace('Z', '+00:00'))
        event_id = data.get('event_id')  # For updates, exclude current event
        
        # Check for overlapping schedules
        query = EventSchedule.query.filter(
            EventSchedule.event_date <= event_date,
            EventSchedule.end_date >= event_date
        )
        
        if event_id:
            query = query.filter(EventSchedule.id != event_id)
        
        conflicting_schedules = query.all()
        
        return jsonify({
            'success': True,
            'has_conflicts': len(conflicting_schedules) > 0,
            'conflicting_schedules': [{
                'id': schedule.id,
                'title': schedule.title,
                'event_date': schedule.event_date.isoformat(),
                'end_date': schedule.end_date.isoformat() if schedule.end_date else None,
                'location': schedule.location
            } for schedule in conflicting_schedules]
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd sprawdzania harmonogramów: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@schedules_api_bp.route('/bulk-delete/schedules', methods=['POST'])
@login_required
@admin_required_api
def bulk_delete_schedules():
    """Bulk delete schedules"""
    try:
        data = request.get_json()
        schedule_ids = data.get('schedule_ids', [])
        
        if not schedule_ids:
            return jsonify({
                'success': False,
                'message': 'Brak harmonogramów do usunięcia'
            }), 400
        
        schedules = EventSchedule.query.filter(EventSchedule.id.in_(schedule_ids)).all()
        
        # Delete associated groups
        try:
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            for schedule in schedules:
                group_manager.delete_event_group(schedule.id)
        except Exception as e:
            logger.warning(f"⚠️ Błąd usuwania grup wydarzeń: {e}")
        
        for schedule in schedules:
            db.session.delete(schedule)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {len(schedules)} harmonogramów'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd masowego usuwania harmonogramów: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@schedules_api_bp.route('/cleanup/orphaned-groups', methods=['POST'])
@login_required
@admin_required_api
def cleanup_orphaned_groups():
    """Clean up orphaned event groups"""
    try:
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        success, message = group_manager.cleanup_orphaned_event_groups()
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd czyszczenia osieroconych grup: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
