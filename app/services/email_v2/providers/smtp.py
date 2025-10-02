"""
SMTP provider - fallback dostawca e-maili
"""
import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Tuple

from .base import BaseEmailProvider

class SMTPProvider(BaseEmailProvider):
    """SMTP provider jako fallback dla Mailgun"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Konfiguracja SMTP
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        
        # Domyślne dane nadawcy
        self.from_email = os.getenv('SMTP_FROM_EMAIL', self.smtp_username)
        self.from_name = os.getenv('SMTP_FROM_NAME', 'Klub Lepszego Życia')
        
        # Rate limiting (bardziej konserwatywny niż Mailgun)
        self.rate_limit_delay = float(os.getenv('SMTP_RATE_DELAY', '1.0'))  # 1 sekunda
        self.max_emails_per_minute = int(os.getenv('SMTP_MAX_PER_MINUTE', '60'))
        self.max_emails_per_hour = int(os.getenv('SMTP_MAX_PER_HOUR', '1000'))
        
        # Liczniki
        self.emails_sent_this_minute = 0
        self.emails_sent_this_hour = 0
        self.minute_start_time = time.time()
        self.hour_start_time = time.time()
    
    def send_email(self, to_email: str, subject: str, html_content: str = None, 
                   text_content: str = None, from_email: str = None, 
                   from_name: str = None) -> Tuple[bool, str]:
        """Wysyła pojedynczy e-mail przez SMTP"""
        try:
            if not self.is_available():
                return False, "SMTP nie jest dostępny"
            
            # Sprawdź rate limiting
            if not self._check_rate_limits():
                return False, "Przekroczono limity wysyłania SMTP"
            
            # Przygotuj e-mail
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{from_name or self.from_name} <{from_email or self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Dodaj treść
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # Wyślij e-mail
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            self._update_counters()
            return True, "E-mail wysłany pomyślnie przez SMTP"
            
        except Exception as e:
            return False, f"Błąd wysyłania e-maila przez SMTP: {str(e)}"
    
    def send_batch(self, emails: List[Dict[str, Any]]) -> Tuple[bool, str, Dict[str, int]]:
        """Wysyła e-maile w batchu przez SMTP"""
        try:
            if not self.is_available():
                return False, "SMTP nie jest dostępny", {'sent': 0, 'failed': 0}
            
            stats = {'sent': 0, 'failed': 0}
            errors = []
            
            # SMTP jest wolniejszy, więc mniejsze batche
            batch_size = int(os.getenv('SMTP_BATCH_SIZE', '10'))
            delay_between_batches = float(os.getenv('SMTP_BATCH_DELAY', '5.0'))
            
            for i in range(0, len(emails), batch_size):
                batch = emails[i:i + batch_size]
                
                if self.logger:
                    self.logger.info(f"📦 Przetwarzam SMTP batch {i//batch_size + 1}: {len(batch)} e-maili")
                
                # Wyślij batch
                batch_sent, batch_failed, batch_errors = self._send_batch_internal(batch)
                
                stats['sent'] += batch_sent
                stats['failed'] += batch_failed
                errors.extend(batch_errors)
                
                # Opóźnienie między batchami
                if i + batch_size < len(emails):
                    time.sleep(delay_between_batches)
            
            success = stats['failed'] == 0
            message = f"Wysłano {stats['sent']} e-maili przez SMTP, błędów: {stats['failed']}"
            
            return success, message, stats
            
        except Exception as e:
            return False, f"Błąd wysyłania batch przez SMTP: {str(e)}", {'sent': 0, 'failed': len(emails)}
    
    def is_available(self) -> bool:
        """Sprawdza czy SMTP jest dostępny"""
        return bool(self.smtp_username and self.smtp_password)
    
    def _check_rate_limits(self) -> bool:
        """Sprawdza limity wysyłania SMTP"""
        now = time.time()
        
        # Reset liczników co minutę
        if now - self.minute_start_time >= 60:
            self.emails_sent_this_minute = 0
            self.minute_start_time = now
        
        # Reset liczników co godzinę
        if now - self.hour_start_time >= 3600:
            self.emails_sent_this_hour = 0
            self.hour_start_time = now
        
        # Sprawdź limity
        if self.emails_sent_this_minute >= self.max_emails_per_minute:
            return False
        
        if self.emails_sent_this_hour >= self.max_emails_per_hour:
            return False
        
        return True
    
    def _update_counters(self):
        """Aktualizuje liczniki wysłanych e-maili"""
        self.emails_sent_this_minute += 1
        self.emails_sent_this_hour += 1
    
    def _send_batch_internal(self, emails: List[Dict[str, Any]]) -> Tuple[int, int, List[str]]:
        """Wysyła pojedynczy batch e-maili przez SMTP"""
        sent = 0
        failed = 0
        errors = []
        
        for email_data in emails:
            try:
                # Sprawdź rate limiting
                if not self._check_rate_limits():
                    errors.append("Przekroczono limity wysyłania SMTP")
                    failed += 1
                    continue
                
                # Wyślij e-mail
                success, message = self.send_email(
                    to_email=email_data['to_email'],
                    subject=email_data['subject'],
                    html_content=email_data.get('html_content'),
                    text_content=email_data.get('text_content'),
                    from_email=email_data.get('from_email'),
                    from_name=email_data.get('from_name')
                )
                
                if success:
                    sent += 1
                else:
                    failed += 1
                    errors.append(message)
                
                # Opóźnienie między e-mailami
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                failed += 1
                errors.append(str(e))
        
        return sent, failed, errors




