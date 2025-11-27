"""
Email Scheduler - Inteligentne planowanie emaili (v3 - przepisany)

System obsługuje 4 typy emaili:
1. Kampanie natychmiastowe - priorytet 2, wysyłka natychmiast
2. Kampanie planowane - priorytet 2, wysyłka według scheduled_at
3. Powiadomienia o wydarzeniach - priorytet 1, wysyłka 24h/1h/5min przed wydarzeniem
4. Inne maile systemowe - priorytet 0 (najwyższy), wysyłka natychmiast
"""
import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

from app import db
from app.models import (
    EventSchedule, UserGroup, UserGroupMember, User, 
    EmailQueue, EmailTemplate, EmailCampaign, EmailReminder
)
from app.utils.timezone_utils import get_local_now


class EmailScheduler:
    """
    Nowy Email Scheduler v3 - prosty i niezawodny
    
    Zasady:
    - Wszystkie emaile dodawane do EmailQueue od razu
    - Priorytetyzacja: 0 (system) > 1 (wydarzenia) > 2 (kampanie)
    - Inteligentne wyliczanie przypomnień o wydarzeniach
    - Automatyczna kontrola duplikatów
    """
    
    # Konfiguracja przypomnień o wydarzeniach
    REMINDER_OFFSETS = {
        '24h': timedelta(hours=24),
        '1h': timedelta(hours=1),
        '5min': timedelta(minutes=5)
    }
    
    # Priorytety emaili
    PRIORITY_SYSTEM = 0      # Reset hasła, powitania, alerty
    PRIORITY_EVENT = 1       # Przypomnienia o wydarzeniach
    PRIORITY_CAMPAIGN = 2    # Kampanie emailowe
    
    def __init__(self):
        """Inicjalizacja EmailScheduler"""
        self.logger = logging.getLogger(__name__)
        self.daily_limit = int(os.getenv('EMAIL_DAILY_LIMIT', '10000'))
        
        self.logger.info("📧 EmailScheduler v3 zainicjalizowany")
    
    def schedule_immediate_email(self, to_email: str, template_name: str, 
                                context: Dict = None, email_type: str = 'system',
                                event_id: int = None) -> Tuple[bool, str]:
        """
        Planuje wysyłkę emaila natychmiastowego (typ 1 i 4)
        
        Args:
            to_email: Adres email odbiorcy
            template_name: Nazwa szablonu email
            context: Kontekst dla zmiennych w szablonie
            email_type: Typ emaila ('system' lub 'other')
            event_id: ID wydarzenia (opcjonalne)
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            # Określ priorytet
            priority = self.PRIORITY_SYSTEM if email_type == 'system' else self.PRIORITY_CAMPAIGN
            
            # Pobierz szablon
            template = EmailTemplate.query.filter_by(
                name=template_name,
                is_active=True
            ).first()
            
            if not template:
                return False, f"Szablon '{template_name}' nie został znaleziony"
            
            # Renderuj szablon
            html_content, text_content = self._render_template(template, context or {})
            subject = self._render_subject(template.subject, context or {})
            
            # Dodaj do kolejki z natychmiastowym scheduled_at
            scheduled_at = get_local_now()
            
            success, message, queue_id = self._add_to_queue(
                recipient_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                priority=priority,
                scheduled_at=scheduled_at,
                template_id=template.id,
                template_name=template_name,
                event_id=event_id,
                context=context
            )
            
            if success:
                self.logger.info(f"✅ Email {template_name} zaplanowany dla {to_email} (priorytet {priority})")
            
            return success, message
            
        except Exception as e:
            self.logger.error(f"❌ Błąd planowania emaila natychmiastowego: {e}")
            return False, f"Błąd planowania emaila: {str(e)}"
    
    def schedule_campaign(self, campaign_id: int) -> Tuple[bool, str]:
        """
        Planuje wysyłkę kampanii emailowej (typ 1 i 2)
        
        Args:
            campaign_id: ID kampanii
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            # Pobierz kampanię
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return False, f"Kampania {campaign_id} nie została znaleziona"
            
            # Sprawdź czy kampania nie jest już wysłana
            if campaign.status in ['sent', 'sending']:
                return False, f"Kampania {campaign_id} jest już w trakcie wysyłki lub wysłana"
            
            # Pobierz odbiorców
            recipients = self._get_campaign_recipients(campaign)
            if not recipients:
                return False, "Brak odbiorców kampanii"
            
            # Określ scheduled_at
            if campaign.send_type == 'immediate':
                scheduled_at = get_local_now()
            else:  # scheduled
                scheduled_at = campaign.scheduled_at or get_local_now()
            
            # Pobierz szablon (jeśli istnieje)
            template = campaign.template if campaign.template_id else None
            
            # Przygotuj kontekst
            base_context = {}
            if campaign.content_variables:
                try:
                    base_context = json.loads(campaign.content_variables)
                except json.JSONDecodeError:
                    self.logger.warning(f"⚠️ Błąd parsowania zmiennych kampanii {campaign_id}")
            
            # Dodaj emaile do kolejki
            scheduled_count = 0
            for recipient in recipients:
                try:
                    # Przygotuj kontekst dla odbiorcy
                    recipient_context = base_context.copy()
                    recipient_context.update({
                        'user_name': recipient.first_name or 'Użytkowniku',
                        'user_email': recipient.email,
                        'campaign_name': campaign.name,
                        'message_subject': campaign.subject,
                        'message_content': campaign.html_content or campaign.text_content or '',
                        'admin_message': campaign.html_content or campaign.text_content or ''
                    })
                    
                    # Dodaj linki do wypisania
                    try:
                        from app.services.unsubscribe_manager import unsubscribe_manager
                        recipient_context.update({
                            'unsubscribe_url': unsubscribe_manager.get_unsubscribe_url(recipient.email),
                            'delete_account_url': unsubscribe_manager.get_delete_account_url(recipient.email)
                        })
                    except Exception as e:
                        self.logger.warning(f"⚠️ Błąd generowania linków unsubscribe: {e}")
                        recipient_context.update({
                            'unsubscribe_url': 'mailto:kontakt@klublepszezycie.pl',
                            'delete_account_url': 'mailto:kontakt@klublepszezycie.pl'
                        })
                    
                    # Jeśli jest szablon, użyj go
                    if template:
                        html_content, text_content = self._render_template(template, recipient_context)
                        subject = self._render_subject(template.subject, recipient_context)
                    else:
                        # Użyj treści z kampanii
                        html_content = campaign.html_content or ''
                        text_content = campaign.text_content or ''
                        subject = campaign.subject
                    
                    # Sprawdź duplikaty (dla kampanii używamy email, bo mogą być custom emails bez user_id)
                    duplicate_check_key = f"campaign_{campaign_id}_{recipient.email}"
                    
                    success, message, queue_id = self._add_to_queue(
                        recipient_email=recipient.email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                        priority=self.PRIORITY_CAMPAIGN,
                        scheduled_at=scheduled_at,
                        template_id=template.id if template else None,
                        template_name=template.name if template else None,
                        campaign_id=campaign_id,
                        context=recipient_context,
                        duplicate_check_key=duplicate_check_key,
                        user_id=recipient.id if hasattr(recipient, 'id') else None
                    )
                    
                    if success:
                        scheduled_count += 1
                        
                except Exception as e:
                    self.logger.error(f"❌ Błąd dodawania emaila dla {recipient.email}: {e}")
            
            # Aktualizuj status kampanii
            if scheduled_count > 0:
                campaign.status = 'scheduled' if campaign.send_type == 'scheduled' else 'ready'
                campaign.total_recipients = scheduled_count
                db.session.commit()
                
                self.logger.info(f"✅ Kampania {campaign_id}: zaplanowano {scheduled_count} emaili")
                return True, f"Zaplanowano {scheduled_count} emaili dla kampanii '{campaign.name}'"
            else:
                return False, "Nie udało się zaplanować żadnych emaili"
            
        except Exception as e:
            self.logger.error(f"❌ Błąd planowania kampanii {campaign_id}: {e}")
            return False, f"Błąd planowania kampanii: {str(e)}"
    
    def reschedule_event_reminders(self, event_id: int) -> Tuple[bool, str]:
        """
        Usuwa stare przypomnienia i planuje nowe (gdy admin zmienia datę wydarzenia)
        
        Args:
            event_id: ID wydarzenia
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            # Pobierz wydarzenie
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, f"Wydarzenie {event_id} nie zostało znalezione"
            
            self.logger.info(f"🔄 Rescheduling przypomnień dla wydarzenia: {event.title} (ID: {event_id})")
            
            # 1. Usuń stare przypomnienia z EmailQueue (pending)
            deleted_queue = EmailQueue.query.filter_by(
                event_id=event_id,
                status='pending'
            ).delete(synchronize_session=False)
            
            # 2. Usuń stare wpisy z EmailReminder
            deleted_reminders = EmailReminder.query.filter_by(
                event_id=event_id
            ).delete(synchronize_session=False)
            
            # 3. Zresetuj flagę
            event.reminders_scheduled = False
            db.session.commit()
            
            self.logger.info(f"🗑️ Usunięto {deleted_queue} emaili z kolejki i {deleted_reminders} wpisów EmailReminder")
            
            # 4. Zaplanuj nowe przypomnienia
            success, message = self.schedule_event_reminders(event_id)
            
            if success:
                return True, f"Rescheduling zakończony: {message} (usunięto {deleted_queue} starych emaili)"
            else:
                return False, f"Błąd reschedulingu: {message}"
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"❌ Błąd reschedulingu przypomnień: {e}")
            return False, f"Błąd reschedulingu: {str(e)}"
    
    def schedule_event_reminders(self, event_id: int, force: bool = False) -> Tuple[bool, str]:
        """
        Planuje przypomnienia o wydarzeniu (typ 3)
        
        Logika:
        - Jeśli do wydarzenia >= 24h: wysyła 3 przypomnienia (24h, 1h, 5min)
        - Jeśli do wydarzenia >= 1h: wysyła 2 przypomnienia (1h, 5min)
        - Jeśli do wydarzenia >= 5min: wysyła 1 przypomnienie (5min)
        - Jeśli do wydarzenia < 5min: nie wysyła nic
        
        Args:
            event_id: ID wydarzenia
            force: Jeśli True, pomija sprawdzenie flagi reminders_scheduled
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            # Pobierz wydarzenie
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, f"Wydarzenie {event_id} nie zostało znalezione"
            
            # Sprawdź czy przypomnienia już zostały zaplanowane (chyba że force=True)
            if not force and event.reminders_scheduled:
                return True, f"Przypomnienia dla wydarzenia '{event.title}' już zostały zaplanowane"
            
            # Pobierz uczestników
            participants = self._get_event_participants(event_id)
            if not participants:
                return False, "Brak uczestników wydarzenia"
            
            # Wylicz które przypomnienia wysłać
            now = get_local_now()
            # Normalizuj timezone
            now_naive = now.replace(tzinfo=None) if hasattr(now, 'tzinfo') and now.tzinfo else now
            event_date_naive = event.event_date.replace(tzinfo=None) if hasattr(event.event_date, 'tzinfo') and event.event_date.tzinfo else event.event_date
            
            time_until_event = event_date_naive - now_naive
            
            reminders_to_send = []
            if time_until_event >= timedelta(hours=24):
                reminders_to_send = ['24h', '1h', '5min']
            elif time_until_event >= timedelta(hours=1):
                reminders_to_send = ['1h', '5min']
            elif time_until_event >= timedelta(minutes=5):
                reminders_to_send = ['5min']
            else:
                self.logger.warning(f"⚠️ Wydarzenie {event.title} rozpoczyna się za mniej niż 5 minut - pomijam przypomnienia")
                return False, "Wydarzenie rozpoczyna się za mniej niż 5 minut"
            
            self.logger.info(f"📅 Wydarzenie '{event.title}': czas do rozpoczęcia: {time_until_event}, przypomnienia: {reminders_to_send}")
            
            # Cache szablonów po ID (wydajniejsze niż wielokrotne query po name)
            templates_cache = {}
            for reminder_type in reminders_to_send:
                template_name = f'event_reminder_{reminder_type}'
                template = EmailTemplate.query.filter_by(
                    name=template_name,
                    is_active=True
                ).first()
                
                if template:
                    templates_cache[reminder_type] = template
                else:
                    self.logger.warning(f"⚠️ Szablon {template_name} nie znaleziony")
            
            if not templates_cache:
                return False, "Brak aktywnych szablonów przypomnień"
            
            # Dodaj przypomnienia do kolejki
            scheduled_count = 0
            skipped_duplicates = 0
            
            for participant in participants:
                # Pomiń uczestników bez ID (tymczasowi użytkownicy)
                if not participant.id:
                    self.logger.warning(f"⚠️ Pomijam uczestnika bez ID: {participant.email}")
                    continue
                
                for reminder_type in reminders_to_send:
                    try:
                        # Sprawdź czy szablon istnieje
                        if reminder_type not in templates_cache:
                            continue
                        
                        template = templates_cache[reminder_type]
                        
                        # SPRAWDŹ DUPLIKAT w EmailReminder (user_id + event_id + reminder_type)
                        existing_reminder = EmailReminder.query.filter_by(
                            user_id=participant.id,
                            event_id=event_id,
                            reminder_type=reminder_type
                        ).first()
                        
                        if existing_reminder:
                            # Sprawdź czy powiązany email w kolejce nadal istnieje
                            if existing_reminder.email_queue_id:
                                existing_queue_item = EmailQueue.query.get(existing_reminder.email_queue_id)
                                
                                if existing_queue_item and existing_queue_item.status == 'pending':
                                    # Email nadal w kolejce - to prawdziwy duplikat
                                    self.logger.info(f"⏭️ Pomijam duplikat: user={participant.id}, event={event_id}, type={reminder_type} (email w kolejce)")
                                    skipped_duplicates += 1
                                    continue
                                else:
                                    # Email nie istnieje lub został wysłany - usuń stary reminder
                                    self.logger.info(f"🗑️ Usuwam stary EmailReminder (email {existing_reminder.email_queue_id} nie istnieje lub został wysłany)")
                                    db.session.delete(existing_reminder)
                                    db.session.flush()
                            else:
                                # Brak powiązanego emaila - usuń stary reminder
                                self.logger.info(f"🗑️ Usuwam stary EmailReminder (brak email_queue_id)")
                                db.session.delete(existing_reminder)
                                db.session.flush()
                        
                        # Wylicz scheduled_at
                        reminder_offset = self.REMINDER_OFFSETS[reminder_type]
                        scheduled_at_naive = event_date_naive - reminder_offset
                        
                        # Jeśli czas minął, POMIŃ (nie wysyłamy spóźnionych przypomnień)
                        if scheduled_at_naive <= now_naive:
                            self.logger.info(f"⏭️ Pomijam przypomnienie {reminder_type} dla user_id={participant.id} - czas minął")
                            continue
                        
                        # Przygotuj kontekst
                        # Generuj link śledzący dla tego użytkownika i wydarzenia
                        try:
                            from app.utils.event_link_tracker import event_link_tracker
                            tracking_url = event_link_tracker.get_tracking_url(
                                user_id=participant.id,
                                event_id=event_id,
                                original_url=event.get_event_url()
                            )
                            event_url = tracking_url if tracking_url else event.get_event_url()
                        except Exception as e:
                            self.logger.warning(f"⚠️ Błąd generowania linku śledzącego: {e}, używam domyślnego URL")
                            event_url = event.get_event_url()
                        
                        context = {
                            'user_name': participant.first_name or 'Użytkowniku',
                            'event_title': event.title,
                            'event_date': event.event_date.strftime('%d.%m.%Y'),
                            'event_time': event.event_date.strftime('%H:%M'),
                            'event_location': event.location or 'Online',
                            'event_url': event_url,
                            'event_datetime': event.event_date.strftime('%d.%m.%Y %H:%M'),
                            'event_description': event.description or ''
                        }
                        
                        # Dodaj linki do wypisania
                        try:
                            from app.services.unsubscribe_manager import unsubscribe_manager
                            context.update({
                                'unsubscribe_url': unsubscribe_manager.get_unsubscribe_url(participant.email),
                                'delete_account_url': unsubscribe_manager.get_delete_account_url(participant.email)
                            })
                        except Exception as e:
                            self.logger.warning(f"⚠️ Błąd generowania linków unsubscribe: {e}")
                            context.update({
                                'unsubscribe_url': 'mailto:kontakt@klublepszezycie.pl',
                                'delete_account_url': 'mailto:kontakt@klublepszezycie.pl'
                            })
                        
                        # Renderuj szablon
                        html_content, text_content = self._render_template(template, context)
                        subject = self._render_subject(template.subject, context)
                        
                        # Klucz duplikatu (użyj user_id zamiast email)
                        duplicate_check_key = f"event_reminder_{event_id}_{participant.id}_{template.id}_{reminder_type}"
                        
                        # Dodaj do kolejki
                        success, message, queue_id = self._add_to_queue(
                            recipient_email=participant.email,
                            subject=subject,
                            html_content=html_content,
                            text_content=text_content,
                            priority=self.PRIORITY_EVENT,
                            scheduled_at=scheduled_at_naive,
                            template_id=template.id,
                            template_name=template.name,
                            event_id=event_id,
                            context=context,
                            duplicate_check_key=duplicate_check_key,
                            user_id=participant.id
                        )
                        
                        if success:
                            # Dodaj wpis do EmailReminder (zapobieganie duplikatom)
                            email_reminder = EmailReminder(
                                user_id=participant.id,
                                event_id=event_id,
                                reminder_type=reminder_type,
                                email_queue_id=queue_id
                            )
                            db.session.add(email_reminder)
                            scheduled_count += 1
                            
                    except Exception as e:
                        self.logger.error(f"❌ Błąd dodawania przypomnienia {reminder_type} dla user_id={participant.id}: {e}")
            
            # Oznacz przypomnienia jako zaplanowane
            if scheduled_count > 0:
                event.reminders_scheduled = True
                db.session.commit()
                
                total_expected = len(participants) * len(reminders_to_send)
                message = f"Zaplanowano {scheduled_count} przypomnień dla {len(participants)} uczestników"
                if skipped_duplicates > 0:
                    message += f" (pominięto {skipped_duplicates} duplikatów)"
                
                self.logger.info(f"✅ Wydarzenie '{event.title}': {message}")
                return True, message
            else:
                return False, "Nie udało się zaplanować żadnych przypomnień"
            
        except Exception as e:
            self.logger.error(f"❌ Błąd planowania przypomnień o wydarzeniu {event_id}: {e}")
            return False, f"Błąd planowania przypomnień: {str(e)}"
    
    def _get_event_participants(self, event_id: int) -> List[User]:
        """
        Pobiera uczestników wydarzenia
        
        Uczestnicy = członkowie klubu + członkowie grupy wydarzenia
        """
        try:
            participants = set()  # Używamy set aby uniknąć duplikatów
            
            # 1. Członkowie klubu
            club_members = User.query.filter_by(
                club_member=True,
                is_active=True
            ).all()
            
            for user in club_members:
                if user.email:  # Tylko użytkownicy z emailem
                    participants.add(user.id)
            
            # 2. Członkowie grupy wydarzenia
            event_group = UserGroup.query.filter_by(
                group_type='event_based',
                event_id=event_id
            ).first()
            
            if event_group:
                group_members = UserGroupMember.query.filter_by(
                    group_id=event_group.id,
                    is_active=True
                ).all()
                
                for member in group_members:
                    user = User.query.get(member.user_id)
                    if user and user.is_active and user.email:
                        participants.add(user.id)
            
            # 3. Pobierz pełne obiekty użytkowników
            user_objects = []
            for user_id in participants:
                user = User.query.get(user_id)
                if user:
                    user_objects.append(user)
            
            self.logger.info(f"📊 Znaleziono {len(user_objects)} uczestników dla wydarzenia {event_id}")
            return user_objects
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania uczestników wydarzenia {event_id}: {e}")
            return []
    
    def _get_campaign_recipients(self, campaign: EmailCampaign) -> List[User]:
        """Pobiera odbiorców kampanii"""
        try:
            recipients = []
            
            if campaign.recipient_type == 'groups' and campaign.recipient_groups:
                # Odbiorcy z grup
                group_ids = json.loads(campaign.recipient_groups)
                for group_id in group_ids:
                    members = UserGroupMember.query.filter_by(
                        group_id=group_id,
                        is_active=True
                    ).all()
                    
                    for member in members:
                        user = User.query.get(member.user_id)
                        if user and user.is_active and user.email:
                            recipients.append(user)
            
            elif campaign.recipient_type == 'users' and campaign.recipient_users:
                # Konkretni użytkownicy
                user_ids = json.loads(campaign.recipient_users)
                for user_id in user_ids:
                    user = User.query.get(user_id)
                    if user and user.is_active and user.email:
                        recipients.append(user)
            
            elif campaign.recipient_type == 'custom' and campaign.custom_emails:
                # Niestandardowe emaile
                custom_emails = json.loads(campaign.custom_emails)
                for email in custom_emails:
                    # Utwórz tymczasowy obiekt użytkownika
                    temp_user = type('User', (), {
                        'email': email,
                        'first_name': email.split('@')[0],
                        'id': None
                    })()
                    recipients.append(temp_user)
            
            # Usuń duplikaty (po emailu)
            seen_emails = set()
            unique_recipients = []
            for recipient in recipients:
                if recipient.email not in seen_emails:
                    seen_emails.add(recipient.email)
                    unique_recipients.append(recipient)
            
            return unique_recipients
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania odbiorców kampanii: {e}")
            return []
    
    def _render_template(self, template: EmailTemplate, context: Dict) -> Tuple[str, str]:
        """Renderuje szablon HTML i tekstowy"""
        try:
            from jinja2 import Template
            
            # Renderuj HTML
            if template.html_content:
                html_template = Template(template.html_content)
                html_content = html_template.render(**context)
            else:
                html_content = ''
            
            # Renderuj tekst
            if template.text_content:
                text_template = Template(template.text_content)
                text_content = text_template.render(**context)
            else:
                text_content = ''
            
            return html_content, text_content
            
        except Exception as e:
            self.logger.error(f"❌ Błąd renderowania szablonu: {e}")
            return template.html_content or '', template.text_content or ''
    
    def _render_subject(self, subject: str, context: Dict) -> str:
        """Renderuje subject emaila"""
        try:
            if not subject:
                return subject
            
            from jinja2 import Template
            subject_template = Template(subject)
            return subject_template.render(**context)
            
        except Exception as e:
            self.logger.error(f"❌ Błąd renderowania subject: {e}")
            return subject
    
    def _add_to_queue(self, recipient_email: str, subject: str, html_content: str,
                     text_content: str, priority: int, scheduled_at: datetime,
                     template_id: int = None, template_name: str = None,
                     event_id: int = None, campaign_id: int = None,
                     context: Dict = None, duplicate_check_key: str = None,
                     user_id: int = None) -> Tuple[bool, str, int]:
        """
        Dodaje email do kolejki
        
        Returns:
            Tuple[bool, str, int]: (sukces, komunikat, queue_id)
        """
        try:
            # Sprawdź duplikaty
            if duplicate_check_key:
                existing = EmailQueue.check_duplicate(
                    recipient_email=recipient_email,
                    subject=subject,
                    duplicate_check_key=duplicate_check_key
                )
                
                if existing:
                    return False, f"Email już istnieje w kolejce (ID: {existing.id})", existing.id
            
            # Konwertuj context na JSON
            context_json = json.dumps(context) if context else None
            
            # Utwórz email queue
            email_queue = EmailQueue(
                recipient_email=recipient_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                priority=priority,
                scheduled_at=scheduled_at,
                status='pending',
                template_id=template_id,
                template_name=template_name,
                event_id=event_id,
                campaign_id=campaign_id,
                context=context_json,
                duplicate_check_key=duplicate_check_key
            )
            
            db.session.add(email_queue)
            db.session.flush()  # Flush aby otrzymać ID przed commit
            
            queue_id = email_queue.id
            
            return True, f"Email dodany do kolejki (ID: {queue_id})", queue_id
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"❌ Błąd dodawania do kolejki: {e}")
            return False, f"Błąd dodawania do kolejki: {str(e)}", None
