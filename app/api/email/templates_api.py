"""
Email templates API - complete template management
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import EmailTemplate, EmailQueue
from app.validators.email_validators import EmailValidator
from app.utils.timezone_utils import get_local_now
from app.services.template_manager import TemplateManager
from app.services.fixture_loader import load_email_templates_fixtures
from app import db
import json
import logging

email_templates_bp = Blueprint('email_templates_api', __name__)
logger = logging.getLogger(__name__)

@email_templates_bp.route('/email/templates', methods=['GET'])
@login_required
def get_templates():
    """Pobiera listę szablonów emaili"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_type = request.args.get('filter', 'all')
        
        # Buduj zapytanie
        query = EmailTemplate.query
        
        if filter_type != 'all':
            query = query.filter_by(template_type=filter_type)
        
        # Sortuj po dacie utworzenia
        query = query.order_by(EmailTemplate.created_at.desc())
        
        # Paginacja
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        templates = []
        for template in pagination.items:
            variables = {}
            if template.variables:
                try:
                    variables = json.loads(template.variables)
                except json.JSONDecodeError:
                    variables = {}
            
            templates.append({
                'id': template.id,
                'name': template.name,
                'subject': template.subject,
                'template_type': template.template_type,
                'html_content': template.html_content,
                'text_content': template.text_content,
                'variables': variables,
                'is_active': template.is_active,
                'is_default': template.is_default,
                'created_at': template.created_at.isoformat() if template.created_at else None,
                'updated_at': template.updated_at.isoformat() if template.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'templates': templates,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'next_num': pagination.next_num,
                'prev_num': pagination.prev_num
            }
        })
    except Exception as e:
        logger.error(f"❌ Błąd pobierania szablonów: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@email_templates_bp.route('/email/templates', methods=['POST'])
@login_required
def create_template():
    """Tworzy nowy szablon emaila"""
    try:
        data = request.get_json()
        
        # Walidacja danych
        is_valid, error_msg = EmailValidator.validate_template_data(data)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        template = EmailTemplate(
            name=data['name'],
            subject=data['subject'],
            template_type=data.get('template_type', 'custom'),
            html_content=data['html_content'],
            text_content=data.get('text_content', ''),
            variables=data.get('variables', ''),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Szablon utworzony pomyślnie'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd tworzenia szablonu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_templates_bp.route('/email/templates/<int:template_id>', methods=['GET'])
@login_required
def get_template(template_id):
    """Pobiera pojedynczy szablon emaila"""
    try:
        template = EmailTemplate.query.get(template_id)
        if not template:
            return jsonify({'success': False, 'error': 'Szablon nie istnieje'}), 404
        
        return jsonify({
            'success': True,
            'template': {
                'id': template.id,
                'name': template.name,
                'subject': template.subject,
                'template_type': template.template_type,
                'html_content': template.html_content,
                'text_content': template.text_content,
                'variables': template.variables,
                'is_active': template.is_active,
                'is_default': template.is_default
            }
        })
    except Exception as e:
        logger.error(f"❌ Błąd pobierania szablonu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_templates_bp.route('/email/templates/<int:template_id>', methods=['PUT'])
@login_required
def update_template(template_id):
    """Aktualizuje szablon emaila"""
    try:
        template = EmailTemplate.query.get(template_id)
        if not template:
            return jsonify({'success': False, 'error': 'Szablon nie istnieje'}), 404
        
        data = request.get_json()
        
        # Walidacja danych
        is_valid, error_msg = EmailValidator.validate_template_data(data)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Sprawdź czy próbuje zmienić nazwę szablonu domyślnego
        if template.is_default and data.get('name') != template.name:
            return jsonify({'success': False, 'error': 'Nazwa szablonu domyślnego nie może być zmieniona'}), 400
        
        # Aktualizuj pola
        template.name = data['name']
        template.subject = data['subject']
        template.template_type = data.get('template_type', template.template_type)
        template.html_content = data['html_content']
        template.text_content = data.get('text_content', '')
        template.variables = data.get('variables', '')
        template.is_active = data.get('is_active', True)
        template.updated_at = get_local_now()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Szablon zaktualizowany pomyślnie'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd aktualizacji szablonu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_templates_bp.route('/email/templates/<int:template_id>', methods=['DELETE'])
@login_required
def delete_template(template_id):
    """Usuwa szablon emaila"""
    try:
        template = EmailTemplate.query.get(template_id)
        if not template:
            return jsonify({'success': False, 'error': 'Szablon nie istnieje'}), 404
        
        # Sprawdź czy szablon jest domyślny
        if template.is_default:
            return jsonify({'success': False, 'error': 'Nie można usunąć szablonu domyślnego'}), 400
        
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Szablon usunięty pomyślnie'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania szablonu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_templates_bp.route('/email/campaigns/templates', methods=['GET'])
@login_required
def get_campaign_templates():
    """Pobiera szablony dostępne dla kampanii"""
    try:
        templates = EmailTemplate.query.filter_by(is_active=True).all()
        
        templates_data = []
        for template in templates:
            variables = {}
            if template.variables:
                try:
                    variables = json.loads(template.variables)
                except json.JSONDecodeError:
                    variables = {}
            
            templates_data.append({
                'id': template.id,
                'name': template.name,
                'subject': template.subject,
                'template_type': template.template_type,
                'html_content': template.html_content,
                'text_content': template.text_content,
                'variables': variables,
                'created_at': template.created_at.isoformat() if template.created_at else None
            })
        
        return jsonify({'success': True, 'templates': templates_data})
    except Exception as e:
        logger.error(f"❌ Błąd pobierania szablonów kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_templates_bp.route('/email/templates/reset', methods=['POST'])
@login_required
def reset_templates():
    """Resetuje szablony do stanu domyślnego"""
    try:
        manager = TemplateManager()
        
        # Najpierw synchronizuj domyślne szablony (z wymuszeniem przeładowania z fixtures)
        success, message = manager.sync_templates_from_defaults(force_reload_fixtures=True)
        if not success:
            return jsonify({'success': False, 'error': message}), 500
        
        # Następnie resetuj szablony z domyślnych
        success, message = manager.reset_templates_to_defaults()
        if not success:
            return jsonify({'success': False, 'error': message}), 500
        
        return jsonify({'success': True, 'message': message})
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd resetowania szablonów: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_templates_bp.route('/email/templates/initialize-defaults', methods=['POST'])
@login_required
def initialize_default_templates():
    """Inicjalizuje domyślne szablony z fixtures"""
    try:
        manager = TemplateManager()
        success, message = manager.initialize_default_templates()
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 500
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd inicjalizacji domyślnych szablonów: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_templates_bp.route('/email/templates/load-fixtures', methods=['POST'])
@login_required
def load_fixtures():
    """Ładuje szablony z fixtures (jak Django loaddata)"""
    try:
        success, message = load_email_templates_fixtures()
        
        if not success:
            return jsonify({'success': False, 'error': message}), 500
        
        return jsonify({'success': True, 'message': message})
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd ładowania fixtures: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_templates_bp.route('/email/templates/save-as-defaults', methods=['POST'])
@login_required
def save_templates_as_defaults():
    """Zapisuje obecne szablony jako domyślne wzory"""
    try:
        manager = TemplateManager()
        success, message = manager.save_current_templates_as_defaults()
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 500
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd zapisywania szablonów jako domyślne: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_templates_bp.route('/email/templates/sync-defaults', methods=['POST'])
@login_required
def sync_default_templates():
    """Synchronizuje domyślne szablony"""
    try:
        manager = TemplateManager()
        success, message = manager.sync_templates_from_defaults()
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 500
            
    except Exception as e:
        logger.error(f"❌ Błąd synchronizacji domyślnych szablonów: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_templates_bp.route('/bulk-delete/email-templates', methods=['POST'])
@login_required
def bulk_delete_templates():
    """Bulk delete email templates"""
    try:
        data = request.get_json()
        template_ids = data.get('ids', [])
        
        if not template_ids:
            return jsonify({'success': False, 'error': 'Brak szablonów do usunięcia'}), 400
        
        # Delete templates
        deleted_count = 0
        for template_id in template_ids:
            template = EmailTemplate.query.get(template_id)
            if template:
                # Sprawdź czy szablon jest domyślny
                if template.is_default:
                    continue  # Skip default templates
                
                # Delete associated queue items
                EmailQueue.query.filter_by(template_id=template_id).delete()
                # Delete template
                db.session.delete(template)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Usunięto {deleted_count} szablonów',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd masowego usuwania szablonów: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500