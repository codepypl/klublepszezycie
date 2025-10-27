"""
Procesor kolejki e-maili - inteligentne przetwarzanie
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

from app import db
from app.models import EmailQueue, EmailLog
from app.utils.timezone_utils import get_local_now
from ..providers import MailgunProvider, SMTPProvider

class EmailQueueProcessor:
    """
    Inteligentny procesor kolejki e-maili
    
    Zasady:
    1. Automatyczny fallback Mailgun → SMTP
    2. Inteligentne retry z eksponencjalnym backoff
    3. Kontrola dziennych limitów
    4. Priorytetyzacja e-maili
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Inicjalizacja providerów
        self.mailgun = MailgunProvider({})
        self.smtp = SMTPProvider({})
        
        # Konfiguracja
        self.batch_size = int(os.getenv('EMAIL_BATCH_SIZE', '50'))
        self.max_retries = int(os.getenv('EMAIL_MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('EMAIL_RETRY_DELAY', '300'))  # 5 minut
        
        # Ustaw loggery
        self.mailgun.set_logger(self.logger)
        self.smtp.set_logger(self.logger)
    
    def process_queue(self, limit: int = None) -> Dict[str, Any]:
        """
        Przetwarza kolejkę e-maili
        
        Args:
            limit: Maksymalna liczba e-maili do przetworzenia
            
        Returns:
            Dict[str, Any]: Statystyki przetwarzania
        """
        try:
            if limit is None:
                limit = self.batch_size
            
            self.logger.info(f"🔄 Rozpoczynam przetwarzanie kolejki (limit: {limit})")
            
            # Pobierz e-maile do przetworzenia
            queue_items = self._get_emails_to_process(limit)
            
            if not queue_items:
                return {
                    'processed': 0,
                    'success': 0,
                    'failed': 0,
                    'message': 'Brak e-maili do przetworzenia'
                }
            
            # Przetwórz e-maile
            stats = self._process_emails(queue_items)
            
            self.logger.info(f"✅ Przetworzono {stats['processed']} e-maili: {stats['success']} sukces, {stats['failed']} błąd")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Błąd przetwarzania kolejki: {e}")
            return {
                'processed': 0,
                'success': 0,
                'failed': 0,
                'error': str(e)
            }
    
    def retry_failed_emails(self, limit: int = 10) -> Dict[str, Any]:
        """
        Ponawia wysyłanie nieudanych e-maili
        
        Args:
            limit: Maksymalna liczba e-maili do ponowienia
            
        Returns:
            Dict[str, Any]: Statystyki ponawiania
        """
        try:
            self.logger.info(f"🔄 Ponawiam wysyłanie {limit} nieudanych e-maili")
            
            # Pobierz nieudane e-maile
            failed_emails = EmailQueue.query.filter(
                EmailQueue.status == 'failed',
                EmailQueue.retry_count < self.max_retries
            ).order_by(EmailQueue.updated_at.asc()).limit(limit).all()
            
            if not failed_emails:
                return {
                    'retried': 0,
                    'success': 0,
                    'failed': 0,
                    'message': 'Brak e-maili do ponowienia'
                }
            
            # Ponów wysyłanie
            stats = {'retried': 0, 'success': 0, 'failed': 0}
            
            for email in failed_emails:
                try:
                    # Zwiększ licznik prób
                    email.retry_count += 1
                    email.status = 'pending'
                    email.scheduled_at = get_local_now() + timedelta(seconds=self.retry_delay * email.retry_count)
                    
                    db.session.commit()
                    stats['retried'] += 1
                    
                except Exception as e:
                    self.logger.error(f"❌ Błąd ponawiania e-maila {email.id}: {e}")
                    stats['failed'] += 1
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Błąd ponawiania e-maili: {e}")
            return {
                'retried': 0,
                'success': 0,
                'failed': 0,
                'error': str(e)
            }
    
    def cleanup_old_emails(self, days: int = 30) -> Dict[str, Any]:
        """
        Czyści stare e-maile z kolejki
        
        Args:
            days: Liczba dni po których usunąć e-maile
            
        Returns:
            Dict[str, Any]: Statystyki czyszczenia
        """
        try:
            cutoff_date = get_local_now() - timedelta(days=days)
            
            # Usuń stare wysłane e-maile
            deleted_sent = EmailQueue.query.filter(
                EmailQueue.status == 'sent',
                EmailQueue.sent_at < cutoff_date
            ).delete(synchronize_session=False)
            
            # Usuń stare nieudane e-maile (po max retries)
            deleted_failed = EmailQueue.query.filter(
                EmailQueue.status == 'failed',
                EmailQueue.retry_count >= self.max_retries,
                EmailQueue.updated_at < cutoff_date
            ).delete(synchronize_session=False)
            
            db.session.commit()
            
            total_deleted = deleted_sent + deleted_failed
            
            self.logger.info(f"🗑️ Usunięto {total_deleted} starych e-maili z kolejki")
            
            return {
                'deleted_sent': deleted_sent,
                'deleted_failed': deleted_failed,
                'total_deleted': total_deleted,
                'message': f"Usunięto {total_deleted} starych e-maili"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Błąd czyszczenia kolejki: {e}")
            return {
                'deleted_sent': 0,
                'deleted_failed': 0,
                'total_deleted': 0,
                'error': str(e)
            }
    
    def _get_emails_to_process(self, limit: int) -> List[EmailQueue]:
        """
        Pobiera e-maile do przetworzenia z priorytetyzacją
        
        Sortowanie:
        1. Priorytet (0=najwyższy -> 1 -> 2)
        2. Scheduled_at (najstarsze pierwsze)
        """
        now = get_local_now()
        # Normalizuj timezone - usuń dla bezpiecznego porównania
        now_naive = now.replace(tzinfo=None) if hasattr(now, 'tzinfo') and now.tzinfo else now
        
        # Pobierz wszystkie pending emaile z sortowaniem po priorytetach
        # Priorytet 0 (system) > 1 (wydarzenia) > 2 (kampanie)
        all_pending = EmailQueue.query.filter(
            EmailQueue.status == 'pending'
        ).order_by(
            EmailQueue.priority.asc(),      # Najniższy numer = najwyższy priorytet
            EmailQueue.scheduled_at.asc()   # Najstarsze emaile pierwsze
        ).all()
        
        # Filtruj ręcznie z poprawnym timezone handling
        emails_to_process = []
        for email in all_pending:
            scheduled_naive = email.scheduled_at.replace(tzinfo=None) if hasattr(email.scheduled_at, 'tzinfo') and email.scheduled_at.tzinfo else email.scheduled_at
            
            if scheduled_naive <= now_naive:
                emails_to_process.append(email)
                if len(emails_to_process) >= limit:
                    break
        
        self.logger.info(f"📊 Wybrano {len(emails_to_process)} emaili do przetworzenia (limit: {limit})")
        if emails_to_process:
            priority_counts = {}
            for email in emails_to_process:
                priority_counts[email.priority] = priority_counts.get(email.priority, 0) + 1
            self.logger.info(f"   Priorytetyzacja: {priority_counts}")
        
        return emails_to_process
    
    def _process_emails(self, emails: List[EmailQueue]) -> Dict[str, int]:
        """Przetwarza listę e-maili"""
        stats = {'processed': 0, 'success': 0, 'failed': 0}
        
        for email in emails:
            try:
                # Oznacz jako przetwarzany
                email.status = 'processing'
                db.session.commit()
                
                # Wyślij e-mail
                success, message = self._send_email(email)
                
                if success:
                    email.status = 'sent'
                    email.sent_at = get_local_now()
                    stats['success'] += 1
                else:
                    email.status = 'failed'
                    email.error_message = message
                    stats['failed'] += 1
                
                stats['processed'] += 1
                db.session.commit()
                
            except Exception as e:
                email.status = 'failed'
                email.error_message = str(e)
                stats['failed'] += 1
                stats['processed'] += 1
                db.session.commit()
        
        # Aktualizuj statusy kampanii po przetworzeniu emaili
        self._update_campaign_statuses(emails)
        
        return stats
    
    def _update_campaign_statuses(self, emails: List[EmailQueue]) -> None:
        """Aktualizuje statusy kampanii po przetworzeniu emaili"""
        try:
            # Grupuj emaile według campaign_id
            campaign_emails = {}
            for email in emails:
                if email.campaign_id:
                    if email.campaign_id not in campaign_emails:
                        campaign_emails[email.campaign_id] = []
                    campaign_emails[email.campaign_id].append(email)
            
            # Aktualizuj status każdej kampanii
            for campaign_id, campaign_email_list in campaign_emails.items():
                self._update_single_campaign_status(campaign_id, campaign_email_list)
                
        except Exception as e:
            self.logger.error(f"❌ Błąd aktualizacji statusów kampanii: {e}")
    
    def _update_single_campaign_status(self, campaign_id: int, emails: List[EmailQueue]) -> None:
        """Aktualizuje status pojedynczej kampanii"""
        try:
            from app.models import EmailCampaign
            
            campaign = EmailCampaign.query.get(campaign_id)
            if not campaign:
                return
            
            # Sprawdź status wszystkich emaili kampanii (nie tylko przetworzonych)
            all_campaign_emails = EmailQueue.query.filter_by(campaign_id=campaign_id).all()
            
            if not all_campaign_emails:
                return
            
            # Policz statusy emaili
            sent_count = sum(1 for email in all_campaign_emails if email.status == 'sent')
            failed_count = sum(1 for email in all_campaign_emails if email.status == 'failed')
            pending_count = sum(1 for email in all_campaign_emails if email.status in ['pending', 'processing'])
            total_count = len(all_campaign_emails)
            
            # Aktualizuj status kampanii
            if campaign.status in ['ready', 'scheduled', 'sending']:
                if sent_count == total_count:
                    # Wszystkie emaile wysłane
                    campaign.status = 'sent'
                    self.logger.info(f"✅ Kampania {campaign_id} oznaczona jako wysłana ({sent_count}/{total_count})")
                elif failed_count > 0 and sent_count + failed_count == total_count:
                    # Wszystkie emaile przetworzone, ale niektóre nieudane
                    campaign.status = 'completed'
                    self.logger.info(f"⚠️ Kampania {campaign_id} oznaczona jako zakończona z błędami ({sent_count} sukces, {failed_count} błąd)")
                elif pending_count > 0:
                    # Niektóre emaile jeszcze oczekują
                    campaign.status = 'sending'
                    self.logger.info(f"🔄 Kampania {campaign_id} w trakcie wysyłania ({sent_count} wysłane, {pending_count} oczekujące)")
                
                db.session.commit()
                
        except Exception as e:
            self.logger.error(f"❌ Błąd aktualizacji statusu kampanii {campaign_id}: {e}")
    
    def _send_email(self, email: EmailQueue) -> Tuple[bool, str]:
        """Wysyła pojedynczy e-mail z fallback"""
        try:
            # VERBOSE LOGGING - Krok 1: Start
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"📤 PROCESSOR: Rozpoczynam wysyłkę emaila ID: {email.id}")
            self.logger.info(f"   Do: {email.recipient_email}")
            self.logger.info(f"   Temat: {email.subject}")
            self.logger.info(f"   Template: {email.template_name}")
            self.logger.info(f"   Event ID: {email.event_id}")
            self.logger.info(f"   Priority: {email.priority}")
            
            # Dla event emails, re-renderuj z aktualnym event_url
            html_content = email.html_content
            text_content = email.text_content
            subject = email.subject
            
            if email.event_id:
                self.logger.info(f"🔄 Re-renderuję email dla event {email.event_id} z aktualnym event_url")
                success, html, text, subj = self._re_render_event_email(email)
                if success:
                    html_content = html
                    text_content = text
                    subject = subj
                    self.logger.info(f"   ✅ Email zaktualizowany z aktualnym event_url")
            
            # Przygotuj dane e-maila
            email_data = {
                'to_email': email.recipient_email,
                'subject': subject,
                'html_content': html_content,
                'text_content': text_content,
                'from_email': getattr(email, 'from_email', 'noreply@klublepszezycie.pl'),
                'from_name': getattr(email, 'from_name', 'Klub Lepsze Życie')
            }
            
            # VERBOSE LOGGING - Krok 2: Sprawdzenie Mailgun
            self.logger.info(f"🔍 Sprawdzam dostępność Mailgun...")
            self.logger.info(f"   Mailgun available: {self.mailgun.is_available()}")
            
            # Spróbuj Mailgun
            if self.mailgun.is_available():
                self.logger.info(f"📮 Próba wysyłki przez Mailgun...")
                success, message = self.mailgun.send_email(**email_data)
                
                self.logger.info(f"📬 Mailgun result: success={success}, message={message}")
                
                if success:
                    # Loguj e-mail do EmailLog
                    email_log = EmailLog(
                        email=email.recipient_email,
                        subject=email.subject,
                        status='sent',
                        template_id=email.template_id,
                        event_id=email.event_id,
                        campaign_id=email.campaign_id,  # DODANO: campaign_id
                        message_id=message  # Message ID z Mailgun
                    )
                    db.session.add(email_log)
                    
                    self.logger.info(f"✅ Email wysłany przez Mailgun!")
                    self.logger.info(f"{'='*60}\n")
                    return True, message
                else:
                    self.logger.warning(f"⚠️ Mailgun failed: {message}")
            else:
                self.logger.warning(f"⚠️ Mailgun nie jest dostępny")
            
            # VERBOSE LOGGING - Krok 3: Fallback do SMTP
            self.logger.info(f"🔄 Próba fallback do SMTP...")
            self.logger.info(f"   SMTP available: {self.smtp.is_available()}")
            
            # Fallback do SMTP
            if self.smtp.is_available():
                success, message = self.smtp.send_email(**email_data)
                
                self.logger.info(f"📬 SMTP result: success={success}, message={message}")
                
                if success:
                    # Loguj e-mail do EmailLog
                    email_log = EmailLog(
                        email=email.recipient_email,
                        subject=email.subject,
                        status='sent',
                        template_id=email.template_id,
                        event_id=email.event_id,
                        campaign_id=email.campaign_id  # DODANO: campaign_id
                    )
                    db.session.add(email_log)
                    
                    self.logger.info(f"✅ Email wysłany przez SMTP!")
                    self.logger.info(f"{'='*60}\n")
                    return True, f"SMTP fallback: {message}"
                else:
                    self.logger.error(f"❌ SMTP fallback failed: {message}")
            else:
                self.logger.error(f"❌ SMTP nie jest dostępny")
            
            self.logger.error(f"❌ Brak dostępnych providerów!")
            self.logger.info(f"{'='*60}\n")
            return False, "Brak dostępnych providerów e-maili"
            
        except Exception as e:
            self.logger.error(f"❌ Exception w _send_email: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            self.logger.info(f"{'='*60}\n")
            return False, f"Błąd wysyłania e-maila: {str(e)}"
    
    def _re_render_event_email(self, email: EmailQueue) -> Tuple[bool, str, str, str]:
        """
        Re-renderuje email dla wydarzenia z aktualnym event_url
        
        Returns:
            Tuple[bool, str, str, str]: (success, html_content, text_content, subject)
        """
        try:
            # Pobierz wydarzenie
            from app.models.events_model import EventSchedule
            event = EventSchedule.query.get(email.event_id)
            
            if not event:
                self.logger.warning(f"⚠️ Wydarzenie {email.event_id} nie znalezione, używam starego HTML")
                return False, email.html_content, email.text_content, email.subject
            
            # Pobierz template
            from app.models import EmailTemplate
            template = None
            if email.template_id:
                template = EmailTemplate.query.get(email.template_id)
            elif email.template_name:
                template = EmailTemplate.query.filter_by(name=email.template_name, is_active=True).first()
            
            if not template:
                self.logger.warning(f"⚠️ Template nie znalezione, używam starego HTML")
                return False, email.html_content, email.text_content, email.subject
            
            # Przygotuj kontekst z aktualnymi danymi
            from app.models.user_model import User
            user = User.query.filter_by(email=email.recipient_email).first()
            
            # Parse old context to get some variables
            import json
            old_context = {}
            if email.context:
                try:
                    old_context = json.loads(email.context)
                except:
                    pass
            
            # Build new context with current event data
            context = {
                'user_name': user.first_name if user else old_context.get('user_name', 'Użytkowniku'),
                'event_title': event.title,
                'event_date': event.event_date.strftime('%d.%m.%Y'),
                'event_time': event.event_date.strftime('%H:%M'),
                'event_location': event.location or 'Online',
                'event_url': event.get_event_url(),  # AKTUALNY event_url!
                'event_datetime': event.event_date.strftime('%d.%m.%Y %H:%M'),
                'event_description': event.description or ''
            }
            
            # Dodaj linki do wypisania
            try:
                from app.services.unsubscribe_manager import unsubscribe_manager
                context.update({
                    'unsubscribe_url': unsubscribe_manager.get_unsubscribe_url(email.recipient_email),
                    'delete_account_url': unsubscribe_manager.get_delete_account_url(email.recipient_email)
                })
            except Exception as e:
                self.logger.warning(f"⚠️ Błąd generowania linków unsubscribe: {e}")
                context.update({
                    'unsubscribe_url': 'mailto:kontakt@klublepszezycie.pl',
                    'delete_account_url': 'mailto:kontakt@klublepszezycie.pl'
                })
            
            # Render template
            from jinja2 import Template
            html_template = Template(template.html_content)
            html_content = html_template.render(**context)
            
            text_template = Template(template.text_content)
            text_content = text_template.render(**context)
            
            subject_template = Template(template.subject)
            subject = subject_template.render(**context)
            
            return True, html_content, text_content, subject
            
        except Exception as e:
            self.logger.error(f"❌ Błąd re-renderowania emaila: {e}")
            return False, email.html_content, email.text_content, email.subject
