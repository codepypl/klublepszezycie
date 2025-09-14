#!/usr/bin/env python3
"""
Skrypt do resetowania szablonów emaili do stanu domyślnego
"""
import json
from app import create_app
from models import db, EmailTemplate

def get_default_templates():
    """Zwraca domyślne szablony emaili"""
    return [
        {
            'name': 'welcome',
            'template_type': 'welcome',
            'subject': 'Witamy w Klubie Lepsze Życie!',
            'html_content': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Witamy w Klubie Lepsze Życie!</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #2c3e50; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f8f9fa; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .btn { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
        .highlight { background: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Witamy w Klubie Lepsze Życie!</h1>
        </div>
        <div class="content">
            <p>Cześć {{user_name}},</p>
            
            <p>Dziękujemy za dołączenie do Klubu Lepsze Życie! Jesteśmy podekscytowani, że będziesz częścią naszej społeczności.</p>
            
            <div class="highlight">
                <h3>Twoje dane logowania:</h3>
                <p><strong>Email:</strong> {{user_email}}</p>
                <p><strong>Hasło tymczasowe:</strong> {{temporary_password}}</p>
            </div>
            
            <p>Zalecamy zmianę hasła po pierwszym zalogowaniu. Możesz to zrobić w ustawieniach swojego konta.</p>
            
            <p style="text-align: center;">
                <a href="{{login_url}}" class="btn">Zaloguj się do klubu</a>
            </p>
            
            <p>W klubie znajdziesz:</p>
            <ul>
                <li>Ekskluzywne wydarzenia i warsztaty</li>
                <li>Dostęp do materiałów edukacyjnych</li>
                <li>Możliwość nawiązywania kontaktów z innymi członkami</li>
                <li>Wsparcie w rozwoju osobistym</li>
            </ul>
            
            <p>Jeśli masz jakiekolwiek pytania, nie wahaj się z nami skontaktować.</p>
            
            <p>Pozdrawiamy,<br>Zespół Klubu Lepsze Życie</p>
        </div>
        <div class="footer">
            <p>
                <a href="{{unsubscribe_url}}">Wypisz się z klubu</a> | 
                <a href="{{delete_account_url}}">Usuń konto</a>
            </p>
            <p>Klub Lepsze Życie - Rozwijaj się z nami!</p>
        </div>
    </div>
</body>
</html>''',
            'text_content': '''Witamy w Klubie Lepsze Życie!

Cześć {{user_name}},

Dziękujemy za dołączenie do Klubu Lepsze Życie! Jesteśmy podekscytowani, że będziesz częścią naszej społeczności.

Twoje dane logowania:
Email: {{user_email}}
Hasło tymczasowe: {{temporary_password}}

Zalecamy zmianę hasła po pierwszym zalogowaniu. Możesz to zrobić w ustawieniach swojego konta.

Link do logowania: {{login_url}}

W klubie znajdziesz:
- Ekskluzywne wydarzenia i warsztaty
- Dostęp do materiałów edukacyjnych
- Możliwość nawiązywania kontaktów z innymi członkami
- Wsparcie w rozwoju osobistym

Jeśli masz jakiekolwiek pytania, nie wahaj się z nami skontaktować.

Pozdrawiamy,
Zespół Klubu Lepsze Życie

---
Wypisz się z klubu: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
            'variables': json.dumps(['user_name', 'user_email', 'temporary_password', 'login_url', 'unsubscribe_url', 'delete_account_url']),
            'is_active': True
        },
        {
            'name': 'event_registration',
            'template_type': 'event_registration',
            'subject': 'Potwierdzenie rejestracji na wydarzenie',
            'html_content': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Potwierdzenie rejestracji na wydarzenie</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #27ae60; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f8f9fa; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .event-info { background: #e8f5e8; padding: 15px; border-left: 4px solid #27ae60; margin: 15px 0; }
        .btn { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Potwierdzenie rejestracji</h1>
        </div>
        <div class="content">
            <p>Cześć {{user_name}},</p>
            
            <p>Dziękujemy za rejestrację na wydarzenie!</p>
            
            <div class="event-info">
                <h3>Szczegóły wydarzenia:</h3>
                <p><strong>Tytuł:</strong> {{event_title}}</p>
                <p><strong>Data:</strong> {{event_date}}</p>
                <p><strong>Godzina:</strong> {{event_time}}</p>
                <p><strong>Lokalizacja:</strong> {{event_location}}</p>
            </div>
            
            <p>Wydarzenie zostało dodane do Twojego kalendarza. Otrzymasz przypomnienie 24 godziny przed rozpoczęciem.</p>
            
            <p>Jeśli masz pytania dotyczące wydarzenia, skontaktuj się z nami.</p>
            
            <p>Pozdrawiamy,<br>Zespół Klubu Lepsze Życie</p>
        </div>
        <div class="footer">
            <p>
                <a href="{{unsubscribe_url}}">Wypisz się z klubu</a> | 
                <a href="{{delete_account_url}}">Usuń konto</a>
            </p>
            <p>Klub Lepsze Życie - Rozwijaj się z nami!</p>
        </div>
    </div>
</body>
</html>''',
            'text_content': '''Potwierdzenie rejestracji na wydarzenie

Cześć {{user_name}},

Dziękujemy za rejestrację na wydarzenie!

Szczegóły wydarzenia:
Tytuł: {{event_title}}
Data: {{event_date}}
Godzina: {{event_time}}
Lokalizacja: {{event_location}}

Wydarzenie zostało dodane do Twojego kalendarza. Otrzymasz przypomnienie 24 godziny przed rozpoczęciem.

Jeśli masz pytania dotyczące wydarzenia, skontaktuj się z nami.

Pozdrawiamy,
Zespół Klubu Lepsze Życie

---
Wypisz się z klubu: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
            'variables': json.dumps(['user_name', 'event_title', 'event_date', 'event_time', 'event_location', 'unsubscribe_url', 'delete_account_url']),
            'is_active': True
        },
        {
            'name': 'event_reminder_24h',
            'template_type': 'event_reminder',
            'subject': 'Przypomnienie: {{event_title}} - jutro!',
            'html_content': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Przypomnienie o wydarzeniu</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #f39c12; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f8f9fa; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .event-info { background: #fff3cd; padding: 15px; border-left: 4px solid #f39c12; margin: 15px 0; }
        .btn { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Przypomnienie o wydarzeniu</h1>
        </div>
        <div class="content">
            <p>Cześć {{user_name}},</p>
            
            <p>Przypominamy o jutrzejszym wydarzeniu!</p>
            
            <div class="event-info">
                <h3>{{event_title}}</h3>
                <p><strong>Data:</strong> {{event_date}}</p>
                <p><strong>Godzina:</strong> {{event_time}}</p>
                <p><strong>Lokalizacja:</strong> {{event_location}}</p>
            </div>
            
            <p>Nie zapomnij o wydarzeniu! Jeśli nie możesz uczestniczyć, daj nam znać.</p>
            
            <p>Pozdrawiamy,<br>Zespół Klubu Lepsze Życie</p>
        </div>
        <div class="footer">
            <p>
                <a href="{{unsubscribe_url}}">Wypisz się z klubu</a> | 
                <a href="{{delete_account_url}}">Usuń konto</a>
            </p>
            <p>Klub Lepsze Życie - Rozwijaj się z nami!</p>
        </div>
    </div>
</body>
</html>''',
            'text_content': '''Przypomnienie o wydarzeniu

Cześć {{user_name}},

Przypominamy o jutrzejszym wydarzeniu!

{{event_title}}
Data: {{event_date}}
Godzina: {{event_time}}
Lokalizacja: {{event_location}}

Nie zapomnij o wydarzeniu! Jeśli nie możesz uczestniczyć, daj nam znać.

Pozdrawiamy,
Zespół Klubu Lepsze Życie

---
Wypisz się z klubu: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
            'variables': json.dumps(['user_name', 'event_title', 'event_date', 'event_time', 'event_location', 'unsubscribe_url', 'delete_account_url']),
            'is_active': True
        },
        {
            'name': 'event_reminder_1h',
            'template_type': 'event_reminder',
            'subject': 'Przypomnienie: {{event_title}} - za godzinę!',
            'html_content': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Przypomnienie o wydarzeniu</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #e74c3c; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f8f9fa; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .event-info { background: #f8d7da; padding: 15px; border-left: 4px solid #e74c3c; margin: 15px 0; }
        .btn { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Przypomnienie o wydarzeniu</h1>
        </div>
        <div class="content">
            <p>Cześć {{user_name}},</p>
            
            <p>Wydarzenie rozpocznie się za godzinę!</p>
            
            <div class="event-info">
                <h3>{{event_title}}</h3>
                <p><strong>Data:</strong> {{event_date}}</p>
                <p><strong>Godzina:</strong> {{event_time}}</p>
                <p><strong>Lokalizacja:</strong> {{event_location}}</p>
            </div>
            
            <p>Przygotuj się na wydarzenie! Jeśli masz pytania, skontaktuj się z nami.</p>
            
            <p>Pozdrawiamy,<br>Zespół Klubu Lepsze Życie</p>
        </div>
        <div class="footer">
            <p>
                <a href="{{unsubscribe_url}}">Wypisz się z klubu</a> | 
                <a href="{{delete_account_url}}">Usuń konto</a>
            </p>
            <p>Klub Lepsze Życie - Rozwijaj się z nami!</p>
        </div>
    </div>
</body>
</html>''',
            'text_content': '''Przypomnienie o wydarzeniu

Cześć {{user_name}},

Wydarzenie rozpocznie się za godzinę!

{{event_title}}
Data: {{event_date}}
Godzina: {{event_time}}
Lokalizacja: {{event_location}}

Przygotuj się na wydarzenie! Jeśli masz pytania, skontaktuj się z nami.

Pozdrawiamy,
Zespół Klubu Lepsze Życie

---
Wypisz się z klubu: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
            'variables': json.dumps(['user_name', 'event_title', 'event_date', 'event_time', 'event_location', 'unsubscribe_url', 'delete_account_url']),
            'is_active': True
        },
        {
            'name': 'event_reminder_5min',
            'template_type': 'event_reminder',
            'subject': 'Wydarzenie {{event_title}} rozpoczyna się za 5 minut!',
            'html_content': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Przypomnienie o wydarzeniu</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #8e44ad; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f8f9fa; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .event-info { background: #e8d5f2; padding: 15px; border-left: 4px solid #8e44ad; margin: 15px 0; }
        .btn { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Wydarzenie rozpoczyna się za 5 minut!</h1>
        </div>
        <div class="content">
            <p>Cześć {{user_name}},</p>
            
            <p>Wydarzenie rozpocznie się za 5 minut!</p>
            
            <div class="event-info">
                <h3>{{event_title}}</h3>
                <p><strong>Data:</strong> {{event_date}}</p>
                <p><strong>Godzina:</strong> {{event_time}}</p>
                <p><strong>Lokalizacja:</strong> {{event_location}}</p>
                {% if meeting_link %}
                <p><strong>Link do spotkania:</strong> <a href="{{meeting_link}}">{{meeting_link}}</a></p>
                {% endif %}
            </div>
            
            <p>Dołącz do wydarzenia już teraz!</p>
            
            <p>Pozdrawiamy,<br>Zespół Klubu Lepsze Życie</p>
        </div>
        <div class="footer">
            <p>
                <a href="{{unsubscribe_url}}">Wypisz się z klubu</a> | 
                <a href="{{delete_account_url}}">Usuń konto</a>
            </p>
            <p>Klub Lepsze Życie - Rozwijaj się z nami!</p>
        </div>
    </div>
</body>
</html>''',
            'text_content': '''Wydarzenie rozpoczyna się za 5 minut!

Cześć {{user_name}},

Wydarzenie rozpocznie się za 5 minut!

{{event_title}}
Data: {{event_date}}
Godzina: {{event_time}}
Lokalizacja: {{event_location}}
{% if meeting_link %}
Link do spotkania: {{meeting_link}}
{% endif %}

Dołącz do wydarzenia już teraz!

Pozdrawiamy,
Zespół Klubu Lepsze Życie

---
Wypisz się z klubu: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
            'variables': json.dumps(['user_name', 'event_title', 'event_date', 'event_time', 'event_location', 'meeting_link', 'unsubscribe_url', 'delete_account_url']),
            'is_active': True
        },
        {
            'name': 'admin_notification',
            'template_type': 'admin_notification',
            'subject': 'Powiadomienie administratora',
            'html_content': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Powiadomienie administratora</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #34495e; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f8f9fa; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .notification { background: #d1ecf1; padding: 15px; border-left: 4px solid #17a2b8; margin: 15px 0; }
        .info-row { margin: 10px 0; }
        .label { font-weight: bold; color: #34495e; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Powiadomienie administratora</h1>
        </div>
        <div class="content">
            <div class="notification">
                <h3>Nowa osoba dołączyła do klubu</h3>
                <div class="info-row">
                    <span class="label">Imię:</span> {{user_name}}
                </div>
                <div class="info-row">
                    <span class="label">Email:</span> {{user_email}}
                </div>
                <div class="info-row">
                    <span class="label">Telefon:</span> {{user_phone}}
                </div>
                <div class="info-row">
                    <span class="label">Data dołączenia:</span> {{registration_date}}
                </div>
            </div>
            
            <p>Pozdrawiamy,<br>System Klubu Lepsze Życie</p>
        </div>
        <div class="footer">
            <p>Klub Lepsze Życie - Panel administracyjny</p>
        </div>
    </div>
</body>
</html>''',
            'text_content': '''Powiadomienie administratora

Nowa osoba dołączyła do klubu

Imię: {{user_name}}
Email: {{user_email}}
Telefon: {{user_phone}}
Data dołączenia: {{registration_date}}

Pozdrawiamy,
System Klubu Lepsze Życie''',
            'variables': json.dumps(['user_name', 'user_email', 'user_phone', 'registration_date']),
            'is_active': True
        },
        {
            'name': 'admin_message',
            'template_type': 'campaign',
            'subject': '{{message_subject}}',
            'html_content': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{message_subject}}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #34495e; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f8f9fa; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .message { background: #ffffff; padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin: 15px 0; }
        .highlight { background: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 15px 0; }
        .btn { display: inline-block; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
        .btn:hover { background: #2980b9; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{message_subject}}</h1>
        </div>
        <div class="content">
            <div class="message">
                <h2>Cześć {{recipient_name}}!</h2>
                
                <p>{{message_content}}</p>
                
                <div class="highlight">
                    <h3>{{highlight_title}}</h3>
                    <p>{{highlight_content}}</p>
                </div>
                
                <p style="text-align: center;">
                    <a href="{{cta_url}}" class="btn">{{cta_text}}</a>
                </p>
                
                <div class="highlight">
                    <h4>Dodatkowe informacje:</h4>
                    <p>{{additional_info}}</p>
                </div>
                
                <p>Jeśli masz pytania, skontaktuj się z nami.</p>
                
                <p>Pozdrawiamy,<br>Zespół Klubu Lepsze Życie</p>
            </div>
        </div>
        <div class="footer">
            <p>
                <a href="{{unsubscribe_url}}">Wypisz się z klubu</a> | 
                <a href="{{delete_account_url}}">Usuń konto</a>
            </p>
            <p>Klub Lepsze Życie - Rozwijaj się z nami!</p>
        </div>
    </div>
</body>
</html>''',
            'text_content': '''{{message_subject}}

Cześć {{recipient_name}}!

{{message_content}}

{{highlight_title}}
{{highlight_content}}

{{cta_text}}: {{cta_url}}

Dodatkowe informacje:
{{additional_info}}
Jeśli masz pytania, skontaktuj się z nami.

Pozdrawiamy,
Zespół Klubu Lepsze Życie

---
Wypisz się z klubu: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
            'variables': json.dumps(['message_subject', 'recipient_name', 'message_content', 'highlight_title', 'highlight_content', 'cta_text', 'cta_url', 'additional_info', 'unsubscribe_url', 'delete_account_url']),
            'is_active': True
        },
        {
            'name': 'password_reset',
            'template_type': 'system',
            'subject': 'Resetowanie hasła - Klub Lepsze Życie',
            'html_content': '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Resetowanie hasła - Klub Lepsze Życie</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #e74c3c; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f8f9fa; }
        .footer { padding: 20px; text-align: center; font-size: 12px; color: #666; }
        .btn { display: inline-block; padding: 15px 30px; background: #e74c3c; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }
        .warning { background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0; }
        .security-tips { background: #e8f4f8; padding: 15px; border-radius: 5px; margin: 15px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Resetowanie hasła</h1>
        </div>
        <div class="content">
            <p>Cześć {{user_name}},</p>
            
            <p>Otrzymaliśmy prośbę o resetowanie hasła do Twojego konta w Klubie Lepsze Życie.</p>
            
            <div class="warning">
                <h3>⚠️ Ważne informacje:</h3>
                <ul>
                    <li>Ten link jest ważny przez {{expires_hours}} godzin</li>
                    <li>Link można użyć tylko raz</li>
                    <li>Jeśli nie prosiłeś o resetowanie hasła, zignoruj ten email</li>
                </ul>
            </div>
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{{reset_url}}" class="btn">Zresetuj hasło</a>
            </p>
            
            <p>Jeśli przycisk nie działa, skopiuj i wklej poniższy link do przeglądarki:</p>
            <p style="word-break: break-all; background: #f1f1f1; padding: 10px; border-radius: 3px;">
                {{reset_url}}
            </p>
            
            <div class="security-tips">
                <h3>💡 Wskazówki dotyczące bezpieczeństwa:</h3>
                <ul>
                    <li>Używaj silnego hasła z wielkimi i małymi literami, cyframi i znakami specjalnymi</li>
                    <li>Nie udostępniaj swojego hasła nikomu</li>
                    <li>Regularnie zmieniaj hasło</li>
                    <li>Jeśli podejrzewasz, że Twoje konto zostało naruszone, skontaktuj się z nami</li>
                </ul>
            </div>
            
            <p>Jeśli masz problemy z dostępem do konta lub masz pytania, skontaktuj się z naszym zespołem wsparcia.</p>
            
            <p>Pozdrawiamy,<br>Zespół Klubu Lepsze Życie</p>
        </div>
        <div class="footer">
            <p>
                <a href="{{unsubscribe_url}}">Wypisz się z klubu</a> | 
                <a href="{{delete_account_url}}">Usuń konto</a>
            </p>
            <p>Klub Lepsze Życie - Rozwijaj się z nami!</p>
        </div>
    </div>
</body>
</html>''',
            'text_content': '''Resetowanie hasła - Klub Lepsze Życie

Cześć {{user_name}},

Otrzymaliśmy prośbę o resetowanie hasła do Twojego konta w Klubie Lepsze Życie.

WAŻNE INFORMACJE:
- Ten link jest ważny przez {{expires_hours}} godzin
- Link można użyć tylko raz
- Jeśli nie prosiłeś o resetowanie hasła, zignoruj ten email

Link do resetowania hasła:
{{reset_url}}

WSKAZÓWKI DOTYCZĄCE BEZPIECZEŃSTWA:
- Używaj silnego hasła z wielkimi i małymi literami, cyframi i znakami specjalnymi
- Nie udostępniaj swojego hasła nikomu
- Regularnie zmieniaj hasło
- Jeśli podejrzewasz, że Twoje konto zostało naruszone, skontaktuj się z nami

Jeśli masz problemy z dostępem do konta lub masz pytania, skontaktuj się z naszym zespołem wsparcia.

Pozdrawiamy,
Zespół Klubu Lepsze Życie

---
Wypisz się z klubu: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
            'variables': json.dumps(['user_name', 'reset_url', 'expires_hours', 'unsubscribe_url', 'delete_account_url']),
            'is_active': True
        }
    ]

def reset_templates():
    """Resetuje szablony do stanu domyślnego"""
    app = create_app()
    with app.app_context():
        try:
            from models import EmailLog, EmailQueue, EmailCampaign
            
            # Pobierz domyślne szablony
            default_templates = get_default_templates()
            
            # Usuń wszystkie tabele w odpowiedniej kolejności (od child do parent)
            EmailLog.query.delete()
            print("🗑️ Usunięto logi emaili")
            
            EmailQueue.query.delete()
            print("🗑️ Usunięto kolejki emaili")
            
            EmailCampaign.query.delete()
            print("🗑️ Usunięto kampanie emaili")
            
            # Potem usuń wszystkie istniejące szablony
            EmailTemplate.query.delete()
            print("🗑️ Usunięto istniejące szablony")
            
            # Dodaj domyślne szablony
            for template_data in default_templates:
                template = EmailTemplate(**template_data)
                db.session.add(template)
            
            db.session.commit()
            print(f"✅ Zresetowano {len(default_templates)} szablonów do stanu domyślnego")
            
            # Wyświetl listę zresetowanych szablonów
            print("\nZresetowane szablony:")
            for template in default_templates:
                print(f"  - {template['name']} ({template['template_type']})")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Błąd podczas resetowania szablonów: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True

if __name__ == "__main__":
    reset_templates()


