"""
Narzędzie do monitorowania wysyłania e-maili i statystyk Mailgun
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
from app import db
from app.models import EmailQueue, EmailLog, EmailCampaign
from app.services.mailgun_api_service import MailgunAPIService

class EmailMonitor:
    """Monitor wysyłania e-maili"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mailgun_service = MailgunAPIService()
    
    def get_sending_stats(self, hours: int = 24) -> Dict:
        """Pobiera statystyki wysyłania z ostatnich N godzin"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Statystyki z bazy danych
            total_sent = EmailLog.query.filter(
                EmailLog.sent_at >= cutoff_time,
                EmailLog.status == 'sent'
            ).count()
            
            total_failed = EmailLog.query.filter(
                EmailLog.sent_at >= cutoff_time,
                EmailLog.status == 'failed'
            ).count()
            
            # Statystyki kolejki
            queue_pending = EmailQueue.query.filter_by(status='pending').count()
            queue_processing = EmailQueue.query.filter_by(status='processing').count()
            queue_sent = EmailQueue.query.filter_by(status='sent').count()
            queue_failed = EmailQueue.query.filter_by(status='failed').count()
            
            # Statystyki kampanii
            active_campaigns = EmailCampaign.query.filter(
                EmailCampaign.status.in_(['sending', 'scheduled'])
            ).count()
            
            return {
                'period_hours': hours,
                'emails_sent': total_sent,
                'emails_failed': total_failed,
                'success_rate': round((total_sent / (total_sent + total_failed)) * 100, 2) if (total_sent + total_failed) > 0 else 0,
                'queue_stats': {
                    'pending': queue_pending,
                    'processing': queue_processing,
                    'sent': queue_sent,
                    'failed': queue_failed,
                    'total': queue_pending + queue_processing + queue_sent + queue_failed
                },
                'active_campaigns': active_campaigns,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania statystyk: {e}")
            return {'error': str(e)}
    
    def get_rate_limit_status(self) -> Dict:
        """Sprawdza status limitów wysyłania"""
        try:
            # Test połączenia z Mailgun
            api_available, api_message = self.mailgun_service.test_connection()
            
            return {
                'api_available': api_available,
                'api_message': api_message,
                'rate_limits': {
                    'max_per_minute': self.mailgun_service.max_emails_per_minute,
                    'max_per_hour': getattr(self.mailgun_service, 'max_emails_per_hour', 10000),
                    'delay_between_emails': self.mailgun_service.rate_limit_delay
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Błąd sprawdzania limitów: {e}")
            return {'error': str(e)}
    
    def get_failed_emails(self, limit: int = 50) -> List[Dict]:
        """Pobiera listę nieudanych e-maili"""
        try:
            failed_emails = EmailQueue.query.filter_by(status='failed').limit(limit).all()
            
            result = []
            for email in failed_emails:
                result.append({
                    'id': email.id,
                    'recipient_email': email.recipient_email,
                    'subject': email.subject,
                    'error_message': email.error_message,
                    'created_at': email.created_at.isoformat() if email.created_at else None,
                    'campaign_id': email.campaign_id,
                    'event_id': email.event_id
                })
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania nieudanych e-maili: {e}")
            return []
    
    def retry_failed_emails(self, limit: int = 10) -> Dict:
        """Ponawia wysyłanie nieudanych e-maili"""
        try:
            from app.services.email_service import EmailService
            email_service = EmailService()
            
            stats = email_service.retry_failed_emails(limit)
            
            return {
                'success': True,
                'retried': stats['retried'],
                'success_count': stats['success'],
                'failed_count': stats['failed'],
                'message': f"Ponowiono {stats['retried']} e-maili: {stats['success']} sukces, {stats['failed']} błąd"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Błąd ponawiania e-maili: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_campaign_stats(self, campaign_id: int) -> Dict:
        """Pobiera statystyki kampanii"""
        try:
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return {'error': 'Kampania nie została znaleziona'}
            
            # Statystyki z kolejki
            total_queued = EmailQueue.query.filter_by(campaign_id=campaign_id).count()
            sent_emails = EmailQueue.query.filter_by(campaign_id=campaign_id, status='sent').count()
            failed_emails = EmailQueue.query.filter_by(campaign_id=campaign_id, status='failed').count()
            pending_emails = EmailQueue.query.filter_by(campaign_id=campaign_id, status='pending').count()
            
            return {
                'campaign_id': campaign_id,
                'campaign_name': campaign.name,
                'status': campaign.status,
                'total_queued': total_queued,
                'sent': sent_emails,
                'failed': failed_emails,
                'pending': pending_emails,
                'success_rate': round((sent_emails / total_queued) * 100, 2) if total_queued > 0 else 0,
                'created_at': campaign.created_at.isoformat() if campaign.created_at else None,
                'scheduled_at': campaign.scheduled_at.isoformat() if campaign.scheduled_at else None
            }
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania statystyk kampanii: {e}")
            return {'error': str(e)}
    
    def cleanup_old_emails(self, days: int = 30) -> Dict:
        """Czyści stare e-maile z kolejki"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Usuń stare wysłane e-maile
            old_sent = EmailQueue.query.filter(
                EmailQueue.status == 'sent',
                EmailQueue.sent_at < cutoff_date
            ).delete()
            
            # Usuń stare nieudane e-maile (starsze niż 7 dni)
            old_failed_cutoff = datetime.now() - timedelta(days=7)
            old_failed = EmailQueue.query.filter(
                EmailQueue.status == 'failed',
                EmailQueue.created_at < old_failed_cutoff
            ).delete()
            
            db.session.commit()
            
            return {
                'success': True,
                'deleted_sent': old_sent,
                'deleted_failed': old_failed,
                'message': f"Usunięto {old_sent} wysłanych i {old_failed} nieudanych e-maili"
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"❌ Błąd czyszczenia starych e-maili: {e}")
            return {'success': False, 'error': str(e)}




