"""
Nowoczesny system powiadomień emailowych
- Asynchroniczne wysyłanie przez Mailgun
- Kolejka emaili z planowaniem
- Ochrona przed duplikatami
- Tokeny bezpieczeństwa
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging
from app import db
import asyncio
import aiohttp
import json
import os
from dataclasses import dataclass
from enum import Enum

from app.models import db, User, EventSchedule, UserGroup, UserGroupMember
from app.models.email_model import EmailQueue, EmailReminder
from app.utils.timezone_utils import get_local_now
from app.utils.crypto_utils import encrypt_email
from app.blueprints.public_controller import generate_unsubscribe_token

class NotificationType(Enum):
    """Typy powiadomień"""
    EVENT_REMINDER_24H = "event_reminder_24h"
    EVENT_REMINDER_1H = "event_reminder_1h"
    EVENT_REMINDER_5MIN = "event_reminder_5min"
    WELCOME = "welcome"
    PASSWORD_CHANGED = "password_changed"
    CLUB_MEMBER_WELCOME = "club_member_welcome"

@dataclass
class NotificationRecipient:
    """Odbiorca powiadomienia"""
    user_id: Optional[int]
    email: str
    name: str
    is_external: bool = False

@dataclass
class ScheduledNotification:
    """Zaplanowane powiadomienie"""
    recipient: NotificationRecipient
    notification_type: NotificationType
    context: Dict
    scheduled_at: datetime
    event_id: Optional[int] = None

class NotificationScheduler:
    """Planista powiadomień"""
    
    def __init__(self):
        self.base_url = os.getenv('BASE_URL', 'https://klublepszezycie.pl')
    
    def schedule_event_reminders(self, event_id: int) -> Tuple[bool, str]:
        """Planuje przypomnienia o wydarzeniu"""
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, "Wydarzenie nie zostało znalezione"
            
            # Znajdź uczestników wydarzenia
            participants = self._get_event_participants(event_id)
            if not participants:
                return False, "Brak uczestników wydarzenia"
            
            scheduled_count = 0
            now = get_local_now().replace(tzinfo=None)
            event_date = event.event_date
            
            for participant in participants:
                # Planuj przypomnienia
                reminders = self._calculate_reminders(event_date, now)
                
                for reminder_time, reminder_type in reminders:
                    # Sprawdź czy już nie zostało wysłane lub zaplanowane
                    if self._is_reminder_sent(participant.user_id, event_id, reminder_type, participant):
                        continue
                    
                    # Przygotuj kontekst
                    context = self._prepare_event_context(event, participant)
                    
                    # Zaplanuj powiadomienie
                    success = self._schedule_notification(
                        recipient=participant,
                        notification_type=NotificationType(reminder_type),
                        context=context,
                        scheduled_at=reminder_time,
                        event_id=event_id
                    )
                    
                    if success:
                        scheduled_count += 1
            
            return True, f"Zaplanowano {scheduled_count} przypomnień"
            
        except Exception as e:
            logging.error(f"Błąd planowania przypomnień: {str(e)}")
            return False, f"Błąd: {str(e)}"
    
    def _get_event_participants(self, event_id: int) -> List[NotificationRecipient]:
        """Pobiera uczestników wydarzenia (zapisanych + członków klubu)"""
        participants = []
        
        # 1. Znajdź uczestników konkretnego wydarzenia (event_based)
        event_groups = UserGroup.query.filter_by(group_type='event_based').all()
        
        for group in event_groups:
            try:
                criteria = json.loads(group.criteria) if group.criteria else {}
                group_event_id = criteria.get('event_id')
                
                if group_event_id == event_id:
                    members = UserGroupMember.query.filter_by(
                        group_id=group.id, 
                        is_active=True
                    ).all()
                    
                    for member in members:
                        if member.user_id:
                            user = User.query.get(member.user_id)
                            if user:
                                participants.append(NotificationRecipient(
                                    user_id=user.id,
                                    email=user.email,
                                    name=user.first_name or 'Użytkowniku'
                                ))
                        else:
                            # External member
                            participants.append(NotificationRecipient(
                                user_id=None,
                                email=member.email,
                                name=member.name or 'Użytkowniku',
                                is_external=True
                            ))
            except Exception as e:
                logging.warning(f"Błąd przetwarzania grupy wydarzenia {group.id}: {e}")
                continue
        
        # 2. Dodaj wszystkich członków klubu
        club_groups = UserGroup.query.filter_by(group_type='club_members').all()
        
        for group in club_groups:
            try:
                members = UserGroupMember.query.filter_by(
                    group_id=group.id, 
                    is_active=True
                ).all()
                
                for member in members:
                    if member.user_id:
                        user = User.query.get(member.user_id)
                        if user:
                            # Sprawdź czy już nie jest w liście (żeby uniknąć duplikatów)
                            if not any(p.user_id == user.id for p in participants):
                                participants.append(NotificationRecipient(
                                    user_id=user.id,
                                    email=user.email,
                                    name=user.first_name or 'Użytkowniku'
                                ))
                    else:
                        # External member - sprawdź czy już nie jest w liście
                        if not any(p.email == member.email for p in participants):
                            participants.append(NotificationRecipient(
                                user_id=None,
                                email=member.email,
                                name=member.name or 'Użytkowniku',
                                is_external=True
                            ))
            except Exception as e:
                logging.warning(f"Błąd przetwarzania grupy klubu {group.id}: {e}")
                continue
        
        return participants
    
    def _calculate_reminders(self, event_date: datetime, now: datetime) -> List[Tuple[datetime, str]]:
        """Oblicza czasy przypomnień"""
        reminders = []
        
        # 24h przed
        reminder_24h = event_date - timedelta(hours=24)
        if reminder_24h > now:
            reminders.append((reminder_24h, "event_reminder_24h"))
        
        # 1h przed
        reminder_1h = event_date - timedelta(hours=1)
        if reminder_1h > now:
            reminders.append((reminder_1h, "event_reminder_1h"))
        
        # 5min przed
        reminder_5min = event_date - timedelta(minutes=5)
        if reminder_5min > now:
            reminders.append((reminder_5min, "event_reminder_5min"))
        
        return reminders
    
    def _is_reminder_sent(self, user_id: Optional[int], event_id: int, reminder_type: str, participant: NotificationRecipient) -> bool:
        """Sprawdza czy przypomnienie już zostało wysłane lub zaplanowane"""
        # Sprawdź w EmailReminder (już wysłane)
        if user_id:
            existing_reminder = EmailReminder.query.filter_by(
                user_id=user_id,
                event_id=event_id,
                reminder_type=reminder_type
            ).first()
            if existing_reminder:
                return True
        
        # Sprawdź w EmailQueue (zaplanowane do wysłania)
        existing_queue = EmailQueue.query.filter_by(
            recipient_email=participant.email,
            template_name=reminder_type,
            status='pending'
        ).first()
        
        return existing_queue is not None
    
    def _prepare_event_context(self, event: EventSchedule, participant: NotificationRecipient) -> Dict:
        """Przygotowuje kontekst dla powiadomienia o wydarzeniu"""
        return {
            'user_name': participant.name,
            'event_title': event.title,
            'event_date': event.event_date.strftime('%d.%m.%Y'),
            'event_time': event.event_date.strftime('%H:%M'),
            'event_description': event.description or '',
            'event_location': event.location or 'Online',
            'meeting_link': event.meeting_link or '',
            'unsubscribe_url': '',  # Będzie ustawione przy wysyłaniu
            'delete_account_url': ''  # Będzie ustawione przy wysyłaniu
        }
    
    def _schedule_notification(self, recipient: NotificationRecipient, 
                             notification_type: NotificationType,
                             context: Dict, scheduled_at: datetime,
                             event_id: Optional[int] = None) -> bool:
        """Planuje powiadomienie w kolejce"""
        try:
            # Przygotuj szablon emaila
            template_name = notification_type.value
            
            # Utwórz rekord w kolejce
            email_queue = EmailQueue(
                recipient_email=recipient.email,
                recipient_name=recipient.name,
                subject=self._get_email_subject(notification_type, context),
                template_name=template_name,
                context=json.dumps(context),
                scheduled_at=scheduled_at,
                status='pending',
                priority=self._get_priority_for_template(template_name, scheduled_at),
                created_at=datetime.utcnow()
            )
            
            db.session.add(email_queue)
            db.session.commit()
            
            return True
            
        except Exception as e:
            logging.error(f"Błąd planowania powiadomienia: {e}")
            db.session.rollback()
            return False
    
    def _get_priority_for_template(self, template_name: str, scheduled_at: datetime) -> int:
        """Zwraca priorytet na podstawie szablonu i czasu wysyłki"""
        now = datetime.utcnow()
        time_until_send = (scheduled_at - now).total_seconds() / 3600  # w godzinach
        
        # Priorytet na podstawie czasu wysyłki - im wcześniej, tym wyższy priorytet
        if '24h' in template_name:
            return 1  # Najwyższy priorytet - wysyłany najwcześniej
        elif '1h' in template_name:
            return 2  # Średni priorytet - wysyłany później
        elif '5min' in template_name:
            return 3  # Najniższy priorytet - wysyłany najpóźniej
        else:
            # Dla innych typów - na podstawie czasu
            if time_until_send <= 1:
                return 1
            elif time_until_send <= 24:
                return 2
            else:
                return 3
    
    def _get_email_subject(self, notification_type: NotificationType, context: Dict) -> str:
        """Zwraca temat emaila na podstawie typu"""
        subjects = {
            NotificationType.EVENT_REMINDER_24H: f"Przypomnienie: {context['event_title']} jutro",
            NotificationType.EVENT_REMINDER_1H: f"Przypomnienie: {context['event_title']} za godzinę",
            NotificationType.EVENT_REMINDER_5MIN: f"Przypomnienie: {context['event_title']} za 5 minut",
            NotificationType.WELCOME: "Witamy w Klubie Lepsze Życie!",
            NotificationType.PASSWORD_CHANGED: "Hasło zostało zmienione",
            NotificationType.CLUB_MEMBER_WELCOME: "Witamy w gronie członków klubu!"
        }
        
        return subjects.get(notification_type, "Powiadomienie z Klubu Lepsze Życie")

class MailgunSender:
    """Asynchroniczny sender emaili przez Mailgun"""
    
    def __init__(self):
        self.mailgun_domain = os.getenv('MAILGUN_DOMAIN')
        self.mailgun_api_key = os.getenv('MAILGUN_API_KEY')
        self.batch_size = 1000  # Zwiększony limit - Mailgun obsługuje do 1000
        self.base_url = os.getenv('BASE_URL', 'https://klublepszezycie.pl')
        
        # Debug info
        if not self.mailgun_domain:
            logging.warning("MAILGUN_DOMAIN not set")
        if not self.mailgun_api_key:
            logging.warning("MAILGUN_API_KEY not set")
        if not self.base_url:
            logging.warning("BASE_URL not set, using default")
        self.max_batch_size = 1000  # Maksymalny rozmiar paczki
        self.min_batch_size = 100   # Minimalny rozmiar paczki
    
    def get_optimal_batch_size(self, queue_size: int) -> int:
        """Zwraca optymalny rozmiar paczki na podstawie rozmiaru kolejki"""
        if queue_size <= 100:
            return min(queue_size, self.min_batch_size)
        elif queue_size <= 1000:
            return min(queue_size, 500)
        elif queue_size <= 5000:
            return min(queue_size, self.max_batch_size)
        else:
            # Dla bardzo dużych kolejek - podziel na mniejsze paczki
            return self.max_batch_size
    
    async def send_batch(self, emails: List[EmailQueue]) -> Tuple[bool, str]:
        """Wysyła paczkę emaili przez Mailgun"""
        if not emails:
            return True, "Brak emaili do wysłania"
        
        try:
            # Przygotuj dane dla Mailgun
            mailgun_data = self._prepare_mailgun_batch(emails)
            
            # Wyślij przez Mailgun API
            success = await self._send_to_mailgun(mailgun_data)
            
            if success:
                # Oznacz jako wysłane
                self._mark_as_sent(emails)
                return True, f"Wysłano {len(emails)} emaili przez Mailgun"
            else:
                # Fallback do SMTP
                logging.warning("Mailgun failed, trying SMTP fallback...")
                from app.services.email_fallback_sender import EmailFallbackSender
                
                fallback_sender = EmailFallbackSender()
                fallback_success, fallback_message = await fallback_sender.send_batch(emails)
                
                if fallback_success:
                    # Oznacz jako wysłane
                    self._mark_as_sent(emails)
                    return True, f"Wysłano {len(emails)} emaili przez SMTP fallback"
                else:
                    return False, f"Błąd wysyłania przez Mailgun i SMTP: {fallback_message}"
                
        except Exception as e:
            logging.error(f"Błąd wysyłania paczki emaili: {e}")
            return False, f"Błąd: {str(e)}"
    
    def _prepare_mailgun_batch(self, emails: List[EmailQueue]) -> Dict:
        """Przygotowuje dane dla Mailgun API"""
        batch_data = {
            'from': f"Klub Lepsze Życie <noreply@{self.mailgun_domain}>",
            'to': [],
            'subject': [],
            'html': [],
            'text': [],
            'vars': {}
        }
        
        for i, email in enumerate(emails):
            # Przygotuj kontekst z tokenami
            context = json.loads(email.context)
            self._add_security_tokens(context, email.recipient_email)
            
            # Renderuj szablon
            html_content, text_content = self._render_template(
                email.template_name, 
                context
            )
            
            batch_data['to'].append(email.recipient_email)
            batch_data['subject'].append(email.subject)
            batch_data['html'].append(html_content)
            batch_data['text'].append(text_content)
            
            # Dodaj zmienne per email
            batch_data['vars'][f'email_{i}'] = context
        
        return batch_data
    
    def _add_security_tokens(self, context: Dict, email: str):
        """Dodaje tokeny bezpieczeństwa do kontekstu - nowy system v2"""
        from app.services.unsubscribe_manager import unsubscribe_manager
        
        unsubscribe_url = unsubscribe_manager.get_unsubscribe_url(email)
        delete_account_url = unsubscribe_manager.get_delete_account_url(email)
        
        context['unsubscribe_url'] = unsubscribe_url
        context['delete_account_url'] = delete_account_url
    
    def _render_template(self, template_name: str, context: Dict) -> Tuple[str, str]:
        """Renderuje szablon emaila"""
        # TODO: Implementować renderowanie szablonów
        # Na razie zwróć podstawowe szablony
        return (
            f"<h1>{context.get('user_name', 'Użytkowniku')}</h1>",
            f"Witaj {context.get('user_name', 'Użytkowniku')}"
        )
    
    async def _send_to_mailgun(self, data: Dict) -> bool:
        """Wysyła dane do Mailgun API"""
        try:
            if not self.mailgun_domain or not self.mailgun_api_key:
                logging.error("Mailgun configuration missing: domain or API key not set")
                return False
                
            url = f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages"
            
            logging.info(f"Sending to Mailgun: {url}")
            logging.info(f"Data keys: {list(data.keys())}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    auth=aiohttp.BasicAuth('api', self.mailgun_api_key),
                    data=data
                ) as response:
                    response_text = await response.text()
                    logging.info(f"Mailgun response status: {response.status}")
                    logging.info(f"Mailgun response: {response_text}")
                    
                    if response.status == 200:
                        return True
                    else:
                        logging.error(f"Mailgun API error: {response.status} - {response_text}")
                        return False
                    
        except Exception as e:
            logging.error(f"Błąd API Mailgun: {e}")
            return False
    
    def _mark_as_sent(self, emails: List[EmailQueue]):
        """Oznacza emaile jako wysłane"""
        try:
            for email in emails:
                email.status = 'sent'
                email.sent_at = datetime.utcnow()
                
                # Dodaj rekord EmailReminder dla przypomnień o wydarzeniach
                if 'event_reminder' in email.template_name:
                    context = json.loads(email.context)
                    # TODO: Znajdź event_id z kontekstu
                    # reminder = EmailReminder(...)
                    # db.session.add(reminder)
            
            db.session.commit()
            
        except Exception as e:
            logging.error(f"Błąd oznaczania jako wysłane: {e}")
            db.session.rollback()

class NotificationProcessor:
    """Główny procesor powiadomień"""
    
    def __init__(self):
        self.scheduler = NotificationScheduler()
        self.sender = MailgunSender()
    
    def process_event_reminders(self) -> Tuple[bool, str]:
        """Przetwarza przypomnienia o wydarzeniach"""
        try:
            # Znajdź wydarzenia w najbliższych 25 godzinach
            now = get_local_now().replace(tzinfo=None)
            events = EventSchedule.query.filter(
                EventSchedule.is_active == True,
                EventSchedule.is_published == True,
                EventSchedule.event_date > now,
                EventSchedule.event_date <= now + timedelta(hours=25)
            ).all()
            
            processed_count = 0
            
            for event in events:
                success, message = self.scheduler.schedule_event_reminders(event.id)
                if success:
                    processed_count += 1
            
            return True, f"Przetworzono {processed_count} wydarzeń"
            
        except Exception as e:
            logging.error(f"Błąd przetwarzania przypomnień: {e}")
            return False, f"Błąd: {str(e)}"
    
    async def process_email_queue(self) -> Tuple[bool, str]:
        """Przetwarza kolejkę emaili z dynamicznym rozmiarem paczki"""
        try:
            # Najpierw przetwórz zaplanowane kampanie
            campaigns_result = self.process_scheduled_campaigns()
            if campaigns_result[0]:  # Jeśli sukces
                logging.info(f"Zaplanowane kampanie: {campaigns_result[1]}")
            
            # Pobierz emaile do wysłania
            now = datetime.utcnow()
            all_pending = EmailQueue.query.filter(
                EmailQueue.status == 'pending',
                EmailQueue.scheduled_at <= now
            ).order_by(EmailQueue.priority.asc(), EmailQueue.scheduled_at.asc()).all()
            
            if not all_pending:
                return True, "Brak emaili do wysłania"
            
            # Określ optymalny rozmiar paczki
            queue_size = len(all_pending)
            batch_size = self.sender.get_optimal_batch_size(queue_size)
            
            # Pobierz emaile do wysłania (limit)
            pending_emails = all_pending[:batch_size]
            
            logging.info(f"Przetwarzanie {len(pending_emails)} emaili z {queue_size} w kolejce (batch size: {batch_size})")
            
            # Wyślij paczkę
            success, message = await self.sender.send_batch(pending_emails)
            
            return success, message
            
        except Exception as e:
            logging.error(f"Błąd przetwarzania kolejki: {e}")
            return False, f"Błąd: {str(e)}"
    
    def process_scheduled_campaigns(self) -> Tuple[bool, str]:
        """Przetwarza zaplanowane kampanie emailowe"""
        try:
            from app.models.email_model import EmailCampaign, UserGroupMember
            from app.models.user_model import User
            
            # Znajdź kampanie zaplanowane do wysłania
            # Tylko kampanie które są 'scheduled' (nie draft) i mają datę w przeszłości
            now = datetime.utcnow()
            scheduled_campaigns = EmailCampaign.query.filter(
                EmailCampaign.status == 'scheduled',
                EmailCampaign.scheduled_at <= now
            ).all()
            
            if not scheduled_campaigns:
                return True, "Brak zaplanowanych kampanii do wysłania"
            
            processed_count = 0
            
            for campaign in scheduled_campaigns:
                try:
                    # Pobierz odbiorców z grup
                    recipient_groups = json.loads(campaign.recipient_groups) if campaign.recipient_groups else []
                    recipients = []
                    
                    for group_id in recipient_groups:
                        members = UserGroupMember.query.filter_by(
                            group_id=group_id, 
                            is_active=True
                        ).all()
                        
                        for member in members:
                            if member.user_id:
                                user = User.query.get(member.user_id)
                                if user:
                                    recipients.append({
                                        'email': user.email,
                                        'name': user.first_name or 'Użytkowniku',
                                        'user_id': user.id
                                    })
                            else:
                                # External member
                                recipients.append({
                                    'email': member.email,
                                    'name': member.name or 'Użytkowniku',
                                    'user_id': None
                                })
                    
                    # Dodaj emaile do kolejki
                    for recipient in recipients:
                        queue_item = EmailQueue(
                            campaign_id=campaign.id,
                            template_id=campaign.template_id,
                            recipient_email=recipient['email'],
                            recipient_name=recipient['name'],
                            template_name=f'campaign_{campaign.id}',
                            subject=campaign.subject,
                            html_content=campaign.html_content,
                            text_content=campaign.text_content,
                            context=campaign.content_variables,
                            status='pending',
                            priority=2,  # Normal priority for campaigns
                            scheduled_at=now
                        )
                        db.session.add(queue_item)
                    
                    # Oznacz kampanię jako wysyłaną
                    campaign.status = 'sending'
                    campaign.sent_at = now
                    
                    processed_count += 1
                    
                except Exception as e:
                    logging.error(f"Błąd przetwarzania kampanii {campaign.id}: {e}")
                    campaign.status = 'failed'
                    continue
            
            db.session.commit()
            
            logging.info(f"Przetworzono {processed_count} zaplanowanych kampanii")
            return True, f"Przetworzono {processed_count} kampanii"
            
        except Exception as e:
            logging.error(f"Błąd przetwarzania zaplanowanych kampanii: {e}")
            db.session.rollback()
            return False, f"Błąd: {str(e)}"
    
    def update_event_notifications(self, event_id: int, new_event_date: datetime) -> Tuple[bool, str]:
        """Aktualizuje powiadomienia dla wydarzenia po zmianie godziny"""
        try:
            from app.models.email_model import EmailQueue
            from datetime import timedelta
            
            # Znajdź wszystkie powiadomienia dla tego wydarzenia
            notifications = EmailQueue.query.filter(
                EmailQueue.template_name.like('event_reminder%'),
                EmailQueue.status == 'pending'
            ).all()
            
            updated_count = 0
            
            for notification in notifications:
                # Oblicz nowy czas wysyłki na podstawie typu powiadomienia
                if '24h' in notification.template_name:
                    new_scheduled_time = new_event_date - timedelta(hours=24)
                elif '1h' in notification.template_name:
                    new_scheduled_time = new_event_date - timedelta(hours=1)
                elif '5min' in notification.template_name:
                    new_scheduled_time = new_event_date - timedelta(minutes=5)
                else:
                    continue  # Nieznany typ powiadomienia
                
                # Aktualizuj czas wysyłki
                notification.scheduled_at = new_scheduled_time
                updated_count += 1
            
            # Zapisz zmiany
            db.session.commit()
            
            logging.info(f"Zaktualizowano {updated_count} powiadomień dla wydarzenia {event_id}")
            return True, f"Zaktualizowano {updated_count} powiadomień"
            
        except Exception as e:
            logging.error(f"Błąd aktualizacji powiadomień dla wydarzenia {event_id}: {str(e)}")
            db.session.rollback()
            return False, f"Błąd: {str(e)}"
    
    def get_queue_stats(self) -> Dict:
        """Zwraca statystyki kolejki emaili"""
        try:
            from app.models.email_model import EmailQueue
            from datetime import datetime, timedelta
            
            now = datetime.utcnow()
            
            # Podstawowe statystyki
            total_emails = EmailQueue.query.count()
            pending_emails = EmailQueue.query.filter_by(status='pending').count()
            sent_emails = EmailQueue.query.filter_by(status='sent').count()
            failed_emails = EmailQueue.query.filter_by(status='failed').count()
            
            # Emails do wysłania teraz
            ready_to_send = EmailQueue.query.filter(
                EmailQueue.status == 'pending',
                EmailQueue.scheduled_at <= now
            ).count()
            
            # Emails do wysłania w najbliższej godzinie
            next_hour = now + timedelta(hours=1)
            upcoming_emails = EmailQueue.query.filter(
                EmailQueue.status == 'pending',
                EmailQueue.scheduled_at > now,
                EmailQueue.scheduled_at <= next_hour
            ).count()
            
            # Szacowany czas wysyłki
            if ready_to_send > 0:
                batch_size = self.sender.get_optimal_batch_size(ready_to_send)
                estimated_batches = (ready_to_send + batch_size - 1) // batch_size
                estimated_time_minutes = estimated_batches * 0.5  # 30 sekund na paczkę
            else:
                estimated_batches = 0
                estimated_time_minutes = 0
            
            return {
                'total_emails': total_emails,
                'pending_emails': pending_emails,
                'sent_emails': sent_emails,
                'failed_emails': failed_emails,
                'ready_to_send': ready_to_send,
                'upcoming_emails': upcoming_emails,
                'estimated_batches': estimated_batches,
                'estimated_time_minutes': estimated_time_minutes,
                'queue_health': self._assess_queue_health(ready_to_send, upcoming_emails)
            }
            
        except Exception as e:
            logging.error(f"Błąd pobierania statystyk kolejki: {e}")
            return {}
    
    def _assess_queue_health(self, ready_to_send: int, upcoming_emails: int) -> str:
        """Ocenia stan zdrowia kolejki"""
        total_backlog = ready_to_send + upcoming_emails
        
        if total_backlog == 0:
            return "healthy"
        elif total_backlog <= 1000:
            return "good"
        elif total_backlog <= 5000:
            return "warning"
        else:
            return "critical"

# Funkcje pomocnicze dla kompatybilności
def process_event_reminders() -> Tuple[bool, str]:
    """Funkcja kompatybilności z istniejącym kodem"""
    processor = NotificationProcessor()
    return processor.process_event_reminders()

async def process_email_queue() -> Tuple[bool, str]:
    """Funkcja kompatybilności z istniejącym kodem"""
    processor = NotificationProcessor()
    return await processor.process_email_queue()
