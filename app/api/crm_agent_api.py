"""
Agent Work API Endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import User, db
from app.models.crm_model import Contact, Call, ImportFile, BlacklistEntry
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
        from flask import request
        data = request.get_json()
        campaign_id = data.get('campaign_id') if data else None
        
        if not campaign_id:
            return jsonify({
                'success': False,
                'error': 'Campaign ID is required'
            }), 400
        # Priority order: callbacks > potentials > new contacts
        # 1. First check for callbacks (scheduled calls)
        callback_contact = Contact.query.join(Call).join(ImportFile).filter(
            Call.next_call_date <= datetime.now(),
            Call.status == 'callback',
            Contact.is_active == True,
            Contact.is_blacklisted == False,
            Contact.campaign_id == campaign_id,  # Filter by selected campaign
            ImportFile.is_active == True  # Only from active import containers
        ).first()
        
        if callback_contact:
            # Get the callback call record to get callback_date
            callback_call = Call.query.filter(
                Call.contact_id == callback_contact.id,
                Call.status == 'callback',
                Call.next_call_date <= datetime.now()
            ).first()
            
            contact_data = {
                'id': callback_contact.id,
                'name': callback_contact.name,
                'phone': callback_contact.phone,
                'email': callback_contact.email,
                'company': callback_contact.company,
                'notes': callback_contact.notes,
                'priority': 'callback',
                'campaign_script': callback_contact.campaign.script_content if callback_contact.campaign else None,
                'campaign_name': callback_contact.campaign.name if callback_contact.campaign else None
            }
            
            if callback_call and callback_call.next_call_date:
                contact_data['callback_date'] = callback_call.next_call_date.isoformat()
            
            return jsonify({
                'success': True,
                'contact': contact_data
            })
        
        # 2. Check for potential leads (contacts with previous calls but not leads/rejections)
        # Only include contacts that haven't reached max attempts and aren't leads/rejections
        potential_contact = Contact.query.join(Call).join(ImportFile).filter(
            Contact.is_active == True,
            Contact.is_blacklisted == False,
            Contact.campaign_id == campaign_id,  # Filter by selected campaign
            Contact.call_attempts < Contact.max_call_attempts,
            ImportFile.is_active == True,  # Only from active import containers
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
                    'priority': 'potential',
                    'campaign_script': potential_contact.campaign.script_content if potential_contact.campaign else None,
                    'campaign_name': potential_contact.campaign.name if potential_contact.campaign else None
                }
            })
        
        # 3. Check for new contacts (no calls yet)
        new_contact = Contact.query.join(ImportFile).filter(
            Contact.is_active == True,
            Contact.is_blacklisted == False,
            Contact.campaign_id == campaign_id,  # Filter by selected campaign
            ImportFile.is_active == True,  # Only from active import containers
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
                    'priority': 'new',
                    'campaign_script': new_contact.campaign.script_content if new_contact.campaign else None,
                    'campaign_name': new_contact.campaign.name if new_contact.campaign else None
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
        timezone = data.get('timezone', 'Europe/Warsaw')
        call_duration_seconds = data.get('call_duration_seconds', 0)
        record_duration_seconds = data.get('record_duration_seconds', 0)
        
        if not call_id or not outcome:
            return jsonify({'success': False, 'error': 'Call ID and outcome required'}), 400
        
        # Get call record
        call = Call.query.get(call_id)
        if not call:
            return jsonify({'success': False, 'error': 'Call not found'}), 404
        
        # Set call end time
        now = datetime.now()
        call.call_end_time = now
        
        # Use provided durations (from frontend) or calculate from timestamps
        if call_duration_seconds > 0:
            call.duration_seconds = call_duration_seconds
            call.duration_minutes = int(call_duration_seconds / 60)
        elif call.call_start_time:
            duration = now - call.call_start_time
            call.duration_seconds = int(duration.total_seconds())
            call.duration_minutes = int(duration.total_seconds() / 60)
        
        # Update call with outcome
        call.status = outcome
        call.notes = notes
        
        # Add record handling duration to notes
        if record_duration_seconds > 0:
            record_duration_note = f"\n\n[Czas obsługi rekordu: {record_duration_seconds}s]"
            call.notes = (call.notes or '') + record_duration_note
        
        if outcome == 'callback' and callback_date:
            # Parse callback date with timezone awareness
            from datetime import timezone as dt_timezone
            import pytz
            
            try:
                # Parse the datetime string
                callback_dt = datetime.fromisoformat(callback_date.replace('Z', '+00:00'))
                
                # Convert to specified timezone if not already timezone-aware
                if callback_dt.tzinfo is None:
                    tz = pytz.timezone(timezone)
                    callback_dt = tz.localize(callback_dt)
                
                # Store in UTC
                call.next_call_date = callback_dt.astimezone(pytz.UTC)
                
            except Exception as e:
                return jsonify({'success': False, 'error': f'Invalid callback date format: {str(e)}'}), 400
        
        # If it's a lead, register for event
        if outcome == 'lead':
            call.is_lead_registered = True
        
        # Update contact call attempts
        contact = call.contact
        contact.call_attempts += 1
        contact.last_call_date = datetime.now()
        
        # If it's explicitly blacklisted, add to blacklist
        if outcome == 'blacklist':
            # Add phone to blacklist for this campaign
            blacklist_entry = BlacklistEntry(
                phone=contact.phone,
                reason=f"Dodany przez agenta: {notes or 'Brak powodu'}",
                campaign_id=contact.campaign_id,
                blacklisted_by=current_user.id,
                contact_id=contact.id,
                is_active=True
            )
            db.session.add(blacklist_entry)
            contact.is_blacklisted = True
        
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
            'duration_minutes': call.duration_minutes,
            'call_duration_seconds': call_duration_seconds,
            'record_duration_seconds': record_duration_seconds
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
        
        # Count callbacks (available now or overdue)
        callback_contacts = Contact.query.join(Call).filter(
            Call.next_call_date <= datetime.now(),
            Call.status == 'callback',
            Contact.is_active == True,
            Contact.is_blacklisted == False
        ).all()
        
        callbacks = len(callback_contacts)
        print(f"🔍 Debug callbacks: found {callbacks} callback contacts")
        for contact in callback_contacts:
            print(f"  - Contact {contact.id}: {contact.name}, next_call: {contact.calls.filter_by(status='callback').first().next_call_date if contact.calls.filter_by(status='callback').first() else 'None'}")
        
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
        
        # Calculate daily time statistics (always fresh calculation)
        from app.models.stats_model import Stats
        from app.models.user_logs_model import UserLogs
        
        print(f"🔍 Calculating fresh stats for user {current_user.id} on {today}")
        
        # Get all login/logout logs for today for this user
        today_logs = UserLogs.query.filter(
            UserLogs.user_id == current_user.id,
            UserLogs.created_at >= today_start,
            UserLogs.created_at <= today_end,
            UserLogs.action_type.in_(['login', 'logout'])
        ).order_by(UserLogs.created_at.asc()).all()
        
        print(f"🔍 Found {len(today_logs)} login/logout logs for today")
        
        total_login_time_seconds = 0
        login_time = None
        
        # Calculate total login time by pairing login/logout events
        for log in today_logs:
            print(f"🔍 Processing log: {log.action_type} at {log.created_at}")
            if log.action_type == 'login':
                login_time = log.created_at
                print(f"🔍 Login detected at {login_time}")
            elif log.action_type == 'logout' and login_time:
                session_duration = (log.created_at - login_time).total_seconds()
                total_login_time_seconds += max(0, session_duration)
                print(f"🔍 Logout detected, session duration: {session_duration}s, total so far: {total_login_time_seconds}s")
                login_time = None
        
        # If user is still logged in (no logout for last login), add time until now
        if login_time:
            current_time = datetime.now()
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=login_time.tzinfo)
            session_duration = (current_time - login_time).total_seconds()
            total_login_time_seconds += max(0, session_duration)
            print(f"🔍 User still logged in, adding {session_duration}s to total: {total_login_time_seconds}s")
        
        # Calculate work time - get from daily work time tracking (localStorage on frontend)
        # For now, we'll use a combination of call time and estimated work time
        # In the future, this should be retrieved from the frontend's daily work time tracking
        total_work_time_seconds = total_call_time + (callbacks_today * 300)  # Call time + 5min per callback
        
        # TODO: Get real work time from frontend localStorage
        # This should be called from the frontend and passed to this endpoint
        # For now, we'll use the estimated calculation above
        
        # Calculate break time (login time - work time)
        total_break_time_seconds = max(0, total_login_time_seconds - total_work_time_seconds)
        
        print(f"🔍 Final calculated stats: login={total_login_time_seconds}s, work={total_work_time_seconds}s, break={total_break_time_seconds}s")
        print(f"🔍 Breakdown: call_time={total_call_time}s, callbacks_today={callbacks_today}, lunch=1800s")
        
        # Save daily statistics to Stats table (always update with fresh calculations)
        today_date = today
        
        # Save daily stats for this user
        Stats.set_value('daily_login_time_seconds', int(total_login_time_seconds), 
                       related_id=current_user.id, related_type='user', date_period=today_date)
        Stats.set_value('daily_work_time_seconds', int(total_work_time_seconds), 
                       related_id=current_user.id, related_type='user', date_period=today_date)
        Stats.set_value('daily_break_time_seconds', int(total_break_time_seconds), 
                       related_id=current_user.id, related_type='user', date_period=today_date)
        Stats.set_value('daily_calls_count', leads_today + rejections_today + callbacks_today + 
                       no_answer_today + busy_today + wrong_number_today,
                       related_id=current_user.id, related_type='user', date_period=today_date)
        Stats.set_value('daily_leads_count', leads_today,
                       related_id=current_user.id, related_type='user', date_period=today_date)
        Stats.set_value('daily_callbacks_count', callbacks_today,
                       related_id=current_user.id, related_type='user', date_period=today_date)
        
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
                'total_call_time_seconds': int(total_call_time),
                'total_call_time_minutes': int(total_call_time / 60),
                'avg_call_time_seconds': int(avg_call_time),
                'avg_call_time_minutes': int(avg_call_time / 60),
                'longest_call_seconds': int(longest_call_time),
                'longest_call_minutes': int(longest_call_time / 60),
                'total_login_time_seconds': int(total_login_time_seconds),
                'total_work_time_seconds': int(total_work_time_seconds),
                'total_break_time_seconds': int(total_break_time_seconds)
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

@agent_api_bp.route('/add-contact-note', methods=['POST'])
@login_required
@ankieter_required
def add_contact_note():
    """Add note to contact"""
    try:
        data = request.get_json()
        contact_id = data.get('contact_id')
        note = data.get('note')
        
        if not contact_id or not note:
            return jsonify({'success': False, 'error': 'Contact ID and note required'}), 400
        
        # Get contact
        contact = Contact.query.get(contact_id)
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        # Update contact notes
        current_notes = contact.notes or ''
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        new_note = f"[{timestamp}] {current_user.first_name or 'Agent'}: {note}"
        
        if current_notes:
            contact.notes = current_notes + '\n\n' + new_note
        else:
            contact.notes = new_note
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Note added successfully',
            'contact': {
                'id': contact.id,
                'name': contact.name,
                'phone': contact.phone,
                'email': contact.email,
                'company': contact.company,
                'notes': contact.notes
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/contact/<int:contact_id>')
@login_required
@ankieter_required
def get_contact(contact_id):
    """Get contact details"""
    try:
        contact = Contact.query.get(contact_id)
        if not contact:
            return jsonify({'success': False, 'error': 'Contact not found'}), 404
        
        return jsonify({
            'success': True,
            'contact': {
                'id': contact.id,
                'name': contact.name,
                'phone': contact.phone,
                'email': contact.email,
                'company': contact.company,
                'notes': contact.notes
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/campaigns', methods=['GET'])
@login_required
@ankieter_required
def get_campaigns_for_ankieter():
    """Get campaigns with contact counts for ankieter"""
    try:
        from app.models.crm_model import Campaign, ImportFile
        
        # Get all active campaigns that have contacts
        campaigns = Campaign.query.join(ImportFile).filter(
            Campaign.is_active == True
        ).distinct().all()
        
        campaigns_data = []
        for campaign in campaigns:
            # Count contacts in this campaign that are available for calling
            total_contacts = Contact.query.filter_by(
                campaign_id=campaign.id,
                is_active=True,
                is_blacklisted=False
            ).count()
            
            # Count new contacts (no calls yet)
            new_contacts = Contact.query.filter(
                Contact.campaign_id == campaign.id,
                Contact.is_active == True,
                Contact.is_blacklisted == False
            ).filter(
                ~Contact.id.in_(db.session.query(Call.contact_id))
            ).count()
            
            # Count callback contacts
            callback_contacts = Contact.query.join(Call).filter(
                Contact.campaign_id == campaign.id,
                Contact.is_active == True,
                Contact.is_blacklisted == False,
                Call.status == 'callback',
                Call.next_call_date <= datetime.now()
            ).count()
            
            # Count potential leads
            potential_contacts = Contact.query.join(Call).filter(
                Contact.campaign_id == campaign.id,
                Contact.is_active == True,
                Contact.is_blacklisted == False,
                Contact.call_attempts < Contact.max_call_attempts
            ).filter(
                Call.status.in_(['no_answer', 'busy', 'wrong_number'])
            ).filter(
                ~Contact.id.in_(
                    db.session.query(Call.contact_id).filter(Call.status.in_(['lead', 'rejection']))
                )
            ).count()
            
            available_contacts = new_contacts + callback_contacts + potential_contacts
            
            # Show all active campaigns, even if no contacts are available
            campaigns_data.append({
                'id': campaign.id,
                'name': campaign.name,
                'description': campaign.description,
                'total_contacts': total_contacts,
                'available_contacts': available_contacts,
                'new_contacts': new_contacts,
                'callback_contacts': callback_contacts,
                'potential_contacts': potential_contacts,
                'script_content': campaign.script_content  # Add script content
            })
        
        return jsonify({
            'success': True,
            'campaigns': campaigns_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/campaign/<int:campaign_id>/script', methods=['GET'])
@login_required
@ankieter_required
def get_campaign_script(campaign_id):
    """Get campaign script for ankieter"""
    try:
        from app.models.crm_model import Campaign
        
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Campaign not found'}), 404
        
        if not campaign.is_active:
            return jsonify({'success': False, 'error': 'Campaign is not active'}), 400
        
        return jsonify({
            'success': True,
            'script_content': campaign.script_content,
            'campaign_name': campaign.name
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@agent_api_bp.route('/daily-work-time', methods=['GET'])
@login_required
@ankieter_required
def get_daily_work_time():
    """Get daily work time from localStorage or calculate from work sessions"""
    try:
        # For now, return 0 - this will be updated when agent actually works
        # In future, this could be stored in database or retrieved from localStorage
        return jsonify({
            'success': True,
            'work_time_seconds': 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
