#!/usr/bin/env python3
"""
Skrypt do tworzenia podstawowych szablonów emaili
"""
import os
import sys
from datetime import datetime

# Dodaj ścieżkę do aplikacji
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, EmailTemplate

def create_templates():
    """Tworzy podstawowe szablony emaili"""
    templates = [
        {
            'name': 'welcome',
            'subject': 'Witamy w Klubie Lepsze Życie! 🎉',
            'html_content': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Witamy w Klubie Lepsze Życie!</h2>
                <p>Cześć {{user_name}}!</p>
                <p>Dziękujemy za dołączenie do naszego klubu. Jesteśmy podekscytowani, że będziesz częścią naszej społeczności!</p>
                <p>Wkrótce otrzymasz informacje o naszych wydarzeniach i spotkaniach.</p>
                <p>Pozdrawiamy,<br>Zespół Klubu Lepsze Życie</p>
            </div>
            ''',
            'text_content': '''
            Witamy w Klubie Lepsze Życie!
            
            Cześć {{user_name}}!
            
            Dziękujemy za dołączenie do naszego klubu. Jesteśmy podekscytowani, że będziesz częścią naszej społeczności!
            
            Wkrótce otrzymasz informacje o naszych wydarzeniach i spotkaniach.
            
            Pozdrawiamy,
            Zespół Klubu Lepsze Życie
            ''',
            'template_type': 'welcome',
            'variables': '["user_name", "user_email"]'
        },
        {
            'name': 'registration_confirmation',
            'subject': 'Potwierdzenie zapisu na wydarzenie: {{event_title}}',
            'html_content': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Potwierdzenie zapisu na wydarzenie</h2>
                <p>Cześć {{user_name}}!</p>
                <p>Potwierdzamy Twoje zapisanie na wydarzenie:</p>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #2c3e50; margin-top: 0;">{{event_title}}</h3>
                    <p><strong>Data:</strong> {{event_date}}</p>
                </div>
                <p>Wkrótce otrzymasz przypomnienie o wydarzeniu.</p>
                <p>Pozdrawiamy,<br>Zespół Klubu Lepsze Życie</p>
            </div>
            ''',
            'text_content': '''
            Potwierdzenie zapisu na wydarzenie
            
            Cześć {{user_name}}!
            
            Potwierdzamy Twoje zapisanie na wydarzenie:
            
            {{event_title}}
            Data: {{event_date}}
            
            Wkrótce otrzymasz przypomnienie o wydarzeniu.
            
            Pozdrawiamy,
            Zespół Klubu Lepsze Życie
            ''',
            'template_type': 'registration_confirmation',
            'variables': '["user_name", "event_title", "event_date"]'
        },
        {
            'name': 'club_welcome',
            'subject': 'Witamy w gronie członków klubu! 🎉',
            'html_content': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Witamy w gronie członków klubu!</h2>
                <p>Cześć {{user_name}}!</p>
                <p>Gratulujemy! Jesteś teraz oficjalnym członkiem Klubu Lepsze Życie!</p>
                <p>Jako członek klubu będziesz otrzymywać:</p>
                <ul>
                    <li>Ekskluzywne zaproszenia na wydarzenia</li>
                    <li>Dostęp do zamkniętych spotkań</li>
                    <li>Materiały edukacyjne</li>
                    <li>Wsparcie naszej społeczności</li>
                </ul>
                <p>Pozdrawiamy,<br>Zespół Klubu Lepsze Życie</p>
            </div>
            ''',
            'text_content': '''
            Witamy w gronie członków klubu!
            
            Cześć {{user_name}}!
            
            Gratulujemy! Jesteś teraz oficjalnym członkiem Klubu Lepsze Życie!
            
            Jako członek klubu będziesz otrzymywać:
            - Ekskluzywne zaproszenia na wydarzenia
            - Dostęp do zamkniętych spotkań
            - Materiały edukacyjne
            - Wsparcie naszej społeczności
            
            Pozdrawiamy,
            Zespół Klubu Lepsze Życie
            ''',
            'template_type': 'club_welcome',
            'variables': '["user_name", "user_email"]'
        },
        {
            'name': 'admin_notification',
            'subject': 'Nowa rejestracja na wydarzenie: {{event_title}}',
            'html_content': '''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2c3e50;">Nowa rejestracja na wydarzenie</h2>
                <p>Cześć {{admin_name}}!</p>
                <p>Otrzymaliśmy nową rejestrację na wydarzenie:</p>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #2c3e50; margin-top: 0;">{{event_title}}</h3>
                    <p><strong>Data:</strong> {{event_date}}</p>
                    <p><strong>Użytkownik:</strong> {{user_name}} ({{user_email}})</p>
                </div>
                <p>Pozdrawiamy,<br>System Klubu Lepsze Życie</p>
            </div>
            ''',
            'text_content': '''
            Nowa rejestracja na wydarzenie
            
            Cześć {{admin_name}}!
            
            Otrzymaliśmy nową rejestrację na wydarzenie:
            
            {{event_title}}
            Data: {{event_date}}
            Użytkownik: {{user_name}} ({{user_email}})
            
            Pozdrawiamy,
            System Klubu Lepsze Życie
            ''',
            'template_type': 'admin_notification',
            'variables': '["admin_name", "user_name", "user_email", "event_title", "event_date"]'
        }
    ]
    
    created = 0
    for template_data in templates:
        # Sprawdź czy szablon już istnieje
        existing = EmailTemplate.query.filter_by(name=template_data['name']).first()
        
        if not existing:
            template = EmailTemplate(
                name=template_data['name'],
                subject=template_data['subject'],
                html_content=template_data['html_content'],
                text_content=template_data['text_content'],
                template_type=template_data['template_type'],
                variables=template_data['variables'],
                is_active=True
            )
            
            db.session.add(template)
            created += 1
            print(f"✅ Utworzono szablon: {template_data['name']}")
        else:
            print(f"⚠️  Szablon już istnieje: {template_data['name']}")
    
    db.session.commit()
    print(f"\n🎉 Utworzono {created} nowych szablonów emaili")

def main():
    """Główna funkcja"""
    print("Tworzenie podstawowych szablonów emaili...")
    
    try:
        app = create_app()
        
        with app.app_context():
            create_templates()
            
    except Exception as e:
        print(f"❌ Błąd: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()




