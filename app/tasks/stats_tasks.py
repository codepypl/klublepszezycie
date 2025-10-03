"""
Statistics cleanup tasks
"""
from celery import Celery
from datetime import datetime, timedelta, date
from app.models import db
from app.models.stats_model import Stats
from app.models.user_logs_model import UserLogs
import logging

# Get Celery instance
from app import create_app
app = create_app()
celery = app.extensions.get('celery')

@celery.task
def cleanup_old_stats():
    """Clean up old statistics - keep only last 90 days of daily stats"""
    try:
        cutoff_date = date.today() - timedelta(days=90)
        
        # Count stats to be deleted
        old_stats_count = Stats.query.filter(
            Stats.date_period < cutoff_date,
            Stats.stat_type.in_([
                'daily_login_time_seconds',
                'daily_work_time_seconds', 
                'daily_break_time_seconds',
                'daily_calls_count',
                'daily_leads_count',
                'daily_callbacks_count'
            ])
        ).count()
        
        if old_stats_count > 0:
            # Delete old daily stats
            deleted_count = Stats.query.filter(
                Stats.date_period < cutoff_date,
                Stats.stat_type.in_([
                    'daily_login_time_seconds',
                    'daily_work_time_seconds',
                    'daily_break_time_seconds', 
                    'daily_calls_count',
                    'daily_leads_count',
                    'daily_callbacks_count'
                ])
            ).delete(synchronize_session=False)
            
            db.session.commit()
            
            logging.info(f"🧹 Cleaned up {deleted_count} old daily statistics (older than {cutoff_date})")
            return f"Cleaned up {deleted_count} old daily statistics"
        else:
            logging.info("🧹 No old daily statistics to clean up")
            return "No old daily statistics to clean up"
            
    except Exception as e:
        db.session.rollback()
        error_msg = f"Error cleaning up old stats: {str(e)}"
        logging.error(error_msg)
        return error_msg

@celery.task  
def cleanup_old_user_logs():
    """Clean up old user logs - keep only last 30 days of login/logout logs"""
    try:
        cutoff_datetime = datetime.now() - timedelta(days=30)
        
        # Count logs to be deleted
        old_logs_count = UserLogs.query.filter(
            UserLogs.created_at < cutoff_datetime,
            UserLogs.action_type.in_(['login', 'logout'])
        ).count()
        
        if old_logs_count > 0:
            # Delete old login/logout logs
            deleted_count = UserLogs.query.filter(
                UserLogs.created_at < cutoff_datetime,
                UserLogs.action_type.in_(['login', 'logout'])
            ).delete(synchronize_session=False)
            
            db.session.commit()
            
            logging.info(f"🧹 Cleaned up {deleted_count} old user login/logout logs (older than {cutoff_datetime})")
            return f"Cleaned up {deleted_count} old user logs"
        else:
            logging.info("🧹 No old user login/logout logs to clean up")
            return "No old user login/logout logs to clean up"
            
    except Exception as e:
        db.session.rollback()
        error_msg = f"Error cleaning up old user logs: {str(e)}"
        logging.error(error_msg)
        return error_msg

@celery.task
def monthly_stats_summary():
    """Generate monthly statistics summary and clean up old daily stats"""
    try:
        # Get current month start
        today = date.today()
        month_start = today.replace(day=1)
        
        # Calculate previous month stats
        if month_start.month == 1:
            prev_month_start = month_start.replace(year=month_start.year - 1, month=12)
        else:
            prev_month_start = month_start.replace(month=month_start.month - 1)
        
        # Get all users who had stats in previous month
        users_with_stats = db.session.query(Stats.related_id).filter(
            Stats.related_type == 'user',
            Stats.date_period >= prev_month_start,
            Stats.date_period < month_start,
            Stats.stat_type == 'daily_login_time_seconds'
        ).distinct().all()
        
        summary_stats = []
        
        for (user_id,) in users_with_stats:
            # Get monthly totals for this user
            monthly_stats = {}
            
            for stat_type in [
                'daily_login_time_seconds',
                'daily_work_time_seconds',
                'daily_break_time_seconds',
                'daily_calls_count', 
                'daily_leads_count',
                'daily_callbacks_count'
            ]:
                total = db.session.query(db.func.sum(Stats.stat_value)).filter(
                    Stats.stat_type == stat_type,
                    Stats.related_id == user_id,
                    Stats.related_type == 'user',
                    Stats.date_period >= prev_month_start,
                    Stats.date_period < month_start
                ).scalar() or 0
                
                monthly_stats[stat_type] = total
            
            # Create monthly summary stat
            Stats.set_value(
                f'monthly_{prev_month_start.strftime("%Y_%m")}_login_time_seconds',
                int(monthly_stats['daily_login_time_seconds']),
                related_id=user_id,
                related_type='user',
                date_period=prev_month_start
            )
            
            summary_stats.append({
                'user_id': user_id,
                'month': prev_month_start.strftime('%Y-%m'),
                'login_time': monthly_stats['daily_login_time_seconds'],
                'work_time': monthly_stats['daily_work_time_seconds'],
                'break_time': monthly_stats['daily_break_time_seconds'],
                'total_calls': monthly_stats['daily_calls_count'],
                'leads': monthly_stats['daily_leads_count'],
                'callbacks': monthly_stats['daily_callbacks_count']
            })
        
        logging.info(f"📊 Generated monthly summary for {len(summary_stats)} users for {prev_month_start.strftime('%Y-%m')}")
        return f"Generated monthly summary for {len(summary_stats)} users"
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"Error generating monthly stats summary: {str(e)}"
        logging.error(error_msg)
        return error_msg
