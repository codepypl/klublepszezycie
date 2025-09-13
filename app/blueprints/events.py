"""
Events Management Blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import EventSchedule, EventRegistration

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
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get event registrations with pagination
        registrations_pagination = EventRegistration.query.order_by(
            EventRegistration.created_at.desc()
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        event_registrations = registrations_pagination.items
        
        # Get all events for filter
        events = EventSchedule.query.filter_by(is_published=True).order_by(EventSchedule.event_date.desc()).all()
        
        return render_template('admin/event_registrations.html',
                             event_registrations=event_registrations,
                             events=events,
                             pagination=registrations_pagination)
    except Exception as e:
        flash(f'Błąd podczas ładowania rejestracji: {str(e)}', 'error')
        return render_template('admin/event_registrations.html', 
                             event_registrations=[], 
                             events=[], 
                             pagination=None)

@events_bp.route('/events/email-schedules')
@login_required
def email_schedules():
    """Redirect to new email system"""
    from flask import redirect, url_for
    return redirect(url_for('admin.email_system'))

