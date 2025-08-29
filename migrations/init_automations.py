#!/usr/bin/env python3
"""
Initialization script for email automations
Creates default automations for the system
"""

import sys
import os

# Dodaj ścieżkę do katalogu głównego
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from models import db, EmailTemplate, EmailAutomation
from services.email_automation_service import email_automation_service
from config import config

def create_app():
    """Create Flask app for initialization"""
    app = Flask(__name__)
    app.config.from_object(config['development'])
    
    # Initialize extensions
    db.init_app(app)
    
    return app

def create_default_templates():
    """Create default email templates if they don't exist"""
    templates_data = [
        {
            'name': 'event_reminder_24h_before',
            'subject': 'Przypomnienie: {{event_title}} - jutro o {{event_date}}',
            'html_content': '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Przypomnienie o wydarzeniu</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #007bff; margin-bottom: 10px;">📅 Przypomnienie o wydarzeniu</h1>
        <p style="font-size: 18px; color: #666;">Jutro spotykamy się na wydarzeniu!</p>
    </div>
    
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #28a745; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Przypominamy o jutrzejszym wydarzeniu:</p>
        
        <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #155724; margin-top: 0;">🎯 {{event_title}}</h3>
                            <p><strong>Data:</strong> {{event_date}}</p>
                            <p><strong>Typ:</strong> {{event_type}}</p>
                            {% if meeting_link %}
                            <p><strong>Link do spotkania:</strong> <a href="{{meeting_link}}" style="color: #155724;">{{meeting_link}}</a></p>
                            {% endif %}
                            {% if location %}
                            <p><strong>Miejsce:</strong> {{location}}</p>
                            {% endif %}
        </div>
        
        <p>Do zobaczenia jutro!</p>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Z poważaniem,<br>
            Zespół Klubu Lepsze Życie
        </p>
    </div>
</body>
</html>
            ''',
            'text_content': 'Przypomnienie o jutrzejszym wydarzeniu: {{event_title}} - {{event_date}}',
            'template_type': 'event_reminder_24h_before',
            'variables': '["name", "event_title", "event_date", "event_type", "meeting_link", "location"]'
        },
        {
            'name': 'event_reminder_1h_before',
            'subject': '🔔 Za godzinę: {{event_title}}',
            'html_content': '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wydarzenie za godzinę</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #ffc107; margin-bottom: 10px;">🔔 Wydarzenie za godzinę!</h1>
        <p style="font-size: 18px; color: #666;">Przygotuj się na spotkanie</p>
    </div>
    
    <div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #856404; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Za godzinę rozpoczyna się wydarzenie:</p>
        
        <div style="background-color: #fff; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #856404; margin-top: 0;">🎯 {{event_title}}</h3>
                            <p><strong>Data:</strong> {{event_date}}</p>
                            <p><strong>Typ:</strong> {{event_type}}</p>
                            {% if meeting_link %}
                            <p><strong>Link do spotkania:</strong> <a href="{{meeting_link}}" style="color: #856404;">{{meeting_link}}</a></p>
                            {% endif %}
                            {% if location %}
                            <p><strong>Miejsce:</strong> {{location}}</p>
                            {% endif %}
        </div>
        
        <p><strong>Przygotuj się:</strong></p>
        <ul style="text-align: left;">
            <li>Sprawdź czy masz wszystkie potrzebne materiały</li>
            <li>Upewnij się, że Twój sprzęt działa</li>
            <li>Przyjdź 5 minut wcześniej</li>
        </ul>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Do zobaczenia za godzinę!<br>
            Zespół Klubu Lepsze Życie
        </p>
    </div>
</body>
</html>
            ''',
            'text_content': 'Wydarzenie za godzinę: {{event_title}} - {{event_date}}',
            'template_type': 'event_reminder_1h_before',
            'variables': '["name", "event_title", "event_date", "event_type", "meeting_link", "location"]'
        },
        {
            'name': 'event_reminder_5min_before',
            'subject': '🚀 {{event_title}} rozpoczyna się za 5 minut!',
            'html_content': '''
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wydarzenie za 5 minut</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="text-align: center; margin-bottom: 30px;">
        <h1 style="color: #dc3545; margin-bottom: 10px;">🚀 Wydarzenie za 5 minut!</h1>
        <p style="font-size: 18px; color: #666;">Czas dołączyć do spotkania</p>
    </div>
    
    <div style="background-color: #f8d7da; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #721c24; margin-top: 0;">Cześć {{name}}!</h2>
        <p>Wydarzenie rozpoczyna się za 5 minut:</p>
        
        <div style="background-color: #fff; border: 1px solid #f5c6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
            <h3 style="color: #721c24; margin-top: 0;">🎯 {{event_title}}</h3>
                            <p><strong>Data:</strong> {{event_date}}</p>
                            <p><strong>Typ:</strong> {{event_type}}</p>
                            {% if meeting_link %}
                            <p><strong>Link do spotkania:</strong> <a href="{{meeting_link}}" style="color: #721c24; font-weight: bold;">{{meeting_link}}</a></p>
                            {% endif %}
                            {% if location %}
                            <p><strong>Miejsce:</strong> {{location}}</p>
                            {% endif %}
        </div>
        
        <div style="text-align: center; margin: 20px 0;">
                            {% if meeting_link %}
                            <a href="{{meeting_link}}" style="background-color: #dc3545; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-size: 18px; font-weight: bold;">
                                🚀 DOŁĄCZ TERAZ
                            </a>
                            {% endif %}
        </div>
        
        <p><strong>Ostatnie przygotowania:</strong></p>
        <ul style="text-align: left;">
            <li>Sprawdź połączenie internetowe</li>
            <li>Uruchom aplikację do spotkań</li>
            <li>Przygotuj notatnik</li>
        </ul>
    </div>
    
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
        <p style="color: #666; font-size: 14px;">
            Do zobaczenia za chwilę!<br>
            Zespół Klubu Lepsze Życie
        </p>
    </div>
</body>
</html>
            ''',
            'text_content': 'Wydarzenie za 5 minut: {{event_title}} - {{event_date}}',
            'template_type': 'event_reminder_5min_before',
            'variables': '["name", "event_title", "event_date", "event_type", "meeting_link", "location"]'
        }
    ]
    
    created_templates = []
    
    for template_data in templates_data:
        existing_template = EmailTemplate.query.filter_by(template_type=template_data['template_type']).first()
        if not existing_template:
            template = EmailTemplate(**template_data)
            db.session.add(template)
            created_templates.append(template_data['name'])
            print(f"✓ Utworzono szablon: {template_data['name']}")
        else:
            print(f"✓ Szablon już istnieje: {template_data['name']}")
    
    db.session.commit()
    return created_templates

def create_default_automations():
    """Create default email automations"""
    automations = []
    
    try:
        # Automatyzacja emaila powitalnego
        welcome_automation = email_automation_service.create_welcome_automation()
        automations.append(welcome_automation)
        print(f"✓ Utworzono automatyzację: {welcome_automation.name}")
        
        # Automatyzacje przypomnień o wydarzeniach
        reminder_types = ['24h_before', '1h_before', '5min_before']
        for reminder_type in reminder_types:
            try:
                automation = email_automation_service.create_event_reminder_automation(reminder_type)
                automations.append(automation)
                print(f"✓ Utworzono automatyzację: {automation.name}")
            except Exception as e:
                print(f"⚠️ Nie udało się utworzyć automatyzacji {reminder_type}: {e}")
        
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia automatyzacji: {e}")
        return False
    
    return automations

def main():
    """Main initialization function"""
    print("🚀 Inicjalizacja systemu automatyzacji emailowych...")
    print("=" * 60)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Utwórz domyślne szablony
            print("\n📧 Tworzenie domyślnych szablonów emaili...")
            created_templates = create_default_templates()
            
            if created_templates:
                print(f"✅ Utworzono {len(created_templates)} nowych szablonów")
            else:
                print("ℹ️ Wszystkie szablony już istnieją")
            
            # Utwórz domyślne automatyzacje
            print("\n🤖 Tworzenie domyślnych automatyzacji...")
            automations = create_default_automations()
            
            if automations:
                print(f"✅ Utworzono {len(automations)} automatyzacji")
            else:
                print("❌ Nie udało się utworzyć automatyzacji")
                return False
            
            print("\n🎉 Inicjalizacja zakończona pomyślnie!")
            print("\n📋 Utworzone automatyzacje:")
            for automation in automations:
                print(f"   • {automation.name} ({automation.automation_type})")
            
            print("\n✨ System automatyzacji jest gotowy do użycia!")
            return True
            
        except Exception as e:
            print(f"\n❌ Błąd podczas inicjalizacji: {e}")
            return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

