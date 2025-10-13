"""
Email queue API - complete queue management
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import EmailQueue, db
from app.services.email_v2 import EmailManager
from app.services.email_v2.queue.processor import EmailQueueProcessor
from app.utils.timezone_utils import get_local_now
import logging

email_queue_bp = Blueprint('email_queue_api', __name__)
logger = logging.getLogger(__name__)

@email_queue_bp.route('/email/queue', methods=['GET'])
@login_required
def get_queue():
    """Pobiera listę kolejki emaili z paginacją i filtrowaniem"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_status = request.args.get('filter', 'all')
        
        # Buduj zapytanie
        query = EmailQueue.query
        
        if filter_status != 'all':
            query = query.filter_by(status=filter_status)
        
        # Sortuj po dacie utworzenia
        query = query.order_by(EmailQueue.created_at.desc())
        
        # Paginacja
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        emails = []
        for email in pagination.items:
            emails.append({
                'id': email.id,
                'to_email': email.recipient_email,
                'to_name': email.recipient_name,
                'subject': email.subject,
                'status': email.status,
                'retry_count': email.retry_count,
                'max_retries': email.max_retries,
                'scheduled_at': email.scheduled_at.isoformat() if email.scheduled_at else None,
                'sent_at': email.sent_at.isoformat() if email.sent_at else None,
                'error_message': email.error_message,
                'created_at': email.created_at.isoformat() if email.created_at else None,
                'campaign_id': email.campaign_id,
                'template_id': email.template_id
            })
        
        return jsonify({
            'success': True,
            'emails': emails,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'next_num': pagination.next_num,
                'prev_num': pagination.prev_num
            }
        })
    except Exception as e:
        logger.error(f"❌ Błąd pobierania kolejki: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@email_queue_bp.route('/email/process-queue', methods=['POST'])
@login_required
def process_queue():
    """Przetwarza kolejkę emaili"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 50)
        
        # Przetwórz kolejkę
        processor = EmailQueueProcessor()
        stats = processor.process_queue(limit)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd przetwarzania kolejki: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_queue_bp.route('/email/queue-progress', methods=['GET'])
@login_required
def get_queue_progress():
    """Pobiera postęp przetwarzania kolejki"""
    try:
        total = EmailQueue.query.count()
        pending = EmailQueue.query.filter_by(status='pending').count()
        processing = EmailQueue.query.filter_by(status='processing').count()
        sent = EmailQueue.query.filter_by(status='sent').count()
        failed = EmailQueue.query.filter_by(status='failed').count()
        
        # Oblicz procent postępu
        if total == 0:
            percent = 100
        else:
            percent = ((sent + failed) / total) * 100
        
        return jsonify({
            'success': True,
            'progress': {
                'total': total,
                'pending': pending,
                'processing': processing,
                'sent': sent,
                'failed': failed,
                'percent': round(percent, 1)
            }
        })
    except Exception as e:
        logger.error(f"❌ Błąd pobierania postępu kolejki: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@email_queue_bp.route('/email/retry-failed', methods=['POST'])
@login_required
def retry_failed_emails():
    """Ponawia nieudane emaile"""
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
        logger.error(f"❌ Błąd ponawiania emaili: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_queue_bp.route('/email/queue/clear-all', methods=['POST'])
@login_required
def clear_all_emails():
    """Czyści całą kolejkę emaili (zachowuje wysłane jako historię)"""
    try:
        # Policz emaile przed usunięciem
        total_count = EmailQueue.query.count()
        pending_count = EmailQueue.query.filter_by(status='pending').count()
        failed_count = EmailQueue.query.filter_by(status='failed').count()
        processing_count = EmailQueue.query.filter_by(status='processing').count()
        sent_count = EmailQueue.query.filter_by(status='sent').count()
        
        # Usuń wszystkie emaile oprócz wysłanych
        deleted_count = EmailQueue.query.filter(
            EmailQueue.status.in_(['pending', 'failed', 'processing'])
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} emaili z kolejki. Zachowano {sent_count} wysłanych emaili jako historię.',
            'deleted_count': deleted_count,
            'kept_count': sent_count,
            'stats': {
                'total_before': total_count,
                'pending_before': pending_count,
                'failed_before': failed_count,
                'processing_before': processing_count,
                'sent_before': sent_count
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd czyszczenia całej kolejki: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_queue_bp.route('/email/retry/<int:email_id>', methods=['POST'])
@login_required
def retry_single_email(email_id):
    """Ponawia pojedynczy email"""
    try:
        email = EmailQueue.query.get(email_id)
        if not email:
            return jsonify({'success': False, 'error': 'Email nie istnieje'}), 404
        
        email_manager = EmailManager()
        success, message = email_manager.send_immediate_email(
            email.recipient_email,
            email.subject,
            email.html_content,
            email.text_content,
            template_id=email.template_id,  # Przekaż template_id z oryginalnego emaila
            event_id=email.event_id,       # Przekaż event_id z oryginalnego emaila
            campaign_id=email.campaign_id  # Przekaż campaign_id z oryginalnego emaila
        )
        
        if success:
            email.status = 'sent'
            email.sent_at = get_local_now()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Email ponowiony pomyślnie'})
        else:
            email.status = 'failed'
            email.error_message = message
            email.retry_count += 1
            db.session.commit()
            return jsonify({'success': False, 'error': message}), 500
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd ponawiania pojedynczego emaila: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_queue_bp.route('/email/queue/<int:email_id>', methods=['DELETE'])
@login_required
def delete_email_from_queue(email_id):
    """Usuwa email z kolejki"""
    try:
        email = EmailQueue.query.get(email_id)
        if not email:
            return jsonify({'success': False, 'error': 'Email nie istnieje'}), 404
        
        # Nie można usuwać już wysłanych e-maili
        if email.status == 'sent':
            return jsonify({'success': False, 'error': 'Nie można usuwać wysłanych e-maili. Kolejka służy jako historia wysłanych wiadomości.'}), 400
        
        db.session.delete(email)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Email usunięty z kolejki'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania emaila z kolejki: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_queue_bp.route('/bulk-delete/email-queue', methods=['POST'])
@login_required
def bulk_delete_emails():
    """Bulk delete emails from queue"""
    try:
        data = request.get_json()
        email_ids = data.get('ids', [])
        
        if not email_ids:
            return jsonify({'success': False, 'error': 'Brak emaili do usunięcia'}), 400
        
        # Delete emails from queue
        deleted_count = 0
        for email_id in email_ids:
            email = EmailQueue.query.get(email_id)
            if email:
                # Nie można usuwać już wysłanych e-maili
                if email.status == 'sent':
                    continue  # Skip sent emails
                
                db.session.delete(email)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Usunięto {deleted_count} emaili z kolejki',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd masowego usuwania emaili: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_queue_bp.route('/email/queue/clear', methods=['POST'])
@login_required
def clear_queue():
    """Czyści kolejkę emaili (zachowuje wysłane jako historię)"""
    try:
        # Policz emaile przed usunięciem
        total_before = EmailQueue.query.count()
        pending_before = EmailQueue.query.filter_by(status='pending').count()
        failed_before = EmailQueue.query.filter_by(status='failed').count()
        processing_before = EmailQueue.query.filter_by(status='processing').count()
        sent_before = EmailQueue.query.filter_by(status='sent').count()
        
        if total_before == 0:
            return jsonify({
                'success': True, 
                'message': 'Kolejka emaili jest już pusta!',
                'stats': {
                    'total_before': total_before,
                    'deleted': 0,
                    'kept': 0
                }
            })
        
        # Usuń wszystkie emaile oprócz wysłanych
        deleted_count = EmailQueue.query.filter(
            EmailQueue.status.in_(['pending', 'failed', 'processing'])
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} emaili z kolejki, zachowano {sent_before} wysłanych jako historię',
            'stats': {
                'total_before': total_before,
                'deleted': deleted_count,
                'kept': sent_before,
                'pending': pending_before,
                'failed': failed_before,
                'processing': processing_before
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd czyszczenia kolejki: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_queue_bp.route('/email/queue/stats', methods=['GET'])
@login_required
def get_queue_stats():
    """Pobiera statystyki kolejki emaili"""
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

@email_queue_bp.route('/email/queue-stats', methods=['GET'])
@login_required
def get_detailed_queue_stats():
    """Zwraca szczegółowe statystyki kolejki emaili"""
    try:
        from app.models import EmailLog
        
        # Podstawowe statystyki kolejki
        total = EmailQueue.query.count()
        pending = EmailQueue.query.filter_by(status='pending').count()
        failed = EmailQueue.query.filter_by(status='failed').count()
        processing = EmailQueue.query.filter_by(status='processing').count()
        sent = EmailQueue.query.filter_by(status='sent').count()
        
        # Statystyki z logów (jeśli istnieją)
        total_sent_logs = EmailLog.query.count() if hasattr(EmailLog, 'query') else 0
        total_failed_logs = EmailLog.query.filter_by(status='failed').count() if hasattr(EmailLog, 'query') else 0
        
        # Oblicz procent sukcesu
        total_processed = sent + failed
        success_rate = (sent / total_processed * 100) if total_processed > 0 else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'queue': {
                    'total': total,
                    'pending': pending,
                    'failed': failed,
                    'processing': processing,
                    'sent': sent
                },
                'logs': {
                    'total_sent': total_sent_logs,
                    'total_failed': total_failed_logs
                },
                'performance': {
                    'success_rate': round(success_rate, 2),
                    'total_processed': total_processed
                }
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania szczegółowych statystyk kolejki: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500