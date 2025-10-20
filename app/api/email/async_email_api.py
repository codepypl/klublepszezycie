"""
Async Email API - Asynchroniczne dodawanie emaili do kolejki
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import logging

from app import db
from app.models import User, EmailTemplate, EventSchedule
from app.services.email_cron_service import email_cron_service
from app.utils.timezone_utils import get_local_now

logger = logging.getLogger(__name__)

async_email_bp = Blueprint('async_email', __name__, url_prefix='/api/email/async')

@async_email_bp.route('/send', methods=['POST'])
@login_required
def send_email_async():
    """
    Dodaje email do kolejki asynchronicznie
    
    Body:
        {
            "to_email": "user@example.com",
            "template_name": "welcome",
            "context": {"name": "John", "event_title": "Meeting"},
            "priority": 2,
            "scheduled_at": "2024-01-01T10:00:00Z",  # opcjonalne
            "event_id": 123,  # opcjonalne
            "campaign_id": 456  # opcjonalne
        }
    """
    try:
        data = request.get_json()
        
        # Walidacja wymaganych pól
        required_fields = ['to_email', 'template_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Brakuje wymaganego pola: {field}'
                }), 400
        
        # Walidacja emaila
        to_email = data['to_email']
        if not to_email or '@' not in to_email:
            return jsonify({
                'success': False,
                'error': 'Nieprawidłowy adres email'
            }), 400
        
        # Walidacja szablonu
        template_name = data['template_name']
        template = EmailTemplate.query.filter_by(name=template_name, is_active=True).first()
        if not template:
            return jsonify({
                'success': False,
                'error': f'Szablon {template_name} nie istnieje'
            }), 400
        
        # Przygotuj parametry
        context = data.get('context', {})
        priority = data.get('priority', 2)
        scheduled_at = None
        
        if data.get('scheduled_at'):
            try:
                scheduled_at = datetime.fromisoformat(data['scheduled_at'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Nieprawidłowy format daty scheduled_at'
                }), 400
        
        event_id = data.get('event_id')
        campaign_id = data.get('campaign_id')
        
        # Dodaj email do kolejki
        success, message, email_id = email_cron_service.add_email_to_queue(
            to_email=to_email,
            template_name=template_name,
            context=context,
            priority=priority,
            scheduled_at=scheduled_at,
            event_id=event_id,
            campaign_id=campaign_id
        )
        
        if success:
            logger.info(f"✅ Email dodany do kolejki: {to_email} ({template_name}) przez {current_user.email}")
            return jsonify({
                'success': True,
                'message': message,
                'email_id': email_id
            })
        else:
            logger.warning(f"⚠️ Błąd dodawania emaila: {message}")
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Błąd API send_email_async: {e}")
        return jsonify({
            'success': False,
            'error': 'Błąd serwera'
        }), 500

@async_email_bp.route('/send-batch', methods=['POST'])
@login_required
def send_batch_emails_async():
    """
    Dodaje wiele emaili do kolejki asynchronicznie
    
    Body:
        {
            "emails": [
                {
                    "to_email": "user1@example.com",
                    "template_name": "welcome",
                    "context": {"name": "John"}
                },
                {
                    "to_email": "user2@example.com", 
                    "template_name": "reminder",
                    "context": {"event_title": "Meeting"}
                }
            ],
            "priority": 2,
            "campaign_id": 456
        }
    """
    try:
        data = request.get_json()
        
        if 'emails' not in data or not isinstance(data['emails'], list):
            return jsonify({
                'success': False,
                'error': 'Brakuje listy emaili'
            }), 400
        
        emails = data['emails']
        if len(emails) > 1000:  # Limit bezpieczeństwa
            return jsonify({
                'success': False,
                'error': 'Maksymalnie 1000 emaili na raz'
            }), 400
        
        priority = data.get('priority', 2)
        campaign_id = data.get('campaign_id')
        
        results = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for i, email_data in enumerate(emails):
            try:
                success, message, email_id = email_cron_service.add_email_to_queue(
                    to_email=email_data['to_email'],
                    template_name=email_data['template_name'],
                    context=email_data.get('context', {}),
                    priority=priority,
                    campaign_id=campaign_id
                )
                
                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'index': i,
                        'email': email_data['to_email'],
                        'error': message
                    })
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'index': i,
                    'email': email_data.get('to_email', 'unknown'),
                    'error': str(e)
                })
        
        logger.info(f"✅ Batch email: {results['success']} sukces, {results['failed']} błąd")
        
        return jsonify({
            'success': True,
            'message': f'Przetworzono {len(emails)} emaili',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd API send_batch_emails_async: {e}")
        return jsonify({
            'success': False,
            'error': 'Błąd serwera'
        }), 500

@async_email_bp.route('/schedule-event-reminder', methods=['POST'])
@login_required
def schedule_event_reminder():
    """
    Planuje przypomnienia o wydarzeniu
    
    Body:
        {
            "event_id": 123,
            "reminder_times": ["24h", "1h", "5min"],
            "template_name": "event_reminder"
        }
    """
    try:
        data = request.get_json()
        
        event_id = data.get('event_id')
        if not event_id:
            return jsonify({
                'success': False,
                'error': 'Brakuje event_id'
            }), 400
        
        # Pobierz wydarzenie
        event = EventSchedule.query.get(event_id)
        if not event:
            return jsonify({
                'success': False,
                'error': 'Wydarzenie nie istnieje'
            }), 400
        
        reminder_times = data.get('reminder_times', ['24h', '1h', '5min'])
        template_name = data.get('template_name', 'event_reminder')
        
        # Sprawdź szablon
        template = EmailTemplate.query.filter_by(name=template_name, is_active=True).first()
        if not template:
            return jsonify({
                'success': False,
                'error': f'Szablon {template_name} nie istnieje'
            }), 400
        
        # Pobierz uczestników wydarzenia
        from app.models import UserGroupMember, UserGroup
        participants = db.session.query(User).join(
            UserGroupMember, User.id == UserGroupMember.user_id
        ).join(
            UserGroup, UserGroupMember.group_id == UserGroup.id
        ).filter(
            UserGroup.event_id == event_id,
            UserGroupMember.status == 'active'
        ).all()
        
        if not participants:
            return jsonify({
                'success': False,
                'error': 'Brak uczestników wydarzenia'
            }), 400
        
        # Zaplanuj przypomnienia
        scheduled_count = 0
        reminder_offsets = {
            '24h': timedelta(hours=24),
            '1h': timedelta(hours=1),
            '5min': timedelta(minutes=5)
        }
        
        for participant in participants:
            for reminder_time in reminder_times:
                if reminder_time not in reminder_offsets:
                    continue
                
                # Oblicz czas wysłania
                reminder_datetime = event.start_time - reminder_offsets[reminder_time]
                
                # Sprawdź czy nie w przeszłości
                if reminder_datetime <= get_local_now():
                    continue
                
                # Przygotuj kontekst
                context = {
                    'user_name': participant.first_name or participant.email,
                    'event_title': event.title,
                    'event_date': event.start_time.strftime('%Y-%m-%d %H:%M'),
                    'event_url': event.get_event_url(),
                    'reminder_time': reminder_time
                }
                
                # Dodaj do kolejki
                success, message, email_id = email_cron_service.add_email_to_queue(
                    to_email=participant.email,
                    template_name=template_name,
                    context=context,
                    priority=1,  # Priorytet dla wydarzeń
                    scheduled_at=reminder_datetime,
                    event_id=event_id
                )
                
                if success:
                    scheduled_count += 1
        
        logger.info(f"✅ Zaplanowano {scheduled_count} przypomnień o wydarzeniu {event_id}")
        
        return jsonify({
            'success': True,
            'message': f'Zaplanowano {scheduled_count} przypomnień',
            'scheduled_count': scheduled_count,
            'participants_count': len(participants)
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd API schedule_event_reminder: {e}")
        return jsonify({
            'success': False,
            'error': 'Błąd serwera'
        }), 500

@async_email_bp.route('/stats', methods=['GET'])
@login_required
def get_queue_stats():
    """Zwraca statystyki kolejki emaili"""
    try:
        stats = email_cron_service.get_queue_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd API get_queue_stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Błąd serwera'
        }), 500

@async_email_bp.route('/cleanup', methods=['POST'])
@login_required
def cleanup_old_emails():
    """Czyści stare emaile z kolejki"""
    try:
        days = request.json.get('days', 30) if request.json else 30
        
        if not isinstance(days, int) or days < 1:
            return jsonify({
                'success': False,
                'error': 'Nieprawidłowa liczba dni'
            }), 400
        
        deleted_count = email_cron_service.cleanup_old_emails(days=days)
        
        logger.info(f"🗑️ Usunięto {deleted_count} starych emaili przez {current_user.email}")
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} starych emaili',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd API cleanup_old_emails: {e}")
        return jsonify({
            'success': False,
            'error': 'Błąd serwera'
        }), 500

