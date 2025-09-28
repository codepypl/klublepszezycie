from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.email_model import EmailLog
from app.models.events_model import EventSchedule
from app.models.email_model import EmailTemplate, EmailCampaign
from sqlalchemy import desc, or_, and_, func
from datetime import datetime, timedelta

log_bp = Blueprint('log_api', __name__)

@log_bp.route('/logs', methods=['GET'])
@login_required
def get_logs():
    """Pobiera logi emaili z rozszerzonymi filtrami"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Filters
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        time_from = request.args.get('time_from', '')
        time_to = request.args.get('time_to', '')
        event_id = request.args.get('event_id', '')
        campaign_id = request.args.get('campaign_id', '')
        template_id = request.args.get('template_id', '')
        
        query = EmailLog.query
        
        # Apply filters
        if search:
            query = query.filter(
                or_(
                    EmailLog.email.ilike(f'%{search}%'),
                    EmailLog.subject.ilike(f'%{search}%'),
                    EmailLog.error_message.ilike(f'%{search}%')
                )
            )
        
        if status and status != 'all':
            query = query.filter_by(status=status)
        
        if event_id:
            query = query.filter_by(event_id=event_id)
        
        if campaign_id:
            query = query.filter_by(campaign_id=campaign_id)
        
        if template_id:
            query = query.filter_by(template_id=template_id)
        
        if date_from:
            try:
                date_from_obj = datetime.fromisoformat(date_from)
                query = query.filter(EmailLog.sent_at >= date_from_obj)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to_obj = datetime.fromisoformat(date_to + ' 23:59:59')
                query = query.filter(EmailLog.sent_at <= date_to_obj)
            except ValueError:
                pass
        
        # Time filters
        if time_from:
            try:
                time_from_obj = datetime.strptime(time_from, '%H:%M').time()
                query = query.filter(EmailLog.sent_at.cast(db.Time) >= time_from_obj)
            except ValueError:
                pass
        
        if time_to:
            try:
                time_to_obj = datetime.strptime(time_to, '%H:%M').time()
                query = query.filter(EmailLog.sent_at.cast(db.Time) <= time_to_obj)
            except ValueError:
                pass
        
        # Pagination
        pagination = query.order_by(desc(EmailLog.sent_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs = []
        for log in pagination.items:
            # Get event info
            event_info = None
            if log.event_id:
                event = EventSchedule.query.get(log.event_id)
                if event:
                    event_info = {
                        'id': event.id,
                        'title': event.title,
                        'event_date': event.event_date.isoformat() if event.event_date else None
                    }
            
            logs.append({
                'id': log.id,
                'email': log.email,
                'subject': log.subject,
                'status': log.status,
                'sent_at': log.sent_at.isoformat() if log.sent_at else None,
                'error_message': log.error_message,
                'template_id': log.template_id,
                'template_name': log.template.name if log.template else f'Usunięty szablon (ID: {log.template_id})',
                'campaign_id': log.campaign_id,
                'campaign_name': log.campaign.name if log.campaign else f'Usunięta kampania (ID: {log.campaign_id})' if log.campaign_id else None,
                'event_id': log.event_id,
                'event_info': event_info,
                'recipient_data': log.recipient_data
            })
        
        return jsonify({
            'success': True,
            'logs': logs,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': pagination.per_page
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@log_bp.route('/logs/<int:log_id>', methods=['GET'])
@login_required
def get_log_details(log_id):
    """Pobiera szczegóły logu e-maila"""
    try:
        log = EmailLog.query.get(log_id)
        
        if not log:
            return jsonify({'success': False, 'error': 'Log nie znaleziony'}), 404
        
        # Get related data
        event_info = None
        if log.event_id:
            event = EventSchedule.query.get(log.event_id)
            if event:
                event_info = {
                    'id': event.id,
                    'title': event.title,
                    'event_date': event.event_date.isoformat() if event.event_date else None,
                    'location': event.location,
                    'meeting_link': event.meeting_link
                }
        
        template_info = None
        if log.template_id:
            template = EmailTemplate.query.get(log.template_id)
            if template:
                template_info = {
                    'id': template.id,
                    'name': template.name,
                    'subject': template.subject,
                    'template_type': template.template_type
                }
        
        campaign_info = None
        if log.campaign_id:
            campaign = EmailCampaign.query.get(log.campaign_id)
            if campaign:
                campaign_info = {
                    'id': campaign.id,
                    'name': campaign.name,
                    'status': campaign.status
                }
        
        return jsonify({
            'success': True,
            'log': {
                'id': log.id,
                'email': log.email,
                'subject': log.subject,
                'status': log.status,
                'sent_at': log.sent_at.isoformat() if log.sent_at else None,
                'error_message': log.error_message,
                'recipient_data': log.recipient_data,
                'event_info': event_info,
                'template_info': template_info,
                'campaign_info': campaign_info
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@log_bp.route('/logs/stats', methods=['GET'])
@login_required
def get_logs_stats():
    """Pobiera statystyki logów emaili z bazy danych"""
    try:
        # Get database stats
        total_emails = EmailLog.query.count()
        
        # Status breakdown
        status_stats = db.session.query(
            EmailLog.status,
            func.count(EmailLog.id).label('count')
        ).group_by(EmailLog.status).all()
        
        status_breakdown = {status: count for status, count in status_stats}
        
        # Today's stats
        today = datetime.now().date()
        today_emails = EmailLog.query.filter(
            func.date(EmailLog.sent_at) == today
        ).count()
        
        # This week's stats
        week_ago = datetime.now() - timedelta(days=7)
        week_emails = EmailLog.query.filter(
            EmailLog.sent_at >= week_ago
        ).count()
        
        # This month's stats
        month_ago = datetime.now() - timedelta(days=30)
        month_emails = EmailLog.query.filter(
            EmailLog.sent_at >= month_ago
        ).count()
        
        # Recent activity (last 24 hours)
        day_ago = datetime.now() - timedelta(hours=24)
        recent_emails = EmailLog.query.filter(
            EmailLog.sent_at >= day_ago
        ).count()
        
        # Template stats
        template_stats = db.session.query(
            EmailLog.template_id,
            func.count(EmailLog.id).label('count')
        ).filter(EmailLog.template_id.isnot(None)).group_by(EmailLog.template_id).order_by(
            func.count(EmailLog.id).desc()
        ).limit(10).all()
        
        template_breakdown = []
        for template_id, count in template_stats:
            template = EmailTemplate.query.get(template_id)
            template_breakdown.append({
                'template_id': template_id,
                'count': count,
                'template_name': template.name if template else f'Usunięty szablon (ID: {template_id})'
            })
        
        # Event stats
        event_stats = db.session.query(
            EmailLog.event_id,
            func.count(EmailLog.id).label('count')
        ).filter(EmailLog.event_id.isnot(None)).group_by(EmailLog.event_id).order_by(
            func.count(EmailLog.id).desc()
        ).limit(10).all()
        
        event_breakdown = []
        for event_id, count in event_stats:
            event = EventSchedule.query.get(event_id)
            event_breakdown.append({
                'event_id': event_id,
                'count': count,
                'event_name': event.title if event else f'Usunięte wydarzenie (ID: {event_id})'
            })
        
        return jsonify({
            'success': True,
            'stats': {
                'total_emails': total_emails,
                'today_emails': today_emails,
                'week_emails': week_emails,
                'month_emails': month_emails,
                'recent_emails': recent_emails,
                'status_breakdown': status_breakdown,
                'template_breakdown': template_breakdown,
                'event_breakdown': event_breakdown,
                'last_updated': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@log_bp.route('/logs/cleanup', methods=['POST'])
@login_required
def cleanup_logs():
    """Czyści stare logi (starsze niż 48 godzin)"""
    try:
        import os
        import glob
        from datetime import datetime, timedelta
        from app.models.system_logs_model import SystemLog
        from app.models.user_logs_model import UserLogs
        
        logs_dir = 'app/logs'
        
        if not os.path.exists(logs_dir):
            return jsonify({
                'success': False, 
                'error': f'Katalog {logs_dir} nie istnieje'
            }), 404
        
        # Calculate cutoff date (48 hours ago)
        cutoff_date = datetime.now() - timedelta(hours=48)
        cutoff_timestamp = cutoff_date.timestamp()
        
        # Find all log files
        log_patterns = [
            os.path.join(logs_dir, 'wsgi_*.log'),
            os.path.join(logs_dir, 'app_console_*.log'),
            os.path.join(logs_dir, '*.log.*'),  # Rotated files
        ]
        
        deleted_count = 0
        total_size_freed = 0
        deleted_files = []
        
        for pattern in log_patterns:
            for log_file in glob.glob(pattern):
                try:
                    # Get file modification time
                    file_mtime = os.path.getmtime(log_file)
                    file_size = os.path.getsize(log_file)
                    
                    # Check if file is older than cutoff
                    if file_mtime < cutoff_timestamp:
                        os.remove(log_file)
                        deleted_count += 1
                        total_size_freed += file_size
                        deleted_files.append({
                            'file': log_file,
                            'size': file_size,
                            'modified': datetime.fromtimestamp(file_mtime).isoformat()
                        })
                        
                except Exception as e:
                    return jsonify({
                        'success': False, 
                        'error': f'Błąd podczas usuwania {log_file}: {str(e)}'
                    }), 500
        
        # Clean up database logs
        db_stats = {
            'email_logs': 0,
            'system_logs': 0,
            'user_logs': 0
        }
        
        try:
            # Clean EmailLog entries older than 48 hours
            old_email_logs = EmailLog.query.filter(EmailLog.sent_at < cutoff_date).all()
            for log in old_email_logs:
                db.session.delete(log)
            db_stats['email_logs'] = len(old_email_logs)
            
            # Clean SystemLog entries older than 48 hours
            old_system_logs = SystemLog.query.filter(SystemLog.created_at < cutoff_date).all()
            for log in old_system_logs:
                db.session.delete(log)
            db_stats['system_logs'] = len(old_system_logs)
            
            # Clean UserLogs entries older than 48 hours
            old_user_logs = UserLogs.query.filter(UserLogs.created_at < cutoff_date).all()
            for log in old_user_logs:
                db.session.delete(log)
            db_stats['user_logs'] = len(old_user_logs)
            
            # Commit database changes
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False, 
                'error': f'Błąd podczas czyszczenia bazy danych: {str(e)}'
            }), 500
        
        total_db_cleaned = db_stats['email_logs'] + db_stats['system_logs'] + db_stats['user_logs']
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} plików logów i {total_db_cleaned} wpisów z bazy danych. Zwolniono {total_size_freed / 1024 / 1024:.2f} MB',
            'stats': {
                'deleted_files': deleted_count,
                'size_freed_mb': round(total_size_freed / 1024 / 1024, 2),
                'cutoff_date': cutoff_date.isoformat(),
                'deleted_files_list': deleted_files,
                'database_cleaned': db_stats,
                'total_db_cleaned': total_db_cleaned
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
