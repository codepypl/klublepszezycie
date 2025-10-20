"""
Email Cron Service - System emaili z przetwarzaniem przez cron
"""
import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

from app import db
from app.models import EmailQueue, EmailLog, EmailTemplate, User
from app.utils.timezone_utils import get_local_now
from app.services.email_v2.providers import MailgunProvider, SMTPProvider

logger = logging.getLogger(__name__)

class EmailCronService:
    """
    Serwis emaili z przetwarzaniem przez cron
    
    Zasady:
    1. Maile dodawane asynchronicznie do kolejki
    2. Przetwarzanie uruchamiane przez cron (co 1-5 minut)
    3. Inteligentne retry i fallback
    4. Kontrola limitów i priorytetów
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Konfiguracja
        self.batch_size = int(os.getenv('EMAIL_BATCH_SIZE', '50'))
        self.max_retries = int(os.getenv('EMAIL_MAX_RETRIES', '3'))
        self.retry_delay = int(os.getenv('EMAIL_RETRY_DELAY', '300'))  # 5 minut
        self.daily_limit = int(os.getenv('EMAIL_DAILY_LIMIT', '10000'))
        
        # Inicjalizacja providerów
        self.mailgun = MailgunProvider({})
        self.smtp = SMTPProvider({})
        
        # Ustaw loggery
        self.mailgun.set_logger(self.logger)
        self.smtp.set_logger(self.logger)
        
        self.logger.info("📧 EmailCronService zainicjalizowany")
    
    def add_email_to_queue(self, 
                          to_email: str, 
                          template_name: str, 
                          context: Dict = None, 
                          priority: int = 2,
                          scheduled_at: datetime = None,
                          event_id: int = None,
                          campaign_id: int = None) -> Tuple[bool, str, int]:
        """
        Dodaje email do kolejki asynchronicznie
        
        Args:
            to_email: Adres email odbiorcy
            template_name: Nazwa szablonu
            context: Zmienne szablonu
            priority: Priorytet (0=system, 1=event, 2=campaign)
            scheduled_at: Kiedy wysłać (None = natychmiast)
            event_id: ID wydarzenia (opcjonalne)
            campaign_id: ID kampanii (opcjonalne)
            
        Returns:
            (success, message, email_id)
        """
        try:
            # Sprawdź czy użytkownik istnieje
            user = User.query.filter_by(email=to_email).first()
            if not user:
                return False, f"Użytkownik {to_email} nie istnieje", None
            
            # Pobierz szablon
            template = EmailTemplate.query.filter_by(name=template_name, is_active=True).first()
            if not template:
                return False, f"Szablon {template_name} nie istnieje", None
            
            # Sprawdź duplikaty
            content_hash = self._generate_content_hash(template, context)
            existing = EmailQueue.query.filter_by(
                recipient_email=to_email,
                content_hash=content_hash,
                status='pending'
            ).first()
            
            if existing:
                return False, "Email już istnieje w kolejce", existing.id
            
            # Sprawdź dzienny limit
            if not self._check_daily_limit():
                return False, "Dzienny limit emaili przekroczony", None
            
            # Przygotuj dane emaila
            email_data = {
                'campaign_id': campaign_id,
                'template_id': template.id,
                'event_id': event_id,
                'recipient_email': to_email,
                'recipient_name': user.first_name or user.email,
                'template_name': template_name,
                'subject': self._render_template(template.subject, context or {}),
                'html_content': self._render_template(template.html_content, context or {}),
                'text_content': self._render_template(template.text_content, context or {}),
                'context': json.dumps(context or {}),
                'status': 'pending',
                'priority': priority,
                'retry_count': 0,
                'max_retries': self.max_retries,
                'scheduled_at': scheduled_at or get_local_now(),
                'content_hash': content_hash,
                'duplicate_check_key': f"{to_email}_{template_name}_{event_id or ''}"
            }
            
            # Dodaj do kolejki
            email = EmailQueue(**email_data)
            db.session.add(email)
            db.session.commit()
            
            self.logger.info(f"✅ Dodano email do kolejki: {to_email} ({template_name})")
            return True, "Email dodany do kolejki", email.id
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"❌ Błąd dodawania emaila do kolejki: {e}")
            return False, f"Błąd dodawania do kolejki: {str(e)}", None
    
    def process_queue_cron(self, limit: int = None) -> Dict[str, Any]:
        """
        Przetwarza kolejkę emaili - wywoływane przez cron
        
        Args:
            limit: Maksymalna liczba emaili do przetworzenia
            
        Returns:
            Statystyki przetwarzania
        """
        try:
            self.logger.info("🔄 Rozpoczynam przetwarzanie kolejki emaili (cron)")
            
            # Pobierz emaile do przetworzenia
            query = EmailQueue.query.filter(
                EmailQueue.status == 'pending',
                EmailQueue.scheduled_at <= get_local_now()
            ).order_by(
                EmailQueue.priority.asc(),
                EmailQueue.created_at.asc()
            )
            
            if limit:
                query = query.limit(limit)
            else:
                query = query.limit(self.batch_size)
            
            emails = query.all()
            
            if not emails:
                self.logger.info("ℹ️ Brak emaili do przetworzenia")
                return {
                    'processed': 0,
                    'success': 0,
                    'failed': 0,
                    'skipped': 0
                }
            
            # Przetwórz emaile
            stats = {
                'processed': 0,
                'success': 0,
                'failed': 0,
                'skipped': 0
            }
            
            for email in emails:
                try:
                    # Oznacz jako przetwarzany
                    email.status = 'sending'
                    email.started_at = get_local_now()
                    db.session.commit()
                    
                    # Wyślij email
                    success = self._send_single_email(email)
                    
                    if success:
                        email.status = 'sent'
                        email.sent_at = get_local_now()
                        stats['success'] += 1
                        self.logger.info(f"✅ Wysłano email: {email.recipient_email}")
                    else:
                        # Retry logic
                        if email.retry_count < email.max_retries:
                            email.status = 'pending'
                            email.retry_count += 1
                            email.scheduled_at = get_local_now() + timedelta(minutes=self.retry_delay * email.retry_count)
                            stats['skipped'] += 1
                            self.logger.warning(f"⚠️ Email w kolejce do ponownej próby: {email.recipient_email}")
                        else:
                            email.status = 'failed'
                            stats['failed'] += 1
                            self.logger.error(f"❌ Email nieudany po {email.max_retries} próbach: {email.recipient_email}")
                    
                    stats['processed'] += 1
                    db.session.commit()
                    
                except Exception as e:
                    self.logger.error(f"❌ Błąd przetwarzania emaila {email.id}: {e}")
                    email.status = 'failed'
                    email.error_message = str(e)
                    stats['failed'] += 1
                    stats['processed'] += 1
                    db.session.commit()
            
            self.logger.info(f"✅ Przetworzono {stats['processed']} emaili: {stats['success']} sukces, {stats['failed']} błąd, {stats['skipped']} do ponownej próby")
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Błąd przetwarzania kolejki: {e}")
            return {
                'processed': 0,
                'success': 0,
                'failed': 0,
                'skipped': 0,
                'error': str(e)
            }
    
    def _send_single_email(self, email: EmailQueue) -> bool:
        """
        Wysyła pojedynczy email z fallback
        
        Args:
            email: Obiekt EmailQueue
            
        Returns:
            True jeśli wysłano pomyślnie
        """
        try:
            # Spróbuj Mailgun
            if self.mailgun.is_available():
                success = self.mailgun.send_email(
                    to_email=email.recipient_email,
                    to_name=email.recipient_name,
                    subject=email.subject,
                    html_content=email.html_content,
                    text_content=email.text_content
                )
                if success:
                    return True
            
            # Fallback na SMTP
            if self.smtp.is_available():
                success = self.smtp.send_email(
                    to_email=email.recipient_email,
                    to_name=email.recipient_name,
                    subject=email.subject,
                    html_content=email.html_content,
                    text_content=email.text_content
                )
                if success:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Błąd wysyłania emaila {email.id}: {e}")
            return False
    
    def _generate_content_hash(self, template: EmailTemplate, context: Dict) -> str:
        """Generuje hash zawartości emaila dla detekcji duplikatów"""
        import hashlib
        
        content = f"{template.subject}_{template.html_content}_{json.dumps(context, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _render_template(self, template_content: str, context: Dict) -> str:
        """Renderuje szablon z kontekstem"""
        try:
            from jinja2 import Template
            template = Template(template_content)
            return template.render(**context)
        except Exception as e:
            self.logger.error(f"❌ Błąd renderowania szablonu: {e}")
            return template_content
    
    def _check_daily_limit(self) -> bool:
        """Sprawdza czy nie przekroczono dziennego limitu emaili"""
        today = get_local_now().date()
        sent_today = EmailQueue.query.filter(
            EmailQueue.status == 'sent',
            db.func.date(EmailQueue.sent_at) == today
        ).count()
        
        return sent_today < self.daily_limit
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Zwraca statystyki kolejki"""
        try:
            stats = {
                'pending': EmailQueue.query.filter_by(status='pending').count(),
                'sending': EmailQueue.query.filter_by(status='sending').count(),
                'sent': EmailQueue.query.filter_by(status='sent').count(),
                'failed': EmailQueue.query.filter_by(status='failed').count(),
                'total': EmailQueue.query.count()
            }
            
            # Statystyki dzisiejsze
            today = get_local_now().date()
            stats['sent_today'] = EmailQueue.query.filter(
                EmailQueue.status == 'sent',
                db.func.date(EmailQueue.sent_at) == today
            ).count()
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Błąd pobierania statystyk: {e}")
            return {}
    
    def cleanup_old_emails(self, days: int = 30) -> int:
        """Usuwa stare emaile z kolejki"""
        try:
            cutoff_date = get_local_now() - timedelta(days=days)
            
            # Usuń stare wysłane emaile
            deleted = EmailQueue.query.filter(
                EmailQueue.status.in_(['sent', 'failed']),
                EmailQueue.sent_at < cutoff_date
            ).delete()
            
            db.session.commit()
            
            self.logger.info(f"🗑️ Usunięto {deleted} starych emaili")
            return deleted
            
        except Exception as e:
            self.logger.error(f"❌ Błąd czyszczenia starych emaili: {e}")
            db.session.rollback()
            return 0

# Globalna instancja
email_cron_service = EmailCronService()

