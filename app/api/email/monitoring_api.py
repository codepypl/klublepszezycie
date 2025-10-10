"""
Email monitoring API - complete monitoring and stats
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import EmailQueue, EmailLog, EmailCampaign
from app.services.email_v2 import EmailManager
from app.services.email_v2.queue.processor import EmailQueueProcessor
from app.services.email_v2.monitoring import EmailStats
import logging
from datetime import datetime, timedelta

email_monitoring_bp = Blueprint('email_monitoring_api', __name__)
logger = logging.getLogger(__name__)

@email_monitoring_bp.route('/email/queue-stats', methods=['GET'])
@login_required
def get_queue_stats():
    """Zwraca statystyki kolejki emaili"""
    try:
        total = EmailQueue.query.count()
        pending = EmailQueue.query.filter_by(status='pending').count()
        failed = EmailQueue.query.filter_by(status='failed').count()
        processing = EmailQueue.query.filter_by(status='processing').count()
        sent = EmailQueue.query.filter_by(status='sent').count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'pending': pending,
                'failed': failed,
                'processing': processing,
                'sent': sent
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statystyk kolejki: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_monitoring_bp.route('/email/monitor/stats', methods=['GET'])
@login_required
def get_email_monitor_stats():
    """Pobiera szczegółowe statystyki wysyłania e-maili"""
    try:
        hours = int(request.args.get('hours', 24))
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
        
        stats = {
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
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statystyk monitora: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_monitoring_bp.route('/email/monitor/failed', methods=['GET'])
@login_required
def get_failed_emails():
    """Pobiera listę nieudanych e-maili"""
    try:
        limit = int(request.args.get('limit', 50))
        
        failed_emails = EmailQueue.query.filter_by(status='failed').limit(limit).all()
        
        emails_data = []
        for email in failed_emails:
            emails_data.append({
                'id': email.id,
                'to_email': email.recipient_email,
                'to_name': email.recipient_name,
                'subject': email.subject,
                'error_message': email.error_message,
                'retry_count': email.retry_count,
                'max_retries': email.max_retries,
                'created_at': email.created_at.isoformat() if email.created_at else None,
                'scheduled_at': email.scheduled_at.isoformat() if email.scheduled_at else None
            })
        
        return jsonify({
            'success': True,
            'failed_emails': emails_data,
            'count': len(emails_data)
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania nieudanych e-maili: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_monitoring_bp.route('/email/monitor/retry-failed', methods=['POST'])
@login_required
def retry_failed_emails():
    """Ponawia wysyłanie nieudanych e-maili"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 10)
        
        processor = EmailQueueProcessor()
        stats = processor.retry_failed_emails(limit)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd ponawiania nieudanych e-maili: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_monitoring_bp.route('/email/monitor/campaign/<int:campaign_id>/stats', methods=['GET'])
@login_required
def get_campaign_stats(campaign_id):
    """Pobiera statystyki kampanii"""
    try:
        from app.models import EmailCampaign
        
        campaign = EmailCampaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie znaleziona'}), 404
        
        # Pobierz statystyki z kolejki
        total_emails = EmailQueue.query.filter_by(campaign_id=campaign_id).count()
        sent_emails = EmailQueue.query.filter_by(campaign_id=campaign_id, status='sent').count()
        failed_emails = EmailQueue.query.filter_by(campaign_id=campaign_id, status='failed').count()
        pending_emails = EmailQueue.query.filter_by(campaign_id=campaign_id, status='pending').count()
        processing_emails = EmailQueue.query.filter_by(campaign_id=campaign_id, status='processing').count()
        
        # Oblicz procent sukcesu
        processed_emails = sent_emails + failed_emails
        success_rate = (sent_emails / processed_emails * 100) if processed_emails > 0 else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'campaign_id': campaign_id,
                'campaign_name': campaign.name,
                'campaign_status': campaign.status,
                'emails': {
                    'total': total_emails,
                    'sent': sent_emails,
                    'failed': failed_emails,
                    'pending': pending_emails,
                    'processing': processing_emails
                },
                'performance': {
                    'success_rate': round(success_rate, 2),
                    'processed': processed_emails
                }
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statystyk kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_monitoring_bp.route('/email/monitor/cleanup', methods=['POST'])
@login_required
def cleanup_old_emails():
    """Czyści stare e-maile z kolejki"""
    try:
        data = request.get_json() or {}
        days = data.get('days', 30)
        
        processor = EmailQueueProcessor()
        stats = processor.cleanup_old_emails(days)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd czyszczenia starych e-maili: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_monitoring_bp.route('/email/monitor/health', methods=['GET'])
@login_required
def get_system_health():
    """Pobiera stan systemu e-maili"""
    try:
        # Sprawdź kolejkę
        queue_pending = EmailQueue.query.filter_by(status='pending').count()
        queue_failed = EmailQueue.query.filter_by(status='failed').count()
        queue_processing = EmailQueue.query.filter_by(status='processing').count()
        
        # Sprawdź ostatnie błędy
        recent_errors = EmailQueue.query.filter_by(status='failed').order_by(EmailQueue.created_at.desc()).limit(5).all()
        
        # Określ status systemu
        if queue_failed > 100:
            status = 'critical'
            message = f'Duża liczba błędów w kolejce: {queue_failed}'
        elif queue_pending > 1000:
            status = 'warning'
            message = f'Duża liczba oczekujących emaili: {queue_pending}'
        elif queue_processing > 50:
            status = 'warning'
            message = f'Wiele emaili w przetwarzaniu: {queue_processing}'
        else:
            status = 'healthy'
            message = 'System działa prawidłowo'
        
        health = {
            'status': status,
            'message': message,
            'queue': {
                'pending': queue_pending,
                'processing': queue_processing,
                'failed': queue_failed
            },
            'recent_errors': [
                {
                    'id': e.id,
                    'recipient': e.recipient_email,
                    'error': e.error_message,
                    'created_at': e.created_at.isoformat() if e.created_at else None
                } for e in recent_errors
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'health': health
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania stanu systemu: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_monitoring_bp.route('/email/monitor/daily-stats', methods=['GET'])
@login_required
def get_daily_stats():
    """Pobiera statystyki dzienne"""
    try:
        from datetime import datetime
        
        date_str = request.args.get('date')
        date = datetime.fromisoformat(date_str) if date_str else None
        
        email_stats = EmailStats()
        stats = email_stats.get_daily_stats(date)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statystyk dziennych: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_monitoring_bp.route('/email/monitor/hourly-stats', methods=['GET'])
@login_required
def get_hourly_stats():
    """Pobiera statystyki godzinowe"""
    try:
        from datetime import datetime
        
        date_str = request.args.get('date')
        date = datetime.fromisoformat(date_str) if date_str else None
        
        email_stats = EmailStats()
        stats = email_stats.get_hourly_stats(date)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statystyk godzinowych: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_monitoring_bp.route('/email/monitor/template-stats', methods=['GET'])
@login_required
def get_template_stats():
    """Pobiera statystyki szablonów"""
    try:
        template_name = request.args.get('template_name')
        days = int(request.args.get('days', 7))
        
        email_stats = EmailStats()
        stats = email_stats.get_template_stats(template_name, days)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statystyk szablonów: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_monitoring_bp.route('/email/monitor/event-stats', methods=['GET'])
@login_required
def get_event_stats():
    """Pobiera statystyki wydarzeń"""
    try:
        event_id = request.args.get('event_id', type=int)
        days = int(request.args.get('days', 30))
        
        email_stats = EmailStats()
        stats = email_stats.get_event_stats(event_id, days)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statystyk wydarzeń: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500