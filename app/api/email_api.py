"""
Email API routes
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import db, EmailTemplate, UserGroup, EmailCampaign, EmailQueue, UserGroupMember
from app.utils.timezone_utils import get_local_now
from sqlalchemy import desc
from datetime import datetime
import json

email_bp = Blueprint('email_api', __name__)

@email_bp.route('/email/retry-failed', methods=['POST'])
@login_required
def email_retry_failed():
    """Ponawia nieudane emaile"""
    try:
        from app.services.mailgun_service import EnhancedNotificationProcessor
        email_processor = EnhancedNotificationProcessor()
        stats = email_processor.retry_failed_emails()
        
        return jsonify({
            'success': True, 
            'message': f'Ponowiono {stats["retried"]} emaili. Sukces: {stats["success"]}, Błędy: {stats["failed"]}',
            'stats': stats
        })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/retry/<int:email_id>', methods=['POST'])
@login_required
def email_retry_single(email_id):
    """Ponawia pojedynczy email"""
    try:
        from app.services.mailgun_service import EnhancedNotificationProcessor
        
        email = EmailQueue.query.get(email_id)
        if not email:
            return jsonify({'success': False, 'error': 'Email nie istnieje'}), 404
        email_processor = EnhancedNotificationProcessor()
        
        success, message = email_processor.send_immediate_email(
            email.to_email,
            email.subject,
            email.html_content,
            email.text_content
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
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/queue-stats', methods=['GET'])
@login_required
def email_queue_stats():
    """Get email queue statistics"""
    try:
        from app.models import Stats
        
        # Update stats from database before returning
        stats_data = Stats.update_email_stats()
        
        return jsonify({
            'success': True,
            'stats': {
                'total': stats_data['total_emails'],
                'pending': stats_data['pending_emails'],
                'sent': stats_data['sent_emails'],
                'failed': stats_data['failed_emails']
            }
        })
    except Exception as e:
        logging.error(f"Error getting queue stats: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@email_bp.route('/email/queue', methods=['GET'])
@login_required
def email_queue_list():
    """Get email queue list with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        filter_status = request.args.get('filter', 'all')
        
        # Build query
        query = EmailQueue.query
        
        if filter_status != 'all':
            query = query.filter_by(status=filter_status)
        
        # Order by created_at desc
        query = query.order_by(EmailQueue.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        emails = []
        for email in pagination.items:
            emails.append({
                'id': email.id,
                'to_email': email.to_email,
                'to_name': email.to_name,
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
        logging.error(f"Error getting queue list: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@email_bp.route('/email/process-queue', methods=['POST'])
@login_required
def email_process_queue():
    """Process email queue - start sending pending emails"""
    try:
        from app.services.mailgun_service import EnhancedNotificationProcessor
        import asyncio
        
        processor = EnhancedNotificationProcessor()
        
        # Process email queue asynchronously
        success, message = asyncio.run(processor.process_email_queue())
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({'success': False, 'message': message}), 500
            
    except Exception as e:
        logging.error(f"Error processing email queue: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@email_bp.route('/email/queue-progress', methods=['GET'])
@login_required
def email_queue_progress():
    """Get email queue processing progress"""
    try:
        total = EmailQueue.query.count()
        pending = EmailQueue.query.filter_by(status='pending').count()
        processing = EmailQueue.query.filter_by(status='sending').count()
        sent = EmailQueue.query.filter_by(status='sent').count()
        failed = EmailQueue.query.filter_by(status='failed').count()
        
        # Calculate progress percentage
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
        logging.error(f"Error getting queue progress: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@email_bp.route('/email/queue/<int:email_id>', methods=['DELETE'])
@login_required
def email_delete_from_queue(email_id):
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
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/bulk-delete/email-queue', methods=['POST'])
@login_required
def bulk_delete_email_queue():
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
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/queue/clear-all', methods=['POST'])
@login_required
def email_queue_clear_all():
    """Clear all emails from queue (except sent ones)"""
    try:
        # Count emails before deletion
        total_count = EmailQueue.query.count()
        pending_count = EmailQueue.query.filter_by(status='pending').count()
        failed_count = EmailQueue.query.filter_by(status='failed').count()
        processing_count = EmailQueue.query.filter_by(status='processing').count()
        sent_count = EmailQueue.query.filter_by(status='sent').count()
        
        # Delete all emails except sent ones (keep sent emails as history)
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
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/logs/stats', methods=['GET'])
@login_required
def email_logs_stats():
    """Pobiera statystyki logów e-maili"""
    try:
        from app.models import EmailLog
        
        from app.models import Stats
        
        stats = {
            'total': Stats.get_total_email_logs(),
            'sent': Stats.get_sent_emails(),
            'failed': Stats.get_failed_emails(),
            'bounced': Stats.get_bounced_emails()
        }
        
        return jsonify({'success': True, 'stats': stats})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/logs', methods=['GET'])
@login_required
def email_logs():
    """Pobiera logi e-maili"""
    try:
        from app.models import EmailLog, EmailTemplate, EmailCampaign
        from sqlalchemy import desc, or_
        from datetime import datetime
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Filters
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
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
        
        # Pagination
        pagination = query.order_by(desc(EmailLog.sent_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs = []
        for log in pagination.items:
            logs.append({
                'id': log.id,
                'email': log.email,
                'subject': log.subject,
                'status': log.status,
                'sent_at': log.sent_at.isoformat() if log.sent_at else None,
                'error_message': log.error_message,
                'template_name': log.template.name if log.template else None,
                'campaign_name': log.campaign.name if log.campaign else None,
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

@email_bp.route('/email/logs/<int:log_id>', methods=['GET'])
@login_required
def email_log_details(log_id):
    """Pobiera szczegóły logu e-maila"""
    try:
        from app.models import EmailLog
        
        log = EmailLog.query.get(log_id)
        if not log:
            return jsonify({'success': False, 'error': 'Log nie istnieje'}), 404
        
        return jsonify({
            'success': True,
            'log': {
                'id': log.id,
                'email': log.email,
                'subject': log.subject,
                'status': log.status,
                'sent_at': log.sent_at.isoformat() if log.sent_at else None,
                'error_message': log.error_message,
                'template_name': log.template.name if log.template else None,
                'campaign_name': log.campaign.name if log.campaign else None,
                'recipient_data': log.recipient_data
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/logs/clear-old', methods=['POST'])
@login_required
def email_logs_clear_old():
    """Czyści stare logi e-maili (starsze niż 30 dni)"""
    try:
        from app.models import EmailLog
        from datetime import datetime, timedelta
        
        # Delete logs older than 30 days
        cutoff_date = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now() - timedelta(days=30)
        deleted_count = EmailLog.query.filter(EmailLog.sent_at < cutoff_date).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} starych logów'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/templates', methods=['GET'])
@login_required
def email_templates():
    """Pobiera listę szablonów emaili"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = EmailTemplate.query.order_by(EmailTemplate.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Lista domyślnych szablonów (nie można ich usuwać)
        default_templates = [
            'welcome', 'event_registration', 'event_reminder_24h', 
            'event_reminder_1h', 'event_reminder_5min', 'admin_notification', 
            'admin_message', 'password_reset'
        ]
        
        template_list = []
        for template in pagination.items:
            template_list.append({
                'id': template.id,
                'name': template.name,
                'subject': template.subject,
                'template_type': template.template_type,
                'is_active': template.is_active,
                'is_default': template.is_default,
                'variables': template.variables,
                'created_at': template.created_at.isoformat()
            })
        
        return jsonify({
            'success': True, 
            'templates': template_list,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': pagination.per_page
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/templates', methods=['POST'])
@login_required
def email_create_template():
    """Tworzy nowy szablon emaila"""
    try:
        data = request.get_json()
        
        template = EmailTemplate(
            name=data['name'],
            subject=data['subject'],
            template_type=data['template_type'],
            html_content=data['html_content'],
            text_content=data.get('text_content', ''),
            variables=data.get('variables', ''),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(template)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Szablon utworzony pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/templates/<int:template_id>', methods=['GET'])
@login_required
def email_get_template(template_id):
    """Pobiera pojedynczy szablon emaila"""
    try:
        template = EmailTemplate.query.get(template_id)
        if not template:
            return jsonify({'success': False, 'error': 'Szablon nie istnieje'}), 404
        
        return jsonify({
            'success': True,
            'template': {
                'id': template.id,
                'name': template.name,
                'subject': template.subject,
                'template_type': template.template_type,
                'html_content': template.html_content,
                'text_content': template.text_content,
                'variables': template.variables,
                'is_active': template.is_active,
                'is_default': template.is_default
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/templates/<int:template_id>', methods=['PUT'])
@login_required
def email_update_template(template_id):
    """Aktualizuje szablon emaila"""
    try:
        template = EmailTemplate.query.get(template_id)
        if not template:
            return jsonify({'success': False, 'error': 'Szablon nie istnieje'}), 404
        data = request.get_json()
        
        template.name = data['name']
        template.subject = data['subject']
        template.template_type = data.get('template_type') or template.template_type or 'custom'
        template.html_content = data['html_content']
        template.text_content = data.get('text_content', '')
        template.variables = data.get('variables', '')
        template.is_active = data.get('is_active', True)
        template.is_default = data.get('is_default', False)
        template.updated_at = get_local_now()
        
        # Handle default template management
        if template.is_default:
            from app.services.template_manager import TemplateManager
            manager = TemplateManager()
            success, message = manager.set_template_as_default(template.id)
            if not success:
                return jsonify({'success': False, 'error': message}), 500
        else:
            from app.services.template_manager import TemplateManager
            manager = TemplateManager()
            success, message = manager.remove_template_from_defaults(template.id)
            if not success:
                return jsonify({'success': False, 'error': message}), 500
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Szablon zaktualizowany pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/templates/<int:template_id>', methods=['DELETE'])
@login_required
def email_delete_template(template_id):
    """Usuwa szablon emaila"""
    try:
        template = EmailTemplate.query.get(template_id)
        if not template:
            return jsonify({'success': False, 'error': 'Szablon nie istnieje'}), 404
        
        # Lista domyślnych szablonów (nie można ich usuwać)
        default_templates = [
            'welcome', 'event_registration', 'event_reminder_24h', 
            'event_reminder_1h', 'event_reminder_5min', 'admin_notification', 
            'admin_message', 'password_reset'
        ]
        
        if template.name in default_templates:
            return jsonify({'success': False, 'error': 'Nie można usunąć szablonu domyślnego'}), 400
        
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Szablon usunięty pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/campaigns/templates', methods=['GET'])
@login_required
def email_campaign_templates():
    """Pobiera szablony dostępne dla kampanii"""
    try:
        templates = EmailTemplate.query.filter_by(is_active=True).all()
        
        templates_data = []
        for template in templates:
            variables = {}
            if template.variables:
                try:
                    variables = json.loads(template.variables)
                except json.JSONDecodeError:
                    variables = {}
            
            templates_data.append({
                'id': template.id,
                'name': template.name,
                'subject': template.subject,
                'template_type': template.template_type,
                'html_content': template.html_content,
                'text_content': template.text_content,
                'variables': variables,
                'created_at': template.created_at.isoformat() if template.created_at else None
            })
        
        return jsonify({'success': True, 'templates': templates_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/templates/reset', methods=['POST'])
@login_required
def email_reset_templates():
    """Resetuje szablony do stanu domyślnego"""
    try:
        from app.services.template_manager import TemplateManager
        
        manager = TemplateManager()
        
        # First sync default templates
        success, message = manager.sync_templates_from_defaults()
        if not success:
            return jsonify({'success': False, 'error': message}), 500
        
        # Then reset templates from defaults
        success, message = manager.reset_templates_to_defaults()
        if not success:
            return jsonify({'success': False, 'error': message}), 500
        
        return jsonify({'success': True, 'message': message})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/templates/initialize-defaults', methods=['POST'])
@login_required
def email_initialize_default_templates():
    """Inicjalizuje domyślne szablony w bazie danych"""
    try:
        from app.services.template_manager import TemplateManager
        
        manager = TemplateManager()
        success, message = manager.initialize_default_templates()
        
        if not success:
            return jsonify({'success': False, 'error': message}), 500
        
        return jsonify({'success': True, 'message': message})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/templates/load-fixtures', methods=['POST'])
@login_required
def email_load_fixtures():
    """Ładuje szablony z fixtures (jak Django loaddata)"""
    try:
        from app.services.fixture_loader import load_email_templates_fixtures
        
        success, message = load_email_templates_fixtures()
        
        if not success:
            return jsonify({'success': False, 'error': message}), 500
        
        return jsonify({'success': True, 'message': message})
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/templates/save-as-defaults', methods=['POST'])
@login_required
def email_save_templates_as_defaults():
    """Zapisuje obecne szablony jako domyślne wzory"""
    try:
        from app.services.template_manager import TemplateManager
        
        manager = TemplateManager()
        success, message = manager.save_current_templates_as_defaults()
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/templates/sync-defaults', methods=['POST'])
@login_required
def email_sync_default_templates():
    """Synchronizuje domyślne szablony"""
    try:
        from app.services.template_manager import TemplateManager
        
        manager = TemplateManager()
        success, message = manager.sync_templates_from_defaults()
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/campaigns', methods=['GET'])
@login_required
def email_campaigns():
    """Pobiera listę kampanii emailowych"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = EmailCampaign.query.order_by(EmailCampaign.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        campaign_list = []
        for campaign in pagination.items:
            # Update total_recipients if it's 0 and campaign has groups
            if campaign.total_recipients == 0 and campaign.recipient_groups:
                try:
                    recipient_groups = json.loads(campaign.recipient_groups)
                    total_recipients = 0
                    for group_id in recipient_groups:
                        group_members = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).count()
                        total_recipients += group_members
                    campaign.total_recipients = total_recipients
                    db.session.commit()
                except json.JSONDecodeError:
                    pass
            
            campaign_list.append({
                'id': campaign.id,
                'name': campaign.name,
                'subject': campaign.subject,
                'status': campaign.status,
                'total_recipients': campaign.total_recipients,
                'sent_count': campaign.sent_count,
                'created_at': campaign.created_at.isoformat()
            })
        
        return jsonify({
            'success': True, 
            'campaigns': campaign_list,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': pagination.per_page
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/campaigns', methods=['POST'])
@login_required
def email_create_campaign():
    """Tworzy nową kampanię emailową"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or data.get('name', '').strip() == '':
            return jsonify({'success': False, 'error': 'Nazwa kampanii jest wymagana'}), 400
        
        if not data.get('subject') or data.get('subject', '').strip() == '':
            return jsonify({'success': False, 'error': 'Temat kampanii jest wymagany'}), 400
        
        if not data.get('recipient_groups') or len(data.get('recipient_groups', [])) == 0:
            return jsonify({'success': False, 'error': 'Musisz wybrać co najmniej jedną grupę odbiorców'}), 400
        
        # Handle scheduling - POPRAWIONA LOGIKA
        send_type = data.get('send_type', 'immediate')
        scheduled_at = None
        status = 'draft'  # Zawsze zaczynamy od draft
        
        # Sprawdź czy admin chce wysłać natychmiast czy zaplanować
        if send_type == 'scheduled':
            if not data.get('scheduled_at'):
                return jsonify({'success': False, 'error': 'Proszę wybrać datę i czas wysyłki dla zaplanowanej kampanii'}), 400
            
            from datetime import datetime
            from app.utils.timezone_utils import get_local_timezone
            
            # Parse date from frontend (może być bez timezone)
            date_str = data['scheduled_at']
            if 'T' in date_str and '+' not in date_str and 'Z' not in date_str:
                # Format: "2025-09-28T15:30" (bez timezone) - dodaj lokalną strefę czasową
                scheduled_at = datetime.fromisoformat(date_str)
                scheduled_at = scheduled_at.replace(tzinfo=get_local_timezone())
            else:
                # Format z timezone: "2025-09-28T15:30Z" lub "2025-09-28T15:30+02:00"
                scheduled_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Sprawdź czy data jest w przyszłości
            now = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
            # Upewnij się, że oba datetimes mają strefy czasowe
            if now.tzinfo is None:
                from app.utils.timezone_utils import get_local_timezone
                now = now.replace(tzinfo=get_local_timezone())
            if scheduled_at.tzinfo is None:
                from app.utils.timezone_utils import get_local_timezone
                scheduled_at = scheduled_at.replace(tzinfo=get_local_timezone())
            
            if scheduled_at <= now:
                return jsonify({'success': False, 'error': 'Data wysyłki musi być w przyszłości'}), 400
            
            # Kampania zostaje jako draft - będzie zaplanowana gdy admin kliknie "Wyślij"
            # scheduled_at jest zapisane, ale status pozostaje draft
        
        # Pobierz treść z szablonu jeśli wybrano szablon
        html_content = data.get('html_content', '')
        text_content = data.get('text_content', '')
        
        if data.get('template_id'):
            template = EmailTemplate.query.get(data['template_id'])
            if template:
                html_content = template.html_content or ''
                text_content = template.text_content or ''
                # Jeśli nie podano subject, użyj z szablonu
                if not data.get('subject') and template.subject:
                    data['subject'] = template.subject
        
        campaign = EmailCampaign(
            name=data['name'],
            subject=data['subject'],
            html_content=html_content,
            text_content=text_content,
            template_id=data.get('template_id'),
            content_variables=json.dumps(data.get('content_variables', {})),
            recipient_groups=json.dumps(data['recipient_groups']),
            send_type=send_type,
            scheduled_at=scheduled_at,
            status=status
        )
        
        db.session.add(campaign)
        db.session.flush()  # Flush to get campaign ID
        
        # Calculate total recipients
        total_recipients = 0
        for group_id in data['recipient_groups']:
            group_members = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).count()
            total_recipients += group_members
        
        campaign.total_recipients = total_recipients
        db.session.commit()
        
        # Kampanie są zawsze zapisywane jako draft lub scheduled
        # Wysyłka następuje dopiero po kliknięciu przycisku "Wyślij"
        if send_type == 'immediate':
            return jsonify({'success': True, 'message': 'Kampania utworzona pomyślnie. Możesz ją wysłać używając przycisku "Wyślij".'})
        else:
            return jsonify({'success': True, 'message': 'Kampania zaplanowana pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/campaigns/<int:campaign_id>', methods=['GET'])
@login_required
def email_get_campaign(campaign_id):
    """Pobiera szczegóły kampanii emailowej"""
    try:
        campaign = EmailCampaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie została znaleziona'}), 404
        
        # Parse recipient groups
        recipient_groups = []
        if campaign.recipient_groups:
            try:
                import json
                recipient_groups = json.loads(campaign.recipient_groups)
            except json.JSONDecodeError:
                recipient_groups = []
        
        # Parse content variables
        content_variables = {}
        if campaign.content_variables:
            try:
                content_variables = json.loads(campaign.content_variables)
            except json.JSONDecodeError:
                content_variables = {}
        
        # DEBUG: Sprawdź jak wygląda scheduled_at
        if campaign.scheduled_at:
            print(f"🔍 DEBUG GET: Campaign {campaign.id} scheduled_at raw: {campaign.scheduled_at}")
            print(f"🔍 DEBUG GET: Campaign {campaign.id} scheduled_at isoformat: {campaign.scheduled_at.isoformat()}")
            print(f"🔍 DEBUG GET: Campaign {campaign.id} scheduled_at timezone: {campaign.scheduled_at.tzinfo}")
        
        return jsonify({
            'success': True,
            'campaign': {
                'id': campaign.id,
                'name': campaign.name,
                'subject': campaign.subject,
                'template_id': campaign.template_id,
                'content_variables': content_variables,
                'recipient_groups': recipient_groups,
                'status': campaign.status,
                'send_type': campaign.send_type,
                'scheduled_at': campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
                'sent_at': campaign.sent_at.isoformat() if campaign.sent_at else None,
                'total_recipients': campaign.total_recipients,
                'sent_count': campaign.sent_count,
                'failed_count': campaign.failed_count,
                'created_at': campaign.created_at.isoformat() if campaign.created_at else None,
                'updated_at': campaign.updated_at.isoformat() if campaign.updated_at else None
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/campaigns/<int:campaign_id>', methods=['PUT'])
@login_required
def email_update_campaign(campaign_id):
    """Aktualizuje kampanię emailową"""
    try:
        campaign = EmailCampaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie została znaleziona'}), 404
        
        data = request.get_json()
        
        # Validate required fields if they are being updated
        if 'name' in data and (not data['name'] or data['name'].strip() == ''):
            return jsonify({'success': False, 'error': 'Nazwa kampanii nie może być pusta'}), 400
        
        if 'subject' in data and (not data['subject'] or data['subject'].strip() == ''):
            return jsonify({'success': False, 'error': 'Temat kampanii nie może być pusty'}), 400
        
        # Update campaign fields
        if 'name' in data:
            campaign.name = data['name']
        if 'subject' in data:
            campaign.subject = data['subject']
        if 'template_id' in data:
            campaign.template_id = data['template_id']
        if 'content_variables' in data:
            import json
            campaign.content_variables = json.dumps(data['content_variables'])
        if 'recipient_groups' in data:
            import json
            campaign.recipient_groups = json.dumps(data['recipient_groups'])
            
            # Recalculate total recipients when groups change
            total_recipients = 0
            for group_id in data['recipient_groups']:
                group_members = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).count()
                total_recipients += group_members
            campaign.total_recipients = total_recipients
        else:
            # Always recalculate total recipients even if groups don't change
            # This ensures the count is up-to-date with current group members
            if campaign.recipient_groups:
                try:
                    recipient_groups = json.loads(campaign.recipient_groups)
                    total_recipients = 0
                    for group_id in recipient_groups:
                        group_members = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).count()
                        total_recipients += group_members
                    campaign.total_recipients = total_recipients
                except json.JSONDecodeError:
                    pass
            
        if 'status' in data:
            campaign.status = data['status']
        if 'scheduled_at' in data and data['scheduled_at']:
            from datetime import datetime
            from app.utils.timezone_utils import get_local_timezone
            
            # Parse date from frontend (może być bez timezone)
            date_str = data['scheduled_at']
            if 'T' in date_str and '+' not in date_str and 'Z' not in date_str:
                # Format: "2025-09-28T15:30" (bez timezone) - dodaj lokalną strefę czasową
                scheduled_at = datetime.fromisoformat(date_str)
                campaign.scheduled_at = scheduled_at.replace(tzinfo=get_local_timezone())
            else:
                # Format z timezone: "2025-09-28T15:30Z" lub "2025-09-28T15:30+02:00"
                campaign.scheduled_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Jeśli kampania jest zaplanowana i ma status 'scheduled', zaktualizuj emailQueue
            if campaign.status == 'scheduled':
                print(f"🔄 Updating email queue for campaign {campaign_id} with new scheduled time")
                print(f"🔍 DEBUG: New scheduled_at: {campaign.scheduled_at}")
                try:
                    from app.models.email_model import EmailQueue
                    from app.services.email_service import EmailService
                    
                    # Usuń stare elementy z kolejki dla tej kampanii
                    EmailQueue.query.filter_by(campaign_id=campaign_id, status='pending').delete()
                    print(f"✅ Removed old queue items for campaign {campaign_id}")
                    
                    # Dodaj nowe elementy z nową datą
                    email_service = EmailService()
                    success, message = email_service._add_campaign_to_queue(campaign)
                    
                    if success:
                        print(f"✅ Added new queue items for campaign {campaign_id} with scheduled time {campaign.scheduled_at}")
                    else:
                        print(f"⚠️ Failed to add new queue items: {message}")
                        
                except Exception as e:
                    print(f"⚠️ Error updating email queue for campaign {campaign_id}: {str(e)}")
                    # Kontynuuj mimo błędu - kampania zostanie przetworzona przez Celery Beat
        elif 'scheduled_at' in data and not data['scheduled_at']:
            # Użytkownik usunął datę planowania - usuń elementy z kolejki
            campaign.scheduled_at = None
            print(f"🔄 Removing scheduled time for campaign {campaign_id}")
            try:
                from app.models.email_model import EmailQueue
                EmailQueue.query.filter_by(campaign_id=campaign_id, status='pending').delete()
                print(f"✅ Removed queue items for campaign {campaign_id} (no longer scheduled)")
            except Exception as e:
                print(f"⚠️ Error removing queue items for campaign {campaign_id}: {str(e)}")
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Kampania zaktualizowana pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/campaigns/<int:campaign_id>', methods=['DELETE'])
@login_required
def email_delete_campaign(campaign_id):
    """Usuwa kampanię emailową"""
    try:
        campaign = EmailCampaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie istnieje'}), 404
        
        # Don't allow deleting sent campaigns
        if campaign.status in ['sending', 'sent', 'completed']:
            return jsonify({'success': False, 'error': f'Nie można usunąć kampanii ze statusem "{campaign.status}"'}), 400
        
        db.session.delete(campaign)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Kampania usunięta pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/campaigns/<int:campaign_id>/send', methods=['POST'])
@login_required
def email_send_campaign(campaign_id):
    """Wysyła kampanię emailową"""
    try:
        from app.services.mailgun_service import EnhancedNotificationProcessor
        import json
        
        # Pobierz kampanię
        campaign = EmailCampaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie została znaleziona'}), 404
        
        # POPRAWIONA LOGIKA WYSYŁANIA
        # Draft NIGDY nie może być wysłany - tylko aktywowany
        if campaign.status == 'draft':
            return jsonify({'success': False, 'error': 'Kampania jest szkicem. Najpierw ją aktywuj.'}), 400
        
        # Kampania może być wysłana tylko jeśli jest ready, scheduled lub active
        if campaign.status not in ['ready', 'scheduled']:
            if campaign.status in ['sent', 'sending', 'completed']:
                return jsonify({'success': False, 'error': 'Kampania została już wysłana'}), 400
            else:
                return jsonify({'success': False, 'error': 'Kampania nie może być wysłana w obecnym statusie'}), 400
        
        # Sprawdź logikę wysyłki
        from datetime import datetime
        from app.utils.timezone_utils import get_local_now, get_local_timezone
        now = get_local_now()
        
        # Jeśli kampania ma scheduled_at - zaplanuj ją
        # Zawsze dodaj kampanię do kolejki (niezależnie od daty)
        campaign.status = 'sending'
        
        # Pobierz grupy odbiorców
        if not campaign.recipient_groups:
            return jsonify({'success': False, 'error': 'Kampania nie ma przypisanych grup odbiorców'}), 400
        
        try:
            group_ids = json.loads(campaign.recipient_groups)
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': 'Nieprawidłowy format grup odbiorców'}), 400
        
        if not group_ids:
            return jsonify({'success': False, 'error': 'Kampania nie ma przypisanych grup odbiorców'}), 400
        
        # Użyj systemu kolejki EmailService zamiast bezpośredniego wysyłania
        from app.services.email_service import EmailService
        email_service = EmailService()
        
        # Dodaj kampanię do kolejki
        success, message = email_service._add_campaign_to_queue(campaign)
        
        if success:
            # Aktualizuj status kampanii
            campaign.status = 'sending'
            campaign.updated_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
            db.session.commit()
            
            # Przygotuj komunikat w zależności od daty
            if campaign.scheduled_at:
                # Upewnij się, że oba datetimes mają strefy czasowe
                if now.tzinfo is None:
                    now = now.replace(tzinfo=get_local_timezone())
                if campaign.scheduled_at.tzinfo is None:
                    campaign.scheduled_at = campaign.scheduled_at.replace(tzinfo=get_local_timezone())
                
                if campaign.scheduled_at > now:
                    message_text = f'Kampania dodana do kolejki dla {campaign.total_recipients} odbiorców. Zostanie wysłana {campaign.scheduled_at.strftime("%Y-%m-%d o %H:%M")}'
                else:
                    message_text = f'Kampania dodana do kolejki dla {campaign.total_recipients} odbiorców i zostanie wysłana natychmiast'
            else:
                message_text = f'Kampania dodana do kolejki dla {campaign.total_recipients} odbiorców i zostanie wysłana natychmiast'
            
            return jsonify({'success': True, 'message': message_text})
        else:
            return jsonify({'success': False, 'error': f'Błąd dodawania kampanii do kolejki: {message}'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/groups', methods=['GET'])
@login_required
def email_groups():
    """Pobiera listę grup użytkowników"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = UserGroup.query.order_by(UserGroup.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Lista domyślnych grup (nie można ich usuwać)
        default_groups = ['club_members']
        
        group_list = []
        for group in pagination.items:
            # Znajdź szablon dla grupy
            template_id = None
            template_name = None
            
            # Dla grup wydarzeń, znajdź szablon z wydarzenia
            if group.group_type == 'event_based' and group.criteria:
                try:
                    import json
                    criteria = json.loads(group.criteria)
                    event_id = criteria.get('event_id')
                    if event_id:
                        # Znajdź szablon dla wydarzenia (domyślnie event_reminder_24h)
                        template = EmailTemplate.query.filter_by(name='event_reminder_24h').first()
                        if template:
                            template_id = template.id
                            template_name = template.name
                except (json.JSONDecodeError, KeyError):
                    pass
            
            # Jeśli nie znaleziono szablonu dla wydarzenia, sprawdź kampanie
            if not template_id:
                campaigns_using_group = EmailCampaign.query.filter(
                    EmailCampaign.recipient_groups.contains(str(group.id))
                ).all()
                
                if campaigns_using_group:
                    # Weź pierwszą kampanię z szablonem
                    for campaign in campaigns_using_group:
                        if campaign.template_id:
                            template_id = campaign.template_id
                            # Pobierz nazwę szablonu
                            template = EmailTemplate.query.get(campaign.template_id)
                            if template:
                                template_name = template.name
                            break
            
            group_list.append({
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'group_type': group.group_type,
                'member_count': group.member_count,
                'is_active': group.is_active,
                'is_default': group.group_type in default_groups,
                'created_at': group.created_at.isoformat(),
                'template_id': template_id,
                'template_name': template_name
            })
        
        return jsonify({
            'success': True, 
            'groups': group_list,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': pagination.per_page
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/groups', methods=['POST'])
@login_required
def email_create_group():
    """Tworzy nową grupę użytkowników"""
    try:
        data = request.get_json()
        
        group = UserGroup(
            name=data['name'],
            description=data.get('description', ''),
            group_type=data['group_type'],
            is_active=data.get('is_active', True)
        )
        
        # Add specific criteria based on group type
        if data['group_type'] == 'event_based' and data.get('event_id'):
            group.criteria = json.dumps({'event_id': data['event_id']})
        elif data['group_type'] == 'manual' and data.get('user_ids'):
            group.criteria = json.dumps({'user_ids': data['user_ids']})
        
        db.session.add(group)
        db.session.commit()
        
        # Add users to manual groups
        if data['group_type'] == 'manual' and data.get('user_ids'):
            from app.models import User
            added_count = 0
            for user_id in data['user_ids']:
                user = User.query.get(user_id)
                if user:
                    member = UserGroupMember(
                        group_id=group.id,
                        user_id=user_id,
                        email=user.email,
                        name=user.first_name
                    )
                    db.session.add(member)
                    added_count += 1
            
            # Update member count
            group.member_count = added_count
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Grupa utworzona pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/groups/<int:group_id>', methods=['GET'])
@login_required
def email_get_group(group_id):
    """Pobiera pojedynczą grupę użytkowników"""
    try:
        group = UserGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupa nie istnieje'}), 404
        
        return jsonify({
            'success': True,
            'group': {
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'group_type': group.group_type,
                'member_count': group.member_count,
                'is_active': group.is_active,
                'criteria': group.criteria
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/groups/<int:group_id>', methods=['PUT'])
@login_required
def email_update_group(group_id):
    """Aktualizuje grupę użytkowników"""
    try:
        group = UserGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupa nie istnieje'}), 404
        
        # Lista domyślnych grup i grup wydarzeń (nie można ich edytować)
        default_groups = ['club_members']
        system_groups = default_groups + ['event_based']
        
        if group.group_type in system_groups:
            return jsonify({'success': False, 'error': 'Nie można edytować grup systemowych'}), 400
        
        data = request.get_json()
        
        group.name = data['name']
        group.description = data.get('description', '')
        group.group_type = data['group_type']
        group.updated_at = get_local_now()
        
        # Update criteria based on group type
        if data['group_type'] == 'event_based' and data.get('event_id'):
            group.criteria = json.dumps({'event_id': data['event_id']})
        elif data['group_type'] == 'manual' and data.get('user_ids'):
            group.criteria = json.dumps({'user_ids': data['user_ids']})
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Grupa zaktualizowana pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/groups/<int:group_id>', methods=['DELETE'])
@login_required
def email_delete_group(group_id):
    """Usuwa grupę użytkowników"""
    try:
        group = UserGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupa nie istnieje'}), 404
        
        # Lista domyślnych grup i grup wydarzeń (nie można ich usuwać)
        default_groups = ['club_members']
        system_groups = default_groups + ['event_based']
        
        if group.group_type in system_groups:
            return jsonify({'success': False, 'error': 'Nie można usunąć grup systemowych'}), 400
        
        db.session.delete(group)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Grupa usunięta pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/groups/sync', methods=['POST'])
@login_required
def email_sync_system_groups():
    """Synchronizuje grupy systemowe"""
    try:
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        success, message = group_manager.sync_system_groups()
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/groups/sync-events', methods=['POST'])
@login_required
def email_sync_event_groups():
    """Synchronizuje grupy wydarzeń"""
    try:
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        success, message = group_manager.sync_event_groups()
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/groups/<int:group_id>/members', methods=['GET'])
@login_required
def email_get_group_members(group_id):
    """Pobiera członków grupy użytkowników"""
    try:
        group = UserGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupa nie istnieje'}), 404
        
        # Lista domyślnych grup (członkowie zarządzani automatycznie)
        default_groups = ['club_members']
        
        if group.group_type in default_groups:
            return jsonify({'success': False, 'error': 'Członkowie grup systemowych są zarządzani automatycznie'}), 400
        
        members = []
        for member in group.members:
            members.append({
                'id': member.id,
                'user_id': member.user_id,
                'user_name': member.first_name,
                'email': member.email,
                'member_type': member.member_type,
                'joined_at': member.joined_at.isoformat() if member.joined_at else None
            })
        
        return jsonify({'success': True, 'members': members})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/groups/<int:group_id>/members', methods=['POST'])
@login_required
def email_add_group_member(group_id):
    """Dodaje członka do grupy użytkowników"""
    try:
        group = UserGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupa nie istnieje'}), 404
            
        data = request.get_json()
        
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Brak user_id'}), 400
        
        # Check if user is already in group
        existing_member = UserGroupMember.query.filter_by(
            group_id=group_id, 
            user_id=user_id
        ).first()
        
        if existing_member:
            return jsonify({'success': False, 'error': 'Użytkownik już jest w grupie'}), 400
        
        # Get user details
        from app.models import User
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Użytkownik nie istnieje'}), 404
        
        # Add member to group
        member = UserGroupMember(
            group_id=group_id,
            user_id=user_id,
            name=user.first_name,
            email=user.email,
            member_type='manual'
        )
        
        db.session.add(member)
        group.member_count = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).count()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Członek dodany pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/groups/members/<int:member_id>', methods=['DELETE'])
@login_required
def email_remove_group_member(member_id):
    """Usuwa członka z grupy użytkowników"""
    try:
        member = UserGroupMember.query.get(member_id)
        if not member:
            return jsonify({'success': False, 'error': 'Członek nie istnieje'}), 404
            
        group_id = member.group_id
        
        db.session.delete(member)
        
        # Update member count
        group = UserGroup.query.get(group_id)
        if group:
            group.member_count = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).count()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Członek usunięty pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/campaigns/<int:campaign_id>/update-stats', methods=['POST'])
@login_required
def update_campaign_stats(campaign_id):
    """Aktualizuje statystyki kampanii"""
    try:
        from app.services.mailgun_service import EnhancedNotificationProcessor
        email_processor = EnhancedNotificationProcessor()
        
        success = email_processor.update_campaign_stats(campaign_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Statystyki kampanii zaktualizowane'})
        else:
            return jsonify({'success': False, 'error': 'Nie udało się zaktualizować statystyk'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/bulk-delete/email-campaigns', methods=['POST'])
@login_required
def bulk_delete_campaigns():
    """Bulk delete email campaigns"""
    try:
        data = request.get_json()
        campaign_ids = data.get('ids', [])
        
        if not campaign_ids:
            return jsonify({'success': False, 'error': 'Brak kampanii do usunięcia'}), 400
        
        # Delete campaigns
        deleted_count = 0
        for campaign_id in campaign_ids:
            campaign = EmailCampaign.query.get(campaign_id)
            if campaign:
                # Delete associated queue items
                EmailQueue.query.filter_by(campaign_id=campaign_id).delete()
                # Delete campaign
                db.session.delete(campaign)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Usunięto {deleted_count} kampanii',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/bulk-delete/email-templates', methods=['POST'])
@login_required
def bulk_delete_templates():
    """Bulk delete email templates"""
    try:
        data = request.get_json()
        template_ids = data.get('ids', [])
        
        if not template_ids:
            return jsonify({'success': False, 'error': 'Brak szablonów do usunięcia'}), 400
        
        # Delete templates
        deleted_count = 0
        for template_id in template_ids:
            template = EmailTemplate.query.get(template_id)
            if template:
                # Delete associated queue items
                EmailQueue.query.filter_by(template_id=template_id).delete()
                # Delete template
                db.session.delete(template)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Usunięto {deleted_count} szablonów',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/bulk-delete/email-groups', methods=['POST'])
@login_required
def bulk_delete_email_groups():
    """Bulk delete email groups"""
    try:
        data = request.get_json()
        group_ids = data.get('ids', [])
        
        if not group_ids:
            return jsonify({'success': False, 'error': 'Brak grup do usunięcia'}), 400
        
        # Delete groups (only manual groups can be deleted)
        deleted_count = 0
        for group_id in group_ids:
            group = UserGroup.query.get(group_id)
            if group and group.group_type == 'manual':
                # Delete associated members
                UserGroupMember.query.filter_by(group_id=group_id).delete()
                # Delete group
                db.session.delete(group)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Usunięto {deleted_count} grup',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Event Group Management Functions
def create_event_group(event_id, event_title):
    """Tworzy grupę dla wydarzenia"""
    try:
        # Sprawdź czy grupa już istnieje dla tego event_id
        existing_group = UserGroup.query.filter_by(
            group_type='event_based',
            criteria=json.dumps({'event_id': event_id})
        ).first()
        
        if existing_group:
            # Aktualizuj nazwę i opis jeśli się zmieniły
            new_name = f"Wydarzenie: {event_title}"
            new_description = f"Grupa uczestników wydarzenia: {event_title}"
            
            if existing_group.name != new_name or existing_group.description != new_description:
                existing_group.name = new_name
                existing_group.description = new_description
                db.session.commit()
                print(f"Zaktualizowano grupę wydarzenia: {new_name}")
            
            return existing_group.id
        
        # Utwórz nową grupę
        group = UserGroup(
            name=f"Wydarzenie: {event_title}",
            description=f"Grupa uczestników wydarzenia: {event_title}",
            group_type='event_based',
            criteria=json.dumps({'event_id': event_id})
        )
        
        db.session.add(group)
        db.session.commit()
        
        print(f"✅ Utworzono grupę wydarzenia '{event_title}' (bez automatycznego dodawania członków klubu)")
        
        return group.id
        
    except Exception as e:
        print(f"Błąd tworzenia grupy wydarzenia: {str(e)}")
        return None

def add_user_to_event_group(user_id, event_id):
    """Dodaje użytkownika do grupy wydarzenia"""
    try:
        from app.models import EventSchedule, User
        
        event = EventSchedule.query.get(event_id)
        if not event:
            return False, "Wydarzenie nie zostało znalezione"
        
        # Znajdź lub utwórz grupę
        group_id = create_event_group(event_id, event.title)
        if not group_id:
            return False, "Błąd tworzenia grupy"
        
        # Pobierz użytkownika
        user = User.query.get(user_id)
        if not user:
            return False, "Użytkownik nie został znaleziony"
        
        # Sprawdź czy już jest w grupie
        existing_member = UserGroupMember.query.filter_by(
            group_id=group_id,
            user_id=user_id
        ).first()
        
        if existing_member:
            return True, "Użytkownik już jest w grupie"
        
        # Dodaj do grupy
        member = UserGroupMember(
            group_id=group_id,
            user_id=user_id,
            email=user.email,
            name=user.first_name
        )
        
        db.session.add(member)
        
        # Aktualizuj liczbę członków
        group = UserGroup.query.get(group_id)
        group.member_count = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).count()
        
        db.session.commit()
        
        return True, "Użytkownik dodany do grupy"
        
    except Exception as e:
        return False, f"Błąd dodawania do grupy: {str(e)}"

def delete_event_groups(event_id):
    """Usuwa grupy dla wydarzenia"""
    try:
        event_groups = UserGroup.query.filter_by(
            group_type='event_based',
            criteria=f'{{"event_id": {event_id}}}'
        ).all()
        
        deleted_count = 0
        for group in event_groups:
            # Usuń wszystkich członków
            UserGroupMember.query.filter_by(group_id=group.id).delete()
            
            # Usuń grupę
            db.session.delete(group)
            deleted_count += 1
        
        db.session.commit()
        return True, f"Usunieto {deleted_count} grup"
        
    except Exception as e:
        return False, f"Błąd usuwania grup: {str(e)}"

@email_bp.route('/email/queue-stats', methods=['GET'])
@login_required
def get_queue_stats():
    """Zwraca statystyki kolejki emaili"""
    try:
        from app.services.mailgun_service import EnhancedNotificationProcessor
        
        processor = EnhancedNotificationProcessor()
        stats = processor.get_queue_stats()
        
        if stats:
            return jsonify({
                'success': True,
                'stats': stats
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Błąd pobierania statystyk kolejki'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd: {str(e)}'
        })

@email_bp.route('/email/campaigns/<int:campaign_id>/activate', methods=['POST'])
@login_required
def email_activate_campaign(campaign_id):
    """Aktywuje kampanię (zmienia z draft na ready)"""
    try:
        print(f"🔍 DEBUG: Starting campaign activation for ID {campaign_id}")
        # Pobierz kampanię
        campaign = EmailCampaign.query.get(campaign_id)
        if not campaign:
            print(f"❌ DEBUG: Campaign {campaign_id} not found")
            return jsonify({'success': False, 'error': 'Kampania nie została znaleziona'}), 404
        
        print(f"✅ DEBUG: Found campaign {campaign_id}: {campaign.name}, status: {campaign.status}")
        
        # Można aktywować tylko draft
        if campaign.status != 'draft':
            print(f"❌ DEBUG: Campaign {campaign_id} status is {campaign.status}, not draft")
            return jsonify({'success': False, 'error': 'Można aktywować tylko kampanie w statusie draft'}), 400
        
        print(f"✅ DEBUG: Campaign {campaign_id} validation passed")
        
        # Sprawdź czy kampania ma wszystkie wymagane dane
        missing_fields = []
        if not campaign.name or campaign.name.strip() == '':
            missing_fields.append('nazwę')
        if not campaign.subject or campaign.subject.strip() == '':
            missing_fields.append('temat')
        
        if missing_fields:
            return jsonify({
                'success': False, 
                'error': f'Kampania musi mieć {", ".join(missing_fields)} przed aktywacją'
            }), 400
        
        if not campaign.recipient_groups:
            return jsonify({'success': False, 'error': 'Kampania musi mieć przypisane grupy odbiorców'}), 400
        
        # Aktywuj kampanię
        from datetime import datetime
        from app.utils.timezone_utils import get_local_now, get_local_timezone
        now = get_local_now()
        
        # Sprawdź czy kampania ma datę planowania
        if campaign.scheduled_at:
            # Upewnij się, że oba datetimes mają strefy czasowe
            if now.tzinfo is None:
                # Jeśli now jest naive, dodaj lokalną strefę czasową
                now = now.replace(tzinfo=get_local_timezone())
            if campaign.scheduled_at.tzinfo is None:
                # Jeśli scheduled_at jest naive, dodaj lokalną strefę czasową
                campaign.scheduled_at = campaign.scheduled_at.replace(tzinfo=get_local_timezone())
            
            if campaign.scheduled_at > now:
                # Zaplanuj kampanię
                campaign.status = 'scheduled'
                db.session.commit()
                
                # Dodaj kampanię do kolejki email z zaplanowanym czasem
                try:
                    from app.services.email_service import EmailService
                    email_service = EmailService()
                    success, message = email_service._add_campaign_to_queue(campaign)
                    
                    if not success:
                        print(f"⚠️ Błąd dodawania zaplanowanej kampanii do kolejki: {message}")
                except Exception as e:
                    print(f"⚠️ Błąd dodawania kampanii do kolejki (Celery może nie działać): {str(e)}")
                    # Kontynuuj bez dodawania do kolejki - kampania zostanie przetworzona przez Celery Beat
                
                # Format time in local timezone for display
                from app.utils.timezone_utils import get_local_timezone
                local_tz = get_local_timezone()
                local_time = campaign.scheduled_at.astimezone(local_tz)
                
                return jsonify({
                    'success': True, 
                    'message': f'Kampania została zaplanowana na {local_time.strftime("%Y-%m-%d %H:%M")}'
                })
            else:
                # Data już minęła - usuń datę i ustaw jako ready
                campaign.scheduled_at = None
                campaign.status = 'ready'
                db.session.commit()
                return jsonify({
                    'success': True, 
                    'message': 'Data wysyłki już minęła. Kampania jest gotowa do natychmiastowej wysyłki.'
                })
        else:
            # Brak daty - ustaw jako ready
            campaign.status = 'ready'
            db.session.commit()
            return jsonify({
                'success': True, 
                'message': 'Kampania została aktywowana. Możesz ją teraz wysłać.'
            })
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ CRITICAL ERROR in campaign activation: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_bp.route('/email/test-sending', methods=['POST'])
def email_test_sending():
    """Test wysyłania emaili - wysyła 100 emaili na testowy adres"""
    try:
        from app.tasks.email_tasks import test_email_sending_task
        
        data = request.get_json() or {}
        test_email = data.get('test_email', 'codeitpy@gmail.com')
        count = data.get('count', 100)
        batch_size = data.get('batch_size', 10)
        
        # Uruchom zadanie Celery
        task = test_email_sending_task.delay(test_email, count, batch_size)
        
        return jsonify({
            'success': True, 
            'message': f'Test wysyłania {count} emaili uruchomiony',
            'task_id': task.id,
            'test_email': test_email,
            'count': count,
            'batch_size': batch_size
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


