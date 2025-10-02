"""
Statystyki i monitorowanie e-maili
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app import db
from app.models import EmailQueue, EmailLog, EmailTemplate, EventSchedule
from app.utils.timezone_utils import get_local_now

class EmailStats:
    """
    System statystyk i monitorowania e-maili
    
    Funkcje:
    1. Statystyki wysyłania
    2. Monitorowanie wydajności
    3. Raporty błędów
    4. Analiza kampanii
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_daily_stats(self, date: datetime = None) -> Dict[str, Any]:
        """
        Pobiera statystyki dzienne
        
        Args:
            date: Data (domyślnie dzisiaj)
            
        Returns:
            Dict[str, Any]: Statystyki dzienne
        """
        try:
            if date is None:
                date = get_local_now()
            
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            # Statystyki z kolejki
            queue_stats = {
                'pending': EmailQueue.query.filter(
                    EmailQueue.status == 'pending',
                    EmailQueue.created_at >= day_start,
                    EmailQueue.created_at < day_end
                ).count(),
                'processing': EmailQueue.query.filter(
                    EmailQueue.status == 'processing',
                    EmailQueue.created_at >= day_start,
                    EmailQueue.created_at < day_end
                ).count(),
                'sent': EmailQueue.query.filter(
                    EmailQueue.status == 'sent',
                    EmailQueue.sent_at >= day_start,
                    EmailQueue.sent_at < day_end
                ).count(),
                'failed': EmailQueue.query.filter(
                    EmailQueue.status == 'failed',
                    EmailQueue.created_at >= day_start,
                    EmailQueue.created_at < day_end
                ).count()
            }
            
            # Statystyki z logów
            log_stats = {
                'sent': EmailLog.query.filter(
                    EmailLog.sent_at >= day_start,
                    EmailLog.sent_at < day_end,
                    EmailLog.status == 'sent'
                ).count(),
                'failed': EmailLog.query.filter(
                    EmailLog.sent_at >= day_start,
                    EmailLog.sent_at < day_end,
                    EmailLog.status == 'failed'
                ).count()
            }
            
            return {
                'date': day_start.isoformat(),
                'queue_stats': queue_stats,
                'log_stats': log_stats,
                'total_emails': queue_stats['sent'] + queue_stats['failed'],
                'success_rate': self._calculate_success_rate(queue_stats['sent'], queue_stats['failed'])
            }
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania statystyk dziennych: {e}")
            return {'error': str(e)}
    
    def get_hourly_stats(self, date: datetime = None) -> List[Dict[str, Any]]:
        """
        Pobiera statystyki godzinowe
        
        Args:
            date: Data (domyślnie dzisiaj)
            
        Returns:
            List[Dict[str, Any]]: Lista statystyk godzinowych
        """
        try:
            if date is None:
                date = get_local_now()
            
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            hourly_stats = []
            
            for hour in range(24):
                hour_start = day_start + timedelta(hours=hour)
                hour_end = hour_start + timedelta(hours=1)
                
                sent_count = EmailQueue.query.filter(
                    EmailQueue.status == 'sent',
                    EmailQueue.sent_at >= hour_start,
                    EmailQueue.sent_at < hour_end
                ).count()
                
                failed_count = EmailQueue.query.filter(
                    EmailQueue.status == 'failed',
                    EmailQueue.created_at >= hour_start,
                    EmailQueue.created_at < hour_end
                ).count()
                
                hourly_stats.append({
                    'hour': hour,
                    'sent': sent_count,
                    'failed': failed_count,
                    'total': sent_count + failed_count
                })
            
            return hourly_stats
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania statystyk godzinowych: {e}")
            return []
    
    def get_template_stats(self, template_name: str = None, days: int = 7) -> Dict[str, Any]:
        """
        Pobiera statystyki szablonów
        
        Args:
            template_name: Nazwa szablonu (opcjonalna)
            days: Liczba dni wstecz
            
        Returns:
            Dict[str, Any]: Statystyki szablonów
        """
        try:
            since = get_local_now() - timedelta(days=days)
            
            query = EmailQueue.query.filter(EmailQueue.created_at >= since)
            
            if template_name:
                template = EmailTemplate.query.filter_by(name=template_name).first()
                if template:
                    query = query.filter(EmailQueue.template_id == template.id)
                else:
                    return {'error': f'Szablon {template_name} nie znaleziony'}
            
            # Statystyki
            total = query.count()
            sent = query.filter(EmailQueue.status == 'sent').count()
            failed = query.filter(EmailQueue.status == 'failed').count()
            pending = query.filter(EmailQueue.status == 'pending').count()
            
            return {
                'template_name': template_name,
                'period_days': days,
                'total': total,
                'sent': sent,
                'failed': failed,
                'pending': pending,
                'success_rate': self._calculate_success_rate(sent, failed)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania statystyk szablonów: {e}")
            return {'error': str(e)}
    
    def get_event_stats(self, event_id: int = None, days: int = 30) -> Dict[str, Any]:
        """
        Pobiera statystyki wydarzeń
        
        Args:
            event_id: ID wydarzenia (opcjonalne)
            days: Liczba dni wstecz
            
        Returns:
            Dict[str, Any]: Statystyki wydarzeń
        """
        try:
            since = get_local_now() - timedelta(days=days)
            
            query = EmailQueue.query.filter(EmailQueue.created_at >= since)
            
            if event_id:
                query = query.filter(EmailQueue.event_id == event_id)
            
            # Statystyki
            total = query.count()
            sent = query.filter(EmailQueue.status == 'sent').count()
            failed = query.filter(EmailQueue.status == 'failed').count()
            
            # Lista wydarzeń
            events = EventSchedule.query.filter(
                EventSchedule.created_at >= since
            ).all()
            
            event_stats = []
            for event in events:
                event_emails = EmailQueue.query.filter(
                    EmailQueue.event_id == event.id,
                    EmailQueue.created_at >= since
                ).count()
                
                event_stats.append({
                    'id': event.id,
                    'title': event.title,
                    'date': event.event_date.isoformat(),
                    'emails_sent': event_emails
                })
            
            return {
                'event_id': event_id,
                'period_days': days,
                'total_emails': total,
                'sent': sent,
                'failed': failed,
                'success_rate': self._calculate_success_rate(sent, failed),
                'events': event_stats
            }
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania statystyk wydarzeń: {e}")
            return {'error': str(e)}
    
    def get_failed_emails(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Pobiera listę nieudanych e-maili
        
        Args:
            limit: Maksymalna liczba e-maili
            
        Returns:
            List[Dict[str, Any]]: Lista nieudanych e-maili
        """
        try:
            failed_emails = EmailQueue.query.filter(
                EmailQueue.status == 'failed'
            ).order_by(EmailQueue.updated_at.desc()).limit(limit).all()
            
            result = []
            for email in failed_emails:
                result.append({
                    'id': email.id,
                    'recipient_email': email.recipient_email,
                    'subject': email.subject,
                    'error_message': email.error_message,
                    'retry_count': email.retry_count,
                    'created_at': email.created_at.isoformat() if email.created_at else None,
                    'updated_at': email.updated_at.isoformat() if email.updated_at else None,
                    'template_id': email.template_id,
                    'event_id': email.event_id
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania nieudanych e-maili: {e}")
            return []
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Pobiera stan systemu e-maili
        
        Returns:
            Dict[str, Any]: Stan systemu
        """
        try:
            now = get_local_now()
            
            # Statystyki kolejki
            queue_stats = {
                'pending': EmailQueue.query.filter_by(status='pending').count(),
                'processing': EmailQueue.query.filter_by(status='processing').count(),
                'sent': EmailQueue.query.filter_by(status='sent').count(),
                'failed': EmailQueue.query.filter_by(status='failed').count()
            }
            
            # Statystyki dzisiejsze
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_sent = EmailQueue.query.filter(
                EmailQueue.status == 'sent',
                EmailQueue.sent_at >= today_start
            ).count()
            
            # Statystyki godzinowe (ostatnie 24h)
            last_24h = now - timedelta(hours=24)
            last_24h_sent = EmailQueue.query.filter(
                EmailQueue.status == 'sent',
                EmailQueue.sent_at >= last_24h
            ).count()
            
            # Średnia wysyłania na godzinę
            avg_per_hour = last_24h_sent / 24 if last_24h_sent > 0 else 0
            
            return {
                'timestamp': now.isoformat(),
                'queue_stats': queue_stats,
                'today_sent': today_sent,
                'last_24h_sent': last_24h_sent,
                'avg_per_hour': round(avg_per_hour, 2),
                'health_status': self._calculate_health_status(queue_stats, today_sent)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania stanu systemu: {e}")
            return {'error': str(e)}
    
    def _calculate_success_rate(self, sent: int, failed: int) -> float:
        """Oblicza wskaźnik sukcesu"""
        total = sent + failed
        if total == 0:
            return 0.0
        return round((sent / total) * 100, 2)
    
    def _calculate_health_status(self, queue_stats: Dict[str, int], today_sent: int) -> str:
        """Oblicza status zdrowia systemu"""
        try:
            # Sprawdź czy są problemy z kolejką
            if queue_stats['failed'] > 100:
                return 'critical'
            
            if queue_stats['pending'] > 1000:
                return 'warning'
            
            if queue_stats['failed'] > 50:
                return 'warning'
            
            # Sprawdź dzienny limit
            if today_sent > 900:  # 90% limitu
                return 'warning'
            
            return 'healthy'
            
        except Exception:
            return 'unknown'




