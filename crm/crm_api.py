"""
CRM API Endpoints
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from app.models import User, db
from crm.models import Contact, Call, ImportFile, ImportRecord
from crm.services.queue_manager import QueueManager
from crm.services.event_integration import EventIntegrationService
from crm.services.import_service import ImportService
from crm.services.file_import_service import FileImportService
from crm.utils.file_utils import generate_import_file_path
import os
import uuid
from werkzeug.utils import secure_filename

# Create CRM API blueprint
crm_api_bp = Blueprint('crm_api', __name__, url_prefix='/api/crm')

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

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        if not current_user.is_admin_role():
            return jsonify({'success': False, 'error': 'Admin role required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@crm_api_bp.route('/contacts', methods=['GET'])
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
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/contacts/import', methods=['POST'])
@login_required
@ankieter_required
def import_contacts():
    """Import contacts from XLSX file"""
    try:
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
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/calls/process', methods=['POST'])
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
        
        # Get contact
        contact = Contact.query.get(contact_id)
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
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
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/queue/next', methods=['GET'])
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
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/queue/stats', methods=['GET'])
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
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/contacts/<int:contact_id>', methods=['GET'])
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
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/contacts/<int:contact_id>/calls', methods=['GET'])
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
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/events', methods=['GET'])
@login_required
@ankieter_required
def get_events():
    """Get available events for lead registration"""
    try:
        from app.models import EventSchedule
        
        events = EventSchedule.query.filter_by(is_active=True).all()
        
        event_list = []
        for event in events:
            event_list.append({
                'id': event.id,
                'title': event.title,
                'event_date': event.event_date.isoformat() if event.event_date else None,
                'location': event.location
            })
        
        return jsonify({
            'success': True,
            'events': event_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/blacklist', methods=['POST'])
@login_required
@admin_required
def add_to_blacklist():
    """Add phone number to blacklist"""
    try:
        data = request.get_json()
        
        phone = data.get('phone')
        reason = data.get('reason', 'Manual blacklist')
        contact_id = data.get('contact_id')
        
        if not phone:
            return jsonify({'success': False, 'error': 'Phone number required'}), 400
        
        # Check if already blacklisted
        existing = BlacklistEntry.query.filter_by(phone=phone, is_active=True).first()
        if existing:
            return jsonify({'success': False, 'error': 'Phone number already blacklisted'}), 400
        
        # Add to blacklist
        blacklist_entry = BlacklistEntry(
            phone=phone,
            reason=reason,
            blacklisted_by=current_user.id,
            contact_id=contact_id
        )
        
        db.session.add(blacklist_entry)
        
        # Update contact if provided
        if contact_id:
            contact = Contact.query.get(contact_id)
            if contact:
                contact.is_blacklisted = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Phone number added to blacklist'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/blacklist/<int:blacklist_id>', methods=['DELETE'])
@login_required
@admin_required
def remove_from_blacklist(blacklist_id):
    """Remove phone number from blacklist"""
    try:
        blacklist_entry = BlacklistEntry.query.get(blacklist_id)
        if not blacklist_entry:
            return jsonify({'success': False, 'error': 'Blacklist entry not found'}), 404
        
        # Deactivate instead of delete
        blacklist_entry.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Phone number removed from blacklist'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/imports', methods=['GET'])
@login_required
@ankieter_required
def get_import_history():
    """Get import history for ankieter"""
    try:
        imports = ImportLog.query.filter_by(imported_by=current_user.id).order_by(ImportLog.created_at.desc()).all()
        
        import_list = []
        for import_log in imports:
            import_list.append({
                'id': import_log.id,
                'filename': import_log.filename,
                'total_records': import_log.total_records,
                'successful_records': import_log.successful_records,
                'failed_records': import_log.failed_records,
                'status': import_log.status,
                'error_message': import_log.error_message,
                'created_at': import_log.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'imports': import_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/analyze-file', methods=['POST'])
@login_required
@ankieter_required
def analyze_file():
    """Analyze uploaded file and return column information"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Generate unique file path with new directory structure
        filename = secure_filename(file.filename)
        upload_folder = os.path.abspath(current_app.config['UPLOAD_FOLDER'])
        file_path = generate_import_file_path(filename, upload_folder)
        file.save(file_path)
        
        # Determine file type
        file_extension = filename.split('.')[-1].lower()
        file_type = 'xlsx' if file_extension in ['xlsx', 'xls'] else 'csv'
        
        # Get CSV separator from form data (default to comma)
        csv_separator = request.form.get('csv_separator', ',')
        
        # Analyze file
        file_import_service = FileImportService()
        result = file_import_service.analyze_file(file_path, file_type, csv_separator)
        
        if not result.get('success', False):
            os.remove(file_path)
            return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 400
        
        # Store file info in session or return it
        return jsonify({
            'success': True,
            'file_data': result['sample_data'],
            'columns': result['columns'],
            'file_info': {
                'filename': filename,
                'file_path': file_path,
                'file_type': file_type,
                'csv_separator': csv_separator,
                'total_rows': result['total_rows']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/preview-mapping', methods=['POST'])
@login_required
@ankieter_required
def preview_mapping():
    """Preview mapping results with sample data"""
    try:
        data = request.get_json()
        file_info = data.get('file_info')
        mapping = data.get('mapping')
        rows_count = data.get('rows_count', 20)
        
        if not file_info or not mapping:
            return jsonify({'success': False, 'error': 'Missing file_info or mapping data'}), 400
        
        # Read the file and apply mapping
        file_import_service = FileImportService()
        result = file_import_service.preview_mapping(
            file_info['file_path'],
            file_info['file_type'],
            file_info['csv_separator'],
            mapping,
            rows_count
        )
        
        if not result.get('success', False):
            return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 400
        
        return jsonify({
            'success': True,
            'preview_data': result['preview_data'],
            'total_rows': result['total_rows']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/extract-file', methods=['POST'])
@login_required
@ankieter_required
def extract_file():
    """Extract file data and create ImportFile record"""
    try:
        data = request.get_json()
        file_info = data.get('file_info')
        file_data = data.get('file_data')
        
        if not file_info or not file_data:
            return jsonify({'success': False, 'error': 'Missing file_info or file_data'}), 400
        
        # Create ImportFile record
        import_file = ImportFile(
            filename=file_info['filename'],
            file_path=file_info['file_path'],
            file_type=file_info['file_type'],
            csv_separator=file_info['csv_separator'],
            total_rows=file_info['total_rows'],
            processed_rows=0,
            import_status='analyzed',
            imported_by=current_user.id
        )
        
        db.session.add(import_file)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'import_file_id': import_file.id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/process-import', methods=['POST'])
@login_required
@ankieter_required
def process_import():
    """Process import and create contacts"""
    try:
        data = request.get_json()
        import_file_id = data.get('import_file_id')
        mapping = data.get('mapping')
        
        if not import_file_id or not mapping:
            return jsonify({'success': False, 'error': 'Missing import_file_id or mapping'}), 400
        
        # Get import file
        import_file = ImportFile.query.get(import_file_id)
        if not import_file:
            return jsonify({'success': False, 'error': 'Import file not found'}), 404
        
        # Process import using FileImportService
        file_import_service = FileImportService()
        
        # First, create ImportRecord entries from file (if not already done)
        if not ImportRecord.query.filter_by(import_file_id=import_file.id).first():
            extract_result = file_import_service.create_import_records_from_file(
                import_file.id,
                import_file.file_path,
                import_file.file_type,
                import_file.csv_separator
            )
            
            if not extract_result.get('success', False):
                return jsonify({'success': False, 'error': extract_result.get('error', 'Failed to extract file data')}), 400
        
        # Then, process records to contacts using existing ImportFile
        result = file_import_service.process_records_to_contacts(
            import_file.id,
            mapping,
            current_user.id
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'imported_count': result['imported'],
                'failed_count': result.get('skipped', 0)
            })
        else:
            return jsonify({'success': False, 'error': result['error']}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/imports/<int:import_id>', methods=['DELETE'])
@login_required
@ankieter_required
def delete_import(import_id):
    """Delete import and associated contacts"""
    try:
        # Get import file
        import_file = ImportFile.query.get(import_id)
        if not import_file:
            return jsonify({'success': False, 'error': 'Import not found'}), 404
        
        # Check if user can delete this import (only admin or owner)
        if current_user.role != 'admin' and import_file.imported_by != current_user.id:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        # Delete associated contacts first
        contacts_deleted = 0
        contacts = Contact.query.join(ImportRecord).filter(ImportRecord.import_file_id == import_id).all()
        for contact in contacts:
            db.session.delete(contact)
            contacts_deleted += 1
        
        # Delete import records
        ImportRecord.query.filter_by(import_file_id=import_id).delete()
        
        # Delete physical file if exists
        if import_file.file_path and os.path.exists(import_file.file_path):
            try:
                os.remove(import_file.file_path)
            except Exception as e:
                print(f"Error deleting file {import_file.file_path}: {e}")
        
        # Delete import file
        db.session.delete(import_file)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'contacts_deleted': contacts_deleted
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_api_bp.route('/imports/bulk-delete', methods=['POST'])
@login_required
@ankieter_required
def bulk_delete_imports():
    """Bulk delete imports and associated contacts"""
    try:
        data = request.get_json()
        import_ids = data.get('itemIds', [])
        
        if not import_ids:
            return jsonify({'success': False, 'error': 'No imports selected'}), 400
        
        total_contacts_deleted = 0
        
        for import_id in import_ids:
            # Get import file
            import_file = ImportFile.query.get(import_id)
            if not import_file:
                continue
                
            # Check if user can delete this import (only admin or owner)
            if current_user.role != 'admin' and import_file.imported_by != current_user.id:
                continue
            
            # Delete associated contacts first
            contacts = Contact.query.join(ImportRecord).filter(ImportRecord.import_file_id == import_id).all()
            for contact in contacts:
                db.session.delete(contact)
                total_contacts_deleted += 1
            
            # Delete import records
            ImportRecord.query.filter_by(import_file_id=import_id).delete()
            
            # Delete physical file if exists
            if import_file.file_path and os.path.exists(import_file.file_path):
                try:
                    os.remove(import_file.file_path)
                except Exception as e:
                    print(f"Error deleting file {import_file.file_path}: {e}")
            
            # Delete import file
            db.session.delete(import_file)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'deleted_count': len(import_ids),
            'contacts_deleted': total_contacts_deleted
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
