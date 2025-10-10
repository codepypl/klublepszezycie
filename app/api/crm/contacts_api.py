"""
CRM Contacts API - contact management
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models.crm_model import Contact, Call
import logging

logger = logging.getLogger(__name__)

# Create Contacts API blueprint
contacts_api_bp = Blueprint('crm_contacts_api', __name__)

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

@contacts_api_bp.route('/crm/contacts', methods=['GET'])
@login_required
@ankieter_required
def get_contacts():
    """Get contacts for current ankieter"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get contacts assigned to current ankieter
        contacts_query = Contact.query.filter_by(assigned_ankieter_id=current_user.id)
        
        # Apply filters if provided
        status_filter = request.args.get('status')
        if status_filter:
            if status_filter == 'ready':
                contacts_query = contacts_query.filter(
                    Contact.is_blacklisted == False,
                    Contact.call_attempts < Contact.max_call_attempts
                )
            elif status_filter == 'blacklisted':
                contacts_query = contacts_query.filter(Contact.is_blacklisted == True)
            elif status_filter == 'limit_reached':
                contacts_query = contacts_query.filter(
                    Contact.call_attempts >= Contact.max_call_attempts
                )
        
        contacts_pagination = contacts_query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        contacts = []
        for contact in contacts_pagination.items:
            contacts.append({
                'id': contact.id,
                'name': contact.name,
                'phone': contact.phone,
                'email': contact.email,
                'company': contact.company,
                'status': 'blacklisted' if contact.is_blacklisted else 
                         'limit_reached' if contact.call_attempts >= contact.max_call_attempts else 'ready',
                'call_attempts': contact.call_attempts,
                'max_call_attempts': contact.max_call_attempts,
                'last_call_date': contact.last_call_date.isoformat() if contact.last_call_date else None,
                'created_at': contact.created_at.isoformat(),
                'tags': contact.get_tags()
            })
        
        return jsonify({
            'success': True,
            'contacts': contacts,
            'pagination': {
                'page': contacts_pagination.page,
                'per_page': contacts_pagination.per_page,
                'total': contacts_pagination.total,
                'pages': contacts_pagination.pages,
                'has_next': contacts_pagination.has_next,
                'has_prev': contacts_pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania kontaktów: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_api_bp.route('/crm/contacts/<int:contact_id>', methods=['GET'])
@login_required
@ankieter_required
def get_contact(contact_id):
    """Get specific contact details"""
    try:
        contact = Contact.query.get(contact_id)
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        # Check if contact is assigned to current ankieter
        if contact.assigned_ankieter_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
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
                'is_blacklisted': contact.is_blacklisted,
                'call_attempts': contact.call_attempts,
                'max_call_attempts': contact.max_call_attempts,
                'last_call_date': contact.last_call_date.isoformat() if contact.last_call_date else None,
                'created_at': contact.created_at.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania kontaktu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_api_bp.route('/crm/contacts/<int:contact_id>/calls', methods=['GET'])
@login_required
@ankieter_required
def get_contact_calls(contact_id):
    """Get call history for specific contact"""
    try:
        contact = Contact.query.get(contact_id)
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        # Check if contact is assigned to current ankieter
        if contact.assigned_ankieter_id != current_user.id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        calls = Call.query.filter_by(contact_id=contact_id).order_by(Call.call_date.desc()).all()
        
        call_history = []
        for call in calls:
            call_history.append({
                'id': call.id,
                'call_date': call.call_date.isoformat(),
                'status': call.status,
                'priority': call.priority,
                'notes': call.notes,
                'duration_minutes': call.duration_minutes,
                'next_call_date': call.next_call_date.isoformat() if call.next_call_date else None,
                'is_lead_registered': call.is_lead_registered
            })
        
        return jsonify({
            'success': True,
            'calls': call_history
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania historii rozmów: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_api_bp.route('/crm/contacts/import', methods=['POST'])
@login_required
@ankieter_required
def import_contacts():
    """Import contacts from XLSX file"""
    try:
        from flask import current_app
        from app.services.crm_import_service import ImportService
        from app.services.crm_queue_manager import QueueManager
        import os
        import uuid
        from werkzeug.utils import secure_filename
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.xlsx'):
            return jsonify({'success': False, 'error': 'Only XLSX files are allowed'}), 400
        
        # Create import directory if it doesn't exist
        import_dir = os.path.join(current_app.root_path, 'crm', 'data', 'import')
        os.makedirs(import_dir, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(import_dir, unique_filename)
        
        # Save file
        file.save(file_path)
        
        # Import contacts
        result = ImportService.import_xlsx_file(
            file_path=file_path,
            ankieter_id=current_user.id,
            filename=filename
        )
        
        if result['success']:
            # Auto-assign contacts to ankieter
            QueueManager.auto_assign_contacts_to_ankieter(current_user.id)
            
            # Clean up file
            try:
                os.remove(file_path)
            except:
                pass
        
            return jsonify({
                'success': True,
                'message': f"Successfully imported {result['imported']} contacts",
                'imported_count': result['imported'],
                'failed_count': result['skipped']
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
            
    except Exception as e:
        logger.error(f"❌ Błąd importu kontaktów: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@contacts_api_bp.route('/crm/events', methods=['GET'])
@login_required
@ankieter_required
def get_events():
    """Get available events for contact registration"""
    try:
        from app.models.event_model import EventSchedule
        
        events = EventSchedule.query.filter_by(is_active=True).all()
        
        events_data = []
        for event in events:
            events_data.append({
                'id': event.id,
                'name': event.name,
                'description': event.description,
                'date': event.date.isoformat() if event.date else None,
                'location': event.location,
                'max_participants': event.max_participants,
                'current_participants': event.current_participants
            })
        
        return jsonify({
            'success': True,
            'events': events_data
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania wydarzeń: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500




