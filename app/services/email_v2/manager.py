"""
Główny EmailManager - jedyny punkt wejścia do systemu mailingu
Prosty, wydajny i niezawodny system wysyłania e-maili
"""
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from app import db
from app.models import EmailTemplate, EmailQueue, EmailLog, User, EventSchedule, UserGroup, UserGroupMember, DefaultEmailTemplate
from app.utils.timezone_utils import get_local_now

class EmailManager:
    """
    Główny menedżer systemu mailingu
    
    Zasady:
    1. JEDYNY punkt wejścia - wszystkie operacje przez tę klasę
    2. Automatyczna kontrola limitów - nie więcej niż 1000 maili dziennie
    3. Inteligentne sprawdzanie duplikatów - zapobiega nadmiarowym e-mailom
    4. Automatyczny fallback - Mailgun → SMTP
    5. Prosty API - łatwe w użyciu
    """
    
    def __init__(self):
        """Inicjalizacja EmailManager"""
        self.logger = logging.getLogger(__name__)
        
        # Konfiguracja limitów
        self.daily_limit = int(os.getenv('EMAIL_DAILY_LIMIT', '1000'))
        self.batch_size = int(os.getenv('EMAIL_BATCH_SIZE', '50'))
        self.rate_limit_delay = float(os.getenv('EMAIL_RATE_DELAY', '0.1'))  # 100ms
        
        # Inicjalizacja providerów
        self._mailgun_provider = None
        self._smtp_provider = None
        
        self.logger.info(f"📧 EmailManager zainicjalizowany - limit: {self.daily_limit}/dzień")
    
    # =============================================================================
    # PUBLIC API - GŁÓWNE METODY
    # =============================================================================
    
    
    def send_email(self, to_email: str, subject: str, html_content: str = None, 
                   text_content: str = None, template_name: str = None, 
                   context: Dict = None, priority: int = 2, 
                   scheduled_at: datetime = None, campaign_id: int = None, 
                   template_id: int = None) -> Tuple[bool, str]:
        """
        Wysyła pojedynczy e-mail
        
        Args:
            to_email: Adres e-mail odbiorcy
            subject: Temat e-maila
            html_content: Treść HTML (opcjonalna)
            text_content: Treść tekstowa (opcjonalna)
            template_name: Nazwa szablonu (opcjonalna)
            context: Kontekst dla zmiennych (opcjonalny)
            priority: Priorytet (1=wysoki, 2=normalny, 3=niski)
            scheduled_at: Data wysłania (opcjonalna)
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            self.logger.info(f"📧 Wysyłam e-mail do {to_email}: {subject}")
            
            # Sprawdź dzienny limit
            if not self._check_daily_limit():
                return False, "Dzienny limit e-maili osiągnięty"
            
            # Sprawdź duplikaty
            if self._is_duplicate(to_email, subject, html_content, text_content):
                return False, "Duplikat e-maila już istnieje w kolejce"
            
            # Pobierz szablon jeśli podano
            if template_name:
                html_content, text_content = self._render_template(template_name, context or {})
            
            # Dodaj do kolejki
            return self._add_to_queue(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                priority=priority,
                scheduled_at=scheduled_at,
                context=context,
                campaign_id=campaign_id,
                event_id=context.get('event_id') if context else None,
                template_id=template_id
            )
            
        except Exception as e:
            self.logger.error(f"❌ Błąd wysyłania e-maila: {e}")
            return False, f"Błąd wysyłania e-maila: {str(e)}"
    
    def send_template_email(self, to_email: str, template_name: str, 
                           context: Dict = None, priority: int = 2,
                           scheduled_at: datetime = None, campaign_id: int = None) -> Tuple[bool, str]:
        """
        Wysyła e-mail używając szablonu
        
        Args:
            to_email: Adres e-mail odbiorcy
            template_name: Nazwa szablonu
            context: Kontekst dla zmiennych
            priority: Priorytet
            scheduled_at: Data wysłania
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            # Pobierz szablon z EmailTemplate (edytowalne szablony użytkownika)
            template = EmailTemplate.query.filter_by(name=template_name, is_active=True).first()
            
            # Fallback do DefaultEmailTemplate jeśli nie ma w EmailTemplate
            if not template:
                template = DefaultEmailTemplate.query.filter_by(name=template_name, is_active=True).first()
            
            if not template:
                return False, f"Szablon '{template_name}' nie został znaleziony"
            
            # Renderuj szablon
            html_content, text_content = self._render_template(template_name, context or {})
            
            # Renderuj subject
            rendered_subject = template.subject or ""
            for key, value in (context or {}).items():
                placeholder = f"{{{{{key}}}}}"
                rendered_subject = rendered_subject.replace(placeholder, str(value))
            
            # Wyślij e-mail
            return self.send_email(
                to_email=to_email,
                subject=rendered_subject,
                html_content=html_content,
                text_content=text_content,
                priority=priority,
                scheduled_at=scheduled_at,
                campaign_id=campaign_id,
                template_id=template.id,
                context=context  # Przekaż context z event_id
            )
            
        except Exception as e:
            self.logger.error(f"❌ Błąd wysyłania szablonu: {e}")
            return False, f"Błąd wysyłania szablonu: {str(e)}"
    
    def send_event_reminders(self, event_id: int) -> Tuple[bool, str]:
        """
        Planuje przypomnienia o wydarzeniu (24h, 1h, 5min przed)
        
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
            
            # DODATKOWA KONTROLA: Sprawdź czy w kolejce już są emaile dla tego wydarzenia
            existing_emails = EmailQueue.query.filter_by(
                event_id=event_id,
                status='pending'
            ).count()
            
            if existing_emails > 0:
                self.logger.warning(f"⚠️ Wydarzenie {event_id} już ma {existing_emails} emaili w kolejce")
                return True, f"Wydarzenie już ma {existing_emails} emaili w kolejce"
            
            # Pobierz uczestników
            participants = self._get_event_participants(event_id)
            if not participants:
                return False, "Brak uczestników wydarzenia"
            
            # Inteligentny system przypomnień - automatycznie decyduje o liczbie
            reminder_types = self._determine_reminder_strategy(event)
            
            # Oblicz łączną liczbę e-maili na podstawie rzeczywistej strategii
            total_emails = len(participants) * len(reminder_types)
            
            # Sprawdź dzienny limit
            if not self._check_daily_limit(total_emails):
                return False, f"Przekroczenie dziennego limitu: {total_emails} e-maili"
            
            # Zaplanuj przypomnienia
            scheduled_count = 0
            
            # Pobierz czynniki wydarzenia dla logiki natychmiastowego wysyłania
            factors = self._analyze_event_factors(event)
            
            for participant in participants:
                for reminder in reminder_types:
                    # Oblicz czas wysłania
                    if 'hours' in reminder:
                        send_time = event.event_date - timedelta(hours=reminder['hours'])
                    else:
                        send_time = event.event_date - timedelta(minutes=reminder['minutes'])
                    
                    # Sprawdź czy nie jest za późno (porównaj timezone-naive)
                    now = get_local_now()
                    if now.tzinfo is not None:
                        now = now.replace(tzinfo=None)
                    if send_time.tzinfo is not None:
                        send_time_check = send_time.replace(tzinfo=None)
                    else:
                        send_time_check = send_time
                    
                    # Sprawdź czy czas wysłania nie minął
                    if send_time_check <= now:
                        continue
                    
                    # Przygotuj kontekst
                    context = {
                        'user_name': participant.first_name,
                        'event_title': event.title,
                        'event_date': event.event_date.strftime('%d.%m.%Y'),
                        'event_time': event.event_date.strftime('%H:%M'),
                        'event_location': event.location or 'Online',
                        'event_url': f"https://klublepszezycie.pl/events/{event_id}",
                        'event_id': event_id,
                        'user_id': participant.id
                    }
                    
                    # Wyślij przypomnienie
                    success, message = self.send_template_email(
                        to_email=participant.email,
                        template_name=reminder['template'],
                        context=context,
                        priority=1,  # Wysoki priorytet dla przypomnień
                        scheduled_at=send_time
                    )
                    
                    if success:
                        scheduled_count += 1
            
            # Oznacz jako zaplanowane tylko jeśli rzeczywiście wysłano emaile
            if scheduled_count > 0:
                event.reminders_scheduled = True
                db.session.commit()
            
            return True, f"Zaplanowano {scheduled_count} przypomnień dla {len(participants)} uczestników"
            
        except Exception as e:
            self.logger.error(f"❌ Błąd planowania przypomnień: {e}")
            return False, f"Błąd planowania przypomnień: {str(e)}"
    
    def send_event_reminders_for_new_members(self, event_id: int) -> Tuple[bool, str]:
        """
        Planuje przypomnienia o wydarzeniu TYLKO dla nowych członków grupy
        (nie sprawdza flagi reminders_scheduled)
        
        Args:
            event_id: ID wydarzenia
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, "Wydarzenie nie zostało znalezione"
            
            # Pobierz uczestników
            participants = self._get_event_participants(event_id)
            if not participants:
                return False, "Brak uczestników wydarzenia"
            
            # Sprawdź którzy uczestnicy już mają zaplanowane przypomnienia
            existing_reminders = EmailQueue.query.filter_by(
                event_id=event_id,
                status='pending'
            ).all()
            
            existing_emails = {reminder.recipient_email for reminder in existing_reminders}
            
            # Filtruj tylko nowych uczestników (którzy nie mają przypomnień)
            new_participants = [p for p in participants if p.email not in existing_emails]
            
            if not new_participants:
                return True, "Wszyscy uczestnicy już mają zaplanowane przypomnienia"
            
            # Inteligentny system przypomnień - automatycznie decyduje o liczbie
            reminder_types = self._determine_reminder_strategy(event)
            
            # Oblicz łączną liczbę e-maili na podstawie rzeczywistej strategii
            total_emails = len(new_participants) * len(reminder_types)
            
            # Sprawdź dzienny limit
            if not self._check_daily_limit(total_emails):
                return False, f"Przekroczenie dziennego limitu: {total_emails} e-maili"
            
            # Zaplanuj przypomnienia
            scheduled_count = 0
            
            # Pobierz czynniki wydarzenia dla logiki natychmiastowego wysyłania
            factors = self._analyze_event_factors(event)
            
            for participant in new_participants:
                for reminder in reminder_types:
                    # Oblicz czas wysłania
                    if 'hours' in reminder:
                        send_time = event.event_date - timedelta(hours=reminder['hours'])
                    else:
                        send_time = event.event_date - timedelta(minutes=reminder['minutes'])
                    
                    # Sprawdź czy nie jest za późno (porównaj timezone-naive)
                    now = get_local_now()
                    if now.tzinfo is not None:
                        now = now.replace(tzinfo=None)
                    if send_time.tzinfo is not None:
                        send_time_check = send_time.replace(tzinfo=None)
                    else:
                        send_time_check = send_time
                    
                    # Sprawdź czy czas wysłania nie minął
                    if send_time_check <= now:
                        continue
                    
                    # Przygotuj kontekst
                    context = {
                        'user_name': participant.first_name,
                        'event_title': event.title,
                        'event_date': event.event_date.strftime('%d.%m.%Y'),
                        'event_time': event.event_date.strftime('%H:%M'),
                        'event_location': event.location or 'Online',
                        'event_url': f"https://klublepszezycie.pl/events/{event_id}",
                        'event_id': event_id,
                        'user_id': participant.id
                    }
                    
                    # Wyślij przypomnienie
                    success, message = self.send_template_email(
                        to_email=participant.email,
                        template_name=reminder['template'],
                        context=context,
                        priority=1,  # Wysoki priorytet dla przypomnień
                        scheduled_at=send_time
                    )
                    
                    if success:
                        scheduled_count += 1
            
            return True, f"Zaplanowano {scheduled_count} przypomnień dla {len(new_participants)} nowych uczestników"
            
        except Exception as e:
            self.logger.error(f"❌ Błąd planowania przypomnień dla nowych członków: {e}")
            return False, f"Błąd planowania przypomnień dla nowych członków: {str(e)}"
    
    def send_campaign(self, campaign_id: int, recipients: List[str] = None, 
                     group_ids: List[int] = None, scheduled_at: datetime = None) -> Tuple[bool, str]:
        """
        Wysyła kampanię e-mailową
        
        Args:
            campaign_id: ID kampanii
            recipients: Lista adresów e-mail (opcjonalna)
            group_ids: Lista ID grup (opcjonalna)
            scheduled_at: Data wysłania (opcjonalna)
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            from app.models import EmailCampaign, UserGroup, UserGroupMember, User
            
            # Pobierz kampanię
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return False, "Kampania nie została znaleziona"
            
            # Sprawdź czy kampania już została wysłana
            if campaign.status == 'sent':
                return False, "Kampania już została wysłana"
            
            # Pobierz odbiorców
            all_recipients = set()
            
            # Dodaj bezpośrednich odbiorców
            if recipients:
                for email in recipients:
                    all_recipients.add(email)
            
            # Dodaj odbiorców z grup
            if group_ids:
                for group_id in group_ids:
                    group = UserGroup.query.get(group_id)
                    if group:
                        members = UserGroupMember.query.filter_by(
                            group_id=group_id,
                            is_active=True
                        ).all()
                        for member in members:
                            user = User.query.get(member.user_id)
                            if user and user.is_active and user.email:
                                all_recipients.add(user.email)
            
            if not all_recipients:
                return False, "Brak odbiorców kampanii"
            
            # Oblicz łączną liczbę e-maili
            total_emails = len(all_recipients)
            
            # Sprawdź dzienny limit
            if not self._check_daily_limit(total_emails):
                return False, f"Przekroczenie dziennego limitu: {total_emails} e-maili"
            
            # Zaplanuj e-maile
            scheduled_count = 0
            for email in all_recipients:
                success, message = self.send_email(
                    to_email=email,
                    subject=campaign.subject,
                    html_content=campaign.html_content,
                    text_content=campaign.text_content,
                    priority=2,  # Normalny priorytet dla kampanii
                    scheduled_at=scheduled_at,
                    campaign_id=campaign_id  # Przekaż campaign_id
                )
                
                if success:
                    scheduled_count += 1
            
            # Oznacz kampanię jako zaplanowaną
            campaign.status = 'scheduled'
            if scheduled_at:
                campaign.scheduled_at = scheduled_at
            else:
                campaign.scheduled_at = get_local_now()
            
            db.session.commit()
            
            return True, f"Zaplanowano {scheduled_count} e-maili kampanii dla {total_emails} odbiorców"
            
        except Exception as e:
            self.logger.error(f"❌ Błąd wysyłania kampanii: {e}")
            return False, f"Błąd wysyłania kampanii: {str(e)}"
    
    def create_campaign(self, name: str, subject: str, html_content: str = None, 
                       text_content: str = None, description: str = None) -> Tuple[bool, str, int]:
        """
        Tworzy nową kampanię e-mailową
        
        Args:
            name: Nazwa kampanii
            subject: Temat e-maila
            html_content: Treść HTML
            text_content: Treść tekstowa
            description: Opis kampanii (ignorowane - EmailCampaign nie ma tego pola)
            
        Returns:
            Tuple[bool, str, int]: (sukces, komunikat, campaign_id)
        """
        try:
            from app.models import EmailCampaign
            
            # Sprawdź czy kampania o takiej nazwie już istnieje
            existing = EmailCampaign.query.filter_by(name=name).first()
            if existing:
                return False, f"Kampania o nazwie '{name}' już istnieje", 0
            
            # Utwórz kampanię (bez description - EmailCampaign nie ma tego pola)
            campaign = EmailCampaign(
                name=name,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                status='draft'
            )
            
            db.session.add(campaign)
            db.session.commit()
            
            return True, f"Kampania '{name}' została utworzona", campaign.id
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"❌ Błąd tworzenia kampanii: {e}")
            return False, f"Błąd tworzenia kampanii: {str(e)}", 0
    
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
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Pobiera statystyki systemu
        
        Returns:
            Dict[str, Any]: Statystyki
        """
        try:
            today_start = get_local_now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Pobierz statystyki z kolejki
            pending = EmailQueue.query.filter_by(status='pending').count()
            processing = EmailQueue.query.filter_by(status='processing').count()
            failed = EmailQueue.query.filter_by(status='failed').count()
            sent = EmailQueue.query.filter_by(status='sent').count()
            total = pending + processing + failed + sent
            
            # Pobierz statystyki z logów
            sent_today = EmailLog.query.filter(
                EmailLog.sent_at >= today_start,
                EmailLog.status == 'sent'
            ).count()
            
            return {
                'total': total,
                'pending': pending,
                'processing': processing,
                'failed': failed,
                'sent': sent,
                'daily_limit': self.daily_limit,
                'sent_today': sent_today
            }
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania statystyk: {e}")
            return {'error': str(e)}
    
    # =============================================================================
    # PRIVATE METHODS - WEWNĘTRZNE METODY
    # =============================================================================
    
    def _check_daily_limit(self, additional_emails: int = 0) -> bool:
        """Sprawdza dzienny limit e-maili"""
        try:
            today_start = get_local_now().replace(hour=0, minute=0, second=0, microsecond=0)
            sent_today = EmailLog.query.filter(
                EmailLog.sent_at >= today_start,
                EmailLog.status == 'sent'
            ).count()
            
            return (sent_today + additional_emails) <= self.daily_limit
            
        except Exception as e:
            self.logger.error(f"❌ Błąd sprawdzania limitu: {e}")
            return False
    
    def _is_duplicate(self, to_email: str, subject: str, 
                     html_content: str, text_content: str) -> bool:
        """Sprawdza czy e-mail już istnieje w kolejce"""
        try:
            # Sprawdź czy istnieje identyczny e-mail w kolejce
            existing = EmailQueue.query.filter(
                EmailQueue.recipient_email == to_email,
                EmailQueue.subject == subject,
                EmailQueue.status.in_(['pending', 'processing'])
            ).first()
            
            return existing is not None
            
        except Exception as e:
            self.logger.error(f"❌ Błąd sprawdzania duplikatów: {e}")
            return False
    
    def _render_template(self, template_name: str, context: Dict) -> Tuple[str, str]:
        """Renderuje szablon e-maila"""
        try:
            # Pobierz szablon z EmailTemplate (edytowalne szablony użytkownika)
            template = EmailTemplate.query.filter_by(name=template_name, is_active=True).first()
            
            # Fallback do DefaultEmailTemplate jeśli nie ma w EmailTemplate
            if not template:
                template = DefaultEmailTemplate.query.filter_by(name=template_name, is_active=True).first()
            
            if not template:
                raise ValueError(f"Szablon '{template_name}' nie został znaleziony")
            
            # Proste zastępowanie zmiennych
            html_content = template.html_content or ""
            text_content = template.text_content or ""
            
            for key, value in (context or {}).items():
                placeholder = f"{{{{{key}}}}}"
                html_content = html_content.replace(placeholder, str(value))
                text_content = text_content.replace(placeholder, str(value))
            
            return html_content, text_content
            
        except Exception as e:
            self.logger.error(f"❌ Błąd renderowania szablonu: {e}")
            return "", ""
    
    def _add_to_queue(self, to_email: str, subject: str, html_content: str, 
                     text_content: str, priority: int, scheduled_at: datetime, 
                     context: Dict, campaign_id: int = None, event_id: int = None, 
                     template_id: int = None) -> Tuple[bool, str]:
        """Dodaje e-mail do kolejki - IDENTYCZNIE w trybie testowym i produkcyjnym"""
        try:
            # Sprawdź duplikaty PRZED dodaniem do kolejki (w obu trybach)
            if self._is_duplicate(to_email, subject, html_content, text_content):
                return False, "Duplikat e-maila już istnieje w kolejce"
            
            # Sprawdź czy nie jest za późno na wysłanie
            now = get_local_now()
            if scheduled_at:
                # Normalizuj timezone dla porównania
                if now.tzinfo is not None:
                    now = now.replace(tzinfo=None)
                if scheduled_at.tzinfo is not None:
                    scheduled_at_check = scheduled_at.replace(tzinfo=None)
                else:
                    scheduled_at_check = scheduled_at
                
                # Dla wydarzeń za mniej niż 24h - pozwól na wysłanie natychmiast
                # (scheduled_at może być ustawiony na "teraz" z małym opóźnieniem)
                if scheduled_at_check < now - timedelta(minutes=1):
                    return False, "Czas wysłania już minął"
            
            # Utwórz element kolejki (identycznie w obu trybach)
            import json
            queue_item = EmailQueue(
                recipient_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                priority=priority,
                scheduled_at=scheduled_at or get_local_now(),
                status='pending',
                context=json.dumps(context) if context else None,  # Konwertuj context na JSON string
                campaign_id=campaign_id,
                event_id=event_id,
                template_id=template_id  # Zapisz template_id z EmailTemplate
            )
            
            db.session.add(queue_item)
            db.session.commit()
            
            # W trybie testowym wyślij natychmiast po dodaniu do kolejki
            if os.getenv('EMAIL_TEST_MODE', 'false').lower() == 'true':
                # W trybie testowym wyślij natychmiast
                success, message = self._send_immediate_email(queue_item)
                if success:
                    return True, f"E-mail dodany do kolejki i wysłany testowo (ID: {queue_item.id})"
                else:
                    return False, f"E-mail dodany do kolejki, ale błąd wysyłania testowego: {message}"
            
            return True, f"E-mail dodany do kolejki (ID: {queue_item.id})"
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"❌ Błąd dodawania do kolejki: {e}")
            return False, f"Błąd dodawania do kolejki: {str(e)}"
    
    def _send_immediate_email(self, queue_item: EmailQueue) -> Tuple[bool, str]:
        """Wysyła e-mail bezpośrednio (nie przez kolejkę)"""
        try:
            from app.services.email_v2.providers.mailgun import MailgunProvider
            from app.services.email_v2.providers.smtp import SMTPProvider
            
            self.logger.info(f"📧 Wysyłam e-mail do {queue_item.recipient_email}")
            
            # Sprawdź czy to tryb testowy
            if os.getenv('EMAIL_TEST_MODE', 'false').lower() == 'true':
                # W trybie testowym symuluj wysyłkę
                self.logger.info("MailHog nie jest dostępny, symuluję wysyłkę")
                
                # Loguj e-mail
                email_log = EmailLog(
                    email=queue_item.recipient_email,
                    subject=queue_item.subject,
                    status='sent_test',
                    template_id=queue_item.template_id,
                    event_id=queue_item.event_id
                )
                db.session.add(email_log)
                
                # Aktualizuj status w kolejce
                queue_item.status = 'sent'
                queue_item.sent_at = get_local_now()
                db.session.commit()
                
                return True, "E-mail wysłany testowo"
            
            # Inicjalizuj providery
            mailgun = MailgunProvider({})
            smtp = SMTPProvider({})
            
            # Przygotuj dane e-maila
            email_data = {
                'to_email': queue_item.recipient_email,
                'subject': queue_item.subject,
                'html_content': queue_item.html_content,
                'text_content': queue_item.text_content,
                'from_email': queue_item.from_email,
                'from_name': queue_item.from_name
            }
            
            # Spróbuj Mailgun
            if mailgun.is_available():
                success, message = mailgun.send_email(**email_data)
                if success:
                    # Loguj e-mail
                    email_log = EmailLog(
                        email=queue_item.recipient_email,
                        subject=queue_item.subject,
                        status='sent',
                        template_id=queue_item.template_id,  # Zapisz template_id z EmailTemplate
                        event_id=queue_item.event_id,
                        message_id=message  # Zapisz message_id z Mailgun
                    )
                    db.session.add(email_log)
                    
                    # Aktualizuj status w kolejce
                    queue_item.status = 'sent'
                    queue_item.sent_at = get_local_now()
                    db.session.commit()
                    
                    return True, f"Mailgun: {message}"
                else:
                    self.logger.warning(f"⚠️ Mailgun failed: {message}")
            
            # Fallback do SMTP
            if smtp.is_available():
                success, message = smtp.send_email(**email_data)
                if success:
                    # Loguj e-mail
                    email_log = EmailLog(
                        email=queue_item.recipient_email,
                        subject=queue_item.subject,
                        status='sent',
                        template_id=queue_item.template_id,  # Zapisz template_id z EmailTemplate
                        event_id=queue_item.event_id,
                        message_id=message  # Zapisz message_id z SMTP
                    )
                    db.session.add(email_log)
                    
                    # Aktualizuj status w kolejce
                    queue_item.status = 'sent'
                    queue_item.sent_at = get_local_now()
                    db.session.commit()
                    
                    return True, f"SMTP: {message}"
                else:
                    self.logger.error(f"❌ SMTP fallback failed: {message}")
            
            return False, "Brak dostępnych providerów e-maili"
            
        except Exception as e:
            self.logger.error(f"❌ Błąd wysyłania e-maila: {e}")
            return False, f"Błąd wysyłania e-maila: {str(e)}"
    
    
    def _determine_reminder_strategy(self, event: EventSchedule) -> List[Dict]:
        """
        Inteligentnie określa strategię przypomnień na podstawie kontekstu wydarzenia
        
        Strategie:
        - 0 przypomnień: bardzo krótkie wydarzenia, testy, wewnętrzne
        - 1 przypomnienie: standardowe wydarzenia, webinary
        - 2 przypomnienia: ważne wydarzenia, warsztaty, konferencje
        - 3 przypomnienia: kluczowe wydarzenia, płatne, VIP
        """
        try:
            self.logger.info(f"🧠 Analizuję strategię przypomnień dla: {event.title}")
            
            # Analizuj czynniki wydarzenia
            factors = self._analyze_event_factors(event)
            
            # Podejmij decyzję o strategii
            strategy = self._decide_reminder_strategy(factors)
            
            self.logger.info(f"✅ Wybrana strategia: {strategy['name']} ({len(strategy['reminders'])} przypomnień)")
            return strategy['reminders']
            
        except Exception as e:
            self.logger.error(f"❌ Błąd określania strategii: {e}")
            # Fallback do bezpiecznej strategii
            return [{'hours': 24, 'template': 'event_reminder_24h', 'priority': 1}]
    
    def _analyze_event_factors(self, event: EventSchedule) -> Dict:
        """Analizuje czynniki wydarzenia wpływające na strategię przypomnień"""
        now = get_local_now()
        
        # Normalizuj timezone dla porównania
        if now.tzinfo is not None:
            now_naive = now.replace(tzinfo=None)
        else:
            now_naive = now
            
        if event.event_date.tzinfo is not None:
            event_date_naive = event.event_date.replace(tzinfo=None)
        else:
            event_date_naive = event.event_date
            
        time_diff = event_date_naive - now_naive
        minutes_until_event = int(time_diff.total_seconds() / 60)
        
        factors = {
            'event_type': event.event_type or 'unknown',
            'duration_hours': self._calculate_event_duration_hours(event),
            'participants_count': len(self._get_event_participants(event.id)),
            'is_paid': self._is_paid_event(event),
            'is_vip': self._is_vip_event(event),
            'days_until_event': self._get_days_until_event(event),
            'is_weekend': self._is_weekend_event(event),
            'title_keywords': self._extract_title_keywords(event.title),
            'minutes_until_event': minutes_until_event,
            'is_less_than_5min': minutes_until_event <= 5 and minutes_until_event > 0,
            'is_less_than_1h': minutes_until_event <= 60 and minutes_until_event > 0,
            'is_less_than_24h': minutes_until_event <= 24 * 60 and minutes_until_event > 0,
            'is_past_event': minutes_until_event <= 0
        }
        
        self.logger.info(f"📊 Czynniki wydarzenia: {factors}")
        return factors
    
    def _calculate_event_duration_hours(self, event: EventSchedule) -> float:
        """Oblicza długość wydarzenia w godzinach"""
        if event.end_date and event.event_date:
            duration = event.end_date - event.event_date
            return duration.total_seconds() / 3600
        else:
            # Domyślne długości na podstawie typu
            default_durations = {
                'webinar': 1.0, 'workshop': 3.0, 'conference': 8.0,
                'meeting': 0.5, 'training': 4.0, 'seminar': 2.0
            }
            return default_durations.get(event.event_type, 1.0)
    
    def _is_paid_event(self, event: EventSchedule) -> bool:
        """Sprawdza czy wydarzenie jest płatne"""
        paid_keywords = ['płatne', 'paid', 'ticket', 'bilet', 'opłata', 'koszt', 'cena']
        title_lower = event.title.lower()
        description_lower = (event.description or '').lower()
        
        return any(keyword in title_lower or keyword in description_lower 
                  for keyword in paid_keywords)
    
    def _is_vip_event(self, event: EventSchedule) -> bool:
        """Sprawdza czy wydarzenie jest VIP"""
        vip_keywords = ['vip', 'premium', 'exclusive', 'ekskluzywne', 'elitarne', 'zamknięte']
        title_lower = event.title.lower()
        description_lower = (event.description or '').lower()
        
        return any(keyword in title_lower or keyword in description_lower 
                  for keyword in vip_keywords)
    
    def _get_days_until_event(self, event: EventSchedule) -> int:
        """Oblicza liczbę dni do wydarzenia"""
        now = get_local_now()
        if now.tzinfo is not None:
            now = now.replace(tzinfo=None)
        
        event_date = event.event_date
        if event_date.tzinfo is not None:
            event_date = event_date.replace(tzinfo=None)
        
        delta = event_date - now
        return max(0, delta.days)
    
    def _is_weekend_event(self, event: EventSchedule) -> bool:
        """Sprawdza czy wydarzenie jest w weekend"""
        return event.event_date.weekday() >= 5  # 5=sobota, 6=niedziela
    
    def _extract_title_keywords(self, title: str) -> List[str]:
        """Wyodrębnia kluczowe słowa z tytułu"""
        keywords = ['warsztat', 'konferencja', 'szkolenie', 'prezentacja', 
                   'spotkanie', 'webinar', 'meeting', 'training', 'workshop', 'test']
        title_lower = title.lower()
        
        return [keyword for keyword in keywords if keyword in title_lower]
    
    def _decide_reminder_strategy(self, factors: Dict) -> Dict:
        """Podejmuje decyzję o strategii na podstawie czynników"""
        
        # Definicje strategii
        strategies = {
            'none': {
                'name': 'Brak przypomnień',
                'reminders': []
            },
            'minimal': {
                'name': 'Minimalne przypomnienia (1)',
                'reminders': [
                    {'hours': 24, 'template': 'event_reminder_24h', 'priority': 1}
                ]
            },
            'standard': {
                'name': 'Standardowe przypomnienia (2)',
                'reminders': [
                    {'hours': 24, 'template': 'event_reminder_24h', 'priority': 1},
                    {'hours': 1, 'template': 'event_reminder_1h', 'priority': 1}
                ]
            },
            'comprehensive': {
                'name': 'Kompleksowe przypomnienia (3)',
                'reminders': [
                    {'hours': 24, 'template': 'event_reminder_24h', 'priority': 1},
                    {'hours': 1, 'template': 'event_reminder_1h', 'priority': 1},
                    {'minutes': 5, 'template': 'event_reminder_5min', 'priority': 1}
                ]
            }
        }
        
        # Logika decyzyjna
        
        # Wydarzenia w przeszłości - brak przypomnień
        if factors['is_past_event']:
            return strategies['none']
        
        # Bardzo krótkie wydarzenia (< 5 min) - brak przypomnień
        if factors['duration_hours'] < 0.083:
            return strategies['none']
        
        # Testy - brak przypomnień (ale tylko jeśli to rzeczywiście test)
        # USUNIĘTO: Blokowanie przypomnień dla testów - system powinien działać normalnie
        # if 'test' in factors['title_keywords'] and factors['participants_count'] < 5:
        #     return strategies['none']
        
        # WYDARZENIA ZA MNIEJ NIŻ 24H - ZA PLANOWANE PRZYPOMNIENIA
        if factors['is_less_than_24h']:
            # Za mniej niż 5 minut - brak przypomnień (za późno)
            if factors['is_less_than_5min']:
                return {
                    'name': 'Brak przypomnień (za późno)',
                    'reminders': []
                }
            
            # Za mniej niż 1 godzina ale więcej niż 5min - przypomnienie 5min przed
            elif factors['is_less_than_1h']:
                return {
                    'name': 'Przypomnienie 5min przed (zaplanowane)',
                    'reminders': [
                        {'minutes': 5, 'template': 'event_reminder_5min', 'priority': 1}
                    ]
                }
            
            # Za 1-24 godziny - przypomnienia 1h + 5min przed (zaplanowane)
            else:
                return {
                    'name': 'Przypomnienia 1h + 5min przed (zaplanowane)',
                    'reminders': [
                        {'hours': 1, 'template': 'event_reminder_1h', 'priority': 1},
                        {'minutes': 5, 'template': 'event_reminder_5min', 'priority': 1}
                    ]
                }
        
        # Płatne wydarzenia - kompleksowe przypomnienia
        if factors['is_paid']:
            return strategies['comprehensive']
        
        # VIP wydarzenia - kompleksowe przypomnienia
        if factors['is_vip']:
            return strategies['comprehensive']
        
        # Konferencje i warsztaty - standardowe przypomnienia
        if any(keyword in factors['title_keywords'] for keyword in ['konferencja', 'warsztat', 'szkolenie']):
            return strategies['standard']
        
        # Duże wydarzenia (> 50 uczestników) - standardowe przypomnienia
        if factors['participants_count'] > 50:
            return strategies['standard']
        
        # Długie wydarzenia (> 4h) - standardowe przypomnienia
        if factors['duration_hours'] > 4:
            return strategies['standard']
        
        # Weekendowe wydarzenia - standardowe przypomnienia
        if factors['is_weekend']:
            return strategies['standard']
        
        # Długi czas do wydarzenia (> 7 dni) - standardowe przypomnienia
        if factors['days_until_event'] > 7:
            return strategies['standard']
        
        # Domyślnie - minimalne przypomnienia
        return strategies['minimal']

    def _get_event_participants(self, event_id: int) -> List[User]:
        """
        Pobiera uczestników wydarzenia
        
        Logika:
        1. Wszyscy użytkownicy z club_member=True (członkowie klubu - dostaną powiadomienie o każdym wydarzeniu)
        2. Użytkownicy zarejestrowani indywidualnie na to konkretne wydarzenie (przez event_id)
        """
        try:
            participants = set()
            
            # Pobierz wydarzenie
            event = EventSchedule.query.get(event_id)
            if not event:
                self.logger.error(f"❌ Wydarzenie {event_id} nie zostało znalezione")
                return []
            
            # 1. Wszyscy członkowie klubu (club_member=True)
            # Dostają powiadomienia o wszystkich wydarzeniach
            club_members = User.query.filter_by(
                club_member=True,
                is_active=True
            ).all()
            
            for user in club_members:
                participants.add(user)
                self.logger.debug(f"   + {user.email} (członek klubu)")
            
            # 2. Uczestnicy z grupy wydarzenia
            # Sprawdź czy wydarzenie ma grupę i pobierz jej członków
            from app.models import UserGroup, UserGroupMember
            event_group = UserGroup.query.filter_by(event_id=event_id).first()
            if event_group:
                group_members = UserGroupMember.query.filter_by(
                    group_id=event_group.id,
                    is_active=True
                ).all()
                
                for member in group_members:
                    user = User.query.get(member.user_id)
                    if user and user.is_active:
                        participants.add(user)
                        self.logger.debug(f"   + {user.email} (członek grupy wydarzenia)")
            
            # 3. Użytkownicy zarejestrowane indywidualnie na to wydarzenie
            # Osoby, które nie są członkami klubu, ale zarejestrowały się na to konkretne wydarzenie
            # Użyj tabeli event_registrations
            from app.models import EventRegistration
            event_registrations = EventRegistration.query.filter_by(
                event_id=event_id,
                is_active=True
            ).all()
            
            for registration in event_registrations:
                user = User.query.get(registration.user_id)
                if user and user.is_active:
                    participants.add(user)
                    self.logger.debug(f"   + {user.email} (rejestracja indywidualna)")
            
            participants_list = list(participants)
            self.logger.info(f"📊 Znaleziono {len(participants_list)} uczestników dla wydarzenia {event_id}")
            
            return participants_list
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania uczestników: {e}")
            return []
