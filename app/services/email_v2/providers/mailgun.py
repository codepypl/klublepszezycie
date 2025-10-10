"""
Mailgun provider - główny dostawca e-maili
"""
import os
import requests
import time
from typing import Dict, Any, List, Tuple

from .base import BaseEmailProvider

class MailgunProvider(BaseEmailProvider):
    """Provider Mailgun z inteligentnym rate limiting"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Konfiguracja Mailgun
        self.api_key = os.getenv('MAILGUN_API_KEY')
        self.domain = os.getenv('MAILGUN_DOMAIN', 'klublepszezycie.pl').strip('"')
        
        # Sprawdź czy używać EU regionu (na podstawie MAIL_SERVER)
        mail_server = os.getenv('MAIL_SERVER', '')
        if 'eu.mailgun.org' in mail_server:
            self.api_url = f"https://api.eu.mailgun.net/v3/{self.domain}/messages"
        else:
            self.api_url = f"https://api.mailgun.net/v3/{self.domain}/messages"
        
        # Rate limiting
        self.rate_limit_delay = float(os.getenv('MAILGUN_RATE_DELAY', '0.1'))  # 100ms
        self.max_emails_per_minute = int(os.getenv('MAILGUN_MAX_PER_MINUTE', '600'))
        self.max_emails_per_hour = int(os.getenv('MAILGUN_MAX_PER_HOUR', '10000'))
        
        # Liczniki
        self.emails_sent_this_minute = 0
        self.emails_sent_this_hour = 0
        self.minute_start_time = time.time()
        self.hour_start_time = time.time()
        
        # Domyślne dane nadawcy
        self.from_email = os.getenv('MAILGUN_FROM_EMAIL', f'noreply@{self.domain}')
        self.from_name = os.getenv('MAILGUN_FROM_NAME', 'Klub Lepszego Życia')
    
    def send_email(self, to_email: str, subject: str, html_content: str = None, 
                   text_content: str = None, from_email: str = None, 
                   from_name: str = None) -> Tuple[bool, str]:
        """Wysyła pojedynczy e-mail przez Mailgun"""
        try:
            # VERBOSE LOGGING - Krok 1: Sprawdzenie dostępności
            if self.logger:
                self.logger.info(f"📤 Mailgun: Próba wysłania do {to_email}")
                self.logger.info(f"   Temat: {subject}")
                self.logger.info(f"   API URL: {self.api_url}")
                self.logger.info(f"   API Key configured: {'Yes' if self.api_key else 'No'}")
                self.logger.info(f"   Domain: {self.domain}")
            
            if not self.is_available():
                if self.logger:
                    self.logger.error(f"❌ Mailgun nie jest dostępny (brak API key lub domain)")
                return False, "Mailgun nie jest dostępny"
            
            # Sprawdź rate limiting
            if not self._check_rate_limits():
                if self.logger:
                    self.logger.warning(f"⚠️ Przekroczono limity wysyłania")
                return False, "Przekroczono limity wysyłania"
            
            # Przygotuj dane
            data = {
                'from': f"{from_name or self.from_name} <{from_email or self.from_email}>",
                'to': to_email,
                'subject': subject
            }
            
            if html_content:
                data['html'] = html_content
            if text_content:
                data['text'] = text_content
            
            # VERBOSE LOGGING - Krok 2: Przed wysłaniem
            if self.logger:
                self.logger.info(f"🔄 Wysyłam request do Mailgun...")
                self.logger.info(f"   From: {data['from']}")
                self.logger.info(f"   To: {data['to']}")
            
            # Wyślij e-mail
            response = requests.post(
                self.api_url,
                auth=('api', self.api_key),
                data=data,
                timeout=30
            )
            
            # VERBOSE LOGGING - Krok 3: Response
            if self.logger:
                self.logger.info(f"📬 Mailgun response: status_code={response.status_code}")
            
            if response.status_code == 200:
                self._update_counters()
                # Pobierz Message ID z odpowiedzi Mailgun
                try:
                    response_data = response.json()
                    message_id = response_data.get('id', 'unknown')
                    
                    if self.logger:
                        self.logger.info(f"✅ Email wysłany pomyślnie!")
                        self.logger.info(f"   Message ID: {message_id}")
                        self.logger.info(f"   Response: {response_data}")
                    
                    return True, message_id
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"⚠️ Nie można parsować response JSON: {e}")
                        self.logger.info(f"   Raw response: {response.text}")
                    return True, "E-mail wysłany pomyślnie"
            else:
                error_msg = f"Błąd Mailgun: {response.status_code} - {response.text}"
                
                if self.logger:
                    self.logger.error(f"❌ Mailgun błąd: {error_msg}")
                
                return False, error_msg
                
        except Exception as e:
            error_msg = f"Błąd wysyłania e-maila: {str(e)}"
            
            if self.logger:
                self.logger.error(f"❌ Exception podczas wysyłania: {error_msg}")
                import traceback
                self.logger.error(traceback.format_exc())
            
            return False, error_msg
    
    def send_batch(self, emails: List[Dict[str, Any]]) -> Tuple[bool, str, Dict[str, int]]:
        """Wysyła e-maile w batchu z inteligentnym rozłożeniem"""
        try:
            if not self.is_available():
                return False, "Mailgun nie jest dostępny", {'sent': 0, 'failed': 0}
            
            stats = {'sent': 0, 'failed': 0}
            errors = []
            
            # Podziel na mniejsze batche
            batch_size = int(os.getenv('MAILGUN_BATCH_SIZE', '50'))
            delay_between_batches = float(os.getenv('MAILGUN_BATCH_DELAY', '1.0'))
            
            for i in range(0, len(emails), batch_size):
                batch = emails[i:i + batch_size]
                
                if self.logger:
                    self.logger.info(f"📦 Przetwarzam batch {i//batch_size + 1}: {len(batch)} e-maili")
                
                # Wyślij batch
                batch_sent, batch_failed, batch_errors = self._send_batch_internal(batch)
                
                stats['sent'] += batch_sent
                stats['failed'] += batch_failed
                errors.extend(batch_errors)
                
                # Opóźnienie między batchami
                if i + batch_size < len(emails):
                    time.sleep(delay_between_batches)
            
            success = stats['failed'] == 0
            message = f"Wysłano {stats['sent']} e-maili, błędów: {stats['failed']}"
            
            return success, message, stats
            
        except Exception as e:
            return False, f"Błąd wysyłania batch: {str(e)}", {'sent': 0, 'failed': len(emails)}
    
    def is_available(self) -> bool:
        """Sprawdza czy Mailgun jest dostępny"""
        return bool(self.api_key and self.domain)
    
    def _check_rate_limits(self) -> bool:
        """Sprawdza limity wysyłania"""
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
        """Wysyła pojedynczy batch e-maili"""
        sent = 0
        failed = 0
        errors = []
        
        for email_data in emails:
            try:
                # Sprawdź rate limiting
                if not self._check_rate_limits():
                    errors.append("Przekroczono limity wysyłania")
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
