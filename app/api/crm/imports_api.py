"""
CRM Imports API - import management
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from app.models import db
from app.models.crm_model import Contact, ImportFile, ImportRecord, Campaign, Call
from app.services.crm_file_import_service import FileImportService
from app.utils.crm_file_utils import generate_import_file_path
import os
import uuid
from werkzeug.utils import secure_filename
import logging

logger = logging.getLogger(__name__)

# Create Imports API blueprint
imports_api_bp = Blueprint('crm_imports_api', __name__)

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

@imports_api_bp.route('/crm/imports', methods=['GET'])
@login_required
@ankieter_required
def get_import_history():
    """Get import history for ankieter"""
    try:
        imports = ImportFile.query.filter_by(imported_by=current_user.id).order_by(ImportFile.created_at.desc()).all()
        
        import_list = []
        for import_file in imports:
            import_list.append({
                'id': import_file.id,
                'filename': import_file.filename,
                'total_records': import_file.total_records,
                'successful_records': import_file.successful_records,
                'failed_records': import_file.failed_records,
                'status': import_file.status,
                'error_message': import_file.error_message,
                'created_at': import_file.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'imports': import_list
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania historii importów: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@imports_api_bp.route('/crm/imports/<int:import_id>/errors', methods=['GET'])
@login_required
@ankieter_required
def get_import_errors(import_id):
    """Get detailed errors for specific import"""
    try:
        # Check if import belongs to current user
        import_file = ImportFile.query.filter_by(
            id=import_id,
            imported_by=current_user.id
        ).first()
        
        if not import_file:
            return jsonify({'success': False, 'error': 'Import not found'}), 404
        
        # Get failed records with error messages
        failed_records = ImportRecord.query.filter_by(
            import_file_id=import_id,
            processed=True
        ).filter(ImportRecord.error_message.isnot(None)).all()
        
        errors_list = []
        for record in failed_records:
            errors_list.append({
                'row_number': record.row_number,
                'error_message': record.error_message,
                'raw_data': record.get_raw_data()
            })
        
        return jsonify({
            'success': True,
            'import_filename': import_file.filename,
            'total_records': import_file.total_rows,
            'processed_records': import_file.processed_rows,
            'failed_records': len(errors_list),
            'errors': errors_list
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania błędów importu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@imports_api_bp.route('/crm/analyze-file', methods=['POST'])
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
        
        if result.get('success'):
            # Create import file record
            import_file = ImportFile(
                filename=filename,
                file_path=file_path,
                file_type=file_type,
                csv_separator=csv_separator,
                total_rows=result.get('total_rows', 0),
                imported_by=current_user.id
            )
            db.session.add(import_file)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'import_file_id': import_file.id,
                'columns': result.get('columns', []),
                'sample_data': result.get('sample_data', []),
                'total_rows': result.get('total_rows', 0),
                'file_type': file_type
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'File analysis failed')}), 400
            
    except Exception as e:
        logger.error(f"❌ Błąd analizy pliku: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@imports_api_bp.route('/crm/preview-mapping', methods=['POST'])
@login_required
@ankieter_required
def preview_mapping():
    """Preview import mapping before processing"""
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
        
        # Preview mapping
        result = FileImportService.preview_mapping(
            import_file.file_path,
            import_file.file_type,
            import_file.csv_separator,
            mapping,
            data.get('rows_count', 20)
        )
        
        return jsonify({
            'success': result.get('success', False),
            'preview_data': result.get('preview_data', []),
            'total_rows': result.get('total_rows', 0),
            'error': result.get('error', '')
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd podglądu mapowania: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@imports_api_bp.route('/crm/extract-file', methods=['POST'])
@login_required
@ankieter_required
def extract_file():
    """Extract file data to import records"""
    try:
        data = request.get_json()
        import_file_id = data.get('import_file_id')
        
        if not import_file_id:
            return jsonify({'success': False, 'error': 'Missing import_file_id'}), 400
        
        # Get import file
        import_file = ImportFile.query.get(import_file_id)
        if not import_file:
            return jsonify({'success': False, 'error': 'Import file not found'}), 404
        
        # Extract file data
        file_import_service = FileImportService()
        result = file_import_service.create_import_records_from_file(
            import_file.id,
            import_file.file_path,
            import_file.file_type,
            import_file.csv_separator
        )
        
        if result.get('success'):
            # Update import file status
            import_file.import_status = 'extracted'
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f"Extracted {result.get('records_created', 0)} records from file",
                'records_created': result.get('records_created', 0),
                'import_file_id': import_file_id
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'File extraction failed')}), 400
        
    except Exception as e:
        logger.error(f"❌ Błąd ekstrakcji pliku: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@imports_api_bp.route('/crm/process-import', methods=['POST'])
@login_required
@ankieter_required
def process_import():
    """Process import and create contacts"""
    try:
        data = request.get_json()
        import_file_id = data.get('import_file_id')
        mapping = data.get('mapping')
        campaign_id = data.get('campaign_id')
        
        if not import_file_id or not mapping:
            return jsonify({'success': False, 'error': 'Missing import_file_id or mapping'}), 400
        
        if not campaign_id:
            return jsonify({'success': False, 'error': 'Missing campaign_id'}), 400
        
        # Validate campaign exists
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        # Get import file
        import_file = ImportFile.query.get(import_file_id)
        if not import_file:
            return jsonify({'success': False, 'error': 'Import file not found'}), 404
        
        # Assign campaign to import file
        import_file.campaign_id = campaign_id
        db.session.commit()
        
        # First, create ImportRecord entries from file (if not already done)
        if not ImportRecord.query.filter_by(import_file_id=import_file.id).first():
            extract_result = FileImportService.create_import_records_from_file(
                import_file.id,
                import_file.file_path,
                import_file.file_type,
                import_file.csv_separator
            )
            
            if not extract_result.get('success', False):
                return jsonify({'success': False, 'error': extract_result.get('error', 'Failed to extract file data')}), 400
        
        # Then, process records to contacts using existing ImportFile
        result = FileImportService.process_records_to_contacts(
            import_file.id,
            mapping,
            current_user.id,
            campaign_id
        )
        
        if result.get('success'):
            # Update import file status
            import_file.import_status = 'completed'
            import_file.successful_records = result.get('successful_count', 0)
            import_file.failed_records = result.get('failed_count', 0)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f"Successfully processed {result.get('successful_count', 0)} contacts",
                'successful_count': result.get('successful_count', 0),
                'failed_count': result.get('failed_count', 0)
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Import processing failed')}), 400
        
    except Exception as e:
        logger.error(f"❌ Błąd przetwarzania importu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@imports_api_bp.route('/crm/imports/<int:import_id>', methods=['DELETE'])
@login_required
@ankieter_required
def delete_import(import_id):
    """Delete import file and related data"""
    try:
        # Check if import belongs to current user
        import_file = ImportFile.query.filter_by(
            id=import_id,
            imported_by=current_user.id
        ).first()
        
        if not import_file:
            return jsonify({'success': False, 'error': 'Import not found'}), 404
        
        # Get contacts to delete first
        contacts_to_delete = Contact.query.filter_by(import_file_id=import_id).all()
        contact_ids = [contact.id for contact in contacts_to_delete]
        
        # Delete import records that reference these contacts
        if contact_ids:
            ImportRecord.query.filter(ImportRecord.contact_id.in_(contact_ids)).delete()
        
        # Delete import records by import_file_id
        ImportRecord.query.filter_by(import_file_id=import_id).delete()
        
        # Delete calls for each contact first (to avoid foreign key constraint)
        for contact in contacts_to_delete:
            Call.query.filter_by(contact_id=contact.id).delete()
        
        # Delete related contacts
        Contact.query.filter_by(import_file_id=import_id).delete()
        
        # Delete physical file
        try:
            if os.path.exists(import_file.file_path):
                os.remove(import_file.file_path)
        except Exception as e:
            logger.warning(f"Could not delete physical file: {e}")
        
        # Delete import file record
        db.session.delete(import_file)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Import and related data deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania importu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@imports_api_bp.route('/crm/imports/bulk-delete', methods=['POST'])
@login_required
@ankieter_required
def bulk_delete_imports():
    """Bulk delete multiple imports"""
    try:
        data = request.get_json()
        import_ids = data.get('import_ids', [])
        
        if not import_ids:
            return jsonify({'success': False, 'error': 'No imports selected'}), 400
        
        deleted_count = 0
        for import_id in import_ids:
            # Check if import belongs to current user
            import_file = ImportFile.query.filter_by(
                id=import_id,
                imported_by=current_user.id
            ).first()
            
            if import_file:
                # Get contacts to delete first
                contacts_to_delete = Contact.query.filter_by(import_file_id=import_id).all()
                contact_ids = [contact.id for contact in contacts_to_delete]
                
                # Delete import records that reference these contacts
                if contact_ids:
                    ImportRecord.query.filter(ImportRecord.contact_id.in_(contact_ids)).delete()
                
                # Delete import records by import_file_id
                ImportRecord.query.filter_by(import_file_id=import_id).delete()
                
                # Delete calls for each contact first (to avoid foreign key constraint)
                for contact in contacts_to_delete:
                    Call.query.filter_by(contact_id=contact.id).delete()
                
                # Delete contacts
                Contact.query.filter_by(import_file_id=import_id).delete()
                
                # Delete physical file
                try:
                    if os.path.exists(import_file.file_path):
                        os.remove(import_file.file_path)
                except Exception as e:
                    logger.warning(f"Could not delete physical file: {e}")
                
                # Delete import file record
                db.session.delete(import_file)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Deleted {deleted_count} imports successfully',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd masowego usuwania importów: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@imports_api_bp.route('/crm/admin/import-containers', methods=['GET'])
@login_required
@admin_required_api
def get_import_containers():
    """Get all import containers for admin management"""
    try:
        import_files = ImportFile.query.order_by(ImportFile.created_at.desc()).all()
        
        containers = []
        for import_file in import_files:
            # Get contact count for this import
            contact_count = Contact.query.filter_by(import_file_id=import_file.id).count()
            
            containers.append({
                'id': import_file.id,
                'filename': import_file.filename,
                'import_status': import_file.import_status,
                'is_active': import_file.is_active,
                'contact_count': contact_count,
                'processed_rows': import_file.processed_rows,
                'total_rows': import_file.total_rows,
                'created_at': import_file.created_at.isoformat(),
                'importer_name': import_file.importer.first_name or import_file.importer.email
            })
        
        return jsonify({
            'success': True,
            'containers': containers
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania kontenerów importu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@imports_api_bp.route('/crm/admin/import-containers/<int:container_id>/toggle', methods=['POST'])
@login_required
@admin_required_api
def toggle_import_container(container_id):
    """Toggle import container active status"""
    try:
        import_file = ImportFile.query.get(container_id)
        if not import_file:
            return jsonify({'success': False, 'error': 'Import container not found'}), 404
        
        # Toggle active status
        import_file.is_active = not import_file.is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Import container {"aktywowany" if import_file.is_active else "deaktywowany"}',
            'is_active': import_file.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd przełączania kontenera importu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

