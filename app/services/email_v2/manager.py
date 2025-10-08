"""
Nowy, prosty EmailManager - przepisany od nowa
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from app import db
from app.models import EmailTemplate, EmailQueue, EmailLog, User, EventSchedule, UserGroup, UserGroupMember
from app.utils.timezone_utils import get_local_now

class EmailManager:
    """
    Nowy, prosty menedżer systemu mailingu
    
    Zasady:
    1. Prosty i niezawodny
    2. Automatyczny fallback Mailgun → SMTP
    3. Kontrola duplikatów
    4. Logowanie wszystkich operacji
    """
    
    def __init__(self):
        """Inicjalizacja EmailManager"""
        self.logger = logging.getLogger(__name__)
        
        # Konfiguracja limitów
        self.daily_limit = int(os.getenv('EMAIL_DAILY_LIMIT', '1000'))
        
        # Inicjalizacja providerów
        self._mailgun_provider = None
        self._smtp_provider = None
        
        self.logger.info(f"📧 EmailManager zainicjalizowany - limit: {self.daily_limit}/dzień")
    
    def send_template_email(self, to_email: str, template_name: str, 
                   context: Dict = None, priority: int = 2, 
                   scheduled_at: datetime = None, campaign_id: int = None, 
                           event_id: int = None) -> Tuple[bool, str]:
        """
        Wysyła e-mail z szablonu
        
        Args:
            to_email: Adres e-mail odbiorcy
            template_name: Nazwa szablonu
            context: Kontekst dla zmiennych
            priority: Priorytet (1=wysoki, 2=normalny, 3=niski)
            scheduled_at: Data wysłania (opcjonalna)
            campaign_id: ID kampanii (opcjonalne)
            event_id: ID wydarzenia (opcjonalne)
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            self.logger.info(f"📧 Wysyłam e-mail do {to_email}: {template_name}")
            
            # Sprawdź dzienny limit
            if not self._check_daily_limit():
                return False, "Dzienny limit e-maili osiągnięty"
            
            # Sprawdź duplikaty
            if self._is_duplicate(to_email, template_name, event_id):
                return False, "Duplikat e-maila już istnieje w kolejce"
            
            # Pobierz szablon
            template = EmailTemplate.query.filter_by(name=template_name).first()
            if not template:
                return False, f"Szablon '{template_name}' nie został znaleziony"
            
            # Renderuj szablon
            html_content, text_content = self._render_template(template, context or {})
            
            # Renderuj subject
            rendered_subject = self._render_subject(template.subject, context or {})
            
            # Dodaj do kolejki
            return self._add_to_queue(
                to_email=to_email,
                subject=rendered_subject,
                html_content=html_content,
                text_content=text_content,
                priority=priority,
                scheduled_at=scheduled_at,
                context=context,
                campaign_id=campaign_id,
                event_id=event_id,
                template_id=template.id,
                template_name=template_name
            )
            
        except Exception as e:
            self.logger.error(f"❌ Błąd wysyłania szablonu: {e}")
            return False, f"Błąd wysyłania szablonu: {str(e)}"
    
    def send_event_reminders(self, event_id: int) -> Tuple[bool, str]:
        """
        Planuje przypomnienia o wydarzeniu (1h i 5min przed)
        
        Args:
            event_id: ID wydarzenia
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, "Wydarzenie nie zostało znalezione"
            
            # Zresetuj flagę przypomnień (usuniemy stare emaile i zaplanujemy nowe)
            event.reminders_scheduled = False
            
            # Usuń wszystkie stare emaile dla tego wydarzenia (pending i sent)
            old_emails = EmailQueue.query.filter_by(event_id=event_id).all()
            if old_emails:
                self.logger.info(f"🗑️ Usuwam {len(old_emails)} starych emaili dla wydarzenia {event_id}")
                for email in old_emails:
                    db.session.delete(email)
                db.session.commit()
                self.logger.info(f"✅ Usunięto {len(old_emails)} starych emaili")
            
            # Pobierz uczestników
            participants = self._get_event_participants(event_id)
            if not participants:
                return False, "Brak uczestników wydarzenia"
            
            # Zaplanuj przypomnienia
            scheduled_count = 0
            
            for participant in participants:
                # Przygotuj kontekst dla e-maili
                context = {
                    'user_name': participant.first_name or 'Użytkowniku',
                    'event_title': event.title,
                    'event_date': event.event_date.strftime('%d.%m.%Y'),
                    'event_time': event.event_date.strftime('%H:%M'),
                    'event_location': getattr(event, 'location', '') or 'Online',
                    'event_url': f"https://klublepszezycie.pl/events/{event_id}",
                    'event_id': event_id,
                    'user_id': participant.id
                }
                
                # Przypomnienie 1h przed
                send_time_1h = event.event_date - timedelta(hours=1)
                now = get_local_now()
                
                # Normalizuj timezone dla porównania
                if now.tzinfo is not None:
                    now_naive = now.replace(tzinfo=None)
                else:
                    now_naive = now
                    
                if send_time_1h.tzinfo is not None:
                    send_time_1h_naive = send_time_1h.replace(tzinfo=None)
                else:
                    send_time_1h_naive = send_time_1h
                
                # Jeśli czas już minął, wyślij za 1 minutę
                if send_time_1h_naive <= now_naive:
                    send_time_1h = now + timedelta(minutes=1)
                
                success, message = self.send_template_email(
                    to_email=participant.email,
                    template_name='event_reminder_1h',
                    context=context,
                    priority=1,
                    scheduled_at=send_time_1h,
                    event_id=event_id
                )
                
                if success:
                    scheduled_count += 1
                
                # Przypomnienie 5min przed
                send_time_5min = event.event_date - timedelta(minutes=5)
                
                # Normalizuj timezone dla porównania
                if send_time_5min.tzinfo is not None:
                    send_time_5min_naive = send_time_5min.replace(tzinfo=None)
                else:
                    send_time_5min_naive = send_time_5min
                
                # Jeśli czas już minął, wyślij za 2 minuty
                if send_time_5min_naive <= now_naive:
                    send_time_5min = now + timedelta(minutes=2)
                
                success, message = self.send_template_email(
                    to_email=participant.email,
                    template_name='event_reminder_5min',
                    context=context,
                    priority=1,
                    scheduled_at=send_time_5min,
                    event_id=event_id
                )
                    
                if success:
                    scheduled_count += 1
            
            # Oznacz jako zaplanowane
            if scheduled_count > 0:
                event.reminders_scheduled = True
                db.session.commit()
            
            return True, f"Zaplanowano {scheduled_count} przypomnień dla {len(participants)} uczestników"
            
        except Exception as e:
            self.logger.error(f"❌ Błąd planowania przypomnień: {e}")
            return False, f"Błąd planowania przypomnień: {str(e)}"
    
    def process_queue(self, limit: int = None) -> Dict[str, int]:
        """
        Przetwarza kolejkę e-maili
        
        Args:
            limit: Maksymalna liczba e-maili do przetworzenia
            
        Returns:
            Dict[str, int]: Statystyki przetwarzania
        """
        try:
            from app.services.email_v2.queue.processor import EmailQueueProcessor
            
            # Użyj EmailQueueProcessor
            processor = EmailQueueProcessor()
            return processor.process_queue(limit)
            
        except Exception as e:
            self.logger.error(f"❌ Błąd przetwarzania kolejki: {e}")
            return {'processed': 0, 'success': 0, 'failed': 0, 'error': str(e)}
    
    def get_stats(self) -> Dict[str, int]:
        """
        Pobiera statystyki kolejki e-maili
        
        Returns:
            Dict[str, int]: Statystyki kolejki
        """
        try:
            total = EmailQueue.query.count()
            pending = EmailQueue.query.filter_by(status='pending').count()
            failed = EmailQueue.query.filter_by(status='failed').count()
            processing = EmailQueue.query.filter_by(status='processing').count()
            sent = EmailQueue.query.filter_by(status='sent').count()
            
            return {
                'total': total,
                'pending': pending,
                'failed': failed,
                'processing': processing,
                'sent': sent
            }
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania statystyk: {e}")
            return {
                'total': 0,
                'pending': 0,
                'failed': 0,
                'processing': 0,
                'sent': 0
            }
    
    def _get_event_participants(self, event_id: int) -> List[User]:
        """Pobiera uczestników wydarzenia: członkowie klubu + członkowie grupy wydarzenia"""
        try:
            participants = set()  # Używamy set() aby uniknąć duplikatów
            
            # 1. Dodaj wszystkich członków klubu
            club_members = User.query.filter_by(club_member=True, is_active=True).all()
            for user in club_members:
                participants.add(user.id)
            
            # 2. Dodaj członków grupy wydarzenia (jeśli istnieje)
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
                    if user and user.is_active:
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
            self.logger.error(f"❌ Błąd pobierania uczestników: {e}")
            return []
    
    def _check_daily_limit(self, additional_emails: int = 1) -> bool:
        """Sprawdza dzienny limit e-maili"""
        try:
            today_start = get_local_now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Policz emaile wysłane dzisiaj
            sent_today = EmailQueue.query.filter(
                EmailQueue.status == 'sent',
                EmailQueue.sent_at >= today_start
            ).count()
            
            return (sent_today + additional_emails) <= self.daily_limit
            
        except Exception as e:
            self.logger.error(f"❌ Błąd sprawdzania limitu: {e}")
            return True  # W przypadku błędu, pozwól na wysłanie
    
    def _is_duplicate(self, to_email: str, template_name: str, event_id: int = None) -> bool:
        """Sprawdza czy e-mail nie jest duplikatem"""
        try:
            # Sprawdź czy w ostatnich 5 minutach nie było identycznego e-maila
            recent_cutoff = get_local_now() - timedelta(minutes=5)
            
            query = EmailQueue.query.filter(
                EmailQueue.recipient_email == to_email,
                EmailQueue.template_name == template_name,
                EmailQueue.created_at >= recent_cutoff
            )
            
            if event_id:
                query = query.filter(EmailQueue.event_id == event_id)
            
            return query.count() > 0
            
        except Exception as e:
            self.logger.error(f"❌ Błąd sprawdzania duplikatów: {e}")
            return False  # W przypadku błędu, nie blokuj wysyłki
    
    def _render_template(self, template: EmailTemplate, context: Dict) -> Tuple[str, str]:
        """Renderuje szablon e-maila"""
        try:
            from jinja2 import Template
            
            # Renderuj HTML
            html_template = Template(template.html_content or '')
            html_content = html_template.render(**context)
            
            # Renderuj tekst
            text_template = Template(template.text_content or '')
            text_content = text_template.render(**context)
            
            return html_content, text_content
            
        except Exception as e:
            self.logger.error(f"❌ Błąd renderowania szablonu: {e}")
            return template.html_content or '', template.text_content or ''
    
    def _render_subject(self, subject: str, context: Dict) -> str:
        """Renderuje subject e-maila z kontekstem"""
        try:
            from jinja2 import Template
            
            if not subject:
                return subject
                
            subject_template = Template(subject)
            return subject_template.render(**context)
            
        except Exception as e:
            self.logger.error(f"❌ Błąd renderowania subject: {e}")
            return subject  # Zwróć oryginalny subject w przypadku błędu
    
    def _add_to_queue(self, to_email: str, subject: str, html_content: str, 
                     text_content: str, priority: int, scheduled_at: datetime = None,
                     context: Dict = None, campaign_id: int = None, 
                     event_id: int = None, template_id: int = None,
                     template_name: str = None) -> Tuple[bool, str]:
        """Dodaje e-mail do kolejki"""
        try:
            if scheduled_at is None:
                scheduled_at = get_local_now()
            
            # Konwertuj context na JSON string
            import json
            context_json = json.dumps(context) if context else None
            
            email = EmailQueue(
                recipient_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                priority=priority,
                scheduled_at=scheduled_at,
                status='pending',
                context=context_json,
                campaign_id=campaign_id,
                event_id=event_id,
                template_id=template_id,
                template_name=template_name
            )
            
            db.session.add(email)
            db.session.commit()
            
            return True, f"E-mail dodany do kolejki (ID: {email.id})"
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"❌ Błąd dodawania do kolejki: {e}")
            return False, f"Błąd dodawania do kolejki: {str(e)}"
