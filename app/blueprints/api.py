"""
API routes blueprint
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, EventSchedule, EventRegistration, User, UserGroup, EventRecipientGroup, Section, BenefitItem, Testimonial, FAQ, MenuItem, SocialLink, SEOSettings
from app.services.email_service import EmailService
from app.blueprints.email_api import create_event_group, delete_event_groups
from app.utils.timezone import get_local_now
import json
import pytz
import hashlib
import hmac
import os

api_bp = Blueprint('api', __name__)

def _convert_boolean(value):
    """Convert string to boolean for FormData"""
    if isinstance(value, str):
        return value.lower() == 'true'
    return value

# Email System API Endpoints
@api_bp.route('/email/queue-stats', methods=['GET'])
@login_required
def email_queue_stats():
    """Pobiera statystyki kolejki emaili"""
    try:
        from app.services.email_service import EmailService
        email_service = EmailService()
        stats = email_service.get_queue_stats()
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/email/queue', methods=['GET'])
@login_required
def email_queue():
    """Pobiera kolejkę emaili"""
    try:
        from models import EmailQueue
        from sqlalchemy import desc
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_status = request.args.get('filter', 'pending')
        
        query = EmailQueue.query
        if filter_status != 'all':
            query = query.filter_by(status=filter_status)
        
        pagination = query.order_by(desc(EmailQueue.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        email_list = []
        for email in pagination.items:
            email_list.append({
                'id': email.id,
                'to_email': email.to_email,
                'to_name': email.to_name,
                'subject': email.subject,
                'status': email.status,
                'scheduled_at': email.scheduled_at.isoformat() if email.scheduled_at else None,
                'sent_at': email.sent_at.isoformat() if email.sent_at else None,
                'error_message': email.error_message
            })
        
        return jsonify({
            'success': True, 
            'emails': email_list,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': pagination.per_page
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/email/process-queue', methods=['POST'])
@login_required
def email_process_queue():
    """Przetwarza kolejkę emaili"""
    try:
        from app.services.email_service import EmailService
        email_service = EmailService()
        stats = email_service.process_queue()
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/email/queue-progress', methods=['GET'])
@login_required
def email_queue_progress():
    """Pobiera postęp przetwarzania kolejki emaili"""
    try:
        from models import EmailQueue
        
        # Pobierz statystyki kolejki
        total_pending = EmailQueue.query.filter_by(status='pending').count()
        total_sent = EmailQueue.query.filter_by(status='sent').count()
        total_failed = EmailQueue.query.filter_by(status='failed').count()
        total_processing = EmailQueue.query.filter_by(status='processing').count()
        
        # Oblicz postęp
        total_emails = total_pending + total_sent + total_failed + total_processing
        processed_emails = total_sent + total_failed
        
        if total_emails == 0:
            progress_percent = 100
        else:
            progress_percent = int((processed_emails / total_emails) * 100)
        
        return jsonify({
            'success': True,
            'progress': {
                'percent': progress_percent,
                'processed': processed_emails,
                'total': total_emails,
                'pending': total_pending,
                'sent': total_sent,
                'failed': total_failed,
                'processing': total_processing
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/email/retry-failed', methods=['POST'])
@login_required
def email_retry_failed():
    """Ponawia nieudane emaile"""
    try:
        from app.services.email_service import EmailService
        email_service = EmailService()
        stats = email_service.retry_failed_emails()
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/email/retry/<int:email_id>', methods=['POST'])
@login_required
def email_retry_single(email_id):
    """Ponawia pojedynczy email"""
    try:
        from models import EmailQueue, db
        from app.services.email_service import EmailService
        
        email = EmailQueue.query.get(email_id)
        if not email:
            return jsonify({'success': False, 'error': 'Email nie istnieje'}), 404
            
        if email.status != 'failed':
            return jsonify({'success': False, 'error': 'Email nie jest nieudany'}), 400
        
        # Reset status
        email.status = 'pending'
        email.error_message = None
        email.retry_count = 0
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Email dodany do ponowienia'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/email/delete/<int:email_id>', methods=['DELETE'])
@login_required
def email_delete_single(email_id):
    """Usuwa pojedynczy email z kolejki"""
    try:
        from models import EmailQueue, db
        
        email = EmailQueue.query.get(email_id)
        if not email:
            return jsonify({'success': False, 'error': 'Email nie istnieje'}), 404
        
        db.session.delete(email)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Email usunięty'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# All email endpoints removed - will be redesigned from scratch

# All email endpoints removed - will be redesigned from scratch

# All email endpoints removed - will be redesigned from scratch

# All email endpoints removed - will be redesigned from scratch

# All email endpoints removed - will be redesigned from scratch

# All email endpoints removed - will be redesigned from scratch

# All email endpoints removed - will be redesigned from scratch

# Events API
@api_bp.route('/events', methods=['GET'])
def get_events():
    """Get all events"""
    try:
        events = EventSchedule.query.all()
        return jsonify([{
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'event_date': event.event_date.isoformat() if event.event_date else None,
            'end_date': event.end_date.isoformat() if event.end_date else None,
            'event_type': event.event_type,
            'location': event.location,
            'meeting_link': event.meeting_link,
            'max_participants': event.max_participants,
            'is_active': event.is_active,
            'is_published': event.is_published,
            'hero_background': event.hero_background,
            'hero_background_type': event.hero_background_type,
            'created_at': event.created_at.isoformat() if event.created_at else None,
            'updated_at': event.updated_at.isoformat() if event.updated_at else None
        } for event in events])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Event Schedule API
@api_bp.route('/event-schedule', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_event_schedule():
    """Event Schedule API"""
    try:
        from models import EventSchedule
        from datetime import datetime
        
        if request.method == 'GET':
            events = EventSchedule.query.order_by(EventSchedule.event_date.desc()).all()
            return jsonify([{
                'id': event.id,
                'title': event.title,
                'event_type': event.event_type,
                'event_date': event.event_date.isoformat() if event.event_date else None,
                'end_date': event.end_date.isoformat() if event.end_date else None,
                'description': event.description,
                'meeting_link': event.meeting_link,
                'location': event.location,
                'max_participants': event.max_participants,
                'is_active': event.is_active,
                'is_published': event.is_published,
                'hero_background': event.hero_background,
                'hero_background_type': event.hero_background_type,
                'created_at': event.created_at.isoformat() if event.created_at else None,
                'updated_at': event.updated_at.isoformat() if event.updated_at else None
            } for event in events])
        
        elif request.method == 'POST':
            # Try to get JSON data with force=True to handle different Content-Types
            data = request.get_json(force=True)
            
            if not data:
                return jsonify({'error': 'Brak danych JSON'}), 400
            
            # Walidacja wymaganych pól
            if not data.get('title'):
                return jsonify({'error': 'Tytuł wydarzenia jest wymagany'}), 400
            
            if not data.get('event_type'):
                return jsonify({'error': 'Typ wydarzenia jest wymagany'}), 400
            
            # Walidacja daty wydarzenia
            if data.get('event_date'):
                try:
                    event_date = datetime.fromisoformat(data.get('event_date'))
                    from app.utils.timezone import get_local_now, get_local_timezone
                    now = get_local_now()
                    
                    # Konwertuj event_date do timezone-aware jeśli nie jest
                    if event_date.tzinfo is None:
                        tz = get_local_timezone()
                        event_date = tz.localize(event_date)
                    
                    # Sprawdź czy data wydarzenia nie jest w przeszłości
                    if event_date < now:
                        return jsonify({'error': 'Data wydarzenia nie może być w przeszłości'}), 400
                        
                except ValueError:
                    return jsonify({'error': 'Nieprawidłowy format daty wydarzenia'}), 400
            
            # Walidacja daty zakończenia
            if data.get('end_date'):
                try:
                    end_date = datetime.fromisoformat(data.get('end_date'))
                    if data.get('event_date'):
                        event_date = datetime.fromisoformat(data.get('event_date'))
                        
                        # Konwertuj obie daty do timezone-aware jeśli nie są
                        if end_date.tzinfo is None:
                            tz = get_local_timezone()
                            end_date = tz.localize(end_date)
                        if event_date.tzinfo is None:
                            tz = get_local_timezone()
                            event_date = tz.localize(event_date)
                        
                        if end_date <= event_date:
                            return jsonify({'error': 'Data zakończenia musi być późniejsza niż data rozpoczęcia'}), 400
                except ValueError:
                    return jsonify({'error': 'Nieprawidłowy format daty zakończenia'}), 400
            
            # Przygotuj daty dla EventSchedule
            event_date_obj = None
            end_date_obj = None
            
            if data.get('event_date'):
                event_date_obj = datetime.fromisoformat(data.get('event_date'))
                if event_date_obj.tzinfo is None:
                    tz = get_local_timezone()
                    event_date_obj = tz.localize(event_date_obj)
                # Konwertuj do UTC dla bazy danych
                event_date_obj = event_date_obj.astimezone(pytz.UTC).replace(tzinfo=None)
            
            if data.get('end_date'):
                end_date_obj = datetime.fromisoformat(data.get('end_date'))
                if end_date_obj.tzinfo is None:
                    tz = get_local_timezone()
                    end_date_obj = tz.localize(end_date_obj)
                # Konwertuj do UTC dla bazy danych
                end_date_obj = end_date_obj.astimezone(pytz.UTC).replace(tzinfo=None)
            
            event = EventSchedule(
                title=data.get('title'),
                event_type=data.get('event_type'),
                event_date=event_date_obj,
                end_date=end_date_obj,
                description=data.get('description'),
                meeting_link=data.get('meeting_link'),
                location=data.get('location'),
                max_participants=int(data.get('max_participants', 0)) if data.get('max_participants') else None,
                is_active=data.get('is_active', True),
                is_published=data.get('is_published', False),
                hero_background=data.get('hero_background'),
                hero_background_type=data.get('hero_background_type', 'image')
            )
            
            db.session.add(event)
            db.session.commit()
            
            # Utwórz grupę dla wydarzenia
            group_id = create_event_group(event.id, event.title)
            if group_id:
                print(f"✅ Utworzono grupę dla wydarzenia: {event.title} (ID: {group_id})")
            else:
                print(f"❌ Błąd tworzenia grupy dla wydarzenia: {event.title}")
            
            return jsonify({
                'success': True,
                'message': 'Wydarzenie zostało dodane pomyślnie',
                'id': event.id
            }), 201
        
        elif request.method == 'DELETE':
            data = request.get_json()
            event_ids = data.get('ids', [])
            
            if not event_ids:
                return jsonify({'success': False, 'error': 'Brak ID do usunięcia'})
            
            # Delete groups for these events
            for event_id in event_ids:
                success, message = delete_event_groups(event_id)
                if success:
                    print(f"✅ Usunięto grupy dla wydarzenia ID: {event_id} - {message}")
                else:
                    print(f"❌ Błąd usuwania grup dla wydarzenia ID: {event_id} - {message}")
            
            EventSchedule.query.filter(EventSchedule.id.in_(event_ids)).delete(synchronize_session=False)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Usunięto {len(event_ids)} wydarzeń'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/event-schedule/<int:event_id>', methods=['GET', 'PUT', 'DELETE'])
def api_event_schedule_item(event_id):
    """Single Event Schedule API"""
    try:
        from models import EventSchedule
        from datetime import datetime
        event = EventSchedule.query.get_or_404(event_id)
        
        if request.method == 'GET':
            # Determine event status
            from app.utils.timezone import get_local_now
            now = get_local_now()
            now_naive = now.replace(tzinfo=None)
            
            event_status = 'upcoming'
            if event.event_date and event.end_date:
                # Event has both start and end time
                if now_naive >= event.event_date and now_naive <= event.end_date:
                    event_status = 'current'  # Event is currently happening
                elif now_naive < event.event_date:
                    event_status = 'upcoming'  # Event is in the future
                else:
                    event_status = 'past'  # Event has ended
            elif event.event_date:
                # Event has only start time (legacy support)
                if now_naive >= event.event_date:
                    event_status = 'current'
                else:
                    event_status = 'upcoming'
            
            return jsonify({
                'success': True,
                'event': {
                    'id': event.id,
                    'title': event.title,
                    'event_type': event.event_type,
                    'event_date': event.event_date.isoformat() if event.event_date else None,
                    'end_date': event.end_date.isoformat() if event.end_date else None,
                    'description': event.description,
                    'meeting_link': event.meeting_link,
                    'location': event.location,
                    'max_participants': event.max_participants,
                    'is_active': event.is_active,
                    'is_published': event.is_published,
                    'hero_background': event.hero_background,
                    'hero_background_type': event.hero_background_type,
                    'created_at': event.created_at.isoformat() if event.created_at else None,
                    'updated_at': event.updated_at.isoformat() if event.updated_at else None
                },
                'event_status': event_status
            })
        
        elif request.method == 'PUT':
            # Require login for PUT and DELETE
            from flask_login import login_required
            if not current_user.is_authenticated:
                return jsonify({'error': 'Wymagane logowanie'}), 401
                
            # Try to get JSON data with force=True to handle different Content-Types
            data = request.get_json(force=True)
            
            if not data:
                return jsonify({'error': 'Brak danych JSON'}), 400
            
            event.title = data.get('title', event.title)
            event.event_type = data.get('event_type', event.event_type)
            
            # Handle date conversion
            if data.get('event_date'):
                event.event_date = datetime.fromisoformat(data.get('event_date'))
            if data.get('end_date'):
                event.end_date = datetime.fromisoformat(data.get('end_date'))
            
            event.description = data.get('description', event.description)
            event.meeting_link = data.get('meeting_link', event.meeting_link)
            event.location = data.get('location', event.location)
            event.max_participants = int(data.get('max_participants', 0)) if data.get('max_participants') else None
            
            # Handle boolean fields
            event.is_active = data.get('is_active', event.is_active)
            event.is_published = data.get('is_published', event.is_published)
            
            event.hero_background = data.get('hero_background', event.hero_background)
            event.hero_background_type = data.get('hero_background_type', event.hero_background_type)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Wydarzenie zostało zaktualizowane pomyślnie'})
        
        elif request.method == 'DELETE':
            # Require login for DELETE
            if not current_user.is_authenticated:
                return jsonify({'error': 'Wymagane logowanie'}), 401
                
            # First delete all related registrations
            EventRegistration.query.filter_by(event_id=event.id).delete()
            
            # Delete group for this event
            success, message = delete_event_groups(event.id)
            if success:
                print(f"✅ Usunięto grupy dla wydarzenia: {event.title} - {message}")
            else:
                print(f"❌ Błąd usuwania grup dla wydarzenia: {event.title} - {message}")
            
            # Then delete the event
            db.session.delete(event)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Wydarzenie zostało usunięte pomyślnie'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# Moved from admin.py
@api_bp.route('/benefits', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def api_benefits():
    """Benefits API endpoints"""
    from models import BenefitItem, db
    from flask import request, jsonify
    import os
    from werkzeug.utils import secure_filename
    
    if request.method == 'GET':
        # Get single benefit by ID
        benefit_id = request.args.get('id')
        if benefit_id:
            benefit = BenefitItem.query.get_or_404(benefit_id)
            return jsonify({
                'success': True,
                'benefit': {
                    'id': benefit.id,
                    'title': benefit.title,
                    'description': benefit.description,
                    'icon': benefit.icon,
                    'image': benefit.image,
                    'order': benefit.order,
                    'is_active': benefit.is_active
                }
            })
        
        # Get all benefits
        benefits = BenefitItem.query.order_by(BenefitItem.order.asc()).all()
        return jsonify({
            'success': True,
            'benefits': [{
                'id': b.id,
                'title': b.title,
                'description': b.description,
                'icon': b.icon,
                'image': b.image,
                'order': b.order,
                'is_active': b.is_active
            } for b in benefits]
        })
    
    elif request.method == 'POST':
        # Create new benefit
        try:
            title = request.form.get('title')
            description = request.form.get('description', '')
            icon = request.form.get('icon', '')
            order = int(request.form.get('order', 1))
            # Handle checkbox properly - HTML checkboxes send 'on' when checked, nothing when unchecked
            is_active = 'is_active' in request.form
            
            if not title:
                return jsonify({'success': False, 'error': 'Tytuł jest wymagany'})
            
            # Handle file upload
            image_path = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    if filename:
                        # Create benefits directory if it doesn't exist
                        benefits_dir = os.path.join(current_app.root_path, '..', 'static', 'images', 'benefits')
                        os.makedirs(benefits_dir, exist_ok=True)
                        
                        # Generate unique filename
                        import uuid
                        unique_filename = str(uuid.uuid4().hex) + '.' + filename.rsplit('.', 1)[1].lower()
                        file_path = os.path.join(benefits_dir, unique_filename)
                        file.save(file_path)
                        image_path = f'images/benefits/{unique_filename}'
            
            benefit = BenefitItem(
                title=title,
                description=description,
                icon=icon,
                image=image_path,
                order=order,
                is_active=is_active
            )
            
            db.session.add(benefit)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Korzyść została dodana pomyślnie'})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    elif request.method == 'PUT':
        # Update existing benefit
        try:
            benefit_id = request.form.get('id')
            if not benefit_id:
                return jsonify({'success': False, 'error': 'ID korzyści jest wymagane'})
            
            benefit = BenefitItem.query.get_or_404(benefit_id)
            
            benefit.title = request.form.get('title', benefit.title)
            benefit.description = request.form.get('description', benefit.description)
            benefit.icon = request.form.get('icon', benefit.icon)
            benefit.order = int(request.form.get('order', benefit.order))
            # Handle checkbox properly - HTML checkboxes send 'on' when checked, nothing when unchecked
            benefit.is_active = 'is_active' in request.form
            
            # Handle file upload
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    if filename:
                        # Create benefits directory if it doesn't exist
                        benefits_dir = os.path.join(current_app.root_path, '..', 'static', 'images', 'benefits')
                        os.makedirs(benefits_dir, exist_ok=True)
                        
                        # Generate unique filename
                        import uuid
                        unique_filename = str(uuid.uuid4().hex) + '.' + filename.rsplit('.', 1)[1].lower()
                        file_path = os.path.join(benefits_dir, unique_filename)
                        file.save(file_path)
                        benefit.image = f'images/benefits/{unique_filename}'
            
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Korzyść została zaktualizowana pomyślnie'})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    elif request.method == 'DELETE':
        # Delete benefit(s)
        try:
            benefit_id = request.args.get('id')
            if benefit_id:
                # Delete single benefit
                benefit = BenefitItem.query.get_or_404(benefit_id)
                db.session.delete(benefit)
                db.session.commit()
                return jsonify({'success': True, 'message': 'Korzyść została usunięta pomyślnie'})
            else:
                # Bulk delete
                data = request.get_json()
                benefit_ids = data.get('ids', [])
                if not benefit_ids:
                    return jsonify({'success': False, 'error': 'Brak ID do usunięcia'})
                
                BenefitItem.query.filter(BenefitItem.id.in_(benefit_ids)).delete(synchronize_session=False)
                db.session.commit()
                return jsonify({'success': True, 'message': f'Usunięto {len(benefit_ids)} korzyści'})
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})



@api_bp.route('/benefits/<int:benefit_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_benefit_by_id(benefit_id):
    """Single benefit API endpoint"""
    from models import BenefitItem, db
    from flask import request, jsonify
    
    if request.method == 'GET':
        benefit = BenefitItem.query.get_or_404(benefit_id)
        return jsonify({
            'success': True,
            'benefit': {
                'id': benefit.id,
                'title': benefit.title,
                'description': benefit.description,
                'icon': benefit.icon,
                'image': benefit.image,
                'order': benefit.order,
                'is_active': benefit.is_active
            }
        })
    
    elif request.method == 'DELETE':
        benefit = BenefitItem.query.get_or_404(benefit_id)
        db.session.delete(benefit)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Korzyść została usunięta pomyślnie'})



@api_bp.route('/user-groups', methods=['GET', 'POST'])
@login_required
def api_user_groups():
    """User groups API"""
    if request.method == 'GET':
        try:
            groups = UserGroup.query.all()
            return jsonify([{
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'created_at': group.created_at.isoformat() if group.created_at else None
            } for group in groups])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            if not data.get('name'):
                return jsonify({'error': 'Name is required'}), 400
            
            group = UserGroup(
                name=data['name'],
                description=data.get('description', '')
            )
            
            db.session.add(group)
            db.session.commit()
            
            return jsonify({
                'id': group.id,
                'name': group.name,
                'message': 'User group created successfully'
            }), 201
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500



@api_bp.route('/user-groups/<int:group_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_user_group(group_id):
    """Specific user group API"""
    group = UserGroup.query.get_or_404(group_id)
    
    if request.method == 'GET':
        return jsonify({
            'id': group.id,
            'name': group.name,
            'description': group.description,
            'created_at': group.created_at.isoformat() if group.created_at else None
        })
    
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            
            if 'name' in data:
                group.name = data['name']
            if 'description' in data:
                group.description = data['description']
            
            db.session.commit()
            
            return jsonify({'message': 'User group updated successfully'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(group)
            db.session.commit()
            
            return jsonify({'message': 'User group deleted successfully'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# Schedules API


@api_bp.route('/schedules', methods=['GET'])
@login_required
def api_schedules():
    """Get all schedules"""
    try:
        schedules = EmailSchedule.query.all()
        return jsonify([{
            'id': schedule.id,
            'name': schedule.name,
            'description': schedule.description,
            'template_id': schedule.template_id,
            'template_name': schedule.template.name if schedule.template else None,
            'send_type': schedule.send_type,
            'recipient_type': schedule.recipient_type,
            'status': schedule.status,
            'created_at': schedule.created_at.isoformat() if schedule.created_at else None
        } for schedule in schedules])
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@api_bp.route('/schedules', methods=['POST'])
@login_required
def api_create_schedule():
    """Create new schedule"""
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('template_id'):
            return jsonify({'error': 'Name and template_id are required'}), 400
        
        schedule = EmailSchedule(
            name=data['name'],
            description=data.get('description', ''),
            template_id=data['template_id'],
            send_type=data.get('send_type', 'immediate'),
            recipient_type=data.get('recipient_type', 'all_users'),
            status=data.get('status', 'active'),
            trigger_conditions=json.dumps(data.get('trigger_conditions', {}))
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        return jsonify({
            'id': schedule.id,
            'name': schedule.name,
            'message': 'Schedule created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@api_bp.route('/schedules/<int:schedule_id>', methods=['GET'])
@login_required
def api_get_schedule(schedule_id):
    """Get specific schedule"""
    try:
        schedule = EmailSchedule.query.get_or_404(schedule_id)
        return jsonify({
            'id': schedule.id,
            'name': schedule.name,
            'description': schedule.description,
            'template_id': schedule.template_id,
            'template_name': schedule.template.name if schedule.template else None,
            'send_type': schedule.send_type,
            'recipient_type': schedule.recipient_type,
            'status': schedule.status,
            'trigger_conditions': json.loads(schedule.trigger_conditions) if schedule.trigger_conditions else {},
            'created_at': schedule.created_at.isoformat() if schedule.created_at else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@api_bp.route('/schedules/<int:schedule_id>', methods=['PUT'])
@login_required
def api_update_schedule(schedule_id):
    """Update schedule"""
    try:
        schedule = EmailSchedule.query.get_or_404(schedule_id)
        data = request.get_json()
        
        if 'name' in data:
            schedule.name = data['name']
        if 'description' in data:
            schedule.description = data['description']
        if 'template_id' in data:
            schedule.template_id = data['template_id']
        if 'send_type' in data:
            schedule.send_type = data['send_type']
        if 'recipient_type' in data:
            schedule.recipient_type = data['recipient_type']
        if 'status' in data:
            schedule.status = data['status']
        if 'trigger_conditions' in data:
            schedule.trigger_conditions = json.dumps(data['trigger_conditions'])
        
        db.session.commit()
        
        return jsonify({'message': 'Schedule updated successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@api_bp.route('/schedules/<int:schedule_id>', methods=['DELETE'])
@login_required
def api_delete_schedule(schedule_id):
    """Delete schedule"""
    try:
        schedule = EmailSchedule.query.get_or_404(schedule_id)
        db.session.delete(schedule)
        db.session.commit()
        
        return jsonify({'message': 'Schedule deleted successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Users API

@api_bp.route('/users', methods=['GET'])
@login_required
def api_users():
    """Get all users with pagination and search"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', '')
        
        query = User.query
        
        if search:
            query = query.filter(
                (User.name.ilike(f'%{search}%')) | 
                (User.email.ilike(f'%{search}%'))
            )
        
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        users = []
        for user in pagination.items:
            users.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })
        
        return jsonify({
            'success': True,
            'users': users,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': pagination.per_page
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Search users API


@api_bp.route('/search-users', methods=['GET'])
@login_required
def api_search_users():
    """Search users by name or email"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify([])
        
        users = User.query.filter(
            (User.name.ilike(f'%{query}%')) | 
            (User.email.ilike(f'%{query}%'))
        ).limit(10).all()
        
        return jsonify([{
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'is_active': user.is_active
        } for user in users])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Check schedules API


@api_bp.route('/check-schedules', methods=['POST'])
@login_required
def api_check_schedules():
    """Check and run scheduled emails"""
    try:
        # Email processing would be handled by Celery tasks
        return jsonify({'message': 'Email processing is handled by Celery tasks'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Bulk delete API endpoints


@api_bp.route('/bulk-delete/schedules', methods=['POST'])
@login_required
def api_bulk_delete_schedules():
    """Bulk delete email schedules"""
    try:
        data = request.get_json()
        schedule_ids = data.get('ids', [])
        
        if not schedule_ids:
            return jsonify({'error': 'No IDs provided'}), 400
        
        # Delete schedules
        deleted_count = EmailSchedule.query.filter(EmailSchedule.id.in_(schedule_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully deleted {deleted_count} schedules',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@api_bp.route('/bulk-delete/user-groups', methods=['POST'])
@login_required
def api_bulk_delete_user_groups():
    """Bulk delete user groups"""
    try:
        data = request.get_json()
        group_ids = data.get('ids', [])
        
        if not group_ids:
            return jsonify({'error': 'No IDs provided'}), 400
        
        # Delete user groups
        deleted_count = UserGroup.query.filter(UserGroup.id.in_(group_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully deleted {deleted_count} user groups',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@api_bp.route('/bulk-delete/events', methods=['POST'])
@login_required
def api_bulk_delete_events():
    """Bulk delete events"""
    try:
        data = request.get_json()
        event_ids = data.get('ids', [])
        
        if not event_ids:
            return jsonify({'error': 'No IDs provided'}), 400
        
        # First delete all related registrations for these events
        EventRegistration.query.filter(EventRegistration.event_id.in_(event_ids)).delete(synchronize_session=False)
        
        # Then delete events
        deleted_count = EventSchedule.query.filter(EventSchedule.id.in_(event_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully deleted {deleted_count} events',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@api_bp.route('/bulk-delete/registrations', methods=['POST'])
@login_required
def api_bulk_delete_registrations():
    """Bulk delete event registrations"""
    try:
        data = request.get_json()
        registration_ids = data.get('ids', [])
        
        if not registration_ids:
            return jsonify({'error': 'No IDs provided'}), 400
        
        # Delete registrations
        deleted_count = EventRegistration.query.filter(EventRegistration.id.in_(registration_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully deleted {deleted_count} registrations',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@api_bp.route('/bulk-delete/users', methods=['POST'])
@login_required
def api_bulk_delete_users():
    """Bulk delete users"""
    try:
        data = request.get_json()
        user_ids = data.get('ids', [])
        
        if not user_ids:
            return jsonify({'error': 'No IDs provided'}), 400
        
        # Don't allow deleting current user
        if current_user.id in user_ids:
            return jsonify({'error': 'Cannot delete current user'}), 400
        
        # Delete users
        deleted_count = User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} users',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# All email endpoints removed - will be redesigned from scratch

# User Management API endpoints

@api_bp.route('/user/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_user(user_id):
    """Individual user API"""
    try:
        user = User.query.get_or_404(user_id)
        
        if request.method == 'GET':
            return jsonify({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'club_member': user.club_member,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            # Update user fields
            if 'name' in data:
                user.name = data['name']
            if 'email' in data:
                # Check if email is already taken by another user
                existing_user = User.query.filter(User.email == data['email'], User.id != user_id).first()
                if existing_user:
                    return jsonify({'error': 'Email już jest używany przez innego użytkownika'}), 400
                user.email = data['email']
            if 'phone' in data:
                user.phone = data['phone']
            if 'club_member' in data:
                user.club_member = bool(data['club_member'])
            if 'is_active' in data:
                user.is_active = bool(data['is_active'])
            if 'is_admin' in data:
                user.is_admin = bool(data['is_admin'])
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Użytkownik został zaktualizowany pomyślnie'
            })
        
        elif request.method == 'DELETE':
            # Prevent deleting admin users
            if user.is_admin:
                return jsonify({'error': 'Nie można usunąć użytkownika administratora'}), 400
            
            db.session.delete(user)
        db.session.commit()
        
        return jsonify({
                'success': True,
                'message': 'Użytkownik został usunięty pomyślnie'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Content Management API endpoints


@api_bp.route('/sections', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_sections():
    """Sections API"""
    if request.method == 'GET':
        try:
            from models import Section
            sections = Section.query.order_by(Section.order.asc()).all()
            return jsonify([{
                'id': section.id,
                'name': section.name,
                'title': section.title,
                'subtitle': section.subtitle,
                'content': section.content,
                'order': section.order,
                'is_active': section.is_active,
                'enable_pillars': section.enable_pillars,
                'enable_floating_cards': section.enable_floating_cards,
                'pillars_count': section.pillars_count,
                'floating_cards_count': section.floating_cards_count,
                'pillars_data': section.pillars_data,
                'floating_cards_data': section.floating_cards_data,
                'final_text': section.final_text,
                'created_at': section.created_at.isoformat() if section.created_at else None
            } for section in sections])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            from models import Section
            # Handle both JSON and FormData
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
                # Convert string values to appropriate types
                if 'is_active' in data:
                    data['is_active'] = data['is_active'] == 'on' or data['is_active'] == 'true'
                if 'enable_pillars' in data:
                    data['enable_pillars'] = data['enable_pillars'] == 'on' or data['enable_pillars'] == 'true'
                if 'enable_floating_cards' in data:
                    data['enable_floating_cards'] = data['enable_floating_cards'] == 'on' or data['enable_floating_cards'] == 'true'
                if 'order' in data:
                    try:
                        data['order'] = int(data['order'])
                    except (ValueError, TypeError):
                        data['order'] = 0
                if 'pillars_count' in data:
                    try:
                        data['pillars_count'] = int(data['pillars_count'])
                    except (ValueError, TypeError):
                        data['pillars_count'] = 4
                if 'floating_cards_count' in data:
                    try:
                        data['floating_cards_count'] = int(data['floating_cards_count'])
                    except (ValueError, TypeError):
                        data['floating_cards_count'] = 3
            
            section = Section(
                name=data.get('name', data.get('title', '')),  # Use name or fallback to title
                title=data.get('title'),
                subtitle=data.get('subtitle'),
                content=data.get('content'),
                order=data.get('order', 0),
                is_active=data.get('is_active', True),
                enable_pillars=data.get('enable_pillars', False),
                enable_floating_cards=data.get('enable_floating_cards', False),
                pillars_count=data.get('pillars_count', 4),
                floating_cards_count=data.get('floating_cards_count', 3),
                pillars_data=data.get('pillars_data'),
                floating_cards_data=data.get('floating_cards_data'),
                final_text=data.get('final_text')
            )
            
            db.session.add(section)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Section created successfully',
                'id': section.id,
                'name': section.name,
                'title': section.title,
                'subtitle': section.subtitle,
                'content': section.content,
                'order': section.order,
                'is_active': section.is_active,
                'enable_pillars': section.enable_pillars,
                'enable_floating_cards': section.enable_floating_cards,
                'pillars_count': section.pillars_count,
                'floating_cards_count': section.floating_cards_count,
                'pillars_data': section.pillars_data,
                'floating_cards_data': section.floating_cards_data,
                'final_text': section.final_text,
                'created_at': section.created_at.isoformat() if section.created_at else None
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            from models import Section
            data = request.get_json()
            section_ids = data.get('ids', [])
            if not section_ids:
                return jsonify({'success': False, 'error': 'Brak ID do usunięcia'})
            
            Section.query.filter(Section.id.in_(section_ids)).delete(synchronize_session=False)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Usunięto {len(section_ids)} sekcji'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})



@api_bp.route('/sections/<int:section_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_section(section_id):
    """Single section API"""
    try:
        from models import Section
        section = Section.query.get_or_404(section_id)
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'section': {
                    'id': section.id,
                    'name': section.name,
                    'title': section.title,
                    'subtitle': section.subtitle,
                    'content': section.content,
                    'order': section.order,
                    'is_active': section.is_active,
                    'enable_pillars': section.enable_pillars,
                    'enable_floating_cards': section.enable_floating_cards,
                    'pillars_count': section.pillars_count,
                    'floating_cards_count': section.floating_cards_count,
                    'pillars_data': section.pillars_data,
                    'floating_cards_data': section.floating_cards_data,
                    'final_text': section.final_text,
                    'created_at': section.created_at.isoformat() if section.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            # Handle both JSON and FormData
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
                # Convert string values to appropriate types
                if 'is_active' in data:
                    data['is_active'] = data['is_active'] == 'on' or data['is_active'] == 'true'
                if 'enable_pillars' in data:
                    data['enable_pillars'] = data['enable_pillars'] == 'on' or data['enable_pillars'] == 'true'
                if 'enable_floating_cards' in data:
                    data['enable_floating_cards'] = data['enable_floating_cards'] == 'on' or data['enable_floating_cards'] == 'true'
                if 'order' in data:
                    try:
                        data['order'] = int(data['order'])
                    except (ValueError, TypeError):
                        data['order'] = 0
                if 'pillars_count' in data:
                    try:
                        data['pillars_count'] = int(data['pillars_count'])
                    except (ValueError, TypeError):
                        data['pillars_count'] = 4
                if 'floating_cards_count' in data:
                    try:
                        data['floating_cards_count'] = int(data['floating_cards_count'])
                    except (ValueError, TypeError):
                        data['floating_cards_count'] = 3
            
            section.name = data.get('name', section.name)
            section.title = data.get('title', section.title)
            section.subtitle = data.get('subtitle', section.subtitle)
            section.content = data.get('content', section.content)
            section.order = data.get('order', section.order)
            section.is_active = data.get('is_active', section.is_active)
            section.enable_pillars = data.get('enable_pillars', section.enable_pillars)
            section.enable_floating_cards = data.get('enable_floating_cards', section.enable_floating_cards)
            section.pillars_count = data.get('pillars_count', section.pillars_count)
            section.floating_cards_count = data.get('floating_cards_count', section.floating_cards_count)
            section.pillars_data = data.get('pillars_data', section.pillars_data)
            section.floating_cards_data = data.get('floating_cards_data', section.floating_cards_data)
            section.final_text = data.get('final_text', section.final_text)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Section updated successfully',
                'id': section.id,
                'name': section.name,
                'title': section.title,
                'subtitle': section.subtitle,
                'content': section.content,
                'order': section.order,
                'is_active': section.is_active,
                'enable_pillars': section.enable_pillars,
                'enable_floating_cards': section.enable_floating_cards,
                'pillars_count': section.pillars_count,
                'floating_cards_count': section.floating_cards_count,
                'pillars_data': section.pillars_data,
                'floating_cards_data': section.floating_cards_data,
                'final_text': section.final_text,
                'created_at': section.created_at.isoformat() if section.created_at else None
            })
        
        elif request.method == 'DELETE':
            db.session.delete(section)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Section deleted successfully'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@api_bp.route('/menu', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_menu():
    """Menu API"""
    if request.method == 'GET':
        try:
            from models import MenuItem
            menu_items = MenuItem.query.order_by(MenuItem.order.asc()).all()
            return jsonify([{
                'id': item.id,
                'title': item.title,
                'url': item.url,
                'blog_url': item.blog_url,
                'order': item.order,
                'is_active': item.is_active,
                'blog': item.blog,
                'created_at': item.created_at.isoformat() if item.created_at else None
            } for item in menu_items])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            from models import MenuItem
            data = request.get_json()
            
            menu_item = MenuItem(
                title=data.get('title'),
                url=data.get('url'),
                blog_url=data.get('blog_url'),
                order=data.get('order', 0),
                is_active=data.get('is_active', True),
                blog=data.get('blog', False)
            )
            
            db.session.add(menu_item)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Menu item created successfully',
                'id': menu_item.id,
                'title': menu_item.title,
                'url': menu_item.url,
                'blog_url': menu_item.blog_url,
                'order': menu_item.order,
                'is_active': menu_item.is_active,
                'blog': menu_item.blog,
                'created_at': menu_item.created_at.isoformat() if menu_item.created_at else None
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            from models import MenuItem
            data = request.get_json()
            menu_ids = data.get('ids', [])
            if not menu_ids:
                return jsonify({'success': False, 'error': 'Brak ID do usunięcia'})
            
            MenuItem.query.filter(MenuItem.id.in_(menu_ids)).delete(synchronize_session=False)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Usunięto {len(menu_ids)} elementów menu'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})



@api_bp.route('/menu/<int:item_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_menu_item(item_id):
    """Single menu item API"""
    try:
        from models import MenuItem
        menu_item = MenuItem.query.get_or_404(item_id)
        
        if request.method == 'GET':
            return jsonify({
                'id': menu_item.id,
                'title': menu_item.title,
                'url': menu_item.url,
                'blog_url': menu_item.blog_url,
                'order': menu_item.order,
                'is_active': menu_item.is_active,
                'blog': menu_item.blog,
                'created_at': menu_item.created_at.isoformat() if menu_item.created_at else None
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            menu_item.title = data.get('title', menu_item.title)
            menu_item.url = data.get('url', menu_item.url)
            menu_item.blog_url = data.get('blog_url', menu_item.blog_url)
            menu_item.order = data.get('order', menu_item.order)
            menu_item.is_active = data.get('is_active', menu_item.is_active)
            menu_item.blog = data.get('blog', menu_item.blog)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Menu item updated successfully',
                'id': menu_item.id,
                'title': menu_item.title,
                'url': menu_item.url,
                'order': menu_item.order,
                'is_active': menu_item.is_active,
                'created_at': menu_item.created_at.isoformat() if menu_item.created_at else None
            })
        
        elif request.method == 'DELETE':
            db.session.delete(menu_item)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Menu item deleted successfully'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Pillars and Floating Cards API endpoints


@api_bp.route('/sections/<int:section_id>/pillars', methods=['PUT'])
@login_required
def api_section_pillars(section_id):
    """Update section pillars data"""
    try:
        section = Section.query.get_or_404(section_id)
        
        data = request.get_json()
        pillars_data = data.get('pillars_data')
        final_text = data.get('final_text', '')
        
        if pillars_data:
            section.pillars_data = pillars_data
        if final_text:
            section.final_text = final_text
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Filary zostały zaktualizowane pomyślnie'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@api_bp.route('/sections/<int:section_id>/floating-cards', methods=['PUT'])
@login_required
def api_section_floating_cards(section_id):
    """Update section floating cards data"""
    try:
        section = Section.query.get_or_404(section_id)
        
        data = request.get_json()
        floating_cards_data = data.get('floating_cards_data')
        final_text = data.get('final_text', '')
        
        if floating_cards_data:
            section.floating_cards_data = floating_cards_data
        if final_text:
            section.final_text = final_text
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Karty unoszące się zostały zaktualizowane pomyślnie'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Testimonials API


@api_bp.route('/testimonials', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_testimonials():
    """Testimonials API"""
    if request.method == 'GET':
        try:
            from models import Testimonial
            testimonials = Testimonial.query.order_by(Testimonial.order.asc()).all()
            return jsonify([{
                'id': testimonial.id,
                'author_name': testimonial.author_name,
                'content': testimonial.content,
                'member_since': testimonial.member_since,
                'rating': testimonial.rating,
                'order': testimonial.order,
                'is_active': testimonial.is_active,
                'created_at': testimonial.created_at.isoformat() if testimonial.created_at else None
            } for testimonial in testimonials])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            from models import Testimonial
            data = request.get_json()
            
            testimonial = Testimonial(
                author_name=data.get('author_name'),
                content=data.get('content'),
                member_since=data.get('member_since'),
                rating=data.get('rating', 5),
                order=data.get('order', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(testimonial)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Opinia została dodana pomyślnie',
                'id': testimonial.id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            from models import Testimonial
            data = request.get_json()
            testimonial_ids = data.get('ids', [])
            if not testimonial_ids:
                return jsonify({'success': False, 'error': 'Brak ID do usunięcia'})
            
            Testimonial.query.filter(Testimonial.id.in_(testimonial_ids)).delete(synchronize_session=False)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Usunięto {len(testimonial_ids)} opinii'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})



@api_bp.route('/testimonials/<int:testimonial_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_testimonial(testimonial_id):
    """Single testimonial API"""
    try:
        from models import Testimonial
        testimonial = Testimonial.query.get_or_404(testimonial_id)
        
        if request.method == 'GET':
            return jsonify({
                'id': testimonial.id,
                'author_name': testimonial.author_name,
                'content': testimonial.content,
                'member_since': testimonial.member_since,
                'rating': testimonial.rating,
                'order': testimonial.order,
                'is_active': testimonial.is_active,
                'created_at': testimonial.created_at.isoformat() if testimonial.created_at else None
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            testimonial.author_name = data.get('author_name', testimonial.author_name)
            testimonial.content = data.get('content', testimonial.content)
            testimonial.member_since = data.get('member_since', testimonial.member_since)
            testimonial.rating = data.get('rating', testimonial.rating)
            testimonial.order = data.get('order', testimonial.order)
            testimonial.is_active = data.get('is_active', testimonial.is_active)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Opinia została zaktualizowana pomyślnie'})
        
        elif request.method == 'DELETE':
            db.session.delete(testimonial)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Opinia została usunięta pomyślnie'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# FAQ API


@api_bp.route('/faq', methods=['GET', 'POST', 'DELETE'])
@login_required
def api_faq():
    """FAQ API"""
    if request.method == 'GET':
        try:
            from models import FAQ
            faqs = FAQ.query.order_by(FAQ.order.asc()).all()
            return jsonify([{
                'id': faq.id,
                'question': faq.question,
                'answer': faq.answer,
                'order': faq.order,
                'is_active': faq.is_active,
                'created_at': faq.created_at.isoformat() if faq.created_at else None,
                'updated_at': faq.updated_at.isoformat() if faq.updated_at else None
            } for faq in faqs])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            from models import FAQ
            data = request.get_json()
            print(f"FAQ POST data: {data}")
            
            if not data:
                return jsonify({'error': 'Brak danych JSON'}), 400
            
            faq = FAQ(
                question=data.get('question'),
                answer=data.get('answer'),
                order=data.get('order', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(faq)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Pytanie zostało dodane pomyślnie',
                'id': faq.id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"FAQ POST error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            from models import FAQ
            data = request.get_json()
            faq_ids = data.get('ids', [])
            if not faq_ids:
                return jsonify({'success': False, 'error': 'Brak ID do usunięcia'})
            
            FAQ.query.filter(FAQ.id.in_(faq_ids)).delete(synchronize_session=False)
            db.session.commit()
            return jsonify({'success': True, 'message': f'Usunięto {len(faq_ids)} pytań'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})



@api_bp.route('/faq/<int:faq_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_faq_item(faq_id):
    """Single FAQ API"""
    try:
        from models import FAQ
        faq = FAQ.query.get_or_404(faq_id)
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'faq': {
                    'id': faq.id,
                    'question': faq.question,
                    'answer': faq.answer,
                    'order': faq.order,
                    'is_active': faq.is_active,
                    'created_at': faq.created_at.isoformat() if faq.created_at else None,
                    'updated_at': faq.updated_at.isoformat() if faq.updated_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            faq.question = data.get('question', faq.question)
            faq.answer = data.get('answer', faq.answer)
            faq.order = data.get('order', faq.order)
            faq.is_active = data.get('is_active', faq.is_active)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Pytanie zostało zaktualizowane pomyślnie'})
        
        elif request.method == 'DELETE':
            db.session.delete(faq)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Pytanie zostało usunięte pomyślnie'})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Blog API
@api_bp.route('/blog/categories', methods=['GET'])
@login_required
def api_blog_categories():
    """API endpoint for blog categories"""
    try:
        from models import BlogCategory
        categories = BlogCategory.query.filter_by(is_active=True).order_by(BlogCategory.sort_order).all()
        categories_data = []
        
        for category in categories:
            categories_data.append({
                'id': category.id,
                'title': category.title,
                'slug': category.slug,
                'full_path': category.full_path,
                'posts_count': category.posts_count,
                'parent_id': category.parent_id,
                'created_at': category.created_at.isoformat() if category.created_at else None
            })
        
        return jsonify({
            'success': True,
            'categories': categories_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/blog/posts', methods=['GET'])
@login_required
def api_blog_posts():
    """API endpoint for blog posts"""
    try:
        from models import BlogPost
        posts = BlogPost.query.filter_by(status='published').order_by(BlogPost.published_at.desc()).all()
        posts_data = []
        
        for post in posts:
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'excerpt': post.excerpt,
                'author_name': post.author.name or post.author.email,
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'created_at': post.created_at.isoformat() if post.created_at else None
            })
        
        return jsonify({
            'success': True,
            'posts': posts_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Blog Admin API
@api_bp.route('/blog/admin/posts', methods=['GET', 'POST'])
@login_required
def api_blog_admin_posts():
    """Blog admin posts API"""
    if not current_user.is_admin:
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        if request.method == 'GET':
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            from models import BlogPost
            posts = BlogPost.query.order_by(BlogPost.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            posts_data = []
            for post in posts.items:
                posts_data.append({
                    'id': post.id,
                    'title': post.title,
                    'slug': post.slug,
                    'excerpt': post.excerpt,
                    'content': post.content,
                    'status': post.status,
                    'featured_image': post.featured_image,
                    'author_name': post.author.name or post.author.email,
                    'published_at': post.published_at.isoformat() if post.published_at else None,
                    'created_at': post.created_at.isoformat() if post.created_at else None,
                    'categories': [{'id': cat.id, 'title': cat.title} for cat in post.categories],
                    'tags': [{'id': tag.id, 'name': tag.name} for tag in post.tags],
                    'comments_count': post.comments_count
                })
            
            return jsonify({
                'success': True,
                'posts': posts_data,
                'pagination': {
                    'current_page': posts.page,
                    'total_pages': posts.pages,
                    'total': posts.total,
                    'per_page': posts.per_page
                }
            })
        
        elif request.method == 'POST':
            # Simple FormData handling
            data = {}
            
            # Get all form data
            for key in request.form:
                data[key] = request.form.get(key)
            
            print(f"DEBUG: Raw form data (POST): {data}")
            
            # Parse JSON fields
            try:
                if 'categories' in data and data['categories']:
                    data['categories'] = json.loads(data['categories'])
            except Exception as e:
                print(f"DEBUG: Error parsing categories (POST): {e}")
                data['categories'] = []
            
            try:
                if 'tags' in data and data['tags']:
                    data['tags'] = json.loads(data['tags'])
            except Exception as e:
                print(f"DEBUG: Error parsing tags (POST): {e}")
                data['tags'] = []
            
            print(f"DEBUG: Processed data (POST): {data}")
            
            # Validate blog post data
            from app.utils.validation import validate_blog_post, validate_blog_categories, validate_blog_tags, validate_featured_image
            
            is_valid, errors = validate_blog_post(data)
            if not is_valid:
                return jsonify({'error': '; '.join(errors)}), 400
            
            # Validate categories
            if 'categories' in data and data['categories']:
                is_valid, errors = validate_blog_categories(data['categories'])
                if not is_valid:
                    return jsonify({'error': '; '.join(errors)}), 400
            
            # Validate tags
            if 'tags' in data and data['tags']:
                is_valid, errors = validate_blog_tags(data['tags'])
                if not is_valid:
                    return jsonify({'error': '; '.join(errors)}), 400
            
            # Handle file upload for featured image
            if 'featured_image' in request.files:
                file = request.files['featured_image']
                if file.filename:
                    # Validate file
                    is_valid, error = validate_featured_image(file)
                    if not is_valid:
                        return jsonify({'error': error}), 400
                    
                    # Upload image
                    try:
                        import os
                        import uuid
                        from werkzeug.utils import secure_filename
                        
                        # Generate unique filename
                        filename = secure_filename(file.filename)
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        
                        # Create uploads directory if it doesn't exist
                        uploads_dir = os.path.join(current_app.static_folder, 'uploads')
                        os.makedirs(uploads_dir, exist_ok=True)
                        
                        # Save file
                        file_path = os.path.join(uploads_dir, unique_filename)
                        file.save(file_path)
                        
                        # Set image URL
                        data['featured_image'] = f"/static/uploads/{unique_filename}"
                    except Exception as e:
                        return jsonify({'error': f'Błąd podczas uploadu zdjęcia: {str(e)}'}), 400
            
            
            # Generate unique slug if not provided
            if not data.get('slug'):
                from app.utils.validation import generate_unique_slug
                from models import BlogPost
                data['slug'] = generate_unique_slug(data['title'], BlogPost, 'slug')
            else:
                # Check if provided slug already exists
                from models import BlogPost
                existing = BlogPost.query.filter_by(slug=data['slug']).first()
                if existing:
                    return jsonify({'error': 'Artykuł z tym slug już istnieje'}), 400
            
            # Create post
            post = BlogPost(
                title=data['title'],
                slug=data['slug'],
                excerpt=data.get('excerpt', ''),
                content=data['content'],
                status=data.get('status', 'draft'),
                featured_image=data.get('featured_image', ''),
                author_id=current_user.id,
                allow_comments=_convert_boolean(data.get('allow_comments', True))
            )
            
            db.session.add(post)
            db.session.flush()  # Get the ID
            
            # Handle categories
            if 'categories' in data and data['categories']:
                try:
                    from models import BlogCategory
                    categories = json.loads(data['categories'])
                    for cat_id in categories:
                        category = BlogCategory.query.get(cat_id)
                        if category:
                            post.categories.append(category)
                except:
                    pass  # Ignore invalid categories
            
            # Handle tags
            if 'tags' in data and data['tags']:
                try:
                    from models import BlogTag
                    tags = json.loads(data['tags'])
                    print(f"DEBUG: Processing tags (POST): {tags}")
                    for tag_name in tags:
                        if tag_name.strip():
                            tag = BlogTag.query.filter_by(name=tag_name.strip()).first()
                            if not tag:
                                from app.utils.validation import generate_unique_slug
                                slug = generate_unique_slug(tag_name.strip(), BlogTag, 'slug')
                                tag = BlogTag(name=tag_name.strip(), slug=slug)
                                db.session.add(tag)
                                db.session.flush()  # Flush to get the ID
                                print(f"DEBUG: Created new tag (POST): {tag_name.strip()}")
                            post.tags.append(tag)
                            print(f"DEBUG: Added tag to post (POST): {tag_name.strip()}")
                except Exception as e:
                    print(f"DEBUG: Error processing tags (POST): {e}")
                    pass  # Ignore invalid tags
            
            # Set published_at if status is published
            if post.status == 'published':
                from datetime import datetime
                post.published_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Artykuł został utworzony',
                'post': {
                    'id': post.id,
                    'title': post.title,
                    'slug': post.slug,
                    'status': post.status
                }
            })
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in blog admin posts API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/blog/admin/posts/<int:post_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_blog_admin_post(post_id):
    """Get, update or delete blog post"""
    if not current_user.is_admin:
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from models import BlogPost
        post = BlogPost.query.get_or_404(post_id)
        
        if request.method == 'GET':
            # Debug: check if categories and tags are loaded
            print(f"DEBUG: Post {post.id} categories count: {len(post.categories)}")
            print(f"DEBUG: Post {post.id} tags count: {len(post.tags)}")
            print(f"DEBUG: Categories: {[cat.id for cat in post.categories]}")
            print(f"DEBUG: Tags: {[tag.name for tag in post.tags]}")
            
            return jsonify({
                'success': True,
                'post': {
                    'id': post.id,
                    'title': post.title,
                    'slug': post.slug,
                    'excerpt': post.excerpt,
                    'content': post.content,
                    'status': post.status,
                    'featured_image': post.featured_image,
                    'allow_comments': post.allow_comments,
                    'categories': [{'id': cat.id, 'title': cat.title} for cat in post.categories],
                    'tags': [{'id': tag.id, 'name': tag.name} for tag in post.tags],
                    'published_at': post.published_at.isoformat() if post.published_at else None,
                    'created_at': post.created_at.isoformat() if post.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            # Simple FormData handling
            data = {}
            
            # Get all form data
            for key in request.form:
                data[key] = request.form.get(key)
            
            print(f"DEBUG: Raw form data: {data}")
            
            # Parse JSON fields
            try:
                if 'categories' in data and data['categories']:
                    data['categories'] = json.loads(data['categories'])
            except Exception as e:
                print(f"DEBUG: Error parsing categories: {e}")
                data['categories'] = []
            
            try:
                if 'tags' in data and data['tags']:
                    data['tags'] = json.loads(data['tags'])
            except Exception as e:
                print(f"DEBUG: Error parsing tags: {e}")
                data['tags'] = []
            
            print(f"DEBUG: Processed data: {data}")
            
            # Validate blog post data
            from app.utils.validation import validate_blog_post, validate_blog_categories, validate_blog_tags, validate_featured_image
            
            is_valid, errors = validate_blog_post(data)
            if not is_valid:
                return jsonify({'error': '; '.join(errors)}), 400
            
            # Validate categories
            if 'categories' in data and data['categories']:
                is_valid, errors = validate_blog_categories(data['categories'])
                if not is_valid:
                    return jsonify({'error': '; '.join(errors)}), 400
            
            # Validate tags
            if 'tags' in data and data['tags']:
                is_valid, errors = validate_blog_tags(data['tags'])
                if not is_valid:
                    return jsonify({'error': '; '.join(errors)}), 400
            
            # Handle file upload for featured image
            if 'featured_image' in request.files:
                file = request.files['featured_image']
                if file and file.filename:
                    # Validate file
                    is_valid, error = validate_featured_image(file)
                    if not is_valid:
                        return jsonify({'error': error}), 400
                    
                    # Upload image
                    try:
                        import os
                        import uuid
                        from werkzeug.utils import secure_filename
                        
                        # Generate unique filename
                        filename = secure_filename(file.filename)
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        
                        # Create uploads directory if it doesn't exist
                        uploads_dir = os.path.join(current_app.static_folder, 'uploads')
                        os.makedirs(uploads_dir, exist_ok=True)
                        
                        # Save file
                        file_path = os.path.join(uploads_dir, unique_filename)
                        file.save(file_path)
                        
                        # Set image URL
                        data['featured_image'] = f"/static/uploads/{unique_filename}"
                    except Exception as e:
                        return jsonify({'error': f'Błąd podczas uploadu zdjęcia: {str(e)}'}), 400
            
            # Update basic fields
            if 'title' in data and data['title']:
                post.title = data['title']
            
            if 'slug' in data and data['slug']:
                # Check if new slug already exists (excluding current post)
                existing = BlogPost.query.filter(
                    BlogPost.slug == data['slug'],
                    BlogPost.id != post_id
                ).first()
                if existing:
                    return jsonify({'error': 'Artykuł z tym slug już istnieje'}), 400
                post.slug = data['slug']
            elif 'title' in data and data['title'] and not data.get('slug'):
                # Auto-generate slug from title if no slug provided
                from app.utils.validation import generate_unique_slug
                post.slug = generate_unique_slug(data['title'], BlogPost, 'slug', post_id)
            
            if 'excerpt' in data:
                post.excerpt = data['excerpt']
            
            if 'content' in data:
                post.content = data['content']
            
            if 'status' in data and data['status']:
                post.status = data['status']
                # Set published_at if status changed to published
                if data['status'] == 'published' and not post.published_at:
                    from datetime import datetime
                    post.published_at = datetime.utcnow()
            
            if 'featured_image' in data:
                post.featured_image = data['featured_image']
            
            if 'allow_comments' in data:
                post.allow_comments = _convert_boolean(data['allow_comments'])
            
            # Handle categories
            if 'categories' in data and data['categories']:
                try:
                    from models import BlogCategory
                    categories = json.loads(data['categories'])
                    post.categories.clear()
                    for cat_id in categories:
                        category = BlogCategory.query.get(cat_id)
                        if category:
                            post.categories.append(category)
                except:
                    pass  # Ignore invalid categories
            
            # Handle tags
            print(f"DEBUG: Checking tags in data: {'tags' in data}")
            if 'tags' in data:
                print(f"DEBUG: Tags value: {data['tags']}")
                print(f"DEBUG: Tags type: {type(data['tags'])}")
            
            if 'tags' in data and data['tags']:
                try:
                    from models import BlogTag
                    print(f"DEBUG: Raw tags data: {data['tags']}")
                    print(f"DEBUG: Tags data type: {type(data['tags'])}")
                    
                    # Check if already parsed
                    if isinstance(data['tags'], list):
                        tags = data['tags']
                        print(f"DEBUG: Tags already parsed: {tags}")
                    else:
                        tags = json.loads(data['tags'])
                        print(f"DEBUG: Parsed tags from JSON: {tags}")
                    
                    print(f"DEBUG: About to clear post.tags. Current count: {len(post.tags)}")
                    post.tags.clear()
                    print(f"DEBUG: Cleared post.tags. New count: {len(post.tags)}")
                    
                    for i, tag_name in enumerate(tags):
                        print(f"DEBUG: Processing tag {i+1}/{len(tags)}: '{tag_name}'")
                        if tag_name.strip():
                            tag = BlogTag.query.filter_by(name=tag_name.strip()).first()
                            if not tag:
                                from app.utils.validation import generate_unique_slug
                                slug = generate_unique_slug(tag_name.strip(), BlogTag, 'slug')
                                tag = BlogTag(name=tag_name.strip(), slug=slug)
                                db.session.add(tag)
                                db.session.flush()  # Flush to get the ID
                                print(f"DEBUG: Created new tag: {tag_name.strip()} (ID: {tag.id})")
                            else:
                                print(f"DEBUG: Found existing tag: {tag_name.strip()} (ID: {tag.id})")
                            
                            post.tags.append(tag)
                            print(f"DEBUG: Added tag to post: {tag_name.strip()}")
                            print(f"DEBUG: Post tags count after append: {len(post.tags)}")
                        else:
                            print(f"DEBUG: Skipping empty tag: '{tag_name}'")
                    
                    print(f"DEBUG: Final post.tags count: {len(post.tags)}")
                    print(f"DEBUG: Final post.tags: {[tag.name for tag in post.tags]}")
                except Exception as e:
                    print(f"DEBUG: Error processing tags: {e}")
                    import traceback
                    traceback.print_exc()
                    pass  # Ignore invalid tags
            else:
                print("DEBUG: No tags in data or tags is empty")
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Artykuł został zaktualizowany',
                'post': {
                    'id': post.id,
                    'title': post.title,
                    'slug': post.slug,
                    'status': post.status
                }
            })
        
        elif request.method == 'DELETE':
            # Check if post has comments
            if post.comments_count > 0:
                return jsonify({'error': 'Nie można usunąć artykułu, który ma komentarze'}), 400
            
            db.session.delete(post)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Artykuł został usunięty'
            })
    
    except Exception as e:
        db.session.rollback()
        import traceback
        error_traceback = traceback.format_exc()
        logging.error(f"Error managing blog post: {str(e)}")
        logging.error(f"Traceback: {error_traceback}")
        print(f"ERROR in blog post API: {str(e)}")
        print(f"Traceback: {error_traceback}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/blog/admin/posts/bulk-delete', methods=['POST'])
@login_required
def api_blog_admin_posts_bulk_delete():
    """Bulk delete blog posts"""
    if not current_user.is_admin:
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        data = request.get_json()
        
        if not data or 'ids' not in data:
            return jsonify({'error': 'Brak listy ID do usunięcia'}), 400
        
        post_ids = data.get('ids', [])
        if not post_ids:
            return jsonify({'error': 'Lista ID nie może być pusta'}), 400
        
        # Validate that all IDs are integers
        try:
            post_ids = [int(id) for id in post_ids]
        except (ValueError, TypeError):
            return jsonify({'error': 'Nieprawidłowy format ID'}), 400
        
        from models import BlogPost
        
        # Check if any posts have comments
        posts_with_comments = BlogPost.query.filter(
            BlogPost.id.in_(post_ids),
            BlogPost.comments_count > 0
        ).all()
        
        if posts_with_comments:
            titles = [post.title for post in posts_with_comments]
            return jsonify({
                'error': f'Nie można usunąć artykułów z komentarzami: {", ".join(titles)}'
            }), 400
        
        # Delete posts
        deleted_count = BlogPost.query.filter(BlogPost.id.in_(post_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} artykułów',
            'deleted_count': deleted_count
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in bulk delete blog posts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/blog/admin/categories', methods=['GET', 'POST'])
@login_required
def api_blog_admin_categories():
    """Blog admin categories API"""
    if not current_user.is_admin:
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        if request.method == 'GET':
            from models import BlogCategory
            categories = BlogCategory.query.order_by(BlogCategory.title).all()
            categories_data = []
            
            for category in categories:
                categories_data.append({
                    'id': category.id,
                    'title': category.title,
                    'slug': category.slug,
                    'description': category.description,
                    'parent_id': category.parent_id,
                    'sort_order': category.sort_order,
                    'is_active': category.is_active,
                    'posts_count': category.posts_count,
                    'created_at': category.created_at.isoformat() if category.created_at else None
                })
            
            return jsonify({
                'success': True,
                'categories': categories_data
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            
            # Validation
            if not data.get('title'):
                return jsonify({'error': 'Nazwa jest wymagana'}), 400
            
            # Generate unique slug if not provided
            if not data.get('slug'):
                from app.utils.validation import generate_unique_slug
                from models import BlogCategory
                data['slug'] = generate_unique_slug(data['title'], BlogCategory, 'slug')
            else:
                # Check if provided slug already exists
                from models import BlogCategory
                existing = BlogCategory.query.filter_by(slug=data['slug']).first()
                if existing:
                    return jsonify({'error': 'Kategoria z tym slug już istnieje'}), 400
            
            # Create category
            category = BlogCategory(
                title=data['title'],
                slug=data['slug'],
                description=data.get('description', ''),
                parent_id=data.get('parent_id') if data.get('parent_id') else None,
                sort_order=data.get('sort_order', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(category)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Kategoria została utworzona',
                'category': {
                    'id': category.id,
                    'title': category.title,
                    'slug': category.slug
                }
            })
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in blog admin categories API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/blog/admin/categories/<int:category_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_blog_admin_category(category_id):
    """Get, update or delete blog category"""
    if not current_user.is_admin:
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from models import BlogCategory
        category = BlogCategory.query.get_or_404(category_id)
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'category': {
                    'id': category.id,
                    'title': category.title,
                    'slug': category.slug,
                    'description': category.description,
                    'parent_id': category.parent_id,
                    'sort_order': category.sort_order,
                    'is_active': category.is_active,
                    'posts_count': category.posts_count,
                    'created_at': category.created_at.isoformat() if category.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            # Update fields
            if 'title' in data:
                category.title = data['title']
            if 'slug' in data:
                # Check if new slug already exists (excluding current category)
                existing = BlogCategory.query.filter(
                    BlogCategory.slug == data['slug'],
                    BlogCategory.id != category_id
                ).first()
                if existing:
                    return jsonify({'error': 'Kategoria z tym slug już istnieje'}), 400
                category.slug = data['slug']
            if 'description' in data:
                category.description = data['description']
            if 'parent_id' in data:
                category.parent_id = data['parent_id'] if data['parent_id'] else None
            if 'sort_order' in data:
                category.sort_order = data['sort_order']
            if 'is_active' in data:
                category.is_active = data['is_active']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Kategoria została zaktualizowana',
                'category': {
                    'id': category.id,
                    'title': category.title,
                    'slug': category.slug
                }
            })
        
        elif request.method == 'DELETE':
            # Check if category has posts
            if category.posts_count > 0:
                return jsonify({'error': 'Nie można usunąć kategorii, która ma artykuły'}), 400
            
            # Check if category has children
            if category.children:
                return jsonify({'error': 'Nie można usunąć kategorii, która ma podkategorie'}), 400
            
            db.session.delete(category)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Kategoria została usunięta'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error managing blog category: {str(e)}")
        return jsonify({'error': str(e)}), 500

# File Upload API
@api_bp.route('/upload/image', methods=['POST'])
@login_required
def upload_image():
    """Upload image file"""
    if not current_user.is_admin:
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Brak pliku'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nie wybrano pliku'}), 400
        
        # Check file extension
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'error': 'Nieprawidłowy format pliku. Dozwolone: PNG, JPG, JPEG, GIF, WEBP'}), 400
        
        # Generate unique filename
        import os
        import uuid
        from werkzeug.utils import secure_filename
        
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(uploads_dir, unique_filename)
        file.save(file_path)
        
        # Return URL
        image_url = f"/static/uploads/{unique_filename}"
        
        return jsonify({
            'success': True,
            'url': image_url,
            'filename': unique_filename
        })
        
    except Exception as e:
        logging.error(f"Error uploading image: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Blog Post Images API
@api_bp.route('/blog/admin/posts/<int:post_id>/images', methods=['GET', 'POST'])
@login_required
def api_blog_post_images(post_id):
    """Get or add images to a blog post"""
    if not current_user.is_admin:
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from models import BlogPost, BlogPostImage
        
        # Check if post exists
        post = BlogPost.query.get_or_404(post_id)
        
        if request.method == 'GET':
            # Get all images for the post
            images = BlogPostImage.query.filter_by(post_id=post_id).order_by(BlogPostImage.order.asc()).all()
            return jsonify({
                'success': True,
                'images': [{
                    'id': img.id,
                    'image_url': img.image_url,
                    'alt_text': img.alt_text,
                    'caption': img.caption,
                    'order': img.order,
                    'created_at': img.created_at.isoformat()
                } for img in images]
            })
        
        elif request.method == 'POST':
            # Add new image to post
            image_url = None
            
            # Handle file upload
            if 'image_file' in request.files:
                file = request.files['image_file']
                if file and file.filename:
                    from app.utils.validation import validate_featured_image
                    is_valid, error = validate_featured_image(file)
                    if not is_valid:
                        return jsonify({'error': error}), 400
                    
                    try:
                        import os
                        import uuid
                        from werkzeug.utils import secure_filename
                        
                        # Generate unique filename
                        filename = secure_filename(file.filename)
                        unique_filename = f"{uuid.uuid4()}_{filename}"
                        
                        # Create uploads directory if it doesn't exist
                        uploads_dir = os.path.join(current_app.static_folder, 'uploads')
                        os.makedirs(uploads_dir, exist_ok=True)
                        
                        # Save file
                        file_path = os.path.join(uploads_dir, unique_filename)
                        file.save(file_path)
                        
                        # Set image URL
                        image_url = f"/static/uploads/{unique_filename}"
                    except Exception as e:
                        return jsonify({'error': f'Błąd podczas uploadu zdjęcia: {str(e)}'}), 400
            
            # Handle URL from form data
            if not image_url:
                if request.is_json:
                    data = request.get_json()
                    image_url = data.get('image_url')
                else:
                    image_url = request.form.get('image_url')
            
            if not image_url:
                return jsonify({'error': 'URL obrazu lub plik jest wymagany'}), 400
            
            # Get next order number
            last_image = BlogPostImage.query.filter_by(post_id=post_id).order_by(BlogPostImage.order.desc()).first()
            next_order = (last_image.order + 1) if last_image else 0
            
            # Get other data from form
            if request.is_json:
                data = request.get_json()
                alt_text = data.get('alt_text', '')
                caption = data.get('caption', '')
                order = data.get('order', next_order)
            else:
                alt_text = request.form.get('alt_text', '')
                caption = request.form.get('caption', '')
                order = int(request.form.get('order', next_order))
            
            image = BlogPostImage(
                post_id=post_id,
                image_url=image_url,
                alt_text=alt_text,
                caption=caption,
                order=order
            )
            
            db.session.add(image)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Obraz został dodany do artykułu',
                'image': {
                    'id': image.id,
                    'image_url': image.image_url,
                    'alt_text': image.alt_text,
                    'caption': image.caption,
                    'order': image.order
                }
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error managing blog post images: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/blog/admin/posts/<int:post_id>/images/<int:image_id>', methods=['PUT', 'DELETE'])
@login_required
def api_blog_post_image(post_id, image_id):
    """Update or delete a specific blog post image"""
    if not current_user.is_admin:
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from models import BlogPost, BlogPostImage
        
        # Check if post exists
        post = BlogPost.query.get_or_404(post_id)
        
        # Get the image
        image = BlogPostImage.query.filter_by(id=image_id, post_id=post_id).first()
        if not image:
            return jsonify({'error': 'Obraz nie został znaleziony'}), 404
        
        if request.method == 'PUT':
            # Update image
            data = request.get_json()
            
            if 'alt_text' in data:
                image.alt_text = data['alt_text']
            if 'caption' in data:
                image.caption = data['caption']
            if 'order' in data:
                image.order = data['order']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Obraz został zaktualizowany',
                'image': {
                    'id': image.id,
                    'image_url': image.image_url,
                    'alt_text': image.alt_text,
                    'caption': image.caption,
                    'order': image.order
                }
            })
        
        elif request.method == 'DELETE':
            # Delete image
            db.session.delete(image)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Obraz został usunięty'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error managing blog post image: {str(e)}")
        return jsonify({'error': str(e)}), 500

# SEO API
@api_bp.route('/seo', methods=['GET', 'POST'])
@login_required
def api_seo():
    """SEO API - Get all or create new SEO settings"""
    if request.method == 'GET':
        try:
            seo_settings = SEOSettings.query.order_by(SEOSettings.page_type.asc()).all()
            return jsonify([{
                'id': seo.id,
                'page_type': seo.page_type,
                'page_title': seo.page_title,
                'meta_description': seo.meta_description,
                'meta_keywords': seo.meta_keywords,
                'og_title': seo.og_title,
                'og_description': seo.og_description,
                'og_image': seo.og_image,
                'og_type': seo.og_type,
                'twitter_card': seo.twitter_card,
                'twitter_title': seo.twitter_title,
                'twitter_description': seo.twitter_description,
                'twitter_image': seo.twitter_image,
                'canonical_url': seo.canonical_url,
                'structured_data': seo.structured_data,
                'is_active': seo.is_active,
                'created_at': seo.created_at.isoformat() if seo.created_at else None,
                'updated_at': seo.updated_at.isoformat() if seo.updated_at else None
            } for seo in seo_settings])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            print(f"SEO POST data: {data}")
            
            if not data:
                return jsonify({'error': 'Brak danych JSON'}), 400
            
            # Check if page_type already exists
            existing = SEOSettings.query.filter_by(page_type=data.get('page_type')).first()
            if existing:
                return jsonify({'error': 'Ustawienia SEO dla tego typu strony już istnieją'}), 400
            
            seo = SEOSettings(
                page_type=data.get('page_type'),
                page_title=data.get('page_title', ''),
                meta_description=data.get('meta_description', ''),
                meta_keywords=data.get('meta_keywords', ''),
                og_title=data.get('og_title', ''),
                og_description=data.get('og_description', ''),
                og_image=data.get('og_image', ''),
                og_type=data.get('og_type', 'website'),
                twitter_card=data.get('twitter_card', ''),
                twitter_title=data.get('twitter_title', ''),
                twitter_description=data.get('twitter_description', ''),
                twitter_image=data.get('twitter_image', ''),
                canonical_url=data.get('canonical_url', ''),
                structured_data=data.get('structured_data', ''),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(seo)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Ustawienia SEO zostały utworzone pomyślnie',
                'id': seo.id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"SEO POST error: {str(e)}")
            return jsonify({'error': str(e)}), 500

@api_bp.route('/seo/<int:seo_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_seo_detail(seo_id):
    """SEO API - Get, update or delete specific SEO settings"""
    try:
        seo = SEOSettings.query.get_or_404(seo_id)
        
        if request.method == 'GET':
            return jsonify({
                'id': seo.id,
                'page_type': seo.page_type,
                'page_title': seo.page_title,
                'meta_description': seo.meta_description,
                'meta_keywords': seo.meta_keywords,
                'og_title': seo.og_title,
                'og_description': seo.og_description,
                'og_image': seo.og_image,
                'og_type': seo.og_type,
                'twitter_card': seo.twitter_card,
                'twitter_title': seo.twitter_title,
                'twitter_description': seo.twitter_description,
                'twitter_image': seo.twitter_image,
                'canonical_url': seo.canonical_url,
                'structured_data': seo.structured_data,
                'is_active': seo.is_active,
                'created_at': seo.created_at.isoformat() if seo.created_at else None,
                'updated_at': seo.updated_at.isoformat() if seo.updated_at else None
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'Brak danych JSON'}), 400
            
            # Update fields
            seo.page_title = data.get('page_title', seo.page_title)
            seo.meta_description = data.get('meta_description', seo.meta_description)
            seo.meta_keywords = data.get('meta_keywords', seo.meta_keywords)
            seo.og_title = data.get('og_title', seo.og_title)
            seo.og_description = data.get('og_description', seo.og_description)
            seo.og_image = data.get('og_image', seo.og_image)
            seo.og_type = data.get('og_type', seo.og_type)
            seo.twitter_card = data.get('twitter_card', seo.twitter_card)
            seo.twitter_title = data.get('twitter_title', seo.twitter_title)
            seo.twitter_description = data.get('twitter_description', seo.twitter_description)
            seo.twitter_image = data.get('twitter_image', seo.twitter_image)
            seo.canonical_url = data.get('canonical_url', seo.canonical_url)
            seo.structured_data = data.get('structured_data', seo.structured_data)
            seo.is_active = data.get('is_active', seo.is_active)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Ustawienia SEO zostały zaktualizowane pomyślnie'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(seo)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Ustawienia SEO zostały usunięte pomyślnie'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Dynamic SEO API endpoints
@api_bp.route('/seo/blog/post/<int:post_id>')
def api_blog_post_seo(post_id):
    """Get SEO settings for specific blog post"""
    try:
        from app.utils.seo import SEOManager
        from models import BlogPost
        post = BlogPost.query.get_or_404(post_id)
        seo_data = SEOManager.generate_blog_post_seo(post)
        return jsonify(seo_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/seo/blog/category/<slug>')
def api_blog_category_seo(slug):
    """Get SEO settings for specific blog category"""
    try:
        from app.utils.seo import SEOManager
        from models import BlogCategory
        category = BlogCategory.query.filter_by(slug=slug).first_or_404()
        seo_data = SEOManager.generate_blog_category_seo(category)
        return jsonify(seo_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/seo/blog/tag/<slug>')
def api_blog_tag_seo(slug):
    """Get SEO settings for specific blog tag"""
    try:
        from app.utils.seo import SEOManager
        from models import BlogTag
        tag = BlogTag.query.filter_by(slug=slug).first_or_404()
        seo_data = SEOManager.generate_blog_tag_seo(tag)
        return jsonify(seo_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/seo/event/<int:event_id>')
def api_event_seo(event_id):
    """Get SEO settings for specific event"""
    try:
        from app.utils.seo import SEOManager
        event = EventSchedule.query.get_or_404(event_id)
        seo_data = SEOManager.generate_event_seo(event)
        return jsonify(seo_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/seo/section/<int:section_id>')
def api_section_seo(section_id):
    """Get SEO settings for specific section"""
    try:
        from app.utils.seo import SEOManager
        section = Section.query.get_or_404(section_id)
        seo_data = SEOManager.generate_section_seo(section)
        return jsonify(seo_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/seo/page-types')
def api_seo_page_types():
    """Get available page types for SEO"""
    try:
        from app.utils.seo import SEOManager
        page_types = SEOManager.get_available_page_types()
        return jsonify(page_types)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/seo/auto-generate', methods=['POST'])
@login_required
def api_auto_generate_seo():
    """Auto-generate SEO for dynamic content"""
    try:
        from app.utils.seo import SEOManager
        from models import BlogPost, BlogCategory, BlogTag
        data = request.get_json()
        content_type = data.get('type')  # 'blog_post', 'blog_category', 'blog_tag', 'event', 'section'
        content_id = data.get('id')
        
        if content_type == 'blog_post':
            post = BlogPost.query.get_or_404(content_id)
            page_type = f'blog_post_{post.id}'
            seo_data = SEOManager.generate_blog_post_seo(post)
        elif content_type == 'blog_category':
            category = BlogCategory.query.get_or_404(content_id)
            page_type = f'blog_category_{category.slug}'
            seo_data = SEOManager.generate_blog_category_seo(category)
        elif content_type == 'blog_tag':
            tag = BlogTag.query.get_or_404(content_id)
            page_type = f'blog_tag_{tag.slug}'
            seo_data = SEOManager.generate_blog_tag_seo(tag)
        elif content_type == 'event':
            event = EventSchedule.query.get_or_404(content_id)
            page_type = f'event_{event.id}'
            seo_data = SEOManager.generate_event_seo(event)
        elif content_type == 'section':
            section = Section.query.get_or_404(content_id)
            page_type = f'section_{section.id}'
            seo_data = SEOManager.generate_section_seo(section)
        else:
            return jsonify({'error': 'Invalid content type'}), 400
        
        # Utwórz ustawienia SEO
        seo = SEOManager.create_or_update_seo(page_type, seo_data)
        
        if seo:
            return jsonify({
                'success': True,
                'message': f'SEO settings generated for {content_type}',
                'seo_id': seo.id
            })
        else:
            return jsonify({'error': 'Failed to create SEO settings'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/seo/page/<page_type>')
def api_seo_by_page_type(page_type):
    """Get SEO settings by page type"""
    try:
        seo = SEOSettings.query.filter_by(page_type=page_type, is_active=True).first()
        
        if not seo:
            return jsonify({'error': 'SEO settings not found'}), 404
        
        return jsonify({
            'page_type': seo.page_type,
            'page_title': seo.page_title,
            'meta_description': seo.meta_description,
            'meta_keywords': seo.meta_keywords,
            'og_title': seo.og_title,
            'og_description': seo.og_description,
            'og_image': seo.og_image,
            'og_type': seo.og_type,
            'twitter_card': seo.twitter_card,
            'twitter_title': seo.twitter_title,
            'twitter_description': seo.twitter_description,
            'twitter_image': seo.twitter_image,
            'canonical_url': seo.canonical_url,
            'structured_data': seo.structured_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Social Media API
@api_bp.route('/social', methods=['GET', 'POST'])
@login_required
def api_social():
    """Social Media API - Get all or create new social media link"""
    if request.method == 'GET':
        try:
            social_links = SocialLink.query.order_by(SocialLink.order.asc()).all()
            
            # Build response with target field (if column exists)
            result = []
            for link in social_links:
                link_data = {
                    'id': link.id,
                    'platform': link.platform,
                    'url': link.url,
                    'icon': link.icon,
                    'order': link.order,
                    'is_active': link.is_active,
                    'created_at': link.created_at.isoformat() if link.created_at else None
                }
                
                # Add target field if column exists
                try:
                    link_data['target'] = link.target
                except Exception as target_error:
                    print(f"Target field read error (column may not exist): {target_error}")
                    link_data['target'] = '_blank'  # Default value
                
                result.append(link_data)
            
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            print(f"Social POST data: {data}")
            print(f"Social POST data type: {type(data)}")
            print(f"Social POST target value: {data.get('target') if data else 'No data'}")
            
            if not data:
                return jsonify({'error': 'Brak danych JSON'}), 400
            
            # Validate required fields
            if not data.get('platform'):
                return jsonify({'error': 'Platforma jest wymagana'}), 400
            
            if not data.get('url'):
                return jsonify({'error': 'URL jest wymagany'}), 400
            
            # Basic URL validation
            import re
            url = data.get('url', '').strip()
            if not re.match(r'^https?://', url):
                return jsonify({'error': 'URL musi zaczynać się od http:// lub https://'}), 400
            
            # Get target value with validation
            target_value = data.get('target', '_blank')
            if not target_value or target_value == 'null' or target_value == 'undefined':
                target_value = '_blank'
            print(f"Using target value: {target_value}")
            
            # Create social link with target field (if column exists)
            try:
                social_link = SocialLink(
                    platform=data.get('platform').strip(),
                    url=url,
                    icon=data.get('icon', ''),
                    target=target_value,
                    order=data.get('order', 0),
                    is_active=data.get('is_active', True)
                )
                print("Created SocialLink with target field")
            except Exception as target_error:
                print(f"Target field error, trying without target: {target_error}")
                # Fallback: create without target field if column doesn't exist
                social_link = SocialLink(
                    platform=data.get('platform').strip(),
                    url=url,
                    icon=data.get('icon', ''),
                    order=data.get('order', 0),
                    is_active=data.get('is_active', True)
                )
                print("Created SocialLink without target field")
            
            db.session.add(social_link)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Link social media został utworzony pomyślnie',
                'id': social_link.id
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Social POST error: {str(e)}")
            return jsonify({'error': str(e)}), 500

@api_bp.route('/social/<int:link_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_social_detail(link_id):
    """Social Media API - Get, update or delete specific social media link"""
    try:
        link = SocialLink.query.get_or_404(link_id)
        
        if request.method == 'GET':
            # Build response with target field (if column exists)
            link_data = {
                'id': link.id,
                'platform': link.platform,
                'url': link.url,
                'icon': link.icon,
                'order': link.order,
                'is_active': link.is_active,
                'created_at': link.created_at.isoformat() if link.created_at else None
            }
            
            # Add target field if column exists
            try:
                link_data['target'] = link.target
            except Exception as target_error:
                print(f"Target field read error (column may not exist): {target_error}")
                link_data['target'] = '_blank'  # Default value
            
            return jsonify({
                'success': True,
                'link': link_data
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'Brak danych JSON'}), 400
            
            # Validate URL format if provided
            import re
            url = data.get('url', link.url).strip()
            if url and not re.match(r'^https?://', url):
                return jsonify({'error': 'URL musi zaczynać się od http:// lub https://'}), 400
            
            # Update fields
            link.platform = data.get('platform', link.platform)
            link.url = url if url else link.url
            link.icon = data.get('icon', link.icon)
            
            # Update target field (if column exists)
            try:
                link.target = data.get('target', link.target)
            except Exception as target_error:
                print(f"Target field update error (column may not exist): {target_error}")
                # Target column doesn't exist yet, skip this field
            
            link.order = data.get('order', link.order)
            link.is_active = data.get('is_active', link.is_active)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Link social media został zaktualizowany pomyślnie'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(link)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Link social media został usunięty pomyślnie'
            })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/social/bulk-delete', methods=['DELETE'])
@login_required
def api_social_bulk_delete():
    """Bulk delete social media links"""
    try:
        data = request.get_json()
        
        if not data or 'ids' not in data:
            return jsonify({'error': 'Brak listy ID do usunięcia'}), 400
        
        link_ids = data.get('ids', [])
        if not link_ids:
            return jsonify({'error': 'Lista ID nie może być pusta'}), 400
        
        # Validate that all IDs are integers
        try:
            link_ids = [int(id) for id in link_ids]
        except (ValueError, TypeError):
            return jsonify({'error': 'Nieprawidłowy format ID'}), 400
        
        # Find and delete links
        deleted_count = 0
        for link_id in link_ids:
            link = SocialLink.query.get(link_id)
            if link:
                db.session.delete(link)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} link{deleted_count == 1 and "" or (deleted_count < 5 and "i" or "ów")} pomyślnie',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/social/public', methods=['GET'])
def api_social_public():
    """Get active social media links (public endpoint)"""
    try:
        links = SocialLink.query.filter_by(is_active=True).order_by(SocialLink.order.asc()).all()
        
        return jsonify([{
            'id': link.id,
            'platform': link.platform,
            'url': link.url,
            'icon': link.icon,
            'target': link.target,
            'order': link.order
        } for link in links])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Email System API endpoints

# Unsubscribe and Account Management API endpoints

def generate_unsubscribe_token(email, action='unsubscribe'):
    """Generuje token do wypisania się lub usunięcia konta"""
    secret_key = os.getenv('SECRET_KEY', 'default-secret-key')
    message = f"{email}:{action}"
    token = hmac.new(
        secret_key.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return token

def verify_unsubscribe_token(email, action, token):
    """Weryfikuje token do wypisania się lub usunięcia konta"""
    expected_token = generate_unsubscribe_token(email, action)
    return hmac.compare_digest(token, expected_token)

@api_bp.route('/unsubscribe/<email>/<token>', methods=['GET'])
def unsubscribe(email, token):
    """Wypisanie się z listy mailingowej"""
    try:
        if not verify_unsubscribe_token(email, 'unsubscribe', token):
            return jsonify({'success': False, 'message': 'Nieprawidłowy lub wygasły token'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        if user:
            # Unsubscribe from club
            user.club_member = False
            db.session.commit()
            return jsonify({'success': True, 'message': 'Pomyślnie wypisano z klubu'})
        else:
            return jsonify({'success': False, 'message': 'Użytkownik nie został znaleziony'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Błąd wypisywania: {str(e)}'}), 500

@api_bp.route('/delete-account/<email>/<token>', methods=['DELETE'])
def delete_account(email, token):
    """Usunięcie konta użytkownika"""
    try:
        if not verify_unsubscribe_token(email, 'delete_account', token):
            return jsonify({'success': False, 'message': 'Nieprawidłowy lub wygasły token'}), 400
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        if user:
            # Delete user account
            db.session.delete(user)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Konto zostało pomyślnie usunięte'})
        else:
            return jsonify({'success': False, 'message': 'Użytkownik nie został znaleziony'}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Błąd usuwania konta: {str(e)}'}), 500

# Blog Comments API
@api_bp.route('/blog/comments', methods=['GET'])
@login_required
def api_blog_comments():
    """Get blog comments"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        from models import BlogComment
        comments = BlogComment.query.order_by(BlogComment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'comments': [{
                'id': comment.id,
                'author_name': comment.author_name,
                'author_email': comment.author_email,
                'author_website': comment.author_website,
                'content': comment.content,
                'is_approved': comment.is_approved,
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
                'post': {
                    'id': comment.post.id,
                    'title': comment.post.title,
                    'slug': comment.post.slug
                }
            } for comment in comments.items],
            'pagination': {
                'page': comments.page,
                'pages': comments.pages,
                'per_page': comments.per_page,
                'total': comments.total,
                'has_next': comments.has_next,
                'has_prev': comments.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/blog/comments/<int:comment_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_blog_comment(comment_id):
    """Manage single blog comment"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
        
        from models import BlogComment
        comment = BlogComment.query.get_or_404(comment_id)
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'author_name': comment.author_name,
                    'author_email': comment.author_email,
                    'author_website': comment.author_website,
                    'content': comment.content,
                    'is_approved': comment.is_approved,
                    'created_at': comment.created_at.isoformat() if comment.created_at else None,
                    'post': {
                        'id': comment.post.id,
                        'title': comment.post.title,
                        'slug': comment.post.slug
                    }
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            comment.author_name = data.get('author_name', comment.author_name)
            comment.author_email = data.get('author_email', comment.author_email)
            comment.author_website = data.get('author_website', comment.author_website)
            comment.content = data.get('content', comment.content)
            comment.is_approved = data.get('is_approved', comment.is_approved)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Komentarz został zaktualizowany'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(comment)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Komentarz został usunięty'
            })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/blog/comments/<int:comment_id>/approve', methods=['POST'])
@login_required
def api_blog_comment_approve(comment_id):
    """Approve blog comment"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
        
        from models import BlogComment
        comment = BlogComment.query.get_or_404(comment_id)
        
        comment.is_approved = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Komentarz został zatwierdzony'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/blog/comments/bulk-delete', methods=['POST'])
@login_required
def api_blog_comments_bulk_delete():
    """Bulk delete blog comments"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
        
        data = request.get_json()
        comment_ids = data.get('ids', [])
        
        if not comment_ids:
            return jsonify({'error': 'Brak komentarzy do usunięcia'}), 400
        
        from models import BlogComment
        comments = BlogComment.query.filter(BlogComment.id.in_(comment_ids)).all()
        
        for comment in comments:
            db.session.delete(comment)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {len(comments)} komentarzy'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Blog Tags API
@api_bp.route('/blog/tags', methods=['GET', 'POST'])
@login_required
def api_blog_tags():
    """Manage blog tags"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
        
        from models import BlogTag
        
        if request.method == 'GET':
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            tags = BlogTag.query.order_by(BlogTag.name).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return jsonify({
                'success': True,
                'tags': [{
                    'id': tag.id,
                    'name': tag.name,
                    'slug': tag.slug,
                    'is_active': tag.is_active,
                    'posts_count': len(tag.posts),
                    'created_at': tag.created_at.isoformat() if tag.created_at else None
                } for tag in tags.items],
                'pagination': {
                    'page': tags.page,
                    'pages': tags.pages,
                    'per_page': tags.per_page,
                    'total': tags.total,
                    'has_next': tags.has_next,
                    'has_prev': tags.has_prev
                }
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            
            name = data.get('name', '').strip()
            if not name:
                return jsonify({'error': 'Nazwa tagu jest wymagana'}), 400
            
            # Check if tag already exists
            existing_tag = BlogTag.query.filter_by(name=name).first()
            if existing_tag:
                return jsonify({'error': 'Tag o tej nazwie już istnieje'}), 400
            
            # Generate slug
            from app.utils.validation import generate_slug
            slug = generate_slug(name)
            
            tag = BlogTag(
                name=name,
                slug=slug,
                is_active=data.get('is_active', True)
            )
            
            db.session.add(tag)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Tag został dodany',
                'tag': {
                    'id': tag.id,
                    'name': tag.name,
                    'slug': tag.slug,
                    'is_active': tag.is_active
                }
            })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/blog/tags/<int:tag_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_blog_tag(tag_id):
    """Manage single blog tag"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
        
        from models import BlogTag
        tag = BlogTag.query.get_or_404(tag_id)
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'tag': {
                    'id': tag.id,
                    'name': tag.name,
                    'slug': tag.slug,
                    'is_active': tag.is_active,
                    'posts_count': len(tag.posts),
                    'created_at': tag.created_at.isoformat() if tag.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            name = data.get('name', '').strip()
            if not name:
                return jsonify({'error': 'Nazwa tagu jest wymagana'}), 400
            
            # Check if tag with this name already exists (excluding current tag)
            existing_tag = BlogTag.query.filter(BlogTag.name == name, BlogTag.id != tag.id).first()
            if existing_tag:
                return jsonify({'error': 'Tag o tej nazwie już istnieje'}), 400
            
            # Generate slug if name changed
            if name != tag.name:
                from app.utils.validation import generate_slug
                tag.slug = generate_slug(name)
            
            tag.name = name
            tag.is_active = data.get('is_active', tag.is_active)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Tag został zaktualizowany'
            })
        
        elif request.method == 'DELETE':
            # Check if tag is used by any posts
            if tag.posts:
                return jsonify({'error': 'Nie można usunąć tagu, który jest używany przez artykuły'}), 400
            
            db.session.delete(tag)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Tag został usunięty'
            })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/blog/admin/categories/bulk-delete', methods=['POST'])
@login_required
def api_blog_categories_bulk_delete():
    """Bulk delete blog categories"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
        
        data = request.get_json()
        category_ids = data.get('ids', [])
        
        if not category_ids:
            return jsonify({'error': 'Brak kategorii do usunięcia'}), 400
        
        from models import BlogCategory
        categories = BlogCategory.query.filter(BlogCategory.id.in_(category_ids)).all()
        
        # Check if any category is used by posts
        used_categories = [cat for cat in categories if cat.posts]
        if used_categories:
            return jsonify({'error': f'Nie można usunąć kategorii używanych przez artykuły: {", ".join([cat.title for cat in used_categories])}'}), 400
        
        # Check if any category has child categories
        child_categories = [cat for cat in categories if cat.children]
        if child_categories:
            return jsonify({'error': f'Nie można usunąć kategorii z podkategoriami: {", ".join([cat.title for cat in child_categories])}'}), 400
        
        for category in categories:
            db.session.delete(category)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {len(categories)} kategorii'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/blog/tags/bulk-delete', methods=['POST'])
@login_required
def api_blog_tags_bulk_delete():
    """Bulk delete blog tags"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
        
        data = request.get_json()
        tag_ids = data.get('ids', [])
        
        if not tag_ids:
            return jsonify({'error': 'Brak tagów do usunięcia'}), 400
        
        from models import BlogTag
        tags = BlogTag.query.filter(BlogTag.id.in_(tag_ids)).all()
        
        # Check if any tag is used by posts
        used_tags = [tag for tag in tags if tag.posts]
        if used_tags:
            return jsonify({'error': f'Nie można usunąć tagów używanych przez artykuły: {", ".join([tag.name for tag in used_tags])}'}), 400
        
        for tag in tags:
            db.session.delete(tag)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {len(tags)} tagów'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/bulk-delete/menu', methods=['POST'])
@login_required
def api_bulk_delete_menu():
    """Bulk delete menu items"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
            
        data = request.get_json()
        menu_ids = data.get('ids', [])
        
        if not menu_ids:
            return jsonify({'error': 'Brak elementów do usunięcia'}), 400
        
        from models import MenuItem
        deleted_count = MenuItem.query.filter(MenuItem.id.in_(menu_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} elementów menu',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/bulk-delete/benefits', methods=['POST'])
@login_required
def api_bulk_delete_benefits():
    """Bulk delete benefits"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
            
        data = request.get_json()
        benefit_ids = data.get('ids', [])
        
        if not benefit_ids:
            return jsonify({'error': 'Brak korzyści do usunięcia'}), 400
        
        from models import BenefitItem
        deleted_count = BenefitItem.query.filter(BenefitItem.id.in_(benefit_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} korzyści',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/bulk-delete/sections', methods=['POST'])
@login_required
def api_bulk_delete_sections():
    """Bulk delete sections"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
            
        data = request.get_json()
        section_ids = data.get('ids', [])
        
        if not section_ids:
            return jsonify({'error': 'Brak sekcji do usunięcia'}), 400
        
        from models import Section
        deleted_count = Section.query.filter(Section.id.in_(section_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} sekcji',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/bulk-delete/testimonials', methods=['POST'])
@login_required
def api_bulk_delete_testimonials():
    """Bulk delete testimonials"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
            
        data = request.get_json()
        testimonial_ids = data.get('ids', [])
        
        if not testimonial_ids:
            return jsonify({'error': 'Brak opinii do usunięcia'}), 400
        
        from models import Testimonial
        deleted_count = Testimonial.query.filter(Testimonial.id.in_(testimonial_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} opinii',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/bulk-delete/faq', methods=['POST'])
@login_required
def api_bulk_delete_faq():
    """Bulk delete FAQ"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
            
        data = request.get_json()
        faq_ids = data.get('ids', [])
        
        if not faq_ids:
            return jsonify({'error': 'Brak pytań do usunięcia'}), 400
        
        from models import FAQ
        deleted_count = FAQ.query.filter(FAQ.id.in_(faq_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} pytań',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/bulk-delete/email-templates', methods=['POST'])
@login_required
def api_bulk_delete_email_templates():
    """Bulk delete email templates"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
            
        data = request.get_json()
        template_ids = data.get('ids', [])
        
        if not template_ids:
            return jsonify({'error': 'Brak szablonów do usunięcia'}), 400
        
        from models import EmailTemplate
        # Don't allow deleting default templates
        templates = EmailTemplate.query.filter(EmailTemplate.id.in_(template_ids)).all()
        default_templates = [t for t in templates if t.is_default]
        
        if default_templates:
            return jsonify({'error': f'Nie można usunąć domyślnych szablonów: {", ".join([t.name for t in default_templates])}'}), 400
        
        deleted_count = EmailTemplate.query.filter(
            EmailTemplate.id.in_(template_ids),
            EmailTemplate.is_default == False
        ).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} szablonów',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/bulk-delete/email-groups', methods=['POST'])
@login_required
def api_bulk_delete_email_groups():
    """Bulk delete email groups"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
            
        data = request.get_json()
        group_ids = data.get('ids', [])
        
        if not group_ids:
            return jsonify({'error': 'Brak grup do usunięcia'}), 400
        
        from models import EmailGroup
        # Don't allow deleting default groups
        groups = EmailGroup.query.filter(EmailGroup.id.in_(group_ids)).all()
        default_groups = [g for g in groups if g.is_default]
        
        if default_groups:
            return jsonify({'error': f'Nie można usunąć domyślnych grup: {", ".join([g.name for g in default_groups])}'}), 400
        
        deleted_count = EmailGroup.query.filter(
            EmailGroup.id.in_(group_ids),
            EmailGroup.is_default == False
        ).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} grup',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/bulk-delete/email-campaigns', methods=['POST'])
@login_required
def api_bulk_delete_email_campaigns():
    """Bulk delete email campaigns"""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Brak uprawnień'}), 403
            
        data = request.get_json()
        campaign_ids = data.get('ids', [])
        
        if not campaign_ids:
            return jsonify({'error': 'Brak kampanii do usunięcia'}), 400
        
        from models import EmailCampaign
        # Don't allow deleting sent campaigns
        campaigns = EmailCampaign.query.filter(EmailCampaign.id.in_(campaign_ids)).all()
        sent_campaigns = [c for c in campaigns if c.status in ['sending', 'sent', 'completed']]
        
        if sent_campaigns:
            return jsonify({'error': f'Nie można usunąć wysłanych kampanii: {", ".join([c.name for c in sent_campaigns])}'}), 400
        
        deleted_count = EmailCampaign.query.filter(
            EmailCampaign.id.in_(campaign_ids),
            ~EmailCampaign.status.in_(['sending', 'sent', 'completed'])
        ).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} kampanii',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
