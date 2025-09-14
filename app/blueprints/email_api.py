"""
Email API Blueprint - endpoints dla systemu mailingu
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import db, EmailTemplate, UserGroup, EmailCampaign, EmailQueue, UserGroupMember
from app.utils.timezone import get_local_now
from sqlalchemy import desc
from datetime import datetime
import json

email_api_bp = Blueprint('email_api', __name__)

@email_api_bp.route('/email/retry-failed', methods=['POST'])
@login_required
def email_retry_failed():
    """Ponawia nieudane emaile"""
    try:
        from app.services.email_service import EmailService
        email_service = EmailService()
        stats = email_service.retry_failed_emails()
        
        return jsonify({
            'success': True, 
            'message': f'Ponowiono {stats["retried"]} emaili. Sukces: {stats["success"]}, Błędy: {stats["failed"]}',
            'stats': stats
        })
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_api_bp.route('/email/retry/<int:email_id>', methods=['POST'])
@login_required
def email_retry_single(email_id):
    """Ponawia pojedynczy email"""
    try:
        from app.services.email_service import EmailService
        
        email = EmailQueue.query.get(email_id)
        if not email:
            return jsonify({'success': False, 'error': 'Email nie istnieje'}), 404
        email_service = EmailService()
        
        success, message = email_service.send_email(
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

@email_api_bp.route('/email/queue/<int:email_id>', methods=['DELETE'])
@login_required
def email_delete_from_queue(email_id):
    """Usuwa email z kolejki"""
    try:
        email = EmailQueue.query.get(email_id)
        if not email:
            return jsonify({'success': False, 'error': 'Email nie istnieje'}), 404
        db.session.delete(email)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Email usunięty z kolejki'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_api_bp.route('/email/templates', methods=['GET'])
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
                'is_default': template.name in default_templates,
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

@email_api_bp.route('/email/templates', methods=['POST'])
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

@email_api_bp.route('/email/templates/<int:template_id>', methods=['GET'])
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
                'is_active': template.is_active
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_api_bp.route('/email/templates/<int:template_id>', methods=['PUT'])
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
        template.template_type = data['template_type']
        template.html_content = data['html_content']
        template.text_content = data.get('text_content', '')
        template.variables = data.get('variables', '')
        template.is_active = data.get('is_active', True)
        template.updated_at = get_local_now()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Szablon zaktualizowany pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_api_bp.route('/email/templates/<int:template_id>', methods=['DELETE'])
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

@email_api_bp.route('/email/campaigns/templates', methods=['GET'])
@login_required
def email_campaign_templates():
    """Pobiera szablony dostępne dla kampanii"""
    try:
        templates = EmailTemplate.query.filter_by(is_active=True).all()
        
        templates_data = []
        for template in templates:
            variables = []
            if template.variables:
                try:
                    variables = json.loads(template.variables)
                except json.JSONDecodeError:
                    variables = []
            
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

@email_api_bp.route('/email/templates/reset', methods=['POST'])
@login_required
def email_reset_templates():
    """Resetuje szablony do stanu domyślnego"""
    try:
        from reset_templates import reset_templates
        
        success = reset_templates()
        
        if success:
            return jsonify({'success': True, 'message': 'Szablony zostały zresetowane do stanu domyślnego'})
        else:
            return jsonify({'success': False, 'error': 'Błąd podczas resetowania szablonów'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_api_bp.route('/email/campaigns', methods=['GET'])
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

@email_api_bp.route('/email/campaigns', methods=['POST'])
@login_required
def email_create_campaign():
    """Tworzy nową kampanię emailową"""
    try:
        data = request.get_json()
        
        campaign = EmailCampaign(
            name=data['name'],
            subject=data['subject'],
            template_id=data.get('template_id'),
            content_variables=json.dumps(data.get('content_variables', {})),
            recipient_groups=json.dumps(data['recipient_groups']),
            status='draft'
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
        
        return jsonify({'success': True, 'message': 'Kampania utworzona pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_api_bp.route('/email/campaigns/<int:campaign_id>', methods=['GET'])
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

@email_api_bp.route('/email/campaigns/<int:campaign_id>', methods=['PUT'])
@login_required
def email_update_campaign(campaign_id):
    """Aktualizuje kampanię emailową"""
    try:
        campaign = EmailCampaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie została znaleziona'}), 404
        
        data = request.get_json()
        
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
            campaign.scheduled_at = datetime.fromisoformat(data['scheduled_at'].replace('Z', '+00:00'))
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Kampania zaktualizowana pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_api_bp.route('/email/campaigns/<int:campaign_id>', methods=['DELETE'])
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

@email_api_bp.route('/email/campaigns/<int:campaign_id>/send', methods=['POST'])
@login_required
def email_send_campaign(campaign_id):
    """Wysyła kampanię emailową"""
    try:
        from app.services.email_service import EmailService
        import json
        
        # Pobierz kampanię
        campaign = EmailCampaign.query.get(campaign_id)
        if not campaign:
            return jsonify({'success': False, 'error': 'Kampania nie została znaleziona'}), 404
        
        # Pobierz grupy odbiorców
        if not campaign.recipient_groups:
            return jsonify({'success': False, 'error': 'Kampania nie ma przypisanych grup odbiorców'}), 400
        
        try:
            group_ids = json.loads(campaign.recipient_groups)
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': 'Nieprawidłowy format grup odbiorców'}), 400
        
        if not group_ids:
            return jsonify({'success': False, 'error': 'Kampania nie ma przypisanych grup odbiorców'}), 400
        
        email_service = EmailService()
        
        # Wyślij do każdej grupy
        total_sent = 0
        total_emails = 0
        total_errors = 0
        messages = []
        
        for group_id in group_ids:
            success, message, email_count = email_service.send_campaign_to_group(campaign_id, group_id)
            if success:
                total_sent += 1
                total_emails += email_count
                messages.append(f"Grupa {group_id}: {message}")
            else:
                total_errors += 1
                messages.append(f"Grupa {group_id}: BŁĄD - {message}")
        
        # Aktualizuj status kampanii
        campaign = EmailCampaign.query.get(campaign_id)
        if campaign:
            campaign.status = 'sending'
            campaign.total_recipients = total_emails
            campaign.sent_count = 0  # Zostanie zaktualizowane po wysłaniu
            campaign.failed_count = 0
            campaign.updated_at = datetime.utcnow()
            db.session.commit()
        
        if total_errors == 0:
            return jsonify({'success': True, 'message': f'Kampania dodana do kolejki dla {total_emails} odbiorców w {total_sent} grupach'})
        else:
            return jsonify({'success': False, 'error': f'Wysłano do {total_sent} grup, {total_errors} błędów. Szczegóły: {"; ".join(messages)}'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_api_bp.route('/email/groups', methods=['GET'])
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
            group_list.append({
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'group_type': group.group_type,
                'member_count': group.member_count,
                'is_active': group.is_active,
                'is_default': group.group_type in default_groups,
                'created_at': group.created_at.isoformat()
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

@email_api_bp.route('/email/groups', methods=['POST'])
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
            from models import User
            added_count = 0
            for user_id in data['user_ids']:
                user = User.query.get(user_id)
                if user:
                    member = UserGroupMember(
                        group_id=group.id,
                        user_id=user_id,
                        email=user.email,
                        name=user.name
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

@email_api_bp.route('/email/groups/<int:group_id>', methods=['GET'])
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
                'is_active': group.is_active
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_api_bp.route('/email/groups/<int:group_id>', methods=['PUT'])
@login_required
def email_update_group(group_id):
    """Aktualizuje grupę użytkowników"""
    try:
        group = UserGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupa nie istnieje'}), 404
        
        # Lista domyślnych grup (nie można ich edytować)
        default_groups = ['club_members', 'all_users']
        
        if group.group_type in default_groups:
            return jsonify({'success': False, 'error': 'Nie można edytować grup systemowych'}), 400
        
        data = request.get_json()
        
        group.name = data['name']
        group.description = data.get('description', '')
        group.group_type = data['group_type']
        group.updated_at = get_local_now()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Grupa zaktualizowana pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_api_bp.route('/email/groups/<int:group_id>', methods=['DELETE'])
@login_required
def email_delete_group(group_id):
    """Usuwa grupę użytkowników"""
    try:
        group = UserGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupa nie istnieje'}), 404
        
        # Lista domyślnych grup (nie można ich usuwać)
        default_groups = ['club_members']
        
        if group.group_type in default_groups:
            return jsonify({'success': False, 'error': 'Nie można usunąć grupy domyślnej'}), 400
        
        db.session.delete(group)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Grupa usunięta pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_api_bp.route('/email/groups/sync', methods=['POST'])
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

@email_api_bp.route('/email/groups/<int:group_id>/members', methods=['GET'])
@login_required
def email_get_group_members(group_id):
    """Pobiera członków grupy użytkowników"""
    try:
        group = UserGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupa nie istnieje'}), 404
        
        # Lista domyślnych grup (członkowie zarządzani automatycznie)
        default_groups = ['club_members', 'all_users']
        
        if group.group_type in default_groups:
            return jsonify({'success': False, 'error': 'Członkowie grup systemowych są zarządzani automatycznie'}), 400
        
        members = []
        for member in group.members:
            members.append({
                'id': member.id,
                'user_id': member.user_id,
                'user_name': member.name,
                'email': member.email,
                'member_type': member.member_type,
                'joined_at': member.joined_at.isoformat() if member.joined_at else None
            })
        
        return jsonify({'success': True, 'members': members})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@email_api_bp.route('/email/groups/<int:group_id>/members', methods=['POST'])
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
        from models import User
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Użytkownik nie istnieje'}), 404
        
        # Add member to group
        member = UserGroupMember(
            group_id=group_id,
            user_id=user_id,
            name=user.name,
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

@email_api_bp.route('/email/groups/members/<int:member_id>', methods=['DELETE'])
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

@email_api_bp.route('/email/campaigns/<int:campaign_id>/update-stats', methods=['POST'])
@login_required
def update_campaign_stats(campaign_id):
    """Aktualizuje statystyki kampanii"""
    try:
        from app.services.email_service import EmailService
        email_service = EmailService()
        
        success = email_service.update_campaign_stats(campaign_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Statystyki kampanii zaktualizowane'})
        else:
            return jsonify({'success': False, 'error': 'Nie udało się zaktualizować statystyk'}), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Event Group Management Functions
def create_event_group(event_id, event_title):
    """Tworzy grupę dla wydarzenia"""
    try:
        # Sprawdź czy grupa już istnieje
        existing_group = UserGroup.query.filter_by(
            name=f"Wydarzenie: {event_title}",
            group_type='event_based'
        ).first()
        
        if existing_group:
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
        
        return group.id
        
    except Exception as e:
        print(f"Błąd tworzenia grupy wydarzenia: {str(e)}")
        return None

def add_user_to_event_group(user_id, event_id):
    """Dodaje użytkownika do grupy wydarzenia"""
    try:
        from models import EventSchedule, User
        
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
            name=user.name
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
