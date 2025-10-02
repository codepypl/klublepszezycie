"""
API v2 dla systemu mailingu - nowy, prosty i wydajny
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import logging

from app.services.email_v2 import EmailManager
from app.services.email_v2.queue import EmailQueueProcessor, EmailScheduler
from app.services.email_v2.monitoring import EmailStats

# Utwórz blueprint
email_v2_bp = Blueprint('email_v2_api', __name__)

# Inicjalizacja serwisów
email_manager = EmailManager()
queue_processor = EmailQueueProcessor()
email_scheduler = EmailScheduler()
email_stats = EmailStats()

logger = logging.getLogger(__name__)

# =============================================================================
# PODSTAWOWE OPERACJE
# =============================================================================

@email_v2_bp.route('/email/v2/send', methods=['POST'])
@login_required
def send_email():
    """Wysyła pojedynczy e-mail"""
    try:
        data = request.get_json()
        
        # Walidacja
        required_fields = ['to_email', 'subject']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Brakuje wymaganego pola: {field}'
                }), 400
        
        # Wyślij e-mail
        success, message = email_manager.send_email(
            to_email=data['to_email'],
            subject=data['subject'],
            html_content=data.get('html_content'),
            text_content=data.get('text_content'),
            template_name=data.get('template_name'),
            context=data.get('context', {}),
            priority=data.get('priority', 2),
            scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None
        )
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd wysyłania e-maila: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_v2_bp.route('/email/v2/send-template', methods=['POST'])
@login_required
def send_template_email():
    """Wysyła e-mail używając szablonu"""
    try:
        data = request.get_json()
        
        # Walidacja
        required_fields = ['to_email', 'template_name']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Brakuje wymaganego pola: {field}'
                }), 400
        
        # Wyślij e-mail
        success, message = email_manager.send_template_email(
            to_email=data['to_email'],
            template_name=data['template_name'],
            context=data.get('context', {}),
            priority=data.get('priority', 2),
            scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None
        )
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd wysyłania szablonu: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_v2_bp.route('/email/v2/process-queue', methods=['POST'])
@login_required
def process_queue():
    """Przetwarza kolejkę e-maili"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 50)
        
        # Przetwórz kolejkę
        stats = queue_processor.process_queue(limit)
        
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

# =============================================================================
# PRZYPOMNIENIA O WYDARZENIACH
# =============================================================================

@email_v2_bp.route('/email/v2/schedule-event-reminders', methods=['POST'])
@login_required
def schedule_event_reminders():
    """Planuje przypomnienia o wydarzeniu"""
    try:
        data = request.get_json()
        
        if 'event_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Brakuje event_id'
            }), 400
        
        # Zaplanuj przypomnienia
        success, message = email_scheduler.schedule_event_reminders(data['event_id'])
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd planowania przypomnień: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# KAMPANIE E-MAILOWE
# =============================================================================

@email_v2_bp.route('/email/v2/campaigns', methods=['GET'])
@login_required
def get_campaigns():
    """Pobiera listę kampanii"""
    try:
        from app.models import EmailCampaign
        
        campaigns = EmailCampaign.query.order_by(EmailCampaign.created_at.desc()).all()
        
        campaigns_data = []
        for campaign in campaigns:
            campaigns_data.append({
                'id': campaign.id,
                'name': campaign.name,
                'subject': campaign.subject,
                'status': campaign.status,
                'description': campaign.description,
                'created_at': campaign.created_at.isoformat() if campaign.created_at else None,
                'scheduled_at': campaign.scheduled_at.isoformat() if campaign.scheduled_at else None,
                'sent_at': campaign.sent_at.isoformat() if campaign.sent_at else None
            })
        
        return jsonify({
            'success': True,
            'campaigns': campaigns_data
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania kampanii: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_v2_bp.route('/email/v2/campaigns', methods=['POST'])
@login_required
def create_campaign():
    """Tworzy nową kampanię"""
    try:
        data = request.get_json()
        
        # Walidacja
        required_fields = ['name', 'subject']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Brakuje wymaganego pola: {field}'
                }), 400
        
        # Utwórz kampanię
        success, message, campaign_id = email_manager.create_campaign(
            name=data['name'],
            subject=data['subject'],
            html_content=data.get('html_content'),
            text_content=data.get('text_content'),
            description=data.get('description')
        )
        
        return jsonify({
            'success': success,
            'message': message,
            'campaign_id': campaign_id
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd tworzenia kampanii: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_v2_bp.route('/email/v2/campaigns/<int:campaign_id>/send', methods=['POST'])
@login_required
def send_campaign(campaign_id):
    """Wysyła kampanię"""
    try:
        data = request.get_json() or {}
        
        # Wyślij kampanię
        success, message = email_manager.send_campaign(
            campaign_id=campaign_id,
            recipients=data.get('recipients'),
            group_ids=data.get('group_ids'),
            scheduled_at=datetime.fromisoformat(data['scheduled_at']) if data.get('scheduled_at') else None
        )
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd wysyłania kampanii: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_v2_bp.route('/email/v2/campaigns/<int:campaign_id>/stats', methods=['GET'])
@login_required
def get_campaign_stats(campaign_id):
    """Pobiera statystyki kampanii"""
    try:
        stats = email_stats.get_campaign_stats(campaign_id)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statystyk kampanii: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# STATYSTYKI I MONITOROWANIE
# =============================================================================

@email_v2_bp.route('/email/v2/stats', methods=['GET'])
@login_required
def get_stats():
    """Pobiera podstawowe statystyki"""
    try:
        stats = email_manager.get_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania statystyk: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_v2_bp.route('/email/v2/daily-stats', methods=['GET'])
@login_required
def get_daily_stats():
    """Pobiera statystyki dzienne"""
    try:
        date_str = request.args.get('date')
        date = datetime.fromisoformat(date_str) if date_str else None
        
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

@email_v2_bp.route('/email/v2/hourly-stats', methods=['GET'])
@login_required
def get_hourly_stats():
    """Pobiera statystyki godzinowe"""
    try:
        date_str = request.args.get('date')
        date = datetime.fromisoformat(date_str) if date_str else None
        
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

@email_v2_bp.route('/email/v2/template-stats', methods=['GET'])
@login_required
def get_template_stats():
    """Pobiera statystyki szablonów"""
    try:
        template_name = request.args.get('template_name')
        days = int(request.args.get('days', 7))
        
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

@email_v2_bp.route('/email/v2/event-stats', methods=['GET'])
@login_required
def get_event_stats():
    """Pobiera statystyki wydarzeń"""
    try:
        event_id = request.args.get('event_id', type=int)
        days = int(request.args.get('days', 30))
        
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

@email_v2_bp.route('/email/v2/failed-emails', methods=['GET'])
@login_required
def get_failed_emails():
    """Pobiera listę nieudanych e-maili"""
    try:
        limit = int(request.args.get('limit', 50))
        
        failed_emails = email_stats.get_failed_emails(limit)
        
        return jsonify({
            'success': True,
            'failed_emails': failed_emails,
            'count': len(failed_emails)
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania nieudanych e-maili: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_v2_bp.route('/email/v2/system-health', methods=['GET'])
@login_required
def get_system_health():
    """Pobiera stan systemu e-maili"""
    try:
        health = email_stats.get_system_health()
        
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

# =============================================================================
# ZARZĄDZANIE KOLEJKĄ
# =============================================================================

@email_v2_bp.route('/email/v2/retry-failed', methods=['POST'])
@login_required
def retry_failed_emails():
    """Ponawia wysyłanie nieudanych e-maili"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 10)
        
        stats = queue_processor.retry_failed_emails(limit)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd ponawiania e-maili: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_v2_bp.route('/email/v2/cleanup', methods=['POST'])
@login_required
def cleanup_old_emails():
    """Czyści stare e-maile z kolejki"""
    try:
        data = request.get_json() or {}
        days = data.get('days', 30)
        
        stats = queue_processor.cleanup_old_emails(days)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd czyszczenia kolejki: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# SZABLONY
# =============================================================================

@email_v2_bp.route('/email/v2/templates', methods=['GET'])
@login_required
def get_templates():
    """Pobiera dostępne szablony"""
    try:
        from app.services.email_v2.templates import EmailTemplateEngine
        
        template_engine = EmailTemplateEngine()
        templates = template_engine.get_available_templates()
        
        return jsonify({
            'success': True,
            'templates': templates
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania szablonów: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@email_v2_bp.route('/email/v2/validate-template', methods=['POST'])
@login_required
def validate_template():
    """Waliduje szablon"""
    try:
        data = request.get_json()
        
        if 'template_name' not in data:
            return jsonify({
                'success': False,
                'error': 'Brakuje template_name'
            }), 400
        
        from app.services.email_v2.templates import EmailTemplateEngine
        
        template_engine = EmailTemplateEngine()
        valid, message = template_engine.validate_template(data['template_name'])
        
        return jsonify({
            'success': valid,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd walidacji szablonu: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
