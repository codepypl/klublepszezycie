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
from app.utils.email_utils import create_proper_from_header, create_proper_subject
from app.services.email_template_enricher import EmailTemplateEnricher


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

    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None, template_id: int = None, event_id: int = None, use_queue: bool = True, context: Dict = None) -> Tuple[bool, str]:
        """
        Wysyła pojedynczy email
        
        Args:
            to_email: Adres email odbiorcy
            subject: Temat emaila
            html_content: Treść HTML
            text_content: Treść tekstowa (opcjonalna)
            template_id: ID szablonu (opcjonalne)
            event_id: ID wydarzenia (opcjonalne)
            use_queue: Czy dodać do kolejki (domyślnie True)
            context: Słownik ze zmiennymi do zastąpienia w treści
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            # Ustaw context dla zastępowania zmiennych
            self._current_context = context or {}
            
            if use_queue:
                # Dodaj do kolejki zamiast wysyłać bezpośrednio
                return self.add_to_queue(
                    to_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    template_id=template_id,
                    event_id=event_id
                )
            else:
                # Wysyłanie bezpośrednie (stara logika)
                # Czyszczenie danych wejściowych
                to_email = unidecode(to_email).strip()
                subject = subject.strip()  # Nie usuwaj polskich znaków z tematu

                # Zastąp zmienne w treści (jeśli są przekazane w context)
                if self._current_context:
                    html_content = self._replace_variables(html_content or "", self._current_context)
                    text_content = self._replace_variables(text_content or "", self._current_context)

                # Wzbogacenie treści o linki wypisu i usunięcia konta (tylko jeśli nie zostało już wzbogacone)
                if html_content and ('{{unsubscribe_url}}' in html_content or '{{delete_account_url}}' in html_content):
                    try:
                        enricher = EmailTemplateEnricher()
                        enriched = enricher.enrich_template_content(
                            html_content=html_content or "",
                            text_content=text_content or "",
                            user_email=to_email
                        )
                        html_content = enriched.get('html_content') or html_content or ""
                        text_content = enriched.get('text_content') or text_content or ""
                    except Exception as e:
                        print(f"❌ Błąd wzbogacania treści: {e}")
                        # Jeśli nie udało się wzbogacić, wysyłamy oryginalną treść
                        pass
                
                # Placeholdery unsubscribe/delete są już obsługiwane przez EmailTemplateEnricher
                
                # Tworzenie wiadomości
                msg = MIMEMultipart('alternative')
                
                # Properly encode headers with UTF-8
                msg['From'] = create_proper_from_header(self.from_name, self.from_email)
                msg['To'] = to_email
                msg['Subject'] = create_proper_subject(subject)
                
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
                self._log_email(to_email, subject, 'sent', template_id=template_id, event_id=event_id)
                return True, "Email wysłany pomyślnie"
            
        except Exception as e:
            # Log failed email
            self._log_email(to_email, subject, 'failed', template_id=template_id, event_id=event_id, error_message=str(e))
            return False, f"Błąd wysyłania emaila: {str(e)}"

    def send_template_email(self, to_email: str, template_name: str, context: Dict = None, to_name: str = None, use_queue: bool = True, event_id: int = None) -> Tuple[bool, str]:
        """
        Wysyła email używając szablonu
        
        Args:
            to_email: Adres email odbiorcy
            template_name: Nazwa szablonu
            context: Kontekst dla zmiennych w szablonie
            to_name: Nazwa odbiorcy (opcjonalna)
            use_queue: Czy dodać do kolejki (domyślnie True)
            event_id: ID wydarzenia (opcjonalne)
            
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
            
            # Najpierw wzbogać szablon o linki unsubscribe/delete
            try:
                from app.services.email_template_enricher import EmailTemplateEnricher
                enricher = EmailTemplateEnricher()
                enriched = enricher.enrich_template_content(
                    html_content=template.html_content or "",
                    text_content=template.text_content or "",
                    user_email=to_email
                )
                enriched_html = enriched.get('html_content') or template.html_content or ""
                enriched_text = enriched.get('text_content') or template.text_content or ""
            except Exception as e:
                print(f"❌ Błąd wzbogacania szablonu: {e}")
                enriched_html = template.html_content or ""
                enriched_text = template.text_content or ""
            
            # Następnie zastąp zmienne w wzbogaconym szablonie
            subject = self._replace_variables(template.subject, context)
            html_content = self._replace_variables(enriched_html, context)
            text_content = self._replace_variables(enriched_text, context)
            
            if use_queue:
                # Dodaj do kolejki
                success, message = self.add_to_queue(
                    to_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    text_content=text_content,
                    template_id=template.id,
                    event_id=event_id,
                    context=context,
                    to_name=to_name
                )
                return success, message
            else:
                # Wysyłanie bezpośrednie
                return self.send_email(to_email, subject, html_content, text_content, template_id=template.id, event_id=event_id, use_queue=False)
            
        except Exception as e:
            return False, f"Błąd wysyłania szablonu: {str(e)}"

    def add_to_queue(self, to_email: str, subject: str, html_content: str, 
                    text_content: str = None, template_id: int = None, 
                    campaign_id: int = None, event_id: int = None, context: Dict = None, 
                    scheduled_at: datetime = None, to_name: str = None, 
                    duplicate_check_key: str = None, skip_duplicate_check: bool = False) -> Tuple[bool, str]:
        """
        Dodaje email do kolejki z zabezpieczeniami przed duplikatami
        
        Args:
            to_email: Adres email odbiorcy
            subject: Temat emaila
            html_content: Treść HTML
            text_content: Treść tekstowa (opcjonalna)
            template_id: ID szablonu (opcjonalne)
            campaign_id: ID kampanii (opcjonalne)
            event_id: ID wydarzenia (opcjonalne)
            context: Kontekst dla zmiennych (opcjonalne)
            scheduled_at: Data wysłania (opcjonalne)
            to_name: Nazwa odbiorcy (opcjonalna)
            duplicate_check_key: Klucz do sprawdzania duplikatów (opcjonalny)
            skip_duplicate_check: Pomiń sprawdzanie duplikatów (domyślnie False)
            
        Returns:
            Tuple[bool, str]: (sukces, komunikat)
        """
        try:
            # Sprawdź duplikaty jeśli nie pomijamy sprawdzania
            if not skip_duplicate_check:
                # Special handling for event reminders
                if duplicate_check_key and duplicate_check_key.startswith('event_reminder_'):
                    # Parse the duplicate check key to get IDs
                    parts = duplicate_check_key.split('_')
                    if len(parts) >= 5:
                        event_id = parts[2]
                        user_id = parts[3]
                        template_id = parts[4]
                        reminder_type = parts[5] if len(parts) > 5 else 'unknown'
                        
                        existing_email = EmailQueue.check_event_reminder_duplicate(
                            user_id=int(user_id),
                            event_id=int(event_id),
                            template_id=int(template_id),
                            reminder_type=reminder_type
                        )
                        
                        if existing_email:
                            return False, f"Duplikat przypomnienia o wydarzeniu już istnieje w kolejce (ID: {existing_email.id}, status: {existing_email.status})"
                else:
                    # Standard duplicate check for other emails
                    existing_email = EmailQueue.check_duplicate(
                        recipient_email=to_email,
                        subject=subject,
                        campaign_id=campaign_id,
                        html_content=html_content,
                        text_content=text_content,
                        duplicate_check_key=duplicate_check_key
                    )
                    
                    if existing_email:
                        return False, f"Duplikat emaila już istnieje w kolejce (ID: {existing_email.id}, status: {existing_email.status})"
            
            # Utwórz nowy element kolejki
            queue_item = EmailQueue(
                recipient_email=to_email,
                recipient_name=to_name,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                template_id=template_id,
                campaign_id=campaign_id,
                event_id=event_id,
                context=json.dumps(context) if context else None,
                scheduled_at=scheduled_at or __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now(),
                status='pending',
                duplicate_check_key=duplicate_check_key
            )
            
            db.session.add(queue_item)
            db.session.commit()
            return True, f"Email dodany do kolejki (ID: {queue_item.id})"
            
        except Exception as e:
            print(f"Błąd dodawania do kolejki: {e}")
            db.session.rollback()
            return False, f"Błąd dodawania do kolejki: {str(e)}"
    
    def process_scheduled_campaigns(self):
        """
        Przetwarza zaplanowane kampanie - dodaje je do kolejki gdy nadejdzie czas
        """
        try:
            from app.models import EmailCampaign
            from datetime import datetime
            import json
            
            # Znajdź kampanie zaplanowane na teraz lub wcześniej
            now = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
            scheduled_campaigns = EmailCampaign.query.filter(
                EmailCampaign.status == 'scheduled',
                EmailCampaign.scheduled_at <= now
            ).all()
            
            processed_count = 0
            
            for campaign in scheduled_campaigns:
                try:
                    # Zmień status na sending
                    campaign.status = 'sending'
                    db.session.commit()
                    
                    # Dodaj kampanię do kolejki
                    success, message = self._add_campaign_to_queue(campaign)
                    
                    if success:
                        processed_count += 1
                        print(f"✅ Kampania '{campaign.name}' dodana do kolejki")
                    else:
                        print(f"❌ Błąd dodawania kampanii '{campaign.name}' do kolejki: {message}")
                        # Przywróć status scheduled jeśli błąd
                        campaign.status = 'scheduled'
                        db.session.commit()
                        
                except Exception as e:
                    print(f"❌ Błąd przetwarzania kampanii {campaign.id}: {str(e)}")
                    # Przywróć status scheduled jeśli błąd
                    campaign.status = 'scheduled'
                    db.session.commit()
            
            return True, f"Przetworzono {processed_count} zaplanowanych kampanii"
            
        except Exception as e:
            db.session.rollback()
            print(f"Błąd przetwarzania zaplanowanych kampanii: {str(e)}")
            return False, f"Błąd przetwarzania zaplanowanych kampanii: {str(e)}"
    
    def calculate_send_time(self, event_time, participants_count, batch_size=50, delay_per_email=1):
        """
        Kalkuluje optymalny czas wysyłki na podstawie liczby uczestników
        
        Args:
            event_time: Czas wydarzenia
            participants_count: Liczba uczestników
            batch_size: Rozmiar paczki (domyślnie 50)
            delay_per_email: Opóźnienie między emailami w sekundach
            
        Returns:
            datetime: Optymalny czas rozpoczęcia wysyłki
        """
        from datetime import timedelta
        
        # Oblicz czas potrzebny na wysłanie wszystkich emaili
        total_emails = participants_count
        batches_needed = (total_emails + batch_size - 1) // batch_size
        
        # Czas na wysłanie jednej paczki (batch_size * delay_per_email)
        time_per_batch = batch_size * delay_per_email
        
        # Całkowity czas wysyłki
        total_send_time = batches_needed * time_per_batch
        
        # Dodaj 20% bufora na bezpieczeństwo
        total_send_time_with_buffer = int(total_send_time * 1.2)
        
        # Oblicz czas rozpoczęcia wysyłki
        send_start_time = event_time - timedelta(seconds=total_send_time_with_buffer)
        
        return send_start_time
    
    def schedule_smart_reminders(self, event_id, event_time, participants_count, reminder_hours=[24, 1]):
        """
        Planuje inteligentne przypomnienia z automatycznym dostosowaniem czasu
        
        Args:
            event_id: ID wydarzenia
            event_time: Czas wydarzenia
            participants_count: Liczba uczestników
            reminder_hours: Lista godzin przed wydarzeniem (domyślnie [24, 1])
            
        Returns:
            dict: Informacje o zaplanowanych przypomnieniach
        """
        try:
            from app.models import EmailQueue
            from datetime import datetime, timedelta
            import json
            
            scheduled_reminders = []
            
            for hours_before in reminder_hours:
                # Oblicz docelowy czas przypomnienia
                target_reminder_time = event_time - timedelta(hours=hours_before)
                
                # Oblicz optymalny czas rozpoczęcia wysyłki
                optimal_send_time = self.calculate_send_time(
                    target_reminder_time, 
                    participants_count
                )
                
                # Sprawdź czy nie jest za późno
                if optimal_send_time < __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now():
                    print(f"⚠️ Za późno na przypomnienie {hours_before}h przed wydarzeniem")
                    continue
                
                # Dodaj do kolejki z odpowiednim czasem
                reminder_data = {
                    'event_id': event_id,
                    'reminder_type': f'{hours_before}h',
                    'participants_count': participants_count,
                    'target_time': target_reminder_time.isoformat(),
                    'send_time': optimal_send_time.isoformat()
                }
                
                # Tutaj można dodać logikę tworzenia emaili w kolejce
                # Na razie zwracamy informacje o planowaniu
                scheduled_reminders.append({
                    'hours_before': hours_before,
                    'target_time': target_reminder_time,
                    'send_time': optimal_send_time,
                    'participants_count': participants_count
                })
                
                print(f"📅 Zaplanowano przypomnienie {hours_before}h przed: {optimal_send_time}")
            
            return {
                'success': True,
                'scheduled_reminders': scheduled_reminders,
                'participants_count': participants_count
            }
            
        except Exception as e:
            print(f"❌ Błąd planowania przypomnień: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _add_campaign_to_queue(self, campaign):
        """
        Dodaje kampanię do kolejki emaili
        """
        try:
            from app.models import UserGroupMember, User
            import json
            
            # Pobierz grupy odbiorców
            if campaign.recipient_groups:
                try:
                    group_ids = json.loads(campaign.recipient_groups)
                except json.JSONDecodeError:
                    return False, "Błąd parsowania grup odbiorców"
                
                # Pobierz członków grup
                for group_id in group_ids:
                    members = UserGroupMember.query.filter_by(
                        group_id=group_id, 
                        is_active=True
                    ).all()
                    
                    for member in members:
                        # Pobierz użytkownika
                        user = User.query.get(member.user_id)
                        if not user or not user.is_active:
                            continue
                        
                        # Przygotuj treść emaila
                        html_content = campaign.html_content or ""
                        text_content = campaign.text_content or ""
                        
                        # Sprawdź czy kampania ma jakąkolwiek treść
                        if not html_content and not text_content:
                            print(f"⚠️ Kampania '{campaign.name}' nie ma treści - pomijam użytkownika {user.email}")
                            continue
                        
                        # Zastąp zmienne w treści
                        if campaign.content_variables:
                            try:
                                variables = json.loads(campaign.content_variables)
                                for key, value in variables.items():
                                    placeholder = f"{{{{{key}}}}}"
                                    html_content = html_content.replace(placeholder, str(value))
                                    if text_content:
                                        text_content = text_content.replace(placeholder, str(value))
                            except json.JSONDecodeError:
                                pass
                        
                        # Dodaj do kolejki z datą kampanii (jeśli zaplanowana) lub teraz (jeśli natychmiastowa)
                        if campaign.scheduled_at:
                            email_scheduled_at = campaign.scheduled_at
                            print(f"📅 Using campaign scheduled time: {email_scheduled_at}")
                        else:
                            email_scheduled_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
                            print(f"⚠️ Campaign has no scheduled time, using current time: {email_scheduled_at}")
                        
                        # DEBUG: Sprawdź czy scheduled_at jest prawidłowo przekazywane
                        print(f"🔍 DEBUG: Campaign {campaign.id} scheduled_at: {campaign.scheduled_at}")
                        print(f"🔍 DEBUG: Email scheduled_at: {email_scheduled_at}")
                        
                        success, message = self.add_to_queue(
                            to_email=user.email,
                            to_name=user.first_name,
                            subject=campaign.subject,
                            html_content=html_content,
                            text_content=text_content,
                            campaign_id=campaign.id,
                            scheduled_at=email_scheduled_at
                        )
                        
                        if not success:
                            print(f"Błąd dodawania emaila dla {user.email}: {message}")
            
            return True, "Kampania dodana do kolejki"
            
        except Exception as e:
            return False, f"Błąd dodawania kampanii do kolejki: {str(e)}"

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
            # Zaplanowane kampanie są już w kolejce z przyszłą datą
            # process_scheduled_campaigns() nie jest już potrzebne
            
            # Pobierz emaile do wysłania
            queue_items = EmailQueue.query.filter(
                EmailQueue.status == 'pending',
                EmailQueue.scheduled_at <= __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
            ).limit(limit).all()
            
            for item in queue_items:
                try:
                    # Oznacz jako przetwarzany
                    item.status = 'processing'
                    db.session.commit()
                    
                    # Wyślij email bezpośrednio (nie dodawaj do kolejki)
                    success, message = self.send_email(
                        item.recipient_email,
                        item.subject,
                        item.html_content,
                        item.text_content,
                        template_id=item.template_id,
                        use_queue=False  # WAŻNE: nie dodawaj do kolejki!
                    )
                    
                    if success:
                        item.status = 'sent'
                        item.sent_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
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
                        item.recipient_email,
                        item.subject,
                        'failed',
                        item.template_id,
                        item.campaign_id,
                        item.event_id,
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
                campaign.sent_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
            elif sent_emails > 0 or failed_emails > 0:
                campaign.status = 'sending'
            
            campaign.updated_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
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
                    'recipient_name': member.first_name,
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
                
                success, message = self.add_to_queue(
                    to_email=member.email,
                    subject=campaign.subject,
                    html_content=template.html_content,
                    text_content=template.text_content,
                    campaign_id=campaign_id,
                    context=context
                )
                if success:
                    added_count += 1
                else:
                    print(f"Duplikat dla {member.email}: {message}")
            
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
                
                # Użyj klucza duplikatu dla przypomnień o wydarzeniach
                duplicate_key = f"event_reminder_{event_id}_{registration.id}_{reminder_type}"
                success, message = self.add_to_queue(
                    to_email=registration.email,
                    subject=template.subject,
                    html_content=template.html_content,
                    text_content=template.text_content,
                    template_id=template.id,
                    context=context,
                    scheduled_at=send_time,
                    duplicate_check_key=duplicate_key
                )
                if not success:
                    print(f"Duplikat przypomnienia dla {registration.email}: {message}")
            
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
                    
                    # Wyślij email bezpośrednio (nie dodawaj do kolejki)
                    success, message = self.send_email(
                        item.recipient_email,
                        item.subject,
                        item.html_content,
                        item.text_content,
                        template_id=item.template_id,
                        use_queue=False  # WAŻNE: nie dodawaj do kolejki!
                    )
                    
                    if success:
                        item.status = 'sent'
                        item.sent_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
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
                   event_id: int = None, context: dict = None, error_message: str = None):
        """
        Loguje email używając LogService
        
        Args:
            to_email: Adres email odbiorcy
            subject: Temat emaila
            status: Status wysłania
            template_id: ID szablonu (opcjonalne)
            campaign_id: ID kampanii (opcjonalne)
            event_id: ID wydarzenia (opcjonalne)
            context: Kontekst (opcjonalne)
            error_message: Komunikat błędu (opcjonalne)
        """
        try:
            from app.services.log_service import LogService
            
            success, message = LogService.log_email(
                to_email=to_email,
                subject=subject,
                status=status,
                template_id=template_id,
                campaign_id=campaign_id,
                event_id=event_id,
                context=context,
                error_message=error_message
            )
            
            if not success:
                print(f"Błąd logowania emaila: {message}")
            
        except Exception as e:
            print(f"Błąd logowania emaila: {e}")