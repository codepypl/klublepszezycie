"""
Email campaigns API - complete campaign management
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.services.campaign_service import CampaignService
import logging

email_campaigns_bp = Blueprint('email_campaigns_api', __name__)
campaign_service = CampaignService()
logger = logging.getLogger(__name__)

@email_campaigns_bp.route('/email/campaigns', methods=['GET'])
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
                'description': campaign.description or '',
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

@email_campaigns_bp.route('/email/campaigns', methods=['POST'])
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
        success, message, campaign_id = campaign_service.create_campaign(data)
        
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

@email_campaigns_bp.route('/email/campaigns/<int:campaign_id>', methods=['GET'])
@login_required
def get_campaign(campaign_id):
    """Pobiera szczegóły kampanii emailowej"""
    try:
        from app.models import EmailCampaign
        import json
        
        campaign = EmailCampaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie została znaleziona'}), 404
        
        # Parse recipient groups
        recipient_groups = []
        if campaign.recipient_groups:
            try:
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
        logger.error(f"❌ Błąd pobierania kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_campaigns_bp.route('/email/campaigns/<int:campaign_id>', methods=['PUT'])
@login_required
def update_campaign(campaign_id):
    """Aktualizuje kampanię emailową"""
    try:
        from app.models import EmailCampaign, UserGroupMember
        from app.utils.timezone_utils import get_local_now, get_local_timezone
        from app import db
        import json
        
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
            campaign.content_variables = json.dumps(data['content_variables'])
        if 'recipient_groups' in data:
            campaign.recipient_groups = json.dumps(data['recipient_groups'])
            
            # Recalculate total recipients when groups change
            total_recipients = 0
            for group_id in data['recipient_groups']:
                group_members = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).count()
                total_recipients += group_members
            campaign.total_recipients = total_recipients
        else:
            # Always recalculate total recipients even if groups don't change
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
            
            # Parse date from frontend (może być bez timezone)
            date_str = data['scheduled_at']
            if 'T' in date_str and '+' not in date_str and 'Z' not in date_str:
                # Format: "2025-09-28T15:30" (bez timezone) - dodaj lokalną strefę czasową
                scheduled_at = datetime.fromisoformat(date_str)
                campaign.scheduled_at = scheduled_at.replace(tzinfo=get_local_timezone())
            else:
                # Format z timezone: "2025-09-28T15:30Z" lub "2025-09-28T15:30+02:00"
                campaign.scheduled_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        elif 'scheduled_at' in data and not data['scheduled_at']:
            # Użytkownik usunął datę planowania
            campaign.scheduled_at = None
        
        campaign.updated_at = get_local_now()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Kampania zaktualizowana pomyślnie'})
        
    except Exception as e:
        from app import db
        db.session.rollback()
        logger.error(f"❌ Błąd aktualizacji kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_campaigns_bp.route('/email/campaigns/<int:campaign_id>', methods=['DELETE'])
@login_required
def delete_campaign(campaign_id):
    """Usuwa kampanię emailową"""
    try:
        from app.models import EmailCampaign, EmailQueue
        from app import db
        
        campaign = EmailCampaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie istnieje'}), 404
        
        # Don't allow deleting sent campaigns
        if campaign.status in ['sending', 'sent', 'completed']:
            return jsonify({'success': False, 'error': f'Nie można usunąć kampanii ze statusem "{campaign.status}"'}), 400
        
        # Delete associated queue items
        EmailQueue.query.filter_by(campaign_id=campaign_id).delete()
        # Delete campaign
        db.session.delete(campaign)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Kampania usunięta pomyślnie'})
        
    except Exception as e:
        from app import db
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_campaigns_bp.route('/email/campaigns/<int:campaign_id>/activate', methods=['POST'])
@login_required
def activate_campaign(campaign_id):
    """Aktywuje kampanię (zmienia z draft na ready/scheduled)"""
    try:
        success, message = campaign_service.activate_campaign(campaign_id)
        
        return jsonify({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd aktywacji kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_campaigns_bp.route('/email/campaigns/<int:campaign_id>/update-stats', methods=['POST'])
@login_required
def update_campaign_stats(campaign_id):
    """Aktualizuje statystyki kampanii"""
    try:
        from app.models import EmailQueue, EmailCampaign
        from app import db
        
        campaign = EmailCampaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie znaleziona'}), 404
        
        # Count sent and failed
        sent_count = EmailQueue.query.filter_by(campaign_id=campaign_id, status='sent').count()
        failed_count = EmailQueue.query.filter_by(campaign_id=campaign_id, status='failed').count()
        
        campaign.sent_count = sent_count
        campaign.failed_count = failed_count
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Statystyki kampanii zaktualizowane'})
            
    except Exception as e:
        from app import db
        db.session.rollback()
        logger.error(f"❌ Błąd aktualizacji statystyk kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@email_campaigns_bp.route('/bulk-delete/email-campaigns', methods=['POST'])
@login_required
def bulk_delete_campaigns():
    """Bulk delete email campaigns"""
    try:
        from app.models import EmailCampaign, EmailQueue
        from app import db
        
        data = request.get_json()
        campaign_ids = data.get('ids', [])
        
        if not campaign_ids:
            return jsonify({'success': False, 'error': 'Brak kampanii do usunięcia'}), 400
        
        # Delete campaigns
        deleted_count = 0
        for campaign_id in campaign_ids:
            campaign = EmailCampaign.query.get(campaign_id)
            if campaign:
                # Don't allow deleting sent campaigns
                if campaign.status in ['sending', 'sent', 'completed']:
                    continue  # Skip sent campaigns
                
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
        from app import db
        db.session.rollback()
        logger.error(f"❌ Błąd masowego usuwania kampanii: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500