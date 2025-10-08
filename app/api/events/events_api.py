"""
Events API - event management
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import EventSchedule, User, db
from app.utils.auth_utils import admin_required, admin_required_api
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create Events API blueprint
events_api_bp = Blueprint('events_main_api', __name__)

@events_api_bp.route('/events', methods=['GET'])
@login_required
def get_events():
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
        logger.error(f"❌ Błąd pobierania wydarzeń: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/event-schedule', methods=['GET'])
@login_required
def get_event_schedule():
    """Get event schedule with filtering and pagination"""
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
        logger.error(f"❌ Błąd pobierania harmonogramu wydarzeń: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/event-schedule', methods=['POST'])
@login_required
@admin_required_api
def create_event():
    """Create new event"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'event_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Pole {field} jest wymagane'
                }), 400
        
        # Parse event date
        event_date = datetime.fromisoformat(data['event_date'].replace('Z', '+00:00'))
        
        # Create event
        event = EventSchedule(
            title=data['title'],
            description=data.get('description', ''),
            event_type=data.get('event_type', 'workshop'),
            event_date=event_date,
            end_date=datetime.fromisoformat(data['end_date'].replace('Z', '+00:00')) if data.get('end_date') else None,
            location=data.get('location', ''),
            meeting_link=data.get('meeting_link', ''),
            max_participants=data.get('max_participants', 0),
            is_active=data.get('is_active', True),
            is_published=data.get('is_published', False),
            is_archived=data.get('is_archived', False)
        )
        
        db.session.add(event)
        db.session.commit()
        
        # Automatycznie utwórz grupę dla wydarzenia
        try:
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            group_manager.create_event_group(event.id, event.title)
            logger.info(f"✅ Utworzono grupę dla wydarzenia {event.id}")
        except Exception as e:
            logger.warning(f"⚠️ Błąd tworzenia grupy dla wydarzenia: {e}")
        
        # Automatycznie zaplanuj przypomnienia o wydarzeniu
        try:
            from app.services.email_v2 import EmailManager
            email_manager = EmailManager()
            success, message = email_manager.send_event_reminders(event.id)
            if success:
                logger.info(f"✅ Zaplanowano przypomnienia dla wydarzenia: {event.title}")
            else:
                logger.warning(f"⚠️ Błąd planowania przypomnień: {message}")
        except Exception as e:
            logger.warning(f"⚠️ Błąd planowania przypomnień: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Wydarzenie zostało utworzone',
            'event_id': event.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd tworzenia wydarzenia: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/event-schedule/<int:event_id>', methods=['GET'])
@login_required
def get_event(event_id):
    """Get single event"""
    try:
        event = EventSchedule.query.get_or_404(event_id)
        
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
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania wydarzenia: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/event-schedule/<int:event_id>', methods=['PUT'])
@login_required
@admin_required_api
def update_event(event_id):
    """Update event"""
    try:
        event = EventSchedule.query.get_or_404(event_id)
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'event_type' in data:
            event.event_type = data['event_type']
        if 'event_date' in data:
            event.event_date = datetime.fromisoformat(data['event_date'].replace('Z', '+00:00'))
        if 'end_date' in data and data['end_date']:
            event.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
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
        if 'is_archived' in data:
            event.is_archived = data['is_archived']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Wydarzenie zostało zaktualizowane'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd aktualizacji wydarzenia: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/event-schedule/<int:event_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_event(event_id):
    """Delete event"""
    try:
        event = EventSchedule.query.get_or_404(event_id)
        
        db.session.delete(event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Wydarzenie zostało usunięte'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania wydarzenia: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/events/register', methods=['POST'])
@login_required
def register_for_event():
    """Register user for event"""
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        
        if not event_id:
            return jsonify({
                'success': False,
                'message': 'ID wydarzenia jest wymagane'
            }), 400
        
        event = EventSchedule.query.get(event_id)
        if not event:
            return jsonify({
                'success': False,
                'message': 'Wydarzenie nie zostało znalezione'
            }), 404
        
        # Check if user is already registered (implement based on your registration model)
        # This is a placeholder - you'll need to implement actual registration logic
        
        return jsonify({
            'success': True,
            'message': 'Zostałeś zarejestrowany na wydarzenie'
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd rejestracji na wydarzenie: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/events/archive-ended', methods=['POST'])
@login_required
@admin_required_api
def archive_ended_events():
    """Archive events that have ended"""
    try:
        from datetime import datetime
        
        now = datetime.utcnow()
        ended_events = EventSchedule.query.filter(
            EventSchedule.end_date < now,
            EventSchedule.is_archived == False
        ).all()
        
        archived_count = 0
        for event in ended_events:
            event.is_archived = True
            archived_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Zarchiwizowano {archived_count} zakończonych wydarzeń'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd archiwizacji wydarzeń: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@events_api_bp.route('/bulk-delete/events', methods=['POST'])
@login_required
@admin_required_api
def bulk_delete_events():
    """Bulk delete events"""
    try:
        data = request.get_json()
        event_ids = data.get('event_ids', [])
        
        if not event_ids:
            return jsonify({
                'success': False,
                'message': 'Brak wydarzeń do usunięcia'
            }), 400
        
        events = EventSchedule.query.filter(EventSchedule.id.in_(event_ids)).all()
        
        for event in events:
            db.session.delete(event)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {len(events)} wydarzeń'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd masowego usuwania wydarzeń: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
