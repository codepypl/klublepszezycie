from app import db
from app.models.email_model import EmailLog
from app.models.events_model import EventSchedule
from app.models.email_model import EmailTemplate, EmailCampaign
from sqlalchemy import desc, or_, and_, func
from datetime import datetime, timedelta
import json

class LogService:
    """Serwis do zarządzania logami emaili"""
    
    @staticmethod
    def log_email(to_email: str, subject: str, status: str, 
                  template_id: int = None, campaign_id: int = None, 
                  event_id: int = None, context: dict = None, error_message: str = None):
        """
        Loguje email w bazie danych
        
        Args:
            to_email: Adres email odbiorcy
            subject: Temat emaila
            status: Status emaila (sent, failed, bounced, opened, clicked)
            template_id: ID szablonu (opcjonalne)
            campaign_id: ID kampanii (opcjonalne)
            event_id: ID wydarzenia (opcjonalne)
            context: Kontekst emaila (opcjonalne)
            error_message: Komunikat błędu (opcjonalne)
        """
        try:
            # Convert context to JSON string if it's a dict
            context_str = None
            if context:
                if isinstance(context, dict):
                    context_str = json.dumps(context, ensure_ascii=False)
                else:
                    context_str = str(context)
            
            log_entry = EmailLog(
                email=to_email,
                subject=subject,
                status=status,
                template_id=template_id,
                campaign_id=campaign_id,
                event_id=event_id,
                recipient_data=context_str,
                error_message=error_message,
                sent_at=datetime.now() if status == 'sent' else None
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
            return True, "Log zapisany pomyślnie"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Błąd logowania emaila: {str(e)}"
    
    @staticmethod
    def get_logs(filters: dict = None, page: int = 1, per_page: int = 20):
        """
        Pobiera logi z filtrami
        
        Args:
            filters: Słownik z filtrami
            page: Numer strony
            per_page: Liczba elementów na stronę
            
        Returns:
            Tuple: (logs, pagination_info)
        """
        try:
            query = EmailLog.query
            
            if filters:
                # Search filter
                if filters.get('search'):
                    search_term = filters['search']
                    query = query.filter(
                        or_(
                            EmailLog.email.ilike(f'%{search_term}%'),
                            EmailLog.subject.ilike(f'%{search_term}%'),
                            EmailLog.error_message.ilike(f'%{search_term}%')
                        )
                    )
                
                # Status filter
                if filters.get('status') and filters['status'] != 'all':
                    query = query.filter_by(status=filters['status'])
                
                # Event ID filter
                if filters.get('event_id'):
                    query = query.filter_by(event_id=filters['event_id'])
                
                # Campaign ID filter
                if filters.get('campaign_id'):
                    query = query.filter_by(campaign_id=filters['campaign_id'])
                
                # Template ID filter
                if filters.get('template_id'):
                    query = query.filter_by(template_id=filters['template_id'])
                
                # Date filters
                if filters.get('date_from'):
                    try:
                        date_from_obj = datetime.fromisoformat(filters['date_from'])
                        query = query.filter(EmailLog.sent_at >= date_from_obj)
                    except ValueError:
                        pass
                
                if filters.get('date_to'):
                    try:
                        date_to_obj = datetime.fromisoformat(filters['date_to'] + ' 23:59:59')
                        query = query.filter(EmailLog.sent_at <= date_to_obj)
                    except ValueError:
                        pass
                
                # Time filters
                if filters.get('time_from'):
                    try:
                        time_from_obj = datetime.strptime(filters['time_from'], '%H:%M').time()
                        query = query.filter(EmailLog.sent_at.cast(db.Time) >= time_from_obj)
                    except ValueError:
                        pass
                
                if filters.get('time_to'):
                    try:
                        time_to_obj = datetime.strptime(filters['time_to'], '%H:%M').time()
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
            
            return logs, {
                'page': pagination.page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': pagination.per_page
            }
            
        except Exception as e:
            return [], {'error': str(e)}
    
    @staticmethod
    def get_log_details(log_id: int):
        """
        Pobiera szczegóły logu
        
        Args:
            log_id: ID logu
            
        Returns:
            Dict z danymi logu lub None
        """
        try:
            log = EmailLog.query.get(log_id)
            
            if not log:
                return None
            
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
            
            return {
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
            
        except Exception as e:
            return None
    
    @staticmethod
    def get_logs_stats():
        """
        Pobiera statystyki logów
        
        Returns:
            Dict ze statystykami
        """
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
            
            return {
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
            
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def cleanup_old_logs(hours: int = 48):
        """
        Czyści stare logi
        
        Args:
            hours: Liczba godzin po których logi mają być usunięte
            
        Returns:
            Tuple: (success, message, stats)
        """
        try:
            from app.models.system_logs_model import SystemLog
            from app.models.user_logs_model import UserLogs
            import os
            import glob
            
            cutoff_date = datetime.now() - timedelta(hours=hours)
            
            # Clean database logs
            db_stats = {
                'email_logs': 0,
                'system_logs': 0,
                'user_logs': 0
            }
            
            # Clean EmailLog entries
            old_email_logs = EmailLog.query.filter(EmailLog.sent_at < cutoff_date).all()
            for log in old_email_logs:
                db.session.delete(log)
            db_stats['email_logs'] = len(old_email_logs)
            
            # Clean SystemLog entries
            old_system_logs = SystemLog.query.filter(SystemLog.created_at < cutoff_date).all()
            for log in old_system_logs:
                db.session.delete(log)
            db_stats['system_logs'] = len(old_system_logs)
            
            # Clean UserLogs entries
            old_user_logs = UserLogs.query.filter(UserLogs.created_at < cutoff_date).all()
            for log in old_user_logs:
                db.session.delete(log)
            db_stats['user_logs'] = len(old_user_logs)
            
            # Clean log files
            logs_dir = 'app/logs'
            deleted_files = 0
            total_size_freed = 0
            
            if os.path.exists(logs_dir):
                cutoff_timestamp = cutoff_date.timestamp()
                log_patterns = [
                    os.path.join(logs_dir, 'wsgi_*.log'),
                    os.path.join(logs_dir, 'app_console_*.log'),
                    os.path.join(logs_dir, '*.log.*'),
                ]
                
                for pattern in log_patterns:
                    for log_file in glob.glob(pattern):
                        try:
                            file_mtime = os.path.getmtime(log_file)
                            file_size = os.path.getsize(log_file)
                            
                            if file_mtime < cutoff_timestamp:
                                os.remove(log_file)
                                deleted_files += 1
                                total_size_freed += file_size
                        except Exception:
                            continue
            
            # Commit database changes
            db.session.commit()
            
            total_db_cleaned = db_stats['email_logs'] + db_stats['system_logs'] + db_stats['user_logs']
            
            return True, f'Usunięto {deleted_files} plików logów i {total_db_cleaned} wpisów z bazy danych. Zwolniono {total_size_freed / 1024 / 1024:.2f} MB', {
                'deleted_files': deleted_files,
                'size_freed_mb': round(total_size_freed / 1024 / 1024, 2),
                'database_cleaned': db_stats,
                'total_db_cleaned': total_db_cleaned
            }
            
        except Exception as e:
            db.session.rollback()
            return False, f'Błąd podczas czyszczenia logów: {str(e)}', {}
