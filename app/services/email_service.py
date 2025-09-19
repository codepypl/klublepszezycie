import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any, Optional, Tuple
from unidecode import unidecode

from app import db
from app.models import EmailTemplate, EmailQueue, EmailLog, UserGroup, UserGroupMember, User, EmailCampaign


class EmailService:
    def __init__(self):
        """Inicjalizacja serwisu email"""
        self.smtp_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('MAIL_PORT', '587'))
        self.smtp_username = os.getenv('MAIL_USERNAME', '')
        self.smtp_password = os.getenv('MAIL_PASSWORD', '')
        self.from_email = unidecode(os.getenv('MAIL_DEFAULT_SENDER', '')).strip()
        self.from_name = unidecode(os.getenv('MAIL_DEFAULT_SENDER_NAME', 'Klub Lepszego Zycia')).strip()
        self.use_tls = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
        self.use_ssl = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None, template_id: int = None) -> Tuple[bool, str]:
        """
        Wysyła pojedynczy email
        
        Args:
            to_email: Adres email odbiorcy
            subject: Temat emaila
            html_content: Treść HTML
            text_content: Treść tekstowa (opcjonalna)
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            # Czyszczenie danych wejściowych
            to_email = unidecode(to_email).strip()
            subject = subject.strip()  # Nie usuwaj polskich znaków z tematu
            
            # Tworzenie wiadomości
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr((self.from_name, self.from_email))
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Dodanie treści tekstowej
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                text_part.set_charset('utf-8')
                msg.attach(text_part)
            
            # Dodanie treści HTML
            html_part = MIMEText(html_content, 'html')
            html_part.set_charset('utf-8')
            msg.attach(html_part)
            
            # Wysyłanie
            if self.use_ssl:
                # Użyj SMTP_SSL dla połączeń SSL
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
            else:
                # Użyj SMTP z TLS
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    if self.use_tls:
                        server.starttls()
                    server.login(self.smtp_username, self.smtp_password)
                    server.send_message(msg)
            
            # Log successful email
            self._log_email(to_email, subject, 'sent', template_id=template_id)
            return True, "Email wysłany pomyślnie"
            
        except Exception as e:
            # Log failed email
            self._log_email(to_email, subject, 'failed', template_id=template_id, error_message=str(e))
            return False, f"Błąd wysyłania emaila: {str(e)}"

    def send_template_email(self, to_email: str, template_name: str, context: Dict = None, to_name: str = None, use_queue: bool = True) -> Tuple[bool, str]:
        """
        Wysyła email używając szablonu
        
        Args:
            to_email: Adres email odbiorcy
            template_name: Nazwa szablonu
            context: Kontekst dla zmiennych w szablonie
            to_name: Nazwa odbiorcy (opcjonalna)
            use_queue: Czy dodać do kolejki (domyślnie True)
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            template = EmailTemplate.query.filter_by(name=template_name).first()
            if not template:
                return False, f"Szablon '{template_name}' nie został znaleziony"
            
            if context is None:
                context = {}
            
            # Dodanie nazwy odbiorcy do kontekstu
            if to_name:
                context['recipient_name'] = to_name
            
            # Zastąpienie zmiennych w szablonie
            subject = self._replace_variables(template.subject, context)
            html_content = self._replace_variables(template.html_content, context)
            text_content = self._replace_variables(template.text_content or '', context)
            
            if use_queue:
                # Dodaj do kolejki
                success = self.add_to_queue(
                    to_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    template_id=template.id,
                    context=context,
                    to_name=to_name
                )
                if success:
                    return True, "Email dodany do kolejki"
                else:
                    return False, "Błąd dodawania do kolejki"
            else:
                # Wysyłanie bezpośrednie
                return self.send_email(to_email, subject, html_content, text_content, template_id=template.id)
            
        except Exception as e:
            return False, f"Błąd wysyłania szablonu: {str(e)}"

    def add_to_queue(self, to_email: str, subject: str, html_content: str, 
                    text_content: str = None, template_id: int = None, 
                    campaign_id: int = None, context: Dict = None, 
                    scheduled_at: datetime = None, to_name: str = None) -> bool:
        """
        Dodaje email do kolejki
        
        Args:
            to_email: Adres email odbiorcy
            subject: Temat emaila
            html_content: Treść HTML
            text_content: Treść tekstowa (opcjonalna)
            template_id: ID szablonu (opcjonalne)
            campaign_id: ID kampanii (opcjonalne)
            context: Kontekst dla zmiennych (opcjonalne)
            scheduled_at: Data wysłania (opcjonalne)
            to_name: Nazwa odbiorcy (opcjonalna)
            
        Returns:
            bool: True jeśli dodano pomyślnie
        """
        try:
            queue_item = EmailQueue(
                to_email=to_email,
                to_name=to_name,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                template_id=template_id,
                campaign_id=campaign_id,
                context=json.dumps(context) if context else None,
                scheduled_at=scheduled_at or datetime.utcnow(),
                status='pending'
            )
            
            db.session.add(queue_item)
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"Błąd dodawania do kolejki: {e}")
            db.session.rollback()
            return False

    def process_queue(self, limit: int = 50) -> Dict[str, int]:
        """
        Przetwarza kolejkę emaili
        
        Args:
            limit: Maksymalna liczba emaili do przetworzenia
            
        Returns:
            Dict[str, int]: Statystyki przetwarzania
        """
        stats = {'processed': 0, 'success': 0, 'failed': 0}
        
        try:
            # Pobierz emaile do wysłania
            queue_items = EmailQueue.query.filter(
                EmailQueue.status == 'pending',
                EmailQueue.scheduled_at <= datetime.utcnow()
            ).limit(limit).all()
            
            for item in queue_items:
                try:
                    # Oznacz jako przetwarzany
                    item.status = 'processing'
                    db.session.commit()
                    
                    # Wyślij email
                    success, message = self.send_email(
                        item.to_email,
                        item.subject,
                        item.html_content,
                        item.text_content,
                        template_id=item.template_id
                    )
                    
                    if success:
                        item.status = 'sent'
                        item.sent_at = datetime.utcnow()
                        stats['success'] += 1
                        # Email już został zalogowany przez send_email
                    else:
                        item.status = 'failed'
                        item.error_message = message
                        stats['failed'] += 1
                        
                        # Email już został zalogowany przez send_email
                    
                    stats['processed'] += 1
                    
                except Exception as e:
                    item.status = 'failed'
                    item.error_message = str(e)
                    stats['failed'] += 1
                    stats['processed'] += 1
                    
                    # Loguj błąd
                    self._log_email(
                        item.to_email,
                        item.subject,
                        'failed',
                        item.template_id,
                        item.campaign_id,
                        item.context,
                        str(e)
                    )
                
                db.session.commit()
                
                # Aktualizuj statystyki kampanii jeśli to email kampanii
                if item.campaign_id:
                    self.update_campaign_stats(item.campaign_id)
                
        except Exception as e:
            print(f"Błąd przetwarzania kolejki: {e}")
            db.session.rollback()
        
        return stats

    def update_campaign_stats(self, campaign_id: int) -> bool:
        """
        Aktualizuje statystyki kampanii na podstawie emaili w kolejce
        
        Args:
            campaign_id: ID kampanii
            
        Returns:
            bool: True jeśli zaktualizowano pomyślnie
        """
        try:
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return False
            
            # Policz emaile w kolejce dla tej kampanii
            total_queued = EmailQueue.query.filter_by(campaign_id=campaign_id).count()
            sent_emails = EmailQueue.query.filter_by(campaign_id=campaign_id, status='sent').count()
            failed_emails = EmailQueue.query.filter_by(campaign_id=campaign_id, status='failed').count()
            
            # Aktualizuj statystyki
            campaign.sent_count = sent_emails
            campaign.failed_count = failed_emails
            
            # Ustaw status na podstawie statystyk
            if sent_emails + failed_emails >= total_queued and total_queued > 0:
                campaign.status = 'completed'
                campaign.sent_at = datetime.utcnow()
            elif sent_emails > 0 or failed_emails > 0:
                campaign.status = 'sending'
            
            campaign.updated_at = datetime.utcnow()
            db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"Błąd aktualizacji statystyk kampanii: {e}")
            db.session.rollback()
            return False

    def send_campaign_to_group(self, campaign_id: int, group_id: int) -> Tuple[bool, str, int]:
        """
        Wysyła kampanię do grupy użytkowników
        
        Args:
            campaign_id: ID kampanii
            group_id: ID grupy
            
        Returns:
            Tuple[bool, str, int]: (sukces, komunikat, liczba_dodanych_emaili)
        """
        try:
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return False, "Kampania nie została znaleziona", 0
            
            group = UserGroup.query.get(group_id)
            if not group:
                return False, "Grupa nie została znaleziona", 0
            
            # Pobierz członków grupy
            members = UserGroupMember.query.filter_by(group_id=group_id).all()
            
            if not members:
                return False, "Grupa nie ma członków", 0
            
            # Pobierz szablon kampanii
            template = None
            if campaign.template_id:
                template = EmailTemplate.query.get(campaign.template_id)
            
            if not template:
                return False, "Kampania nie ma przypisanego szablonu", 0
            
            # Dodaj emaile do kolejki
            added_count = 0
            for member in members:
                context = {
                    'recipient_name': member.name,
                    'recipient_email': member.email
                }
                
                # Dodaj zmienne treści z kampanii do kontekstu
                if campaign.content_variables:
                    try:
                        import json
                        content_vars = json.loads(campaign.content_variables)
                        context.update(content_vars)
                    except json.JSONDecodeError:
                        pass
                
                if self.add_to_queue(
                    to_email=member.email,
                    subject=campaign.subject,
                    html_content=template.html_content,
                    text_content=template.text_content,
                    campaign_id=campaign_id,
                    context=context
                ):
                    added_count += 1
            
            return True, f"Kampania dodana do kolejki dla {added_count} członków grupy", added_count
            
        except Exception as e:
            return False, f"Błąd wysyłania kampanii: {str(e)}", 0

    def schedule_event_reminder(self, event_id: int, reminder_type: str = '24h') -> bool:
        """
        Planuje przypomnienie o wydarzeniu
        
        Args:
            event_id: ID wydarzenia
            reminder_type: Typ przypomnienia ('24h', '1h', '5min')
            
        Returns:
            bool: True jeśli zaplanowano pomyślnie
        """
        try:
            from app.models import EventSchedule
            
            event = EventSchedule.query.get(event_id)
            if not event:
                return False
            
            # Określ czas wysłania
            reminder_times = {
                '24h': timedelta(hours=24),
                '1h': timedelta(hours=1),
                '5min': timedelta(minutes=5)
            }
            
            if reminder_type not in reminder_times:
                return False
            
            send_time = event.start_time - reminder_times[reminder_type]
            
            # Pobierz szablon przypomnienia
            template_name = f"event_reminder_{reminder_type}"
            template = EmailTemplate.query.filter_by(name=template_name).first()
            
            if not template:
                return False
            
            # Pobierz zarejestrowanych użytkowników
            from app.models import User
            registrations = User.query.filter_by(
                event_id=event_id,
                account_type='event_registration'
            ).all()
            
            for registration in registrations:
                context = {
                    'event_title': event.title,
                    'event_date': event.start_time.strftime('%d.%m.%Y'),
                    'event_time': event.start_time.strftime('%H:%M'),
                    'event_location': event.location or 'Nie podano',
                    'recipient_name': registration.first_name
                }
                
                self.add_to_queue(
                    to_email=registration.email,
                    subject=template.subject,
                    html_content=template.html_content,
                    text_content=template.text_content,
                    template_id=template.id,
                    context=context,
                    scheduled_at=send_time
                )
            
            return True
            
        except Exception as e:
            print(f"Błąd planowania przypomnienia: {e}")
            return False

    def get_queue_stats(self) -> Dict[str, int]:
        """
        Pobiera statystyki kolejki
        
        Returns:
            Dict[str, int]: Statystyki kolejki
        """
        try:
            stats = {
                'pending': EmailQueue.query.filter_by(status='pending').count(),
                'processing': EmailQueue.query.filter_by(status='processing').count(),
                'sent': EmailQueue.query.filter_by(status='sent').count(),
                'failed': EmailQueue.query.filter_by(status='failed').count(),
                'total': EmailQueue.query.count()
            }
            return stats
        except Exception as e:
            print(f"Błąd pobierania statystyk: {e}")
            return {'pending': 0, 'processing': 0, 'sent': 0, 'failed': 0, 'total': 0}

    def retry_failed_emails(self, limit: int = 10) -> Dict[str, int]:
        """
        Ponawia wysyłanie nieudanych emaili
        
        Args:
            limit: Maksymalna liczba emaili do ponowienia
            
        Returns:
            Dict[str, int]: Statystyki ponowienia
        """
        stats = {'retried': 0, 'success': 0, 'failed': 0}
        
        try:
            failed_items = EmailQueue.query.filter_by(status='failed').limit(limit).all()
            
            for item in failed_items:
                try:
                    # Oznacz jako przetwarzany
                    item.status = 'processing'
                    item.error_message = None
                    db.session.commit()
                    
                    # Wyślij email
                    success, message = self.send_email(
                        item.to_email,
                        item.subject,
                        item.html_content,
                        item.text_content,
                        template_id=item.template_id
                    )
                    
                    if success:
                        item.status = 'sent'
                        item.sent_at = datetime.utcnow()
                        stats['success'] += 1
                    else:
                        item.status = 'failed'
                        item.error_message = message
                        stats['failed'] += 1
                    
                    stats['retried'] += 1
                    db.session.commit()
                    
                except Exception as e:
                    item.status = 'failed'
                    item.error_message = str(e)
                    stats['failed'] += 1
                    stats['retried'] += 1
                    db.session.commit()
            
        except Exception as e:
            print(f"Błąd ponawiania emaili: {e}")
            db.session.rollback()
        
        return stats

    def _replace_variables(self, text: str, context: Dict) -> str:
        """
        Zastępuje zmienne w tekście
        
        Args:
            text: Tekst do przetworzenia
            context: Kontekst ze zmiennymi
            
        Returns:
            str: Przetworzony tekst
        """
        if not text or not context:
            return text
        
        for key, value in context.items():
            text = text.replace(f'{{{{{key}}}}}', str(value))
        
        return text

    def _log_email(self, to_email: str, subject: str, status: str, 
                   template_id: int = None, campaign_id: int = None, 
                   context: str = None, error_message: str = None):
        """
        Loguje email
        
        Args:
            to_email: Adres email odbiorcy
            subject: Temat emaila
            status: Status wysłania
            template_id: ID szablonu (opcjonalne)
            campaign_id: ID kampanii (opcjonalne)
            context: Kontekst (opcjonalne)
            error_message: Komunikat błędu (opcjonalne)
        """
        try:
            log_entry = EmailLog(
                email=to_email,
                subject=subject,
                status=status,
                template_id=template_id,
                campaign_id=campaign_id,
                recipient_data=context,
                error_message=error_message,
                sent_at=datetime.now() if status == 'sent' else None
            )
            
            db.session.add(log_entry)
            db.session.commit()
            
        except Exception as e:
            print(f"Błąd logowania emaila: {e}")
            db.session.rollback()