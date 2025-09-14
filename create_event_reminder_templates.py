#!/usr/bin/env python3
"""
Skrypt do tworzenia szablonów powiadomień o wydarzeniach
"""
import os
import sys
from datetime import datetime

# Dodaj ścieżkę do aplikacji
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, EmailTemplate

def create_event_reminder_templates():
    """Tworzy szablony powiadomień o wydarzeniach"""
    app = create_app()
    
    with app.app_context():
        templates = [
            {
                'name': 'event_reminder_24h',
                'subject': 'Przypomnienie: {{event_title}} - jutro o {{event_time}}',
                'html_content': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f8f9fa;">
                    <div style="background-color: #2c3e50; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">Klub Lepsze Życie</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px;">Przypomnienie o wydarzeniu</p>
                    </div>
                    
                    <div style="padding: 30px; background-color: white;">
                        <h2 style="color: #2c3e50; margin-bottom: 20px;">Cześć {{user_name}}!</h2>
                        
                        <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                            Przypominamy o jutrzejszym wydarzeniu:
                        </p>
                        
                        <div style="background-color: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
                            <h3 style="color: #2c3e50; margin-top: 0;">{{event_title}}</h3>
                            <p style="margin: 5px 0;"><strong>📅 Data:</strong> {{event_date}}</p>
                            <p style="margin: 5px 0;"><strong>🕐 Godzina:</strong> {{event_time}}</p>
                            <p style="margin: 5px 0;"><strong>📍 Miejsce:</strong> {{event_location}}</p>
                        </div>
                        
                        <p style="font-size: 16px; color: #333;">
                            Nie zapomnij o naszym spotkaniu! Będziemy czekać na Ciebie.
                        </p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <div style="background-color: #f0f8f0; padding: 15px; border-radius: 8px; display: inline-block;">
                                <p style="margin: 0; color: #27ae60; font-weight: bold;">📅 Jutro o {{event_time}}</p>
                            </div>
                        </div>
                        
                        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="color: #7f8c8d; margin: 0;">Pozdrawiamy,<br><strong>Zespół Klubu Lepsze Życie</strong></p>
                        </div>
                    </div>
                </div>
                ''',
                'text_content': '''
                PRZYPOMNIENIE O WYDARZENIU
                
                Cześć {{user_name}}!
                
                Przypominamy o jutrzejszym wydarzeniu:
                
                ========================================
                {{event_title}}
                ========================================
                Data: {{event_date}}
                Godzina: {{event_time}}
                Miejsce: {{event_location}}
                
                Nie zapomnij o naszym spotkaniu! Będziemy czekać na Ciebie.
                
                Pozdrawiamy,
                Zespół Klubu Lepsze Życie
                ''',
                'template_type': 'event_reminder',
                'variables': '["user_name", "event_title", "event_date", "event_time", "event_location"]'
            },
            {
                'name': 'event_reminder_1h',
                'subject': 'Przypomnienie: {{event_title}} - za godzinę!',
                'html_content': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f8f9fa;">
                    <div style="background-color: #e74c3c; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">⏰ Uwaga!</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px;">Wydarzenie za godzinę!</p>
                    </div>
                    
                    <div style="padding: 30px; background-color: white;">
                        <h2 style="color: #2c3e50; margin-bottom: 20px;">Cześć {{user_name}}!</h2>
                        
                        <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                            Wydarzenie <strong>{{event_title}}</strong> rozpocznie się za godzinę!
                        </p>
                        
                        <div style="background-color: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                            <h3 style="color: #856404; margin-top: 0;">{{event_title}}</h3>
                            <p style="margin: 5px 0;"><strong>📅 Data:</strong> {{event_date}}</p>
                            <p style="margin: 5px 0;"><strong>🕐 Godzina:</strong> {{event_time}}</p>
                            <p style="margin: 5px 0;"><strong>📍 Miejsce:</strong> {{event_location}}</p>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <div style="background-color: #e74c3c; color: white; padding: 20px; border-radius: 8px; display: inline-block;">
                                <p style="margin: 0; font-size: 18px; font-weight: bold;">⏰ ZA GODZINĘ!</p>
                            </div>
                        </div>
                        
                        <p style="font-size: 16px; color: #333; text-align: center;">
                            Przygotuj się na nasze spotkanie!
                        </p>
                        
                        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="color: #7f8c8d; margin: 0;">Pozdrawiamy,<br><strong>Zespół Klubu Lepsze Życie</strong></p>
                        </div>
                    </div>
                </div>
                ''',
                'text_content': '''
                PRZYPOMNIENIE O WYDARZENIU - ZA GODZINĘ!
                
                Cześć {{user_name}}!
                
                Wydarzenie {{event_title}} rozpocznie się za godzinę!
                
                ========================================
                {{event_title}}
                ========================================
                Data: {{event_date}}
                Godzina: {{event_time}}
                Miejsce: {{event_location}}
                
                Przygotuj się na nasze spotkanie!
                
                Pozdrawiamy,
                Zespół Klubu Lepsze Życie
                ''',
                'template_type': 'event_reminder',
                'variables': '["user_name", "event_title", "event_date", "event_time", "event_location"]'
            },
            {
                'name': 'event_reminder_5min',
                'subject': 'Link do spotkania: {{event_title}} - za 5 minut!',
                'html_content': '''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f8f9fa;">
                    <div style="background-color: #27ae60; color: white; padding: 20px; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">🚀 Spotkanie za 5 minut!</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px;">Dołącz do nas!</p>
                    </div>
                    
                    <div style="padding: 30px; background-color: white;">
                        <h2 style="color: #2c3e50; margin-bottom: 20px;">Cześć {{user_name}}!</h2>
                        
                        <p style="font-size: 16px; color: #333; margin-bottom: 20px;">
                            Wydarzenie <strong>{{event_title}}</strong> rozpocznie się za 5 minut!
                        </p>
                        
                        <div style="background-color: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #27ae60;">
                            <h3 style="color: #155724; margin-top: 0;">{{event_title}}</h3>
                            <p style="margin: 5px 0;"><strong>📅 Data:</strong> {{event_date}}</p>
                            <p style="margin: 5px 0;"><strong>🕐 Godzina:</strong> {{event_time}}</p>
                            <p style="margin: 5px 0;"><strong>📍 Miejsce:</strong> {{event_location}}</p>
                        </div>
                        
                        {% if meeting_link %}
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{{meeting_link}}" style="background-color: #27ae60; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; display: inline-block; font-size: 16px; font-weight: bold;">
                                🚀 DOŁĄCZ DO SPOTKANIA
                            </a>
                        </div>
                        {% endif %}
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <div style="background-color: #27ae60; color: white; padding: 20px; border-radius: 8px; display: inline-block;">
                                <p style="margin: 0; font-size: 18px; font-weight: bold;">⏰ ZA 5 MINUT!</p>
                            </div>
                        </div>
                        
                        <p style="font-size: 16px; color: #333; text-align: center;">
                            Widzimy się już za chwilę!
                        </p>
                        
                        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="color: #7f8c8d; margin: 0;">Pozdrawiamy,<br><strong>Zespół Klubu Lepsze Życie</strong></p>
                        </div>
                    </div>
                </div>
                ''',
                'text_content': '''
                LINK DO SPOTKANIA - ZA 5 MINUT!
                
                Cześć {{user_name}}!
                
                Wydarzenie {{event_title}} rozpocznie się za 5 minut!
                
                ========================================
                {{event_title}}
                ========================================
                Data: {{event_date}}
                Godzina: {{event_time}}
                Miejsce: {{event_location}}
                
                {% if meeting_link %}
                Link do spotkania: {{meeting_link}}
                {% endif %}
                
                Widzimy się już za chwilę!
                
                Pozdrawiamy,
                Zespół Klubu Lepsze Życie
                ''',
                'template_type': 'event_reminder',
                'variables': '["user_name", "event_title", "event_date", "event_time", "event_location", "meeting_link"]'
            }
        ]
        
        for template_data in templates:
            existing_template = EmailTemplate.query.filter_by(name=template_data['name']).first()
            if not existing_template:
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
                print(f"✅ Szablon {template_data['name']} został utworzony pomyślnie!")
            else:
                print(f"❌ Szablon {template_data['name']} już istnieje.")
        
        db.session.commit()
        print("✅ Wszystkie szablony powiadomień zostały utworzone!")

if __name__ == '__main__':
    create_event_reminder_templates()


