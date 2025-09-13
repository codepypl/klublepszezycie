#!/usr/bin/env python3
"""
Dodaje szablon event_registration do bazy danych
"""
from app import create_app
from models import EmailTemplate, db

def add_event_registration_template():
    """Dodaje szablon event_registration"""
    app = create_app()
    
    with app.app_context():
        try:
            # Sprawdź czy szablon już istnieje
            existing = EmailTemplate.query.filter_by(name='event_registration').first()
            if existing:
                print("Szablon event_registration już istnieje")
                return
            
            # Utwórz nowy szablon
            template = EmailTemplate(
                name='event_registration',
                subject='Potwierdzenie zapisu na wydarzenie: {{event_name}}',
                html_content='''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <h2 style="color: #2c3e50; margin-top: 0; text-align: center;">🎉 Potwierdzenie zapisu na wydarzenie</h2>
                    </div>
                    
                    <p style="font-size: 16px; color: #333;">Cześć <strong>{{user_name}}</strong>!</p>
                    
                    <p style="font-size: 16px; color: #333;">Dziękujemy za zapisanie się na nasze wydarzenie. Oto szczegóły:</p>
                    
                    <div style="background-color: #e8f4f8; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
                        <h3 style="color: #2c3e50; margin-top: 0;">{{event_name}}</h3>
                        <p style="margin: 5px 0;"><strong>📅 Data:</strong> {{event_date}}</p>
                        <p style="margin: 5px 0;"><strong>🕐 Godzina:</strong> {{event_time}}</p>
                        <p style="margin: 5px 0;"><strong>📍 Miejsce:</strong> {{event_location}}</p>
                    </div>
                    
                    <div style="background-color: #f0f8f0; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0; color: #27ae60;"><strong>📝 Opis wydarzenia:</strong></p>
                        <p style="margin: 10px 0 0 0; color: #333;">{{event_description}}</p>
                    </div>
                    
                    <p style="font-size: 16px; color: #333;">Wkrótce otrzymasz przypomnienie o wydarzeniu. Jeśli masz pytania, skontaktuj się z nami.</p>
                    
                    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                        <p style="color: #7f8c8d; margin: 0;">Pozdrawiamy,<br><strong>Zespół Klubu Lepsze Życie</strong></p>
                    </div>
                </div>
                ''',
                text_content='''
                POTWIERDZENIE ZAPISU NA WYDARZENIE
                
                Cześć {{user_name}}!
                
                Dziękujemy za zapisanie się na nasze wydarzenie. Oto szczegóły:
                
                ========================================
                {{event_name}}
                ========================================
                Data: {{event_date}}
                Godzina: {{event_time}}
                Miejsce: {{event_location}}
                
                Opis wydarzenia:
                {{event_description}}
                
                Wkrótce otrzymasz przypomnienie o wydarzeniu. Jeśli masz pytania, skontaktuj się z nami.
                
                Pozdrawiamy,
                Zespół Klubu Lepsze Życie
                ''',
                template_type='event_registration',
                variables='["user_name", "user_email", "event_name", "event_date", "event_time", "event_location", "event_description"]',
                is_active=True
            )
            
            db.session.add(template)
            db.session.commit()
            print("✅ Szablon event_registration został utworzony pomyślnie!")
            
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia szablonu: {e}")
            db.session.rollback()

if __name__ == "__main__":
    add_event_registration_template()


