"""
CRM Export API Endpoints
"""
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from functools import wraps
from app.models import User, db
from app.utils.auth_utils import admin_required
import os
import tempfile

# Create CRM Export API blueprint
crm_export_api_bp = Blueprint('crm_export_api', __name__, url_prefix='/api/crm/export')

def admin_required_api(f):
    """Decorator to require admin role for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        if not current_user.is_admin_role():
            return jsonify({'success': False, 'error': 'Admin role required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@crm_export_api_bp.route('/summary', methods=['GET'])
@login_required
@admin_required_api
def get_export_summary():
    """Get export summary with filters"""
    try:
        from app.services.crm_export_service import CRMExportService
        from datetime import datetime
        
        # Get filter parameters
        campaign_id = request.args.get('campaign_id', type=int)
        ankieter_id = request.args.get('ankieter_id', type=int)
        status_filter = request.args.get('status', type=str)
        
        # Parse dates
        date_from = None
        date_to = None
        
        date_from_str = request.args.get('date_from', type=str)
        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid date_from format. Use YYYY-MM-DD'}), 400
        
        date_to_str = request.args.get('date_to', type=str)
        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid date_to format. Use YYYY-MM-DD'}), 400
        
        # Get summary
        summary = CRMExportService.get_export_summary(
            campaign_id=campaign_id,
            ankieter_id=ankieter_id,
            date_from=date_from,
            date_to=date_to,
            status_filter=status_filter
        )
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_export_api_bp.route('/download', methods=['POST'])
@login_required
@admin_required_api
def download_export():
    """Download export file"""
    try:
        from app.services.crm_export_service import CRMExportService
        from datetime import datetime
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Get filter parameters
        campaign_id = data.get('campaign_id')
        ankieter_id = data.get('ankieter_id')
        status_filter = data.get('status')
        
        # Parse dates
        date_from = None
        date_to = None
        
        date_from_str = data.get('date_from')
        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid date_from format. Use YYYY-MM-DD'}), 400
        
        date_to_str = data.get('date_to')
        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid date_to format. Use YYYY-MM-DD'}), 400
        
        # Generate export file
        file_path, filename = CRMExportService.export_calls_data(
            campaign_id=campaign_id,
            ankieter_id=ankieter_id,
            date_from=date_from,
            date_to=date_to,
            status_filter=status_filter
        )
        
        # Send file
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        # Clean up temporary file
        try:
            if 'file_path' in locals():
                os.unlink(file_path)
        except:
            pass

@crm_export_api_bp.route('/campaigns', methods=['GET'])
@login_required
@admin_required_api
def get_campaigns():
    """Get available campaigns for export"""
    try:
        from app.services.crm_export_service import CRMExportService
        
        campaigns = CRMExportService.get_available_campaigns()
        
        return jsonify({
            'success': True,
            'campaigns': campaigns
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_export_api_bp.route('/ankieters', methods=['GET'])
@login_required
@admin_required_api
def get_ankieters():
    """Get available ankieter for export"""
    try:
        from app.services.crm_export_service import CRMExportService
        
        ankieter = CRMExportService.get_available_ankieters()
        
        return jsonify({
            'success': True,
            'ankieters': ankieter
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@crm_export_api_bp.route('/statuses', methods=['GET'])
@login_required
@admin_required_api
def get_statuses():
    """Get available call statuses for export"""
    try:
        from app.services.crm_export_service import CRMExportService
        
        statuses = CRMExportService.get_available_statuses()
        
        return jsonify({
            'success': True,
            'statuses': statuses
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
