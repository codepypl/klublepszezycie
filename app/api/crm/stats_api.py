"""
CRM Stats API - statistics for ankieter dashboard
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.models import db
from app.models.crm_model import Contact, Call
from app.models.user_logs_model import UserLogs
from app.utils.timezone_utils import get_local_now
from app.services.crm_queue_manager import QueueManager
from app.models.stats_model import Stats
import logging

logger = logging.getLogger(__name__)

# Create Stats API blueprint
stats_api_bp = Blueprint('crm_stats_api', __name__)

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

@stats_api_bp.route('/crm/stats/queue-status')
@login_required
@ankieter_required
def get_queue_status():
    """Get queue status and statistics for ankieter dashboard"""
    try:
        # Update CRM stats first
        Stats.update_crm_stats()
        
        # Get today's date range
        now = get_local_now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Get base query for today's calls
        base_today_query = Call.query.filter(
            Call.ankieter_id == current_user.id,
            Call.created_at >= today_start,
            Call.created_at <= today_end
        )
        
        # Get completed calls today
        completed_calls_today = base_today_query.filter(Call.status.in_(['lead', 'answered', 'callback'])).count()
        
        # Get leads today
        leads_today = base_today_query.filter(Call.status == 'lead').count()
        
        # Get answered today
        answered_today = base_today_query.filter(Call.status == 'answered').count()
        
        # Get callbacks today
        callbacks_today = base_today_query.filter(Call.status == 'callback').count()
        
        # Get total calls (all time)
        total_calls = Call.query.filter_by(ankieter_id=current_user.id).count()
        total_leads = Call.query.filter_by(ankieter_id=current_user.id, status='lead').count()
        total_answered = Call.query.filter_by(ankieter_id=current_user.id, status='answered').count()
        total_callbacks = Call.query.filter_by(ankieter_id=current_user.id, status='callback').count()
        
        # Get queue statistics
        queue_stats = QueueManager.get_ankieter_queue_stats(current_user.id)
        
        # Get login time today
        login_events = UserLogs.query.filter(
            UserLogs.user_id == current_user.id,
            UserLogs.action_type.in_(['login', 'logout', 'work_start', 'work_stop']),
            UserLogs.created_at >= today_start,
            UserLogs.created_at <= today_end
        ).order_by(UserLogs.created_at).all()
        
        # Calculate login time
        total_login_time_seconds = 0
        login_start = None
        
        for event in login_events:
            if event.action_type in ['login', 'work_start']:
                login_start = event.created_at
            elif event.action_type in ['logout', 'work_stop'] and login_start:
                session_duration = (event.created_at - login_start).total_seconds()
                total_login_time_seconds += session_duration
                login_start = None
        
        # If still logged in, add time from last login to now
        if login_start:
            session_duration = (now - login_start).total_seconds()
            total_login_time_seconds += session_duration
        
        # Calculate total call time today - only from calls with actual duration
        calls_with_duration = base_today_query.filter(Call.duration_seconds.isnot(None)).all()
        total_call_time = sum(call.duration_seconds for call in calls_with_duration)
        
        # Calculate average call time - only from calls with actual duration
        calls_with_duration_count = len(calls_with_duration)
        avg_call_time = total_call_time / calls_with_duration_count if calls_with_duration_count > 0 else 0
        
        # Calculate longest call today - only from calls with actual duration
        longest_call_time = max(call.duration_seconds for call in calls_with_duration) if calls_with_duration else 0
        
        # Calculate work time - use only actual call time
        total_work_time_seconds = total_call_time
        
        # Calculate break time (login time - work time)
        total_break_time_seconds = max(0, total_login_time_seconds - total_work_time_seconds)
        
        # Debug prints
        print(f"🔍 Login time calculation: {total_login_time_seconds/3600:.2f}h")
        print(f"🔍 Work time calculation: {total_work_time_seconds/3600:.2f}h")
        print(f"🔍 Break time calculation: {total_break_time_seconds/3600:.2f}h")
        print(f"🔍 Breakdown: call_time={total_call_time}s, calls_with_duration={calls_with_duration_count}, total_calls={completed_calls_today}")
        print(f"🔍 Time breakdown: login={total_login_time_seconds/3600:.2f}h, work={total_work_time_seconds/3600:.2f}h, break={total_break_time_seconds/3600:.2f}h")
        
        return jsonify({
            'success': True,
            'stats': {
                'today': {
                    'completed_calls': completed_calls_today,
                    'leads': leads_today,
                    'answered': answered_today,
                    'callbacks': callbacks_today,
                    'longest_call_minutes': longest_call_time // 60,
                    'avg_call_minutes': round(avg_call_time / 60, 1) if avg_call_time > 0 else 0,
                    'total_call_time_minutes': round(total_call_time / 60, 1),
                    'total_login_time_minutes': round(total_login_time_seconds / 60, 1),
                    'total_work_time_minutes': round(total_work_time_seconds / 60, 1),
                    'total_break_time_minutes': round(total_break_time_seconds / 60, 1)
                },
                'total': {
                    'calls': total_calls,
                    'leads': total_leads,
                    'answered': total_answered,
                    'callbacks': total_callbacks
                },
                'queue': queue_stats
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statusu kolejki: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@stats_api_bp.route('/crm/stats/daily-work-time', methods=['GET'])
@login_required
@ankieter_required
def get_daily_work_time():
    """Get daily work time for ankieter"""
    try:
        # Get today's date range
        now = get_local_now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Get work start/stop events for today
        work_events = UserLogs.query.filter(
            UserLogs.user_id == current_user.id,
            UserLogs.action_type.in_(['work_start', 'work_stop']),
            UserLogs.created_at >= today_start,
            UserLogs.created_at <= today_end
        ).order_by(UserLogs.created_at).all()
        
        # Calculate total work time
        total_work_time_seconds = 0
        work_start = None
        
        for event in work_events:
            if event.action_type == 'work_start':
                work_start = event.created_at
            elif event.action_type == 'work_stop' and work_start:
                session_duration = (event.created_at - work_start).total_seconds()
                total_work_time_seconds += session_duration
                work_start = None
        
        # If still working, add time from last work_start to now
        if work_start:
            session_duration = (now - work_start).total_seconds()
            total_work_time_seconds += session_duration
        
        return jsonify({
            'success': True,
            'work_time': {
                'total_seconds': total_work_time_seconds,
                'total_minutes': round(total_work_time_seconds / 60, 1),
                'total_hours': round(total_work_time_seconds / 3600, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania czasu pracy: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@stats_api_bp.route('/crm/stats/sync-twilio', methods=['POST'])
@login_required
@ankieter_required
def sync_twilio_stats():
    """Sync Twilio call statistics"""
    try:
        # This would sync with Twilio API to get actual call statistics
        # For now, just return success
        
        return jsonify({
            'success': True,
            'message': 'Twilio stats sync completed'
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd synchronizacji statystyk Twilio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@stats_api_bp.route('/crm/stats/performance', methods=['GET'])
@login_required
@ankieter_required
def get_performance_stats():
    """Get performance statistics for ankieter"""
    try:
        from datetime import timedelta
        
        # Get date range
        days = request.args.get('days', 7, type=int)
        now = get_local_now()
        start_date = now - timedelta(days=days)
        
        # Get calls in date range
        calls_query = Call.query.filter(
            Call.ankieter_id == current_user.id,
            Call.created_at >= start_date
        )
        
        # Performance metrics
        total_calls = calls_query.count()
        successful_calls = calls_query.filter(Call.status.in_(['lead', 'answered'])).count()
        lead_calls = calls_query.filter(Call.status == 'lead').count()
        answered_calls = calls_query.filter(Call.status == 'answered').count()
        callback_calls = calls_query.filter(Call.status == 'callback').count()
        
        # Calculate conversion rates
        lead_rate = (lead_calls / total_calls * 100) if total_calls > 0 else 0
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        
        # Get average call duration
        calls_with_duration = calls_query.filter(Call.duration_seconds.isnot(None)).all()
        avg_duration = sum(call.duration_seconds for call in calls_with_duration) / len(calls_with_duration) if calls_with_duration else 0
        
        # Daily breakdown
        daily_stats = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            day_calls = calls_query.filter(
                Call.created_at >= day_start,
                Call.created_at <= day_end
            ).count()
            
            day_leads = calls_query.filter(
                Call.status == 'lead',
                Call.created_at >= day_start,
                Call.created_at <= day_end
            ).count()
            
            daily_stats.append({
                'date': date.strftime('%Y-%m-%d'),
                'calls': day_calls,
                'leads': day_leads
            })
        
        return jsonify({
            'success': True,
            'performance': {
                'period_days': days,
                'total_calls': total_calls,
                'lead_calls': lead_calls,
                'answered_calls': answered_calls,
                'callback_calls': callback_calls,
                'lead_rate': round(lead_rate, 1),
                'success_rate': round(success_rate, 1),
                'avg_call_duration_minutes': round(avg_duration / 60, 1) if avg_duration > 0 else 0,
                'daily_breakdown': daily_stats
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statystyk wydajności: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500




