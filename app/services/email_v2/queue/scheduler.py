"""
Planista e-maili - inteligentne planowanie i przypomnienia
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

from app import db
from app.models import EventSchedule, UserGroup, UserGroupMember, User, EmailQueue, EmailTemplate
from app.utils.timezone_utils import get_local_now

class EmailScheduler:
    """
    Inteligentny planista e-maili
    
    Funkcje:
    1. Planowanie przypomnień o wydarzeniach
    2. Planowanie kampanii e-mailowych
    3. Inteligentne rozłożenie w czasie
    4. Kontrola duplikatów
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Konfiguracja
        self.batch_size = int(os.getenv('EMAIL_BATCH_SIZE', '50'))
        self.delay_between_batches = float(os.getenv('EMAIL_BATCH_DELAY', '1.0'))
        self.max_emails_per_hour = int(os.getenv('EMAIL_MAX_PER_HOUR', '1000'))
    
    def schedule_event_reminders(self, event_id: int) -> Tuple[bool, str]:
        """
        Planuje przypomnienia o wydarzeniu
        
        Args:
            event_id: ID wydarzenia
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, "Wydarzenie nie zostało znalezione"
            
            # Sprawdź czy przypomnienia już zostały zaplanowane
            if event.reminders_scheduled:
                return True, "Przypomnienia już zostały zaplanowane"
            
            # Pobierz uczestników
            participants = self._get_event_participants(event_id)
            if not participants:
                return False, "Brak uczestników wydarzenia"
            
            # Oblicz łączną liczbę e-maili
            total_emails = len(participants) * 3  # 3 przypomnienia na osobę
            
            # Sprawdź czy nie przekraczamy limitów
            if not self._check_scheduling_limits(total_emails):
                return False, "Przekroczenie limitów planowania"
            
            # Zaplanuj przypomnienia
            scheduled_count = self._schedule_reminders(event, participants)
            
            # Oznacz jako zaplanowane
            event.reminders_scheduled = True
            db.session.commit()
            
            return True, f"Zaplanowano {scheduled_count} przypomnień dla {len(participants)} uczestników"
            
        except Exception as e:
            self.logger.error(f"❌ Błąd planowania przypomnień: {e}")
            return False, f"Błąd planowania przypomnień: {str(e)}"
    
    def schedule_campaign(self, campaign_id: int, recipients: List[str] = None, 
                         group_ids: List[int] = None, scheduled_at: datetime = None) -> Tuple[bool, str]:
        """
        Planuje kampanię e-mailową
        
        Args:
            campaign_id: ID kampanii
            recipients: Lista adresów e-mail
            group_ids: Lista ID grup
            scheduled_at: Data wysłania
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            # TODO: Implementacja kampanii
            return True, "Kampania zaplanowana"
            
        except Exception as e:
            self.logger.error(f"❌ Błąd planowania kampanii: {e}")
            return False, f"Błąd planowania kampanii: {str(e)}"
    
    def _get_event_participants(self, event_id: int) -> List[User]:
        """Pobiera uczestników wydarzenia"""
        try:
            participants = set()
            
            # Członkowie klubu
            club_group = UserGroup.query.filter_by(
                name="Członkowie klubu",
                group_type='club_members'
            ).first()
            
            if club_group:
                club_members = UserGroupMember.query.filter_by(
                    group_id=club_group.id,
                    is_active=True
                ).all()
                for member in club_members:
                    user = User.query.get(member.user_id)
                    if user and user.is_active:
                        participants.add(user)
            
            # Uczestnicy wydarzenia
            event_participants = User.query.filter_by(
                event_id=event_id,
                account_type='event_registration',
                is_active=True
            ).all()
            
            for participant in event_participants:
                participants.add(participant)
            
            return list(participants)
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania uczestników: {e}")
            return []
    
    def _check_scheduling_limits(self, total_emails: int) -> bool:
        """Sprawdza limity planowania"""
        try:
            # Sprawdź dzienny limit
            today_start = get_local_now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_sent = EmailQueue.query.filter(
                EmailQueue.scheduled_at >= today_start,
                EmailQueue.status.in_(['pending', 'processing', 'sent'])
            ).count()
            
            if today_sent + total_emails > 1000:  # Dzienny limit
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Błąd sprawdzania limitów: {e}")
            return False
    
    def _schedule_reminders(self, event: EventSchedule, participants: List[User]) -> int:
        """Planuje przypomnienia dla uczestników"""
        try:
            scheduled_count = 0
            
            # Typy przypomnień
            reminder_types = [
                {'hours': 24, 'template': 'event_reminder_24h'},
                {'hours': 1, 'template': 'event_reminder_1h'},
                {'minutes': 5, 'template': 'event_reminder_5min'}
            ]
            
            for participant in participants:
                for reminder in reminder_types:
                    # Oblicz czas wysłania
                    if 'hours' in reminder:
                        send_time = event.event_date - timedelta(hours=reminder['hours'])
                    else:
                        send_time = event.event_date - timedelta(minutes=reminder['minutes'])
                    
                    # Sprawdź czy nie jest za późno
                    if send_time <= get_local_now():
                        continue
                    
                    # Pobierz szablon
                    template = EmailTemplate.query.filter_by(
                        name=reminder['template'],
                        is_active=True
                    ).first()
                    
                    if not template:
                        self.logger.warning(f"⚠️ Szablon {reminder['template']} nie znaleziony")
                        continue
                    
                    # Przygotuj kontekst
                    context = {
                        'user_name': participant.first_name or 'Użytkowniku',
                        'event_title': event.title,
                        'event_date': event.event_date.strftime('%d.%m.%Y'),
                        'event_time': event.event_date.strftime('%H:%M'),
                        'event_location': event.location or 'Online',
                        'event_url': f"https://klublepszezycie.pl/events/{event.id}",
                        'event_datetime': event.event_date.strftime('%d.%m.%Y %H:%M'),
                        'event_description': event.description or ''
                    }
                    
                    # Dodaj linki do wypisania i usunięcia konta
                    try:
                        from app.services.unsubscribe_manager import unsubscribe_manager
                        context.update({
                            'unsubscribe_url': unsubscribe_manager.get_unsubscribe_url(participant.email),
                            'delete_account_url': unsubscribe_manager.get_delete_account_url(participant.email)
                        })
                    except Exception as e:
                        self.logger.warning(f"⚠️ Błąd generowania linków unsubscribe dla {participant.email}: {e}")
                        context.update({
                            'unsubscribe_url': 'mailto:kontakt@klublepszezycie.pl',
                            'delete_account_url': 'mailto:kontakt@klublepszezycie.pl'
                        })
                    
                    # Renderuj szablon
                    html_content = self._render_template(template.html_content, context)
                    text_content = self._render_template(template.text_content, context)
                    subject = self._render_template(template.subject, context)
                    
                    # Dodaj do kolejki
                    queue_item = EmailQueue(
                        recipient_email=participant.email,
                        subject=subject,
                        html_content=html_content,
                        text_content=text_content,
                        priority=1,  # Wysoki priorytet dla przypomnień
                        scheduled_at=send_time,
                        status='pending',
                        template_id=template.id,
                        event_id=event.id,
                        context=context
                    )
                    
                    db.session.add(queue_item)
                    scheduled_count += 1
            
            return scheduled_count
            
        except Exception as e:
            self.logger.error(f"❌ Błąd planowania przypomnień: {e}")
            return 0
    
    def _render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """Renderuje szablon z kontekstem"""
        try:
            if not template_content:
                return ""
            
            content = template_content
            for key, value in context.items():
                placeholder = f"{{{{{key}}}}}"
                content = content.replace(placeholder, str(value))
            
            return content
            
        except Exception as e:
            self.logger.error(f"❌ Błąd renderowania szablonu: {e}")
            return template_content or ""
