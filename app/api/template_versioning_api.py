"""
API endpoints for template versioning system
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.services.template_versioning_service import TemplateVersioningService
from app.models import db

template_versioning_bp = Blueprint('template_versioning', __name__)

@template_versioning_bp.route('/api/template-versioning/start-edit/<template_name>', methods=['POST'])
@login_required
def start_editing_template(template_name):
    """Start editing a default template by creating an edited copy"""
    try:
        service = TemplateVersioningService()
        success, message, new_template = service.start_editing_default_template(template_name)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'template': {
                    'id': new_template.id,
                    'name': new_template.name,
                    'version': new_template.version,
                    'subject': new_template.subject,
                    'html_content': new_template.html_content,
                    'text_content': new_template.text_content,
                    'template_type': new_template.template_type,
                    'variables': new_template.variables,
                    'description': new_template.description,
                    'is_default': new_template.is_default,
                    'is_edited_copy': new_template.is_edited_copy,
                    'original_template_name': new_template.original_template_name,
                    'created_at': new_template.created_at.isoformat()
                }
            })
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@template_versioning_bp.route('/api/template-versioning/save/<int:template_id>', methods=['POST'])
@login_required
def save_template_version(template_id):
    """Save a new version of a template"""
    try:
        data = request.get_json()
        changes = data.get('changes', {})
        make_default = data.get('make_default', False)
        
        service = TemplateVersioningService()
        success, message = service.save_template_version(template_id, changes, make_default)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@template_versioning_bp.route('/api/template-versioning/make-default/<int:template_id>', methods=['POST'])
@login_required
def make_template_default(template_id):
    """Make a template version the default template"""
    try:
        service = TemplateVersioningService()
        success, message = service.make_template_default(template_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@template_versioning_bp.route('/api/template-versioning/restore-default/<template_name>', methods=['POST'])
@login_required
def restore_default_template(template_name):
    """Restore a template to its default version"""
    try:
        service = TemplateVersioningService()
        success, message = service.restore_default_template(template_name)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@template_versioning_bp.route('/api/template-versioning/versions/<template_name>', methods=['GET'])
@login_required
def get_template_versions(template_name):
    """Get all versions of a template"""
    try:
        service = TemplateVersioningService()
        versions = service.get_template_versions(template_name)
        
        version_list = []
        for version in versions:
            version_list.append({
                'id': version.id,
                'name': version.name,
                'version': version.version,
                'subject': version.subject,
                'created_at': version.created_at.isoformat(),
                'updated_at': version.updated_at.isoformat(),
                'is_default': version.is_default,
                'is_active': version.is_active,
                'is_edited_copy': version.is_edited_copy,
                'description': version.description,
                'html_preview': version.html_content[:200] + '...' if version.html_content and len(version.html_content) > 200 else version.html_content
            })
        
        return jsonify({'success': True, 'versions': version_list})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_versioning_bp.route('/api/template-versioning/restore/<template_name>/<int:version>', methods=['POST'])
@login_required
def restore_to_version(template_name, version):
    """Restore template to a specific version"""
    try:
        service = TemplateVersioningService()
        success, message = service.restore_to_version(template_name, version)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@template_versioning_bp.route('/api/template-versioning/delete/<int:template_id>', methods=['DELETE'])
@login_required
def delete_template(template_id):
    """Delete a template and all its versions"""
    try:
        service = TemplateVersioningService()
        success, message = service.delete_template(template_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@template_versioning_bp.route('/api/template-versioning/test-email/<template_name>', methods=['POST'])
@login_required
def send_test_email(template_name):
    """Send a test email using a template"""
    try:
        data = request.get_json()
        test_email = data.get('email')
        context = data.get('context', {})
        
        if not test_email:
            return jsonify({'success': False, 'error': 'Email address is required'}), 400
        
        service = TemplateVersioningService()
        success, message = service.send_test_email(template_name, test_email, context)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_versioning_bp.route('/api/template-versioning/info/<template_name>', methods=['GET'])
@login_required
def get_template_info(template_name):
    """Get comprehensive information about a template"""
    try:
        service = TemplateVersioningService()
        info = service.get_template_info(template_name)
        
        if 'error' in info:
            return jsonify({'success': False, 'error': info['error']}), 500
        
        return jsonify({'success': True, 'info': info})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@template_versioning_bp.route('/api/template-versioning/confirmation-modal/<int:template_id>', methods=['GET'])
@login_required
def get_confirmation_modal_data(template_id):
    """Get data for the confirmation modal when making a template default"""
    try:
        # Using the extended EmailTemplate model from email_model.py
        from app.models.email_model import DefaultEmailTemplate
        
        from app.models.email_model import EmailTemplate
        template = EmailTemplate.query.get(template_id)
        if not template:
            return jsonify({'success': False, 'error': 'Template not found'}), 404
        
        # Get default template for comparison
        default_template = DefaultEmailTemplate.query.filter_by(
            name=template.original_template_name
        ).first() if template.original_template_name else None
        
        modal_data = {
            'template_name': template.original_template_name,
            'current_version': template.version,
            'current_subject': template.subject,
            'default_subject': default_template.subject if default_template else None,
            'has_changes': (
                default_template and (
                    template.subject != default_template.subject or
                    template.html_content != default_template.html_content or
                    template.text_content != default_template.text_content
                )
            ) if default_template else True,
            'warning_message': f"Czy na pewno chcesz nadpisać szablon domyślny '{template.original_template_name}' wersją {template.version}?"
        }
        
        return jsonify({'success': True, 'modal_data': modal_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
