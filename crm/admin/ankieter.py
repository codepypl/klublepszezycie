"""
Ankieter routes blueprint
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.utils.auth import ankieter_required
from models import db, User

ankieter_bp = Blueprint('ankieter', __name__, template_folder='templates')

@ankieter_bp.route('/')
@login_required
@ankieter_required
def dashboard():
    """Ankieter dashboard"""
    try:
        # Get statistics for ankieter
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        
        # Get ankieter info
        ankieter_info = {
            'name': current_user.name or current_user.email,
            'role': current_user.role,
            'last_login': current_user.last_login
        }
        
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'ankieter_info': ankieter_info
        }
        
        return render_template('ankieter/dashboard.html', stats=stats)
        
    except Exception as e:
        flash(f'Błąd podczas ładowania dashboardu: {str(e)}', 'error')
        return redirect(url_for('public.index'))

@ankieter_bp.route('/calls')
@login_required
@ankieter_required
def calls():
    """Calls management page"""
    try:
        from crm.services.queue_manager import QueueManager
        from crm.services.event_integration import EventIntegrationService
        
        # Get next contact for ankieter
        next_contact = QueueManager.get_next_contact_for_ankieter(current_user.id)
        
        # Get available events for lead registration
        available_events = EventIntegrationService.get_available_events()
        
        # Get queue statistics
        queue_stats = QueueManager.get_ankieter_queue_stats(current_user.id)
        
        return render_template('ankieter/calls.html',
                             next_contact=next_contact,
                             available_events=available_events,
                             queue_stats=queue_stats)
        
    except Exception as e:
        flash(f'Błąd podczas ładowania strony połączeń: {str(e)}', 'error')
        return redirect(url_for('ankieter.dashboard'))


@ankieter_bp.route('/contacts')
@login_required
@ankieter_required
def contacts():
    """Contacts management page"""
    try:
        from crm.models import Contact
        from crm.services.import_service import ImportService
        
        # Get contacts assigned to current ankieter
        contacts = Contact.query.filter_by(
            assigned_ankieter_id=current_user.id
        ).order_by(Contact.created_at.desc()).limit(50).all()
        
        # Get import history
        import_history = ImportService.get_import_history(current_user.id)
        
        return render_template('ankieter/contacts.html',
                             contacts=contacts,
                             import_history=import_history)
        
    except Exception as e:
        flash(f'Błąd podczas ładowania strony kontaktów: {str(e)}', 'error')
        return redirect(url_for('ankieter.dashboard'))
