"""
Fallback email sender używający standardowego SMTP gdy Mailgun nie działa
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Tuple
from app.models.email_model import EmailQueue
import os
import json

class EmailFallbackSender:
    """Fallback sender używający SMTP gdy Mailgun nie działa"""
    
    def __init__(self):
        self.mail_server = os.getenv('MAIL_SERVER', 'smtp.eu.mailgun.org')
        self.mail_port = int(os.getenv('MAIL_PORT', '587'))
        self.mail_username = os.getenv('MAIL_USERNAME')
        self.mail_password = os.getenv('MAIL_PASSWORD')
        self.mail_use_tls = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
        
        # Debug info
        if not self.mail_username:
            logging.warning("MAIL_USERNAME not set for fallback sender")
        if not self.mail_password:
            logging.warning("MAIL_PASSWORD not set for fallback sender")
    
    async def send_batch(self, emails: List[EmailQueue]) -> Tuple[bool, str]:
        """Wysyła paczkę emaili przez SMTP"""
        try:
            if not self.mail_username or not self.mail_password:
                return False, "SMTP credentials not configured"
            
            # Połącz z serwerem SMTP
            server = smtplib.SMTP(self.mail_server, self.mail_port)
            
            if self.mail_use_tls:
                server.starttls()
            
            # Zaloguj się
            server.login(self.mail_username, self.mail_password)
            
            sent_count = 0
            failed_count = 0
            
            # Wyślij każdy email osobno
            for email in emails:
                try:
                    # Przygotuj email
                    msg = self._prepare_email(email)
                    
                    # Wyślij
                    server.send_message(msg)
                    sent_count += 1
                    
                    logging.info(f"✅ Email sent via SMTP: {email.recipient_email}")
                    
                except Exception as e:
                    failed_count += 1
                    logging.error(f"❌ Failed to send email to {email.recipient_email}: {e}")
            
            # Zamknij połączenie
            server.quit()
            
            if sent_count > 0:
                return True, f"Sent {sent_count} emails via SMTP, {failed_count} failed"
            else:
                return False, f"Failed to send any emails via SMTP"
                
        except Exception as e:
            logging.error(f"❌ SMTP fallback error: {e}")
            return False, f"SMTP error: {str(e)}"
    
    def _prepare_email(self, email: EmailQueue) -> MIMEMultipart:
        """Przygotowuje email do wysłania"""
        msg = MIMEMultipart('alternative')
        
        # Nagłówki
        msg['From'] = f"Klub Lepsze Życie <{self.mail_username}>"
        msg['To'] = email.recipient_email
        msg['Subject'] = email.subject
        
        # Dodaj nazwę odbiorcy jeśli dostępna
        if email.recipient_name:
            msg['To'] = f"{email.recipient_name} <{email.recipient_email}>"
        
        # Parsuj kontekst
        try:
            context = json.loads(email.context) if email.context else {}
        except:
            context = {}
        
        # Dodaj unsubscribe links do kontekstu
        from app.services.unsubscribe_manager import unsubscribe_manager
        context['unsubscribe_url'] = unsubscribe_manager.get_unsubscribe_url(email.recipient_email)
        context['delete_account_url'] = unsubscribe_manager.get_delete_account_url(email.recipient_email)
        
        # HTML content
        html_content = email.html_content or "<p>Brak treści HTML</p>"
        
        # Text content
        text_content = email.text_content or "Brak treści tekstowej"
        
        # Dodaj unsubscribe links do HTML
        if context.get('unsubscribe_url') and context.get('delete_account_url'):
            unsubscribe_html = f'''
<div style="margin-top: 40px; padding: 20px; background-color: #f8f9fa; border-top: 1px solid #dee2e6; text-align: center; font-size: 12px; color: #6c757d;">
    <p style="margin: 0 0 10px 0;">
        <a href="{context['unsubscribe_url']}" target="_blank" style="color: #6c757d; text-decoration: underline;">Zrezygnuj z członkostwa w klubie</a> | 
        <a href="{context['delete_account_url']}" target="_blank" style="color: #dc3545; text-decoration: underline;">Usuń konto</a>
    </p>
    <p style="margin: 0; font-size: 11px;">
        Te linki są ważne przez 30 dni.
    </p>
</div>'''
            
            unsubscribe_text = f'''

---
Zrezygnuj z członkostwa w klubie: {context['unsubscribe_url']}
Usuń konto: {context['delete_account_url']}'''
            
            html_content += unsubscribe_html
            text_content += unsubscribe_text
        
        # Dodaj części
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        return msg
