"""
CRM Controller - Business logic for CRM functionality
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.utils.auth_utils import ankieter_required
from app.models import db, User

# Create blueprint for backward compatibility
ankieter_bp = Blueprint('ankieter', __name__, template_folder='templates')

# CRM Controller Functions (exportable)
@login_required
@ankieter_required
def dashboard():
    """Ankieter dashboard"""
    try:
        # Dashboard now loads statistics via JavaScript API calls
        # Sprawdź rolę użytkownika i wybierz odpowiedni szablon
        if current_user.is_admin_role():
            return render_template('admin/crm/dashboard.html')
        else:
            return render_template('crm/dashboard.html')
        
    except Exception as e:
        flash(f'Błąd podczas ładowania dashboardu: {str(e)}', 'error')
        return redirect(url_for('public.index'))

@login_required
@ankieter_required
def calls():
    """Calls management page"""
    try:
        from app.services.crm_queue_manager import QueueManager
        from app.services.crm_event_integration import EventIntegrationService
        
        # Get next contact for ankieter
        next_contact = QueueManager.get_next_contact_for_ankieter(current_user.id)
        
        # Get available events for lead registration
        available_events = EventIntegrationService.get_available_events()
        
        # Get queue statistics
        queue_stats = QueueManager.get_ankieter_queue_stats(current_user.id)
        
        return render_template('admin/crm/calls.html',
                             next_contact=next_contact,
                             available_events=available_events,
                             queue_stats=queue_stats)
        
    except Exception as e:
        flash(f'Błąd podczas ładowania strony połączeń: {str(e)}', 'error')
        return redirect(url_for('crm.dashboard'))


@login_required
@ankieter_required
def contacts():
    """Contacts management page"""
    try:
        from app.models.crm_model import Contact
        from app.services.crm_import_service import ImportService
        
        # Get pagination parameters
        from flask import request
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Get search and filter parameters
        search = request.args.get('search', '', type=str)
        campaign_filter = request.args.get('campaign_filter', '', type=str)
        call_attempts_filter = request.args.get('call_attempts_filter', '', type=str)
        last_status_filter = request.args.get('last_status_filter', '', type=str)
        company_filter = request.args.get('company_filter', '', type=str)
        last_call_date_from = request.args.get('last_call_date_from', '', type=str)
        last_call_date_to = request.args.get('last_call_date_to', '', type=str)
        callback_date_from = request.args.get('callback_date_from', '', type=str)
        callback_date_to = request.args.get('callback_date_to', '', type=str)
        notes_filter = request.args.get('notes_filter', '', type=str)
        
        # Build query
        # Admin can see all contacts, ankieter only their assigned contacts
        if current_user.is_admin_role():
            query = Contact.query
        else:
            query = Contact.query.filter_by(assigned_ankieter_id=current_user.id)
        
        # Apply filters
        if search:
            query = query.filter(
                Contact.name.ilike(f'%{search}%') |
                Contact.phone.ilike(f'%{search}%') |
                Contact.email.ilike(f'%{search}%') |
                Contact.company.ilike(f'%{search}%')
            )
        
        if campaign_filter:
            query = query.filter(Contact.campaign_id == campaign_filter)
        
        if company_filter:
            query = query.filter(Contact.company.ilike(f'%{company_filter}%'))
        
        if notes_filter:
            query = query.filter(Contact.notes.ilike(f'%{notes_filter}%'))
        
        # Get contacts with pagination first (before complex filters)
        contacts = query.order_by(Contact.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Get last call status for each contact
        from sqlalchemy import func
        from app.models.crm_model import Call
        from app.models import db
        
        contact_analyses = []
        for contact in contacts.items:
            # Get last call status
            last_call = Call.query.filter_by(contact_id=contact.id).order_by(Call.call_date.desc()).first()
            
            # Get call count
            call_count = Call.query.filter_by(contact_id=contact.id).count()
            
            contact.last_status = last_call.status if last_call else None
            contact.last_call_date = last_call.call_date if last_call else None
            contact.call_count = call_count
            
            # Apply complex filters after analysis
            include_contact = True
            
            # Filter by call attempts
            if call_attempts_filter:
                try:
                    filter_attempts = int(call_attempts_filter)
                    if call_count != filter_attempts:
                        include_contact = False
                except ValueError:
                    pass
            
            # Filter by last status
            if last_status_filter and last_status_filter != 'new':
                if contact.last_status != last_status_filter:
                    include_contact = False
            elif last_status_filter == 'new' and contact.last_status is not None:
                include_contact = False
            
            # Filter by last call date
            if last_call_date_from and contact.last_call_date:
                from datetime import datetime
                try:
                    filter_date = datetime.strptime(last_call_date_from, '%Y-%m-%d').date()
                    if contact.last_call_date.date() < filter_date:
                        include_contact = False
                except ValueError:
                    pass
            
            if last_call_date_to and contact.last_call_date:
                from datetime import datetime
                try:
                    filter_date = datetime.strptime(last_call_date_to, '%Y-%m-%d').date()
                    if contact.last_call_date.date() > filter_date:
                        include_contact = False
                except ValueError:
                    pass
            
            # Filter by callback date (next_call_date)
            if callback_date_from and contact.next_call_date:
                from datetime import datetime
                try:
                    filter_date = datetime.strptime(callback_date_from, '%Y-%m-%d').date()
                    if contact.next_call_date.date() < filter_date:
                        include_contact = False
                except ValueError:
                    pass
            
            if callback_date_to and contact.next_call_date:
                from datetime import datetime
                try:
                    filter_date = datetime.strptime(callback_date_to, '%Y-%m-%d').date()
                    if contact.next_call_date.date() > filter_date:
                        include_contact = False
                except ValueError:
                    pass
            
            if include_contact:
                contact_analyses.append(contact)
        
        # Get import history
        import_history = ImportService.get_import_history(current_user.id)
        
        return render_template('admin/crm/contacts.html',
                             contacts=contacts,
                             contact_analyses=contact_analyses,
                             import_history=import_history,
                             search=search)
        
    except Exception as e:
        flash(f'Błąd podczas ładowania strony kontaktów: {str(e)}', 'error')
        return redirect(url_for('crm.dashboard'))

@login_required
@ankieter_required
def work():
    """Agent work screen"""
    try:
        return render_template('crm/work.html')
        
    except Exception as e:
        flash(f'Błąd podczas ładowania ekranu pracy: {str(e)}', 'error')
        return redirect(url_for('crm.dashboard'))

@login_required
@ankieter_required
def export():
    """CRM Export page"""
    try:
        from app.services.crm_export_service import CRMExportService
        
        # Get available options for filters
        campaigns = CRMExportService.get_available_campaigns()
        ankieter = CRMExportService.get_available_ankieters()
        statuses = CRMExportService.get_available_statuses()
        
        return render_template('admin/crm/export.html',
                             campaigns=campaigns,
                             ankieter=ankieter,
                             statuses=statuses)
        
    except Exception as e:
        flash(f'Błąd podczas ładowania strony eksportu: {str(e)}', 'error')
        return redirect(url_for('crm.dashboard'))


# Register routes with blueprint for backward compatibility
@ankieter_bp.route('/')
@login_required
@ankieter_required
def ankieter_dashboard():
    return dashboard()

@ankieter_bp.route('/calls')
@login_required
@ankieter_required
def ankieter_calls():
    return calls()

@ankieter_bp.route('/contacts')
@login_required
@ankieter_required
def ankieter_contacts():
    return contacts()

@ankieter_bp.route('/work')
@login_required
@ankieter_required
def ankieter_work():
    return work()

