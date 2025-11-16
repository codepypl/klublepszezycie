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


def _parse_datetime_safe(datetime_str):
    """Safely parse datetime string, handling both ISO format and timezone"""
    if not datetime_str:
        return None
    if isinstance(datetime_str, datetime):
        return datetime_str
    if isinstance(datetime_str, str):
        if datetime_str.endswith('Z'):
            datetime_str = datetime_str.replace('Z', '+00:00')
        return datetime.fromisoformat(datetime_str)
    return datetime_str


def _parse_bool(value, default=None):
    """
    Safely parse boolean-like values coming from JSON or HTML forms.
    Accepts: True/False, 'true'/'false', 'on'/'off', '1'/'0'.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ('true', '1', 'on', 'yes'):
            return True
        if v in ('false', '0', 'off', 'no'):
            return False
    return default

@events_api_bp.route('/events', methods=['GET'])
@login_required
def get_events():
    """Get all events"""
    try:
        # Auto-archive ended events that are still active/published
        all_ended_events = EventSchedule.query.filter(
            EventSchedule.is_archived == False,
            (EventSchedule.is_active == True) | (EventSchedule.is_published == True)
        ).all()
        
        archived_count = 0
        for event in all_ended_events:
            if event.is_ended():
                success, message = event.archive()
                if success:
                    archived_count += 1
                    logger.info(f"🔄 Auto-archived ended event: {event.title} (ID: {event.id})")
        
        if archived_count > 0:
            logger.info(f"✅ Auto-archived {archived_count} ended event(s)")
        
        # Clean up groups for already archived events (safety check)
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        # Find all archived events that still have groups
        archived_events_with_groups = EventSchedule.query.filter(
            EventSchedule.is_archived == True
        ).all()
        
        for event in archived_events_with_groups:
            # Check if event has groups
            from app.models.user_groups_model import UserGroup
            event_groups = UserGroup.query.filter_by(
                event_id=event.id,
                group_type='event_based'
            ).all()
            
            if event_groups:
                logger.info(f"🧹 Found {len(event_groups)} groups for archived event {event.id}, cleaning up...")
                success, message = group_manager.delete_event_groups(event.id)
                if success:
                    logger.info(f"✅ {message}")
                else:
                    logger.warning(f"⚠️ {message}")
        
        # Clean up orphaned groups (groups with event_id=None or event_id pointing to non-existent/archived event)
        success, message = group_manager.cleanup_orphaned_groups()
        if success and "Usunięto" in message:
            logger.info(f"🧹 {message}")
        
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
        
        # Auto-archive ended events that are still active/published
        # Check all events (not just paginated ones) to ensure we catch all ended events
        # Find all ended events that are still active and/or published
        all_ended_events = EventSchedule.query.filter(
            EventSchedule.is_archived == False,
            (EventSchedule.is_active == True) | (EventSchedule.is_published == True)
        ).all()
        
        archived_count = 0
        for event in all_ended_events:
            if event.is_ended():
                success, message = event.archive()
                if success:
                    archived_count += 1
                    logger.info(f"🔄 Auto-archived ended event: {event.title} (ID: {event.id})")
        
        if archived_count > 0:
            logger.info(f"✅ Auto-archived {archived_count} ended event(s)")
            # Refresh query after archiving
            query = EventSchedule.query
        
        # Clean up groups for already archived events (safety check)
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        # Find all archived events that still have groups
        archived_events_with_groups = EventSchedule.query.filter(
            EventSchedule.is_archived == True
        ).all()
        
        for event in archived_events_with_groups:
            # Check if event has groups
            from app.models.user_groups_model import UserGroup
            event_groups = UserGroup.query.filter_by(
                event_id=event.id,
                group_type='event_based'
            ).all()
            
            if event_groups:
                logger.info(f"🧹 Found {len(event_groups)} groups for archived event {event.id}, cleaning up...")
                success, message = group_manager.delete_event_groups(event.id)
                if success:
                    logger.info(f"✅ {message}")
                else:
                    logger.warning(f"⚠️ {message}")
        
        # Clean up orphaned groups (groups with event_id=None or event_id pointing to non-existent/archived event)
        success, message = group_manager.cleanup_orphaned_groups()
        if success and "Usunięto" in message:
            logger.info(f"🧹 {message}")
        
        # Reapply filters after archiving (if query was refreshed)
        if archived_count > 0:
            if show_archived_param is not None:
                show_archived = show_archived_param.lower() == 'true'
                if not show_archived:
                    query = query.filter(EventSchedule.is_archived == False)
                else:
                    query = query.filter(EventSchedule.is_archived == True)
            
            if show_published == 'true':
                query = query.filter(EventSchedule.is_published == True)
            elif show_published == 'false':
                query = query.filter(EventSchedule.is_published == False)
            
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
                'event_url': event.get_event_url(),  # Zwracamy wynik get_event_url() dla kompatybilności
                'max_participants': event.max_participants,
                'hero_background': event.hero_background,
                'hero_background_type': event.hero_background_type,
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
        # Handle both JSON and FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Handle hero background upload (image or video)
        hero_background = None
        hero_background_type = data.get('hero_background_type', 'image')
        
        from werkzeug.utils import secure_filename
        import time
        import os
        from flask import current_app
        from app.utils.validation_utils import allowed_file
        
        # Check for image file upload
        if 'hero_background_image' in request.files and request.files['hero_background_image'].filename:
            file = request.files['hero_background_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{int(time.time())}_{filename}"
                
                # Create events-specific upload folder
                events_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'events')
                os.makedirs(events_upload_folder, exist_ok=True)
                
                file_path = os.path.join(events_upload_folder, filename)
                file.save(file_path)
                
                hero_background = f'/static/uploads/events/{filename}'
                logger.info(f"✅ Uploaded hero background image: {hero_background}")
        # Check for video file upload
        elif 'hero_background_video_file' in request.files and request.files['hero_background_video_file'].filename:
            file = request.files['hero_background_video_file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{int(time.time())}_{filename}"
                
                # Create events-specific upload folder
                events_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'events')
                os.makedirs(events_upload_folder, exist_ok=True)
                
                file_path = os.path.join(events_upload_folder, filename)
                file.save(file_path)
                
                hero_background = f'/static/uploads/events/{filename}'
                logger.info(f"✅ Uploaded hero background video: {hero_background}")
        elif data.get('hero_background'):
            # Use provided URL
            hero_background = data.get('hero_background')
        elif hero_background_type == 'video' and data.get('hero_background_video'):
            # Video URL
            hero_background = data.get('hero_background_video')
        elif hero_background_type == 'image' and data.get('hero_background_image_url'):
            # Image URL
            hero_background = data.get('hero_background_image_url')
        
        # Validate required fields
        required_fields = ['title', 'event_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Pole {field} jest wymagane'
                }), 400
        
        # Parse event date - handle both ISO format and datetime string
        event_date_str = data['event_date']
        if isinstance(event_date_str, str):
            # Remove 'Z' and replace with timezone if needed
            if event_date_str.endswith('Z'):
                event_date_str = event_date_str.replace('Z', '+00:00')
            event_date = datetime.fromisoformat(event_date_str)
        else:
            event_date = event_date_str
        
        # Create event
        event = EventSchedule(
            title=data['title'],
            description=data.get('description', ''),
            event_type=data.get('event_type', 'workshop'),
            event_date=event_date,
            end_date=_parse_datetime_safe(data.get('end_date')) if data.get('end_date') else None,
            location=data.get('location', ''),
            meeting_link=data.get('meeting_link', ''),
            event_url=data.get('event_url', ''),  # Zachowujemy dla kompatybilności
            max_participants=data.get('max_participants', 0),
            hero_background=hero_background,
            hero_background_type=hero_background_type,
            is_active=_parse_bool(data.get('is_active', True), True),
            is_published=_parse_bool(data.get('is_published', False), False),
            is_archived=_parse_bool(data.get('is_archived', False), False)
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
def get_event(event_id):
    """Get single event - public endpoint (no login required for public event registration)"""
    try:
        event = EventSchedule.query.get_or_404(event_id)
        
        # Only return published events for non-authenticated users
        from flask_login import current_user
        if not current_user.is_authenticated and not event.is_published:
            return jsonify({
                'success': False,
                'message': 'Wydarzenie nie zostało znalezione'
            }), 404
        
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
                'event_url': event.get_event_url(),  # Zwracamy wynik get_event_url() dla kompatybilności
                'max_participants': event.max_participants,
                'hero_background': event.hero_background,
                'hero_background_type': event.hero_background_type,
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
        
        # Handle both JSON and FormData
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Handle hero background removal
        if data.get('remove_hero_background') == 'true' or data.get('remove_hero_background') == True:
            # Delete old file if exists
            if event.hero_background and event.hero_background.startswith('/static/uploads/events/'):
                import os
                from flask import current_app
                old_image_path = event.hero_background.replace('/static/uploads/events/', '')
                old_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'events', old_image_path)
                if os.path.exists(old_full_path):
                    try:
                        os.remove(old_full_path)
                        logger.info(f"✅ Deleted old hero background file: {old_full_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not delete old hero background: {e}")
            event.hero_background = None
            event.hero_background_type = None
        else:
            # Handle hero background image upload
            hero_background = None
            hero_background_type = data.get('hero_background_type', event.hero_background_type or 'image')
            
            from werkzeug.utils import secure_filename
            import time
            import os
            from flask import current_app
            from app.utils.validation_utils import allowed_file
            
            # Check for image file upload
            if 'hero_background_image' in request.files and request.files['hero_background_image'].filename:
                file = request.files['hero_background_image']
                if file and file.filename and allowed_file(file.filename):
                    # Delete old file if exists
                    if event.hero_background and event.hero_background.startswith('/static/uploads/events/'):
                        old_file_path = event.hero_background.replace('/static/uploads/events/', '')
                        old_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'events', old_file_path)
                        if os.path.exists(old_full_path):
                            try:
                                os.remove(old_full_path)
                                logger.info(f"✅ Deleted old hero background file: {old_full_path}")
                            except Exception as e:
                                logger.warning(f"⚠️ Could not delete old hero background: {e}")
                    
                    filename = secure_filename(file.filename)
                    filename = f"{int(time.time())}_{filename}"
                    
                    # Create events-specific upload folder
                    events_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'events')
                    os.makedirs(events_upload_folder, exist_ok=True)
                    
                    file_path = os.path.join(events_upload_folder, filename)
                    file.save(file_path)
                    
                    hero_background = f'/static/uploads/events/{filename}'
                    logger.info(f"✅ Uploaded hero background image: {hero_background}")
            # Check for video file upload
            elif 'hero_background_video_file' in request.files and request.files['hero_background_video_file'].filename:
                file = request.files['hero_background_video_file']
                if file and file.filename and allowed_file(file.filename):
                    # Delete old file if exists
                    if event.hero_background and event.hero_background.startswith('/static/uploads/events/'):
                        old_file_path = event.hero_background.replace('/static/uploads/events/', '')
                        old_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'events', old_file_path)
                        if os.path.exists(old_full_path):
                            try:
                                os.remove(old_full_path)
                                logger.info(f"✅ Deleted old hero background file: {old_full_path}")
                            except Exception as e:
                                logger.warning(f"⚠️ Could not delete old hero background: {e}")
                    
                    filename = secure_filename(file.filename)
                    filename = f"{int(time.time())}_{filename}"
                    
                    # Create events-specific upload folder
                    events_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'events')
                    os.makedirs(events_upload_folder, exist_ok=True)
                    
                    file_path = os.path.join(events_upload_folder, filename)
                    file.save(file_path)
                    
                    hero_background = f'/static/uploads/events/{filename}'
                    logger.info(f"✅ Uploaded hero background video: {hero_background}")
            elif data.get('hero_background'):
                # Use provided URL
                hero_background = data.get('hero_background')
            elif hero_background_type == 'video' and data.get('hero_background_video'):
                # Video URL
                hero_background = data.get('hero_background_video')
            elif hero_background_type == 'image' and data.get('hero_background_image_url'):
                # Image URL
                hero_background = data.get('hero_background_image_url')
            else:
                # Keep existing if no new value provided
                hero_background = event.hero_background
            
            if hero_background is not None:
                event.hero_background = hero_background
            if hero_background_type:
                event.hero_background_type = hero_background_type
        
        # Zapamiętaj starą datę (do sprawdzenia czy się zmieniła)
        old_event_date = event.event_date
        event_date_changed = False
        
        # Update fields
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'event_type' in data:
            event.event_type = data['event_type']
        if 'event_date' in data:
            new_event_date = _parse_datetime_safe(data['event_date'])
            if old_event_date != new_event_date:
                event_date_changed = True
                logger.info(f"📅 Data wydarzenia {event_id} zmieniona: {old_event_date} -> {new_event_date}")
            event.event_date = new_event_date
        if 'end_date' in data and data['end_date']:
            event.end_date = _parse_datetime_safe(data['end_date'])
        if 'location' in data:
            event.location = data['location']
        if 'meeting_link' in data:
            event.meeting_link = data['meeting_link']
        if 'event_url' in data:
            event.event_url = data['event_url']
        if 'max_participants' in data:
            # Cast to int if coming as string from form
            try:
                event.max_participants = int(data['max_participants']) if data['max_participants'] not in (None, '') else None
            except (ValueError, TypeError):
                event.max_participants = event.max_participants
        if 'is_active' in data:
            event.is_active = _parse_bool(data['is_active'], event.is_active)
        if 'is_published' in data:
            event.is_published = _parse_bool(data['is_published'], event.is_published)
        if 'is_archived' in data:
            event.is_archived = _parse_bool(data['is_archived'], event.is_archived)
        
        # Auto-unarchive logic:
        # Jeśli wydarzenie było zarchiwizowane, ale po edycji:
        # - ma datę w przyszłości (lub nie jest zakończone wg is_ended())
        # - i jest aktywne lub opublikowane
        # to automatycznie zdejmij flagę is_archived.
        try:
            if event.is_archived and (event.is_active or event.is_published):
                # Używamy modelowej logiki, która bierze pod uwagę event_date/end_date
                if not event.is_ended():
                    event.is_archived = False
                    logger.info(
                        f"🔄 Auto-unarchive event {event.id}: "
                        f"is_active={event.is_active}, is_published={event.is_published}, "
                        f"event_date={event.event_date}, end_date={event.end_date}"
                    )
        except Exception as e:
            logger.warning(f"⚠️ Auto-unarchive check failed for event {event.id}: {e}")
        
        db.session.commit()
        
        # Jeśli data wydarzenia się zmieniła i przypomnienia były zaplanowane, reschedule
        reschedule_message = None
        if event_date_changed and event.reminders_scheduled:
            try:
                from app.services.email_v2.queue.scheduler import EmailScheduler
                scheduler = EmailScheduler()
                success, message = scheduler.reschedule_event_reminders(event_id)
                
                if success:
                    logger.info(f"✅ Automatyczny rescheduling: {message}")
                    reschedule_message = message
                else:
                    logger.warning(f"⚠️ Błąd automatycznego reschedulingu: {message}")
                    reschedule_message = f"OSTRZEŻENIE: {message}"
                    
            except Exception as e:
                logger.error(f"❌ Błąd automatycznego reschedulingu: {e}")
                reschedule_message = f"OSTRZEŻENIE: Nie udało się zreschedule'ować przypomnień: {str(e)}"
        
        response_message = 'Wydarzenie zostało zaktualizowane'
        if reschedule_message:
            response_message += f'. {reschedule_message}'
        
        return jsonify({
            'success': True,
            'message': response_message,
            'event_date_changed': event_date_changed,
            'reminders_rescheduled': event_date_changed and event.reminders_scheduled
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
        
        # Clean up event groups before deleting event
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        # Delete event groups and their members
        success, message = group_manager.delete_event_groups(event_id)
        if success:
            logger.info(f"✅ {message}")
        else:
            logger.warning(f"⚠️ {message}")
        
        # Clean up orphaned groups (safety measure)
        group_manager.cleanup_orphaned_groups()
        
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
