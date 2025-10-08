"""
CRM Agent API - agent work interface
"""
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import User, db
from app.models.crm_model import Contact, Call, ImportFile, BlacklistEntry
from datetime import datetime
from app.services.twilio_service import twilio_service

logger = logging.getLogger(__name__)

# Create Agent API blueprint
agent_api_bp = Blueprint('crm_agent_api', __name__)

def ankieter_required(f):
    """Decorator to require ankieter role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        if not (current_user.is_ankieter_role() or current_user.is_admin_role()):
            return jsonify({'success': False, 'error': 'Ankieter role required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@agent_api_bp.route('/crm/agent/start-work', methods=['POST'])
@login_required
@ankieter_required
def start_work():
    """Start work session for ankieter"""
    try:
        # Log work start
        from app.models.user_logs_model import UserLogs
        log_entry = UserLogs(
            user_id=current_user.id,
            action_type='work_start',
            details={'timestamp': datetime.now().isoformat()}
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Work session started',
            'ankieter': {
                'id': current_user.id,
                'name': current_user.first_name or current_user.email,
                'role': current_user.account_type
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd rozpoczęcia pracy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/crm/agent/stop-work', methods=['POST'])
@login_required
@ankieter_required
def stop_work():
    """Stop work session for ankieter"""
    try:
        # Log work stop
        from app.models.user_logs_model import UserLogs
        log_entry = UserLogs(
            user_id=current_user.id,
            action_type='work_stop',
            details={'timestamp': datetime.now().isoformat()}
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Work session stopped'
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd zatrzymania pracy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/crm/agent/next-contact', methods=['POST'])
@login_required
@ankieter_required
def get_next_contact():
    """Get next contact for agent to call"""
    try:
        from app.services.crm_queue_manager import QueueManager
        
        # Get next contact from queue
        next_contact = QueueManager.get_next_contact_for_ankieter(current_user.id)
        
        if next_contact:
            # Get contact's call history
            call_history = Call.query.filter_by(contact_id=next_contact.id).order_by(Call.call_date.desc()).limit(5).all()
            
            history = []
            for call in call_history:
                history.append({
                    'id': call.id,
                    'call_date': call.call_date.isoformat(),
                    'status': call.status,
                    'notes': call.notes,
                    'duration_minutes': call.duration_minutes
                })
            
            return jsonify({
                'success': True,
                'contact': {
                    'id': next_contact.id,
                    'name': next_contact.name,
                    'phone': next_contact.phone,
                    'email': next_contact.email,
                    'company': next_contact.company,
                    'notes': next_contact.notes,
                    'call_attempts': next_contact.call_attempts,
                    'max_call_attempts': next_contact.max_call_attempts,
                    'tags': next_contact.get_tags(),
                    'last_call_date': next_contact.last_call_date.isoformat() if next_contact.last_call_date else None
                },
                'call_history': history
            })
        else:
            return jsonify({
                'success': True,
                'contact': None,
                'message': 'No contacts in queue'
            })
            
    except Exception as e:
        logger.error(f"❌ Błąd pobierania następnego kontaktu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/crm/agent/call-history/<int:contact_id>')
@login_required
@ankieter_required
def get_call_history(contact_id):
    """Get call history for specific contact"""
    try:
        # Verify contact belongs to ankieter
        contact = Contact.query.filter_by(
            id=contact_id,
            assigned_ankieter_id=current_user.id
        ).first()
        
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found or access denied'}), 404
        
        # Get call history
        calls = Call.query.filter_by(contact_id=contact_id).order_by(Call.call_date.desc()).all()
        
        call_history = []
        for call in calls:
            call_history.append({
                'id': call.id,
                'call_date': call.call_date.isoformat(),
                'status': call.status,
                'notes': call.notes,
                'duration_minutes': call.duration_minutes,
                'next_call_date': call.next_call_date.isoformat() if call.next_call_date else None,
                'is_lead_registered': call.is_lead_registered
            })
        
        return jsonify({
            'success': True,
            'contact': {
                'id': contact.id,
                'name': contact.name,
                'phone': contact.phone,
                'email': contact.email,
                'company': contact.company
            },
            'call_history': call_history
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania historii rozmów: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/crm/agent/start-call', methods=['POST'])
@login_required
@ankieter_required
def start_call():
    """Start a call session"""
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        
        if not contact_id:
            return jsonify({'success': False, 'error': 'Contact ID required'}), 400
        
        # Get contact
        contact = Contact.query.filter_by(
            id=contact_id,
            assigned_ankieter_id=current_user.id
        ).first()
        
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        # Check if contact is blacklisted
        if contact.is_blacklisted:
            return jsonify({'success': False, 'error': 'Contact is blacklisted'}), 400
        
        # Check if max attempts reached
        if contact.call_attempts >= contact.max_call_attempts:
            return jsonify({'success': False, 'error': 'Maximum call attempts reached'}), 400
        
        # Create call record
        call = Call(
            contact_id=contact_id,
            ankieter_id=current_user.id,
            call_date=datetime.now(),
            status='in_progress',
            priority='normal'
        )
        
        db.session.add(call)
        db.session.commit()
        
        # Log call start
        from app.models.user_logs_model import UserLogs
        log_entry = UserLogs(
            user_id=current_user.id,
            action_type='call_start',
            details={
                'contact_id': contact_id,
                'call_id': call.id,
                'timestamp': datetime.now().isoformat()
            }
        )
        db.session.add(log_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Call started',
            'call_id': call.id,
            'contact': {
                'id': contact.id,
                'name': contact.name,
                'phone': contact.phone,
                'company': contact.company
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd rozpoczęcia rozmowy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/crm/agent/ice-candidate', methods=['POST'])
@login_required
@ankieter_required
def handle_ice_candidate():
    """Handle ICE candidate for WebRTC"""
    try:
        data = request.get_json()
        candidate = data.get('candidate')
        
        # Store ICE candidate for WebRTC connection
        # This would typically be handled by a WebRTC service
        
        return jsonify({
            'success': True,
            'message': 'ICE candidate processed'
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd ICE candidate: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/crm/agent/save-outcome', methods=['POST'])
@login_required
@ankieter_required
def save_call_outcome():
    """Save call outcome and process result"""
    try:
        data = request.get_json()
        
        contact_id = data.get('contact_id')
        call_status = data.get('call_status')
        call_notes = data.get('call_notes', '')
        event_id = data.get('event_id')
        callback_date = data.get('callback_date')
        duration_minutes = data.get('duration_minutes', 0)
        
        if not contact_id or not call_status:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Get contact
        contact = Contact.query.filter_by(
            id=contact_id,
            assigned_ankieter_id=current_user.id
        ).first()
        
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        # Process call result using QueueManager
        from app.services.crm_queue_manager import QueueManager
        
        result = QueueManager.process_call_result(
            contact_id=contact_id,
            ankieter_id=current_user.id,
            call_status=call_status,
            notes=call_notes,
            callback_date=callback_date,
            event_id=event_id,
            duration_minutes=duration_minutes
        )
        
        if result['success']:
            # Log call completion
            from app.models.user_logs_model import UserLogs
            log_entry = UserLogs(
                user_id=current_user.id,
                action_type='call_complete',
                details={
                    'contact_id': contact_id,
                    'call_status': call_status,
                    'duration_minutes': duration_minutes,
                    'timestamp': datetime.now().isoformat()
                }
            )
            db.session.add(log_entry)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'next_contact': result.get('next_contact')
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"❌ Błąd zapisywania wyniku rozmowy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/crm/agent/queue-status')
@login_required
@ankieter_required
def queue_status():
    """Get queue status for ankieter (redirects to stats API)"""
    try:
        from app.services.crm_queue_manager import QueueManager
        
        # Get queue statistics only
        queue_stats = QueueManager.get_ankieter_queue_stats(current_user.id)
        
        return jsonify({
            'success': True,
            'queue': queue_stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statusu kolejki: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/crm/agent/add-contact-note', methods=['POST'])
@login_required
@ankieter_required
def add_contact_note():
    """Add note to contact"""
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        note = data.get('note')
        
        if not contact_id or not note:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Get contact
        contact = Contact.query.filter_by(
            id=contact_id,
            assigned_ankieter_id=current_user.id
        ).first()
        
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        # Add note
        current_notes = contact.notes or ''
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        new_note = f"[{timestamp}] {current_user.first_name or 'Agent'}: {note}"

        if current_notes:
            all_notes = current_notes + '\n\n' + new_note
            contact.notes = sort_notes_by_date(all_notes)
        else:
            contact.notes = new_note
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Note added successfully',
            'notes': contact.notes
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd dodawania notatki: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def sort_notes_by_date(notes_text):
    """Sort notes by date, newest first"""
    if not notes_text:
        return notes_text
    notes = [note.strip() for note in notes_text.split('\n\n') if note.strip()]
    def extract_timestamp(note):
        import re
        match = re.match(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]', note)
        if match:
            from datetime import datetime
            return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M')
        return datetime.min
    notes.sort(key=extract_timestamp, reverse=True)
    return '\n\n'.join(notes)

@agent_api_bp.route('/crm/agent/sort-contact-notes/<int:contact_id>', methods=['POST'])
@login_required
@ankieter_required
def sort_contact_notes(contact_id):
    """Sort contact notes by date"""
    try:
        # Get contact
        contact = Contact.query.filter_by(
            id=contact_id,
            assigned_ankieter_id=current_user.id
        ).first()
        
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        # Sort notes
        if contact.notes:
            contact.notes = sort_notes_by_date(contact.notes)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Notes sorted successfully',
                'notes': contact.notes
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No notes to sort',
                'notes': ''
            })
        
    except Exception as e:
        logger.error(f"❌ Błąd sortowania notatek: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/crm/agent/contact/<int:contact_id>')
@login_required
@ankieter_required
def get_contact_details(contact_id):
    """Get detailed contact information"""
    try:
        # Get contact
        contact = Contact.query.filter_by(
            id=contact_id,
            assigned_ankieter_id=current_user.id
        ).first()
        
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        return jsonify({
            'success': True,
            'contact': {
                'id': contact.id,
                'name': contact.name,
                'phone': contact.phone,
                'email': contact.email,
                'company': contact.company,
                'notes': contact.notes,
                'tags': contact.get_tags(),
                'call_attempts': contact.call_attempts,
                'max_call_attempts': contact.max_call_attempts,
                'last_call_date': contact.last_call_date.isoformat() if contact.last_call_date else None,
                'created_at': contact.created_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania szczegółów kontaktu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/crm/agent/campaigns', methods=['GET'])
@login_required
@ankieter_required
def get_campaigns():
    """Get campaigns for agent"""
    try:
        from app.models.crm_model import Campaign
        
        campaigns = Campaign.query.filter_by(is_active=True).all()
        
        campaigns_data = []
        for campaign in campaigns:
            campaigns_data.append({
                'id': campaign.id,
                'name': campaign.name,
                'description': campaign.description,
                'script_content': campaign.script_content
            })
        
        return jsonify({
            'success': True,
            'campaigns': campaigns_data
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/crm/agent/campaign/<int:campaign_id>/script', methods=['GET'])
@login_required
@ankieter_required
def get_campaign_script(campaign_id):
    """Get campaign script for agent"""
    try:
        from app.models.crm_model import Campaign
        
        campaign = Campaign.query.filter_by(
            id=campaign_id,
            is_active=True
        ).first()
        
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        return jsonify({
            'success': True,
            'script': {
                'id': campaign.id,
                'name': campaign.name,
                'description': campaign.description,
                'script_content': campaign.script_content
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania skryptu kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

