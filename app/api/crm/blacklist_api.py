"""
CRM Blacklist API - blacklist management
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import db, User
from app.models.crm_model import Contact, BlacklistEntry
import logging

logger = logging.getLogger(__name__)

# Create Blacklist API blueprint
blacklist_api_bp = Blueprint('crm_blacklist_api', __name__)

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

def admin_required_api(f):
    """Decorator to require admin role for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        if not current_user.is_admin_role():
            return jsonify({'success': False, 'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@blacklist_api_bp.route('/crm/blacklist', methods=['POST'])
@login_required
@admin_required_api
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
        logger.error(f"❌ Błąd dodawania do blacklisty: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blacklist_api_bp.route('/crm/blacklist/<int:blacklist_id>', methods=['DELETE'])
@login_required
@admin_required_api
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
        logger.error(f"❌ Błąd usuwania z blacklisty: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blacklist_api_bp.route('/crm/admin/blacklist', methods=['GET'])
@login_required
@admin_required_api
def get_blacklist():
    """Get all blacklist entries for admin"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Get active blacklist entries
        query = BlacklistEntry.query.filter_by(is_active=True)
        
        # Apply search filter if provided
        search = request.args.get('search')
        if search:
            query = query.filter(BlacklistEntry.phone.contains(search))
        
        pagination = query.order_by(BlacklistEntry.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        blacklist_data = []
        for entry in pagination.items:
            # Get blacklisted by user info
            blacklisted_by_user = User.query.get(entry.blacklisted_by) if entry.blacklisted_by else None
            
            # Get contact info if available
            contact = Contact.query.get(entry.contact_id) if entry.contact_id else None
            
            blacklist_data.append({
                'id': entry.id,
                'phone': entry.phone,
                'reason': entry.reason,
                'contact_name': contact.name if contact else None,
                'contact_id': entry.contact_id,
                'blacklisted_by': blacklisted_by_user.first_name if blacklisted_by_user else 'System',
                'created_at': entry.created_at.isoformat(),
                'is_active': entry.is_active
            })
        
        return jsonify({
            'success': True,
            'blacklist': blacklist_data,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': pagination.per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania blacklisty: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blacklist_api_bp.route('/crm/admin/blacklist', methods=['POST'])
@login_required
@admin_required_api
def admin_add_to_blacklist():
    """Admin add phone number to blacklist"""
    try:
        data = request.get_json()
        
        phone = data.get('phone')
        reason = data.get('reason', 'Admin blacklist')
        
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
            blacklisted_by=current_user.id
        )
        
        db.session.add(blacklist_entry)
        
        # Update any existing contacts with this phone number
        contacts = Contact.query.filter_by(phone=phone).all()
        for contact in contacts:
            contact.is_blacklisted = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Phone number added to blacklist and {len(contacts)} contacts updated',
            'updated_contacts_count': len(contacts)
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd admin dodawania do blacklisty: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blacklist_api_bp.route('/crm/admin/blacklist/<int:entry_id>', methods=['DELETE'])
@login_required
@admin_required_api
def admin_remove_from_blacklist(entry_id):
    """Admin remove phone number from blacklist"""
    try:
        blacklist_entry = BlacklistEntry.query.get(entry_id)
        if not blacklist_entry:
            return jsonify({'success': False, 'error': 'Blacklist entry not found'}), 404
        
        # Deactivate entry
        blacklist_entry.is_active = False
        db.session.commit()
        
        # Update related contacts
        contacts = Contact.query.filter_by(phone=blacklist_entry.phone).all()
        for contact in contacts:
            contact.is_blacklisted = False
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Phone number removed from blacklist and {len(contacts)} contacts updated',
            'updated_contacts_count': len(contacts)
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd admin usuwania z blacklisty: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blacklist_api_bp.route('/crm/admin/blacklist/bulk-delete', methods=['DELETE'])
@login_required
@admin_required_api
def bulk_remove_from_blacklist():
    """Bulk remove phone numbers from blacklist"""
    try:
        data = request.get_json()
        entry_ids = data.get('entry_ids', [])
        
        if not entry_ids:
            return jsonify({'success': False, 'error': 'No entries selected'}), 400
        
        removed_count = 0
        updated_contacts_count = 0
        
        for entry_id in entry_ids:
            blacklist_entry = BlacklistEntry.query.get(entry_id)
            if blacklist_entry:
                # Deactivate entry
                blacklist_entry.is_active = False
                
                # Update related contacts
                contacts = Contact.query.filter_by(phone=blacklist_entry.phone).all()
                for contact in contacts:
                    contact.is_blacklisted = False
                    updated_contacts_count += 1
                
                removed_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Removed {removed_count} entries from blacklist and updated {updated_contacts_count} contacts',
            'removed_count': removed_count,
            'updated_contacts_count': updated_contacts_count
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd masowego usuwania z blacklisty: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@blacklist_api_bp.route('/crm/admin/blacklist/import', methods=['POST'])
@login_required
@admin_required_api
def import_blacklist():
    """Import phone numbers to blacklist from file"""
    try:
        from flask import current_app
        import pandas as pd
        import os
        import uuid
        from werkzeug.utils import secure_filename
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Check file type
        if not file.filename.lower().endswith(('.xlsx', '.xls', '.csv')):
            return jsonify({'success': False, 'error': 'Only Excel and CSV files are allowed'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, 'crm', 'data', 'temp')
        os.makedirs(upload_folder, exist_ok=True)
        
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        try:
            # Read file
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Validate required columns
            if 'phone' not in df.columns:
                return jsonify({'success': False, 'error': 'File must contain "phone" column'}), 400
            
            # Process phone numbers
            imported_count = 0
            skipped_count = 0
            
            for _, row in df.iterrows():
                phone = str(row['phone']).strip()
                reason = row.get('reason', 'Bulk import')
                
                # Skip empty phones
                if not phone or phone == 'nan':
                    skipped_count += 1
                    continue
                
                # Check if already blacklisted
                existing = BlacklistEntry.query.filter_by(phone=phone, is_active=True).first()
                if existing:
                    skipped_count += 1
                    continue
                
                # Add to blacklist
                blacklist_entry = BlacklistEntry(
                    phone=phone,
                    reason=reason,
                    blacklisted_by=current_user.id
                )
                
                db.session.add(blacklist_entry)
                
                # Update related contacts
                contacts = Contact.query.filter_by(phone=phone).all()
                for contact in contacts:
                    contact.is_blacklisted = True
                
                imported_count += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully imported {imported_count} phone numbers to blacklist',
                'imported_count': imported_count,
                'skipped_count': skipped_count
            })
            
        finally:
            # Clean up temporary file
            try:
                os.remove(file_path)
            except:
                pass
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd importu blacklisty: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500




