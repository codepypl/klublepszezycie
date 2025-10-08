"""
CRM Campaigns API - campaign management
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import db, User
from app.models.crm_model import Campaign
import logging

logger = logging.getLogger(__name__)

# Create Campaigns API blueprint
campaigns_api_bp = Blueprint('crm_campaigns_api', __name__)

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

@campaigns_api_bp.route('/crm/admin/campaigns', methods=['GET'])
@login_required
@admin_required_api
def get_campaigns():
    """Get all campaigns for admin with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = Campaign.query.order_by(Campaign.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        campaigns_data = []
        for campaign in pagination.items:
            # Get campaign creator
            creator = User.query.get(campaign.created_by) if campaign.created_by else None
            
            # Count related data
            import_files_count = campaign.import_files.count()
            contacts_count = campaign.contacts.count()
            calls_count = campaign.calls.count()
            
            campaigns_data.append({
                'id': campaign.id,
                'name': campaign.name,
                'description': campaign.description,
                'script_content': campaign.script_content,
                'created_by': creator.first_name if creator else 'Nieznany',
                'created_at': campaign.created_at.isoformat(),
                'updated_at': campaign.updated_at.isoformat(),
                'is_active': campaign.is_active,
                'import_files_count': import_files_count,
                'contacts_count': contacts_count,
                'calls_count': calls_count
            })
        
        return jsonify({
            'success': True,
            'campaigns': campaigns_data,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': pagination.per_page
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_api_bp.route('/crm/admin/campaigns', methods=['POST'])
@login_required
@admin_required_api
def create_campaign():
    """Create new campaign"""
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        script_content = data.get('script_content', '')
        
        if not name:
            return jsonify({'success': False, 'error': 'Nazwa kampanii jest wymagana'}), 400
        
        # Check if campaign with same name exists
        existing_campaign = Campaign.query.filter_by(name=name).first()
        if existing_campaign:
            return jsonify({'success': False, 'error': 'Kampania o tej nazwie już istnieje'}), 400
        
        campaign = Campaign(
            name=name,
            description=description,
            script_content=script_content,
            created_by=current_user.id
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Kampania została utworzona',
            'campaign': {
                'id': campaign.id,
                'name': campaign.name,
                'description': campaign.description,
                'script_content': campaign.script_content,
                'created_by': current_user.first_name,
                'created_at': campaign.created_at.isoformat(),
                'is_active': campaign.is_active
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd tworzenia kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_api_bp.route('/crm/admin/campaigns/<int:campaign_id>', methods=['PUT'])
@login_required
@admin_required_api
def update_campaign(campaign_id):
    """Update existing campaign"""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie została znaleziona'}), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            # Check if name is unique (excluding current campaign)
            existing_campaign = Campaign.query.filter(
                Campaign.name == data['name'],
                Campaign.id != campaign_id
            ).first()
            if existing_campaign:
                return jsonify({'success': False, 'error': 'Kampania o tej nazwie już istnieje'}), 400
            campaign.name = data['name']
        
        if 'description' in data:
            campaign.description = data['description']
        
        if 'script_content' in data:
            campaign.script_content = data['script_content']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Kampania została zaktualizowana',
            'campaign': {
                'id': campaign.id,
                'name': campaign.name,
                'description': campaign.description,
                'script_content': campaign.script_content,
                'updated_at': campaign.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd aktualizacji kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_api_bp.route('/crm/admin/campaigns/<int:campaign_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_campaign(campaign_id):
    """Delete campaign"""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie została znaleziona'}), 404
        
        # Check if campaign has associated data
        if campaign.contacts.count() > 0:
            return jsonify({'success': False, 'error': 'Nie można usunąć kampanii z przypisanymi kontaktami'}), 400
        
        if campaign.import_files.count() > 0:
            return jsonify({'success': False, 'error': 'Nie można usunąć kampanii z przypisanymi plikami importu'}), 400
        
        db.session.delete(campaign)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Kampania została usunięta'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_api_bp.route('/crm/admin/campaigns/<int:campaign_id>/toggle', methods=['POST'])
@login_required
@admin_required_api
def toggle_campaign(campaign_id):
    """Toggle campaign active status"""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie została znaleziona'}), 404
        
        # Toggle active status
        campaign.is_active = not campaign.is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Kampania {"aktywowana" if campaign.is_active else "deaktywowana"}',
            'is_active': campaign.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd przełączania kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_api_bp.route('/crm/campaigns', methods=['GET'])
@login_required
@ankieter_required
def get_ankieter_campaigns():
    """Get campaigns for ankieter"""
    try:
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
        logger.error(f"❌ Błąd pobierania kampanii dla ankietera: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@campaigns_api_bp.route('/crm/admin/campaigns/<int:campaign_id>/delete-records', methods=['DELETE'])
@login_required
@admin_required_api
def delete_campaign_records(campaign_id):
    """Delete all records associated with campaign"""
    try:
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie została znaleziona'}), 404
        
        # Get counts before deletion
        contacts_count = campaign.contacts.count()
        import_files_count = campaign.import_files.count()
        calls_count = campaign.calls.count()
        
        # Delete related data
        from app.models.crm_model import Contact, ImportFile, Call, ImportRecord
        
        # Get all contacts for this campaign first
        campaign_contacts = Contact.query.filter_by(campaign_id=campaign_id).all()
        contact_ids = [contact.id for contact in campaign_contacts]
        
        # Delete import records that reference these contacts
        if contact_ids:
            ImportRecord.query.filter(ImportRecord.contact_id.in_(contact_ids)).delete()
        
        # Delete calls first (to avoid foreign key constraint)
        Call.query.filter_by(campaign_id=campaign_id).delete()
        
        # Delete contacts
        Contact.query.filter_by(campaign_id=campaign_id).delete()
        
        # Delete import files
        ImportFile.query.filter_by(campaign_id=campaign_id).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {contacts_count} kontaktów, {import_files_count} plików importu i {calls_count} rozmów',
            'deleted_counts': {
                'contacts': contacts_count,
                'import_files': import_files_count,
                'calls': calls_count
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania rekordów kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

