"""
Agent Work API Endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import User, db
from app.models.crm_model import Contact, Call
from datetime import datetime

# Create Agent API blueprint
agent_api_bp = Blueprint('agent_api', __name__, url_prefix='/api/crm/agent')

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

@agent_api_bp.route('/start-work', methods=['POST'])
@login_required
@ankieter_required
def start_work():
    """Start agent work session"""
    try:
        return jsonify({
            'success': True,
            'message': 'Praca rozpoczęta'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/stop-work', methods=['POST'])
@login_required
@ankieter_required
def stop_work():
    """Stop agent work session"""
    try:
        return jsonify({
            'success': True,
            'message': 'Praca zatrzymana'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/next-contact', methods=['POST'])
@login_required
@ankieter_required
def next_contact():
    """Get next contact for agent based on priority"""
    try:
        # Priority order: callbacks > potentials > new contacts
        # 1. First check for callbacks (scheduled calls)
        callback_contact = Contact.query.join(Call).filter(
            Call.next_call_date <= datetime.now(),
            Call.status == 'callback',
            Contact.is_active == True,
            Contact.is_blacklisted == False
        ).first()
        
        if callback_contact:
            return jsonify({
                'success': True,
                'contact': {
                    'id': callback_contact.id,
                    'name': callback_contact.name,
                    'phone': callback_contact.phone,
                    'email': callback_contact.email,
                    'company': callback_contact.company,
                    'notes': callback_contact.notes,
                    'priority': 'callback'
                }
            })
        
        # 2. Check for potential leads (contacts with previous calls but not leads/rejections)
        # Only include contacts that haven't reached max attempts and aren't leads/rejections
        potential_contact = Contact.query.join(Call).filter(
            Contact.is_active == True,
            Contact.is_blacklisted == False,
            Contact.call_attempts < Contact.max_call_attempts,
            Call.status.in_(['no_answer', 'busy', 'wrong_number'])
        ).filter(
            ~Contact.id.in_(
                db.session.query(Call.contact_id).filter(Call.status.in_(['lead', 'rejection']))
            )
        ).first()
        
        if potential_contact:
            return jsonify({
                'success': True,
                'contact': {
                    'id': potential_contact.id,
                    'name': potential_contact.name,
                    'phone': potential_contact.phone,
                    'email': potential_contact.email,
                    'company': potential_contact.company,
                    'notes': potential_contact.notes,
                    'priority': 'potential'
                }
            })
        
        # 3. Check for new contacts (no calls yet)
        new_contact = Contact.query.filter(
            Contact.is_active == True,
            Contact.is_blacklisted == False,
            ~Contact.id.in_(db.session.query(Call.contact_id))
        ).first()
        
        if new_contact:
            return jsonify({
                'success': True,
                'contact': {
                    'id': new_contact.id,
                    'name': new_contact.name,
                    'phone': new_contact.phone,
                    'email': new_contact.email,
                    'company': new_contact.company,
                    'notes': new_contact.notes,
                    'priority': 'new'
                }
            })
        
        return jsonify({
            'success': False,
            'message': 'Brak kontaktów do dzwonienia'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/call-history/<int:contact_id>')
@login_required
@ankieter_required
def call_history(contact_id):
    """Get call history for a contact"""
    try:
        calls = Call.query.filter_by(contact_id=contact_id).order_by(Call.call_date.desc()).all()
        
        call_list = []
        for call in calls:
            call_list.append({
                'id': call.id,
                'call_date': call.call_date.isoformat(),
                'status': call.status,
                'notes': call.notes,
                'duration_minutes': call.duration_minutes
            })
        
        return jsonify({
            'success': True,
            'calls': call_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/start-call', methods=['POST'])
@login_required
@ankieter_required
def start_call():
    """Start a call session"""
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        
        if not contact_id:
            return jsonify({'success': False, 'error': 'Contact ID required'}), 400
        
        # Get current time
        now = datetime.now()
        
        # Check if contact has pending callback
        existing_callback = Call.query.filter(
            Call.contact_id == contact_id,
            Call.status == 'callback',
            Call.next_call_date <= now
        ).first()
        
        if existing_callback:
            # Update existing callback to in_progress
            call = existing_callback
            call.call_date = now
            call.call_start_time = now
            call.status = 'in_progress'
        else:
            # Create new call record
            call = Call(
                contact_id=contact_id,
                ankieter_id=current_user.id,
                call_date=now,
                call_start_time=now,
                status='in_progress'
            )
        
        db.session.add(call)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'call_id': call.id,
            'start_time': now.isoformat()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/save-outcome', methods=['POST'])
@login_required
@ankieter_required
def save_outcome():
    """Save call outcome"""
    try:
        data = request.get_json()
        call_id = data.get('call_id')
        outcome = data.get('outcome')
        notes = data.get('notes', '')
        callback_date = data.get('callback_date')
        
        if not call_id or not outcome:
            return jsonify({'success': False, 'error': 'Call ID and outcome required'}), 400
        
        # Get call record
        call = Call.query.get(call_id)
        if not call:
            return jsonify({'success': False, 'error': 'Call not found'}), 404
        
        # Calculate call duration
        now = datetime.now()
        call.call_end_time = now
        
        if call.call_start_time:
            duration = now - call.call_start_time
            call.duration_seconds = int(duration.total_seconds())
            call.duration_minutes = int(duration.total_seconds() / 60)
        
        # Update call with outcome
        call.status = outcome
        call.notes = notes
        
        if outcome == 'callback' and callback_date:
            call.next_call_date = datetime.fromisoformat(callback_date)
        
        # If it's a lead, register for event
        if outcome == 'lead':
            call.is_lead_registered = True
        
        # Update contact call attempts
        contact = call.contact
        contact.call_attempts += 1
        contact.last_call_date = datetime.now()
        
        # If it's a rejection, add to blacklist
        if outcome == 'rejection':
            contact.is_blacklisted = True
        
        # If max attempts reached, add to blacklist (for no_answer, busy, wrong_number)
        if contact.call_attempts >= contact.max_call_attempts and outcome in ['no_answer', 'busy', 'wrong_number']:
            contact.is_blacklisted = True
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Wynik rozmowy zapisany',
            'duration_seconds': call.duration_seconds,
            'duration_minutes': call.duration_minutes
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/queue-status')
@login_required
@ankieter_required
def queue_status():
    """Get queue status for agent"""
    try:
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Count callbacks
        callbacks = Contact.query.join(Call).filter(
            Call.next_call_date <= datetime.now(),
            Call.status == 'callback',
            Contact.is_active == True,
            Contact.is_blacklisted == False
        ).count()
        
        # Count potentials (contacts with previous calls but not leads/rejections, within max attempts)
        potentials = Contact.query.join(Call).filter(
            Contact.is_active == True,
            Contact.is_blacklisted == False,
            Contact.call_attempts < Contact.max_call_attempts,
            Call.status.in_(['no_answer', 'busy', 'wrong_number'])
        ).filter(
            ~Contact.id.in_(
                db.session.query(Call.contact_id).filter(Call.status.in_(['lead', 'rejection']))
            )
        ).count()
        
        # Count new contacts
        new_contacts = Contact.query.filter(
            Contact.is_active == True,
            Contact.is_blacklisted == False,
            ~Contact.id.in_(db.session.query(Call.contact_id))
        ).count()
        
        # Count total contacts
        total_contacts = Contact.query.filter(
            Contact.is_active == True
        ).count()
        
        # Today's statistics for current agent
        today_calls = Call.query.filter(
            Call.ankieter_id == current_user.id,
            Call.created_at >= today_start,
            Call.created_at <= today_end
        )
        
        leads_today = today_calls.filter(Call.status == 'lead').count()
        rejections_today = today_calls.filter(Call.status == 'rejection').count()
        callbacks_today = today_calls.filter(Call.status == 'callback').count()
        no_answer_today = today_calls.filter(Call.status == 'no_answer').count()
        busy_today = today_calls.filter(Call.status == 'busy').count()
        wrong_number_today = today_calls.filter(Call.status == 'wrong_number').count()
        
        # Calculate total call time today
        total_call_time = db.session.query(db.func.sum(Call.duration_seconds)).filter(
            Call.ankieter_id == current_user.id,
            Call.created_at >= today_start,
            Call.created_at <= today_end,
            Call.duration_seconds.isnot(None)
        ).scalar() or 0
        
        # Calculate average call time
        avg_call_time = 0
        call_count = today_calls.filter(Call.duration_seconds.isnot(None)).count()
        if call_count > 0:
            avg_call_time = total_call_time / call_count
        
        # Calculate longest call today
        longest_call = today_calls.filter(Call.duration_seconds.isnot(None)).order_by(Call.duration_seconds.desc()).first()
        longest_call_time = longest_call.duration_seconds if longest_call else 0
        
        # Total statistics for current agent
        total_leads = Call.query.filter(
            Call.ankieter_id == current_user.id,
            Call.status == 'lead'
        ).count()
        
        total_rejections = Call.query.filter(
            Call.ankieter_id == current_user.id,
            Call.status == 'rejection'
        ).count()
        
        total_callbacks = Call.query.filter(
            Call.ankieter_id == current_user.id,
            Call.status == 'callback'
        ).count()
        
        total_no_answer = Call.query.filter(
            Call.ankieter_id == current_user.id,
            Call.status == 'no_answer'
        ).count()
        
        total_busy = Call.query.filter(
            Call.ankieter_id == current_user.id,
            Call.status == 'busy'
        ).count()
        
        total_wrong_number = Call.query.filter(
            Call.ankieter_id == current_user.id,
            Call.status == 'wrong_number'
        ).count()
        
        # Get next callback time
        next_callback = Call.query.filter(
            Call.ankieter_id == current_user.id,
            Call.status == 'callback',
            Call.next_call_date > datetime.now()
        ).order_by(Call.next_call_date.asc()).first()
        
        next_callback_time = None
        if next_callback:
            next_callback_time = next_callback.next_call_date.isoformat()
        
        return jsonify({
            'success': True,
            'queue': {
                'callbacks': callbacks,
                'potentials': potentials,
                'new_contacts': new_contacts
            },
            'total_contacts': total_contacts,
            'next_callback': next_callback_time,
            'today_stats': {
                'leads': leads_today,
                'rejections': rejections_today,
                'callbacks': callbacks_today,
                'no_answer': no_answer_today,
                'busy': busy_today,
                'wrong_number': wrong_number_today,
                'total_call_time_seconds': total_call_time,
                'total_call_time_minutes': int(total_call_time / 60),
                'avg_call_time_seconds': int(avg_call_time),
                'avg_call_time_minutes': int(avg_call_time / 60),
                'longest_call_seconds': longest_call_time,
                'longest_call_minutes': int(longest_call_time / 60)
            },
            'total_stats': {
                'leads': total_leads,
                'rejections': total_rejections,
                'callbacks': total_callbacks,
                'no_answer': total_no_answer,
                'busy': total_busy,
                'wrong_number': total_wrong_number
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
