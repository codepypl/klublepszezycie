"""
Events routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.blueprints.events_controller import EventsController

events_bp = Blueprint('events', __name__)

@events_bp.route('/events')
@login_required
def index():
    """Events management page"""
    return render_template('admin/event_schedule.html')

@events_bp.route('/events/schedules')
@login_required
def schedules():
    """Event schedules management page"""
    return render_template('admin/schedules.html')

@events_bp.route('/events/registrations')
@login_required
def registrations():
    """Event registrations management page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status = request.args.get('status')
    search = request.args.get('search')
    
    data = EventsController.get_registrations(
        page=page, 
        per_page=per_page, 
        status=status, 
        search=search
    )
    
    if not data['success']:
        flash(f'Błąd: {data["error"]}', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/registrations.html', 
                         registrations=data['registrations'],
                         pagination=data.get('pagination'))

@events_bp.route('/events/register/<int:event_id>', methods=['GET', 'POST'])
@login_required
def register(event_id):
    """Register for event"""
    if request.method == 'POST':
        notes = request.form.get('notes', '').strip()
        
        result = EventsController.register_for_event(event_id, current_user.id, notes)
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('events.registrations'))
        else:
            flash(result['error'], 'error')
    
    # Get event details
    data = EventsController.get_event(event_id)
    
    if not data['success']:
        flash(data['error'], 'error')
        return redirect(url_for('events.index'))
    
    return render_template('events/register.html', event=data['event'])

@events_bp.route('/events/cancel/<int:registration_id>', methods=['POST'])
@login_required
def cancel_registration(registration_id):
    """Cancel event registration"""
    result = EventsController.cancel_registration(registration_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('events.registrations'))