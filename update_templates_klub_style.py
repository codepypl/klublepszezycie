#!/usr/bin/env python3
"""
Skrypt do aktualizacji szablonów e-mail zgodnie ze stylistyką Klub Lepsze Życie
"""

import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, EmailTemplate

def load_css_styles():
    """Wczytaj style CSS z pliku"""
    css_file = os.path.join(os.path.dirname(__file__), 'static', 'css', 'email_templates_klub.css')
    
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Nie znaleziono pliku CSS: {css_file}")
        return None

def create_klub_template_content(template_name, css_styles):
    """Tworzy zawartość szablonu zgodną ze stylistyką Klub Lepsze Życie"""
    
    template_class = get_template_class(template_name)
    subtitle = get_subtitle(template_name)
    content = get_template_content(template_name)
    
    base_html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{subject}}</title>
    <style>
{css_styles}
    </style>
</head>
<body>
    <div class="email-container {template_class}">
        <div class="header">
            <h1>Klub Lepsze Życie</h1>
            <p class="subtitle">{subtitle}</p>
        </div>
        
        <div class="content">
            {content}
        </div>
        
        <div class="footer">
            <div class="logo">Klub Lepsze Życie</div>
            <p>Dziękujemy za bycie częścią naszej społeczności!</p>
            <p>W razie pytań skontaktuj się z nami: kontakt@klublepszezycie.pl</p>
            
            <div class="unsubscribe-links">
                <a href="{{unsubscribe_url}}" target="_blank">Opuść klub</a> |
                <a href="{{delete_account_url}}" target="_blank">Usuń konto</a>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    return base_html.strip()

def get_template_class(template_name):
    """Zwraca klasę CSS dla danego szablonu"""
    if 'reminder_24h' in template_name:
        return 'reminder-24h'
    elif 'reminder_1h' in template_name:
        return 'reminder-1h'
    elif 'reminder_5min' in template_name:
        return 'reminder-5min'
    elif 'security_alert' in template_name:
        return 'security-alert'
    elif 'welcome' in template_name:
        return 'welcome-email'
    return ''

def get_subtitle(template_name):
    """Zwraca podtytuł dla danego szablonu"""
    if 'reminder_24h' in template_name:
        return 'Przypomnienie o wydarzeniu (24h)'
    elif 'reminder_1h' in template_name:
        return 'Przypomnienie o wydarzeniu (1h)'
    elif 'reminder_5min' in template_name:
        return 'Przypomnienie o wydarzeniu (5 min)'
    elif 'security_alert' in template_name:
        return 'Alert bezpieczeństwa'
    elif 'welcome' in template_name:
        return 'Witamy w Klubie!'
    return 'Wiadomość od Klub Lepsze Życie'

def get_template_content(template_name):
    """Zwraca zawartość dla danego szablonu"""
    
    if 'reminder_24h' in template_name or 'reminder_1h' in template_name or 'reminder_5min' in template_name:
        return """            <h2>Przypomnienie o wydarzeniu</h2>
            
            <p>Cześć {{user_name}}!</p>
            
            <p>Przypominamy o nadchodzącym wydarzeniu:</p>
            
            <div class="event-details">
                <h3>{{event_title}}</h3>
                <div class="detail-row">
                    <span class="detail-label">📅 Data:</span>
                    <span class="detail-value">{{event_date}}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">🕐 Godzina:</span>
                    <span class="detail-value">{{event_time}}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">📍 Lokalizacja:</span>
                    <span class="detail-value">{{event_location}}</span>
                </div>
            </div>
            
            <p>Nie przegap tego wydarzenia! Kliknij poniższy przycisk, aby dołączyć:</p>
            
            <div style="text-align: center;">
                <a href="{{event_url}}" class="button">Dołącz do wydarzenia</a>
            </div>
            
            <p>Do zobaczenia na wydarzeniu!</p>
            
            <p>Zespół Klub Lepsze Życie</p>"""
    
    elif 'security_alert' in template_name:
        return """            <h2>Alert bezpieczeństwa</h2>
            
            <p>Cześć {{user_name}}!</p>
            
            <div class="alert danger">
                <strong>⚠️ Wykryto podejrzaną aktywność na Twoim koncie</strong>
            </div>
            
            <p>Zarejestrowaliśmy następującą aktywność:</p>
            
            <div class="event-details">
                <div class="detail-row">
                    <span class="detail-label">🆔 Request ID:</span>
                    <span class="detail-value">{{request_id}}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">🔐 Session ID:</span>
                    <span class="detail-value">{{session_id}}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">⚠️ Poziom zagrożenia:</span>
                    <span class="detail-value">{{severity}}</span>
                </div>
            </div>
            
            <p>Jeśli to nie Ty wykonałeś tę aktywność, natychmiast zmień hasło:</p>
            
            <div style="text-align: center;">
                <a href="{{login_url}}" class="button danger">Zmień hasło</a>
            </div>
            
            <p>Jeśli masz pytania, skontaktuj się z nami.</p>
            
            <p>Zespół bezpieczeństwa Klub Lepsze Życie</p>"""
    
    elif 'welcome' in template_name:
        return """            <h2>Witamy w Klubie Lepsze Życie!</h2>
            
            <p>Cześć {{user_name}}!</p>
            
            <p>Dziękujemy za dołączenie do naszej społeczności! Jesteśmy podekscytowani, że jesteś z nami.</p>
            
            <div class="alert success">
                <strong>🎉 Twoje konto zostało utworzone pomyślnie!</strong>
            </div>
            
            <p>Możesz teraz:</p>
            <ul>
                <li>Zalogować się do swojego konta</li>
                <li>Przeglądać nadchodzące wydarzenia</li>
                <li>Dołączać do naszych spotkań</li>
                <li>Korzystać z wszystkich funkcji klubu</li>
            </ul>
            
            <div style="text-align: center;">
                <a href="{{login_url}}" class="button">Zaloguj się</a>
            </div>
            
            <p>Jeśli masz pytania, nie wahaj się z nami skontaktować!</p>
            
            <p>Zespół Klub Lepsze Życie</p>"""
    
    else:
        return """            <h2>{{subject}}</h2>
            
            <p>Cześć {{user_name}}!</p>
            
            <p>Treść wiadomości...</p>
            
            <p>Zespół Klub Lepsze Życie</p>"""

def update_templates_with_klub_style():
    """Aktualizuje wszystkie szablony e-mail zgodnie ze stylistyką Klub Lepsze Życie"""
    
    print("🎨 Aktualizuję szablony e-mail zgodnie ze stylistyką Klub Lepsze Życie...")
    
    # Wczytaj style CSS
    css_styles = load_css_styles()
    if not css_styles:
        return False, "Nie można wczytać stylów CSS"
    
    app = create_app()
    with app.app_context():
        try:
            # Pobierz wszystkie aktywne szablony
            templates = EmailTemplate.query.filter_by(is_active=True).all()
            
            if not templates:
                return False, "Nie znaleziono aktywnych szablonów"
            
            updated_count = 0
            
            for template in templates:
                print(f"   📝 Aktualizuję szablon: {template.name}")
                
                # Utwórz nową zawartość HTML
                new_html_content = create_klub_template_content(template.name, css_styles)
                
                # Aktualizuj szablon
                template.html_content = new_html_content
                template.updated_at = datetime.utcnow()
                
                updated_count += 1
            
            # Zapisz zmiany
            db.session.commit()
            
            print(f"✅ Zaktualizowano {updated_count} szablonów e-mail")
            return True, f"Zaktualizowano {updated_count} szablonów"
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Błąd aktualizacji szablonów: {str(e)}")
            return False, f"Błąd: {str(e)}"

def main():
    """Główna funkcja"""
    print("🚀 Rozpoczynam aktualizację szablonów e-mail...")
    print(f"📅 Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    success, message = update_templates_with_klub_style()
    
    print("-" * 50)
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
