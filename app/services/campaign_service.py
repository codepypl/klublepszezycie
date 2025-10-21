"""
Service for managing email campaigns
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json
import logging
from app import db
from app.models import EmailCampaign, EmailTemplate, UserGroupMember
from app.utils.timezone_utils import get_local_now, get_local_timezone
from app.validators.email_validators import EmailValidator, CampaignStatusValidator
from app.services.email_v2 import EmailManager

logger = logging.getLogger(__name__)


class CampaignService:
    """Serwis do zarządzania kampaniami emailowymi"""
    
    def __init__(self):
        self.email_manager = EmailManager()
    
    def create_campaign(self, data: Dict) -> Tuple[bool, str, Optional[int]]:
        """Tworzy nową kampanię emailową"""
        try:
            # Walidacja danych
            is_valid, error_msg = EmailValidator.validate_campaign_data(data)
            if not is_valid:
                return False, error_msg, None
            
            # Walidacja grup odbiorców
            try:
                recipient_groups = json.loads(data['recipient_groups']) if isinstance(data['recipient_groups'], str) else data['recipient_groups']
            except json.JSONDecodeError:
                return False, 'Nieprawidłowy format grup odbiorców', None
            
            is_valid, error_msg = EmailValidator.validate_recipient_groups(recipient_groups)
            if not is_valid:
                return False, error_msg, None
            
            # Walidacja zmiennych treści
            content_variables = data.get('content_variables', {})
            is_valid, error_msg = EmailValidator.validate_content_variables(content_variables)
            if not is_valid:
                return False, error_msg, None
            
            # Obsługa planowania
            send_type = data.get('send_type', 'immediate')
            scheduled_at = None
            status = 'draft'
            
            if send_type == 'scheduled':
                is_valid, error_msg, scheduled_datetime = EmailValidator.validate_scheduled_time(data.get('scheduled_at'))
                if not is_valid:
                    return False, error_msg, None
                scheduled_at = scheduled_datetime
            
            # Pobierz treść z szablonu
            html_content, text_content = self._get_template_content(data.get('template_id'))
            
            # Utwórz kampanię
            campaign = EmailCampaign(
                name=data['name'],
                subject=data['subject'],
                html_content=html_content,
                text_content=text_content,
                template_id=data.get('template_id'),
                content_variables=json.dumps(content_variables),
                recipient_groups=json.dumps(recipient_groups),
                send_type=send_type,
                scheduled_at=scheduled_at,
                status=status
            )
            
            db.session.add(campaign)
            db.session.flush()  # Flush to get campaign ID
            
            # Oblicz liczbę odbiorców
            total_recipients = self._calculate_recipients(data['recipient_groups'])
            campaign.total_recipients = total_recipients
            
            db.session.commit()
            
            logger.info(f"✅ Created campaign: {campaign.name} (ID: {campaign.id})")
            return True, 'Kampania utworzona pomyślnie', campaign.id
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error creating campaign: {str(e)}")
            return False, f'Błąd tworzenia kampanii: {str(e)}', None
    
    def update_campaign(self, campaign_id: int, data: Dict) -> Tuple[bool, str]:
        """Aktualizuje kampanię emailową"""
        try:
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return False, 'Kampania nie została znaleziona'
            
            # Walidacja pól jeśli są aktualizowane
            if 'name' in data and (not data['name'] or data['name'].strip() == ''):
                return False, 'Nazwa kampanii nie może być pusta'
            
            if 'subject' in data and (not data['subject'] or data['subject'].strip() == ''):
                return False, 'Temat kampanii nie może być pusty'
            
            # Aktualizuj pola
            if 'name' in data:
                campaign.name = data['name']
            if 'subject' in data:
                campaign.subject = data['subject']
            if 'template_id' in data:
                campaign.template_id = data['template_id']
            if 'content_variables' in data:
                campaign.content_variables = json.dumps(data['content_variables'])
            if 'recipient_groups' in data:
                # Walidacja grup odbiorców
                is_valid, error_msg = EmailValidator.validate_recipient_groups(data['recipient_groups'])
                if not is_valid:
                    return False, error_msg
                
                campaign.recipient_groups = json.dumps(data['recipient_groups'])
                # Przelicz liczbę odbiorców
                campaign.total_recipients = self._calculate_recipients(data['recipient_groups'])
            
            # Obsługa planowania
            if 'scheduled_at' in data:
                if data['scheduled_at']:
                    is_valid, error_msg, scheduled_datetime = EmailValidator.validate_scheduled_time(data['scheduled_at'])
                    if not is_valid:
                        return False, error_msg
                    campaign.scheduled_at = scheduled_datetime
                else:
                    campaign.scheduled_at = None
            
            # Aktualizuj status jeśli podano
            if 'status' in data:
                if not CampaignStatusValidator.can_transition(campaign.status, data['status']):
                    return False, f'Nie można zmienić statusu z {campaign.status} na {data["status"]}'
                campaign.status = data['status']
            
            campaign.updated_at = get_local_now()
            db.session.commit()
            
            logger.info(f"✅ Updated campaign: {campaign.name} (ID: {campaign.id})")
            return True, 'Kampania zaktualizowana pomyślnie'
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error updating campaign: {str(e)}")
            return False, f'Błąd aktualizacji kampanii: {str(e)}'
    
    def activate_campaign(self, campaign_id: int) -> Tuple[bool, str]:
        """Aktywuje kampanię (zmienia z draft na ready/scheduled)"""
        try:
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return False, 'Kampania nie została znaleziona'
            
            if campaign.status != 'draft':
                return False, 'Można aktywować tylko kampanie w statusie draft'
            
            # Sprawdź czy kampania ma wszystkie wymagane dane
            missing_fields = []
            if not campaign.name or campaign.name.strip() == '':
                missing_fields.append('nazwę')
            if not campaign.subject or campaign.subject.strip() == '':
                missing_fields.append('temat')
            
            if missing_fields:
                return False, f'Kampania musi mieć {", ".join(missing_fields)} przed aktywacją'
            
            if not campaign.recipient_groups:
                return False, 'Kampania musi mieć przypisane grupy odbiorców'
            
            # Aktywuj kampanię
            now = get_local_now()
            
            if campaign.scheduled_at:
                # Upewnij się, że oba datetimes mają strefy czasowe
                if now.tzinfo is None:
                    now = now.replace(tzinfo=get_local_timezone())
                if campaign.scheduled_at.tzinfo is None:
                    campaign.scheduled_at = campaign.scheduled_at.replace(tzinfo=get_local_timezone())
                
                if campaign.scheduled_at > now:
                    # Zaplanuj kampanię
                    campaign.status = 'scheduled'
                    db.session.commit()
                    
                    # Dodaj kampanię do kolejki email
                    try:
                        success, message = self._add_campaign_to_queue(campaign)
                        if success:
                            logger.info(f"✅ Campaign {campaign.id} added to queue for {campaign.scheduled_at}")
                        else:
                            logger.warning(f"⚠️ Error adding campaign to queue: {message}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error adding campaign to queue: {str(e)}")
                    
                    return True, f'Kampania została zaplanowana na {campaign.scheduled_at.strftime("%Y-%m-%d %H:%M")}'
                else:
                    # Data już minęła - usuń datę i ustaw jako ready
                    campaign.scheduled_at = None
                    campaign.status = 'ready'
                    db.session.commit()
                    
                    # Dodaj kampanię do kolejki natychmiastowej
                    try:
                        success, message = self._add_campaign_to_queue(campaign)
                        if success:
                            # Aktualizuj status na 'sending' po dodaniu do kolejki
                            campaign.status = 'sending'
                            db.session.commit()
                            logger.info(f"✅ Campaign {campaign.id} added to immediate queue (past date) and marked as sending")
                            return True, f'Data wysyłki już minęła. Kampania została dodana do kolejki natychmiastowej. {message}'
                        else:
                            logger.warning(f"⚠️ Error adding campaign to immediate queue (past date): {message}")
                            return True, f'Data wysyłki już minęła. Kampania jest gotowa, ale wystąpił problem z dodaniem do kolejki: {message}'
                    except Exception as e:
                        logger.warning(f"⚠️ Error adding campaign to immediate queue (past date): {str(e)}")
                        return True, f'Data wysyłki już minęła. Kampania jest gotowa, ale wystąpił problem z dodaniem do kolejki: {str(e)}'
            else:
                # Brak daty - ustaw jako ready i dodaj do kolejki
                campaign.status = 'ready'
                db.session.commit()
                
                # Dodaj kampanię do kolejki natychmiastowej
                try:
                    success, message = self._add_campaign_to_queue(campaign)
                    if success:
                        # Aktualizuj status na 'sending' po dodaniu do kolejki
                        campaign.status = 'sending'
                        db.session.commit()
                        logger.info(f"✅ Campaign {campaign.id} added to immediate queue and marked as sending")
                        return True, f'Kampania została aktywowana i dodana do kolejki. {message}'
                    else:
                        logger.warning(f"⚠️ Error adding campaign to immediate queue: {message}")
                        return True, f'Kampania została aktywowana, ale wystąpił problem z dodaniem do kolejki: {message}'
                except Exception as e:
                    logger.warning(f"⚠️ Error adding campaign to immediate queue: {str(e)}")
                    return True, f'Kampania została aktywowana, ale wystąpił problem z dodaniem do kolejki: {str(e)}'
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error activating campaign: {str(e)}")
            return False, f'Błąd aktywacji kampanii: {str(e)}'
    
    def send_campaign(self, campaign_id: int) -> Tuple[bool, str]:
        """Wysyła kampanię emailową"""
        try:
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return False, 'Kampania nie została znaleziona'
            
            # Sprawdź status kampanii
            if campaign.status == 'draft':
                return False, 'Kampania jest szkicem. Najpierw ją aktywuj.'
            
            if campaign.status not in ['ready', 'scheduled']:
                if campaign.status in ['sent', 'sending', 'completed']:
                    return False, 'Kampania została już wysłana'
                else:
                    return False, 'Kampania nie może być wysłana w obecnym statusie'
            
            # Użyj EmailManager do wysyłki
            from app.services.email_v2 import EmailManager
            
            email_manager = EmailManager()
            
            if campaign.send_type == 'immediate':
                # Wyślij natychmiast - dodaj emaile do kolejki
                success, message = self._add_campaign_emails_to_queue(campaign)
                if not success:
                    return False, message
                message = f"Kampania dodana do kolejki wysyłki"
            elif campaign.send_type == 'scheduled' and campaign.scheduled_at:
                # Zaplanuj wysłanie - dodaj emaile z scheduled_at
                success, message = self._add_campaign_emails_to_queue(campaign, scheduled_at=campaign.scheduled_at)
                if not success:
                    return False, message
                message = f"Kampania zaplanowana na {campaign.scheduled_at}"
            else:
                return False, 'Nieprawidłowy tryb wysyłania lub brak czasu wysłania'
            
            # Aktualizuj status kampanii
            campaign.status = 'sending'
            campaign.updated_at = get_local_now()
            db.session.commit()
            
            logger.info(f"✅ Campaign {campaign_id} scheduled for sending")
            return True, message
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error sending campaign: {str(e)}")
            return False, f'Błąd wysyłania kampanii: {str(e)}'
    
    def _get_template_content(self, template_id: Optional[int]) -> Tuple[str, str]:
        """Pobiera treść z szablonu"""
        if not template_id:
            return '', ''
        
        template = EmailTemplate.query.get(template_id)
        if not template:
            return '', ''
        
        return template.html_content or '', template.text_content or ''
    
    def _calculate_recipients(self, group_ids: List[int]) -> int:
        """Oblicza liczbę odbiorców w grupach"""
        total_recipients = 0
        for group_id in group_ids:
            group_members = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).count()
            total_recipients += group_members
        return total_recipients
    
    def _add_campaign_to_queue(self, campaign: EmailCampaign) -> Tuple[bool, str]:
        """Dodaje kampanię do kolejki emaili"""
        try:
            from app.models import UserGroupMember, User
            
            # Pobierz grupy odbiorców
            if not campaign.recipient_groups:
                return False, "Kampania nie ma przypisanych grup odbiorców"
            
            try:
                group_ids = json.loads(campaign.recipient_groups)
            except json.JSONDecodeError:
                return False, "Nieprawidłowy format grup odbiorców"
            
            if not group_ids:
                return False, "Brak grup odbiorców"
            
            # Pobierz wszystkich członków grup
            all_recipients = []
            for group_id in group_ids:
                members = UserGroupMember.query.filter_by(
                    group_id=group_id, 
                    is_active=True
                ).all()
                
                for member in members:
                    user = User.query.get(member.user_id)
                    if user and user.is_active:
                        all_recipients.append(user)
            
            if not all_recipients:
                return False, "Brak aktywnych odbiorców w wybranych grupach"
            
            # Przygotuj kontekst dla każdego odbiorcy
            content_variables = {}
            if campaign.content_variables:
                try:
                    content_variables = json.loads(campaign.content_variables)
                except json.JSONDecodeError:
                    content_variables = {}
            
            # Dodaj emaile do kolejki
            added_count = 0
            for user in all_recipients:
                # Przygotuj kontekst dla użytkownika
                context = {
                    'user_name': user.first_name or 'Użytkowniku',
                    'user_email': user.email,
                    **content_variables  # Dodaj zmienne z kampanii
                }
                
                # Dodaj email do kolejki
                success, message, queue_id = self.email_manager._add_to_queue(
                    to_email=user.email,
                    subject=campaign.subject,
                    html_content=campaign.html_content,
                    text_content=campaign.text_content,
                    priority=2,  # Normalny priorytet
                    scheduled_at=campaign.scheduled_at,
                    context=context,
                    campaign_id=campaign.id,
                    template_id=campaign.template_id
                )
                
                if success:
                    added_count += 1
                else:
                    logger.warning(f"⚠️ Failed to add email for {user.email}: {message}")
            
            if added_count == 0:
                return False, "Nie udało się dodać żadnego emaila do kolejki"
            
            logger.info(f"✅ Added {added_count} emails to queue for campaign {campaign.id}")
            return True, f"Dodano {added_count} emaili do kolejki"
            
        except Exception as e:
            logger.error(f"❌ Error adding campaign to queue: {str(e)}")
            return False, f"Błąd dodawania kampanii do kolejki: {str(e)}"
    
    def _add_campaign_emails_to_queue(self, campaign, scheduled_at=None):
        """
        Dodaje emaile kampanii do kolejki EmailQueue
        
        Args:
            campaign: EmailCampaign object
            scheduled_at: datetime - kiedy wysłać (None = natychmiast)
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            from app.services.email_v2.queue.scheduler import EmailScheduler
            from app.models import EmailQueue
            import json
            
            logger = logging.getLogger(__name__)
            logger.info(f"📧 Dodaję emaile kampanii {campaign.id} do kolejki")
            
            # Pobierz odbiorców kampanii
            recipients = self._get_campaign_recipients(campaign)
            
            if not recipients:
                return False, "Brak odbiorców kampanii"
            
            # Pobierz szablon
            template = campaign.template
            if not template:
                return False, "Brak szablonu emaila"
            
            # Renderuj szablon
            from app.services.email_v2.templates.engine import EmailTemplateEngine
            template_engine = EmailTemplateEngine()
            
            added_count = 0
            
            for user in recipients:
                try:
                    # Przygotuj kontekst
                    context = {
                        'user': user,
                        'campaign': campaign,
                        'unsubscribe_url': f"https://klublepszezycie.pl/unsubscribe/{user.email}",
                        'site_url': 'https://klublepszezycie.pl'
                    }
                    
                    # Renderuj subject i content
                    rendered_subject = template_engine.render_template(template.subject, context)
                    rendered_html = template_engine.render_template(template.html_content, context)
                    rendered_text = template_engine.render_template(template.text_content, context)
                    
                    # Dodaj do kolejki
                    email_queue = EmailQueue(
                        recipient_email=user.email,
                        recipient_name=f"{user.first_name} {user.last_name}".strip(),
                        subject=rendered_subject,
                        html_content=rendered_html,
                        text_content=rendered_text,
                        priority=2,  # Priorytet kampanii
                        scheduled_at=scheduled_at or get_local_now(),
                        status='pending',
                        template_id=template.id,
                        template_name=template.name,
                        campaign_id=campaign.id,
                        context=json.dumps(context)
                    )
                    
                    db.session.add(email_queue)
                    added_count += 1
                    
                except Exception as e:
                    logger.warning(f"⚠️ Błąd dodawania emaila dla {user.email}: {e}")
                    continue
            
            db.session.commit()
            
            if added_count == 0:
                return False, "Nie udało się dodać żadnego emaila do kolejki"
            
            logger.info(f"✅ Dodano {added_count} emaili do kolejki dla kampanii {campaign.id}")
            return True, f"Dodano {added_count} emaili do kolejki"
            
        except Exception as e:
            logger.error(f"❌ Błąd dodawania kampanii do kolejki: {e}")
            return False, f"Błąd dodawania kampanii do kolejki: {str(e)}"
