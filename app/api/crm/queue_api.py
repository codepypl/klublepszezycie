"""
CRM Queue API - queue and call management
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.services.crm_queue_manager import QueueManager
import logging

logger = logging.getLogger(__name__)

# Create Queue API blueprint
queue_api_bp = Blueprint('crm_queue_api', __name__)

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

@queue_api_bp.route('/crm/calls/process', methods=['POST'])
@login_required
@ankieter_required
def process_call():
    """Process call result"""
    try:
        data = request.get_json()
        
        contact_id = data.get('contact_id')
        call_status = data.get('callStatus')
        event_id = data.get('eventId')
        callback_date = data.get('callbackDate')
        call_notes = data.get('callNotes', '')
        
        if not contact_id or not call_status:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Process call result
        result = QueueManager.process_call_result(
            contact_id=contact_id,
            ankieter_id=current_user.id,
            call_status=call_status,
            event_id=event_id,
            callback_date=callback_date,
            call_notes=call_notes
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'next_contact': result.get('next_contact')
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"❌ Błąd przetwarzania rozmowy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@queue_api_bp.route('/crm/queue/next', methods=['GET'])
@login_required
@ankieter_required
def get_next_contact():
    """Get next contact to call"""
    try:
        next_contact = QueueManager.get_next_contact_for_ankieter(current_user.id)
        
        if next_contact:
            return jsonify({
                'success': True,
                'contact': {
                    'id': next_contact.id,
                    'name': next_contact.name,
                    'phone': next_contact.phone,
                    'email': next_contact.email,
                    'company': next_contact.company,
                    'call_attempts': next_contact.call_attempts,
                    'max_call_attempts': next_contact.max_call_attempts,
                    'tags': next_contact.get_tags()
                }
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

@queue_api_bp.route('/crm/queue/stats', methods=['GET'])
@login_required
@ankieter_required
def get_queue_stats():
    """Get queue statistics for ankieter"""
    try:
        stats = QueueManager.get_ankieter_queue_stats(current_user.id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statystyk kolejki: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500




