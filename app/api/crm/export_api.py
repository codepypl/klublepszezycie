"""
CRM Export API - data export functionality
"""
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from functools import wraps
from app.models import User, db
from app.utils.auth_utils import admin_required
import os
import tempfile
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Create CRM Export API blueprint
export_api_bp = Blueprint('crm_export_api', __name__)

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

@export_api_bp.route('/crm/export/summary', methods=['GET'])
@login_required
@admin_required_api
def export_summary():
    """Export CRM summary data"""
    try:
        from app.models.crm_model import Contact, Call, ImportFile, Campaign, BlacklistEntry
        from datetime import datetime, timedelta
        
        # Get date range
        days = request.args.get('days', 30, type=int)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get summary data
        summary_data = {
            'export_date': datetime.now().isoformat(),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': days
            },
            'totals': {
                'contacts': Contact.query.count(),
                'calls': Call.query.count(),
                'imports': ImportFile.query.count(),
                'campaigns': Campaign.query.count(),
                'blacklist_entries': BlacklistEntry.query.filter_by(is_active=True).count()
            },
            'period_data': {
                'contacts_created': Contact.query.filter(Contact.created_at >= start_date).count(),
                'calls_made': Call.query.filter(Call.created_at >= start_date).count(),
                'leads_generated': Call.query.filter(
                    Call.status == 'lead',
                    Call.created_at >= start_date
                ).count(),
                'imports_processed': ImportFile.query.filter(ImportFile.created_at >= start_date).count()
            },
            'ankieter_stats': []
        }
        
        # Get ankieter statistics
        ankieter_stats = db.session.query(
            User.id,
            User.first_name,
            User.email,
            db.func.count(Call.id).label('total_calls'),
            db.func.count(db.case([(Call.status == 'lead', 1)], else_=None)).label('leads'),
            db.func.count(db.case([(Call.status == 'answered', 1)], else_=None)).label('answered')
        ).join(Call, User.id == Call.ankieter_id).filter(
            Call.created_at >= start_date
        ).group_by(User.id, User.first_name, User.email).all()
        
        for stat in ankieter_stats:
            summary_data['ankieter_stats'].append({
                'id': stat.id,
                'name': stat.first_name or stat.email,
                'total_calls': stat.total_calls,
                'leads': stat.leads,
                'answered': stat.answered
            })
        
        return jsonify({
            'success': True,
            'summary': summary_data
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd eksportu podsumowania: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@export_api_bp.route('/crm/export/download', methods=['POST'])
@login_required
@admin_required_api
def download_export():
    """Download CRM data as Excel file"""
    try:
        from app.models.crm_model import Contact, Call, ImportFile, Campaign, BlacklistEntry
        from datetime import datetime, timedelta
        
        data = request.get_json()
        export_type = data.get('export_type', 'all')
        days = data.get('days', 30, type=int)
        
        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_file.close()
        
        with pd.ExcelWriter(temp_file.name, engine='openpyxl') as writer:
            
            if export_type in ['all', 'contacts']:
                # Export contacts
                contacts = Contact.query.filter(Contact.created_at >= start_date).all()
                contacts_data = []
                for contact in contacts:
                    contacts_data.append({
                        'ID': contact.id,
                        'Name': contact.name,
                        'Phone': contact.phone,
                        'Email': contact.email,
                        'Company': contact.company,
                        'Call Attempts': contact.call_attempts,
                        'Max Call Attempts': contact.max_call_attempts,
                        'Is Blacklisted': contact.is_blacklisted,
                        'Last Call Date': contact.last_call_date.isoformat() if contact.last_call_date else None,
                        'Created At': contact.created_at.isoformat()
                    })
                
                df_contacts = pd.DataFrame(contacts_data)
                df_contacts.to_excel(writer, sheet_name='Contacts', index=False)
            
            if export_type in ['all', 'calls']:
                # Export calls
                calls = Call.query.filter(Call.created_at >= start_date).all()
                calls_data = []
                for call in calls:
                    calls_data.append({
                        'ID': call.id,
                        'Contact ID': call.contact_id,
                        'Contact Name': call.contact.name if call.contact else None,
                        'Ankieter ID': call.ankieter_id,
                        'Ankieter Name': call.ankieter.first_name if call.ankieter else None,
                        'Call Date': call.call_date.isoformat(),
                        'Status': call.status,
                        'Priority': call.priority,
                        'Duration Minutes': call.duration_minutes,
                        'Notes': call.notes,
                        'Next Call Date': call.next_call_date.isoformat() if call.next_call_date else None,
                        'Is Lead Registered': call.is_lead_registered
                    })
                
                df_calls = pd.DataFrame(calls_data)
                df_calls.to_excel(writer, sheet_name='Calls', index=False)
            
            if export_type in ['all', 'campaigns']:
                # Export campaigns
                campaigns = Campaign.query.all()
                campaigns_data = []
                for campaign in campaigns:
                    campaigns_data.append({
                        'ID': campaign.id,
                        'Name': campaign.name,
                        'Description': campaign.description,
                        'Created By': campaign.created_by,
                        'Created At': campaign.created_at.isoformat(),
                        'Updated At': campaign.updated_at.isoformat(),
                        'Is Active': campaign.is_active
                    })
                
                df_campaigns = pd.DataFrame(campaigns_data)
                df_campaigns.to_excel(writer, sheet_name='Campaigns', index=False)
            
            if export_type in ['all', 'blacklist']:
                # Export blacklist
                blacklist_entries = BlacklistEntry.query.filter_by(is_active=True).all()
                blacklist_data = []
                for entry in blacklist_entries:
                    blacklist_data.append({
                        'ID': entry.id,
                        'Phone': entry.phone,
                        'Reason': entry.reason,
                        'Contact ID': entry.contact_id,
                        'Contact Name': entry.contact.name if entry.contact else None,
                        'Blacklisted By': entry.blacklisted_by,
                        'Created At': entry.created_at.isoformat()
                    })
                
                df_blacklist = pd.DataFrame(blacklist_data)
                df_blacklist.to_excel(writer, sheet_name='Blacklist', index=False)
        
        # Send file
        return send_file(
            temp_file.name,
            as_attachment=True,
            download_name=f'crm_export_{export_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania eksportu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@export_api_bp.route('/crm/export/campaigns', methods=['GET'])
@login_required
@admin_required_api
def get_export_campaigns():
    """Get available campaigns for export"""
    try:
        from app.models.crm_model import Campaign
        
        campaigns = Campaign.query.filter_by(is_active=True).all()
        
        campaigns_data = []
        for campaign in campaigns:
            campaigns_data.append({
                'id': campaign.id,
                'name': campaign.name,
                'description': campaign.description
            })
        
        return jsonify({
            'success': True,
            'campaigns': campaigns_data
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania kampanii do eksportu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@export_api_bp.route('/crm/export/ankieters', methods=['GET'])
@login_required
@admin_required_api
def get_export_ankieters():
    """Get available ankieter for export"""
    try:
        ankieter = User.query.filter_by(account_type='ankieter', is_active=True).all()
        
        ankieter_data = []
        for user in ankieter:
            ankieter_data.append({
                'id': user.id,
                'name': user.first_name or user.email,
                'email': user.email
            })
        
        return jsonify({
            'success': True,
            'ankieters': ankieter_data
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania ankieter do eksportu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@export_api_bp.route('/crm/export/statuses', methods=['GET'])
@login_required
@admin_required_api
def get_export_statuses():
    """Get available call statuses for export"""
    try:
        from app.models.crm_model import Call
        
        # Get unique statuses
        statuses = db.session.query(Call.status).distinct().all()
        
        status_list = [status[0] for status in statuses if status[0]]
        
        return jsonify({
            'success': True,
            'statuses': status_list
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statusów do eksportu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500




