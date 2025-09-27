#!/usr/bin/env python3
"""
Aktualizuje szablony email z lepszym wyeksponowaniem kluczowych informacji
i granatowym kolorem zgodnym z logo klublepszezycie.pl
"""

from app import create_app
from app.models.email_model import EmailTemplate
from app.services.email_service import EmailService
from app.models import db

def create_enhanced_welcome_template():
    """Ulepszony szablon powitalny z lepszym wyeksponowaniem"""
    return '''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Witamy w Klubie Lepsze Życie!</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; color: #1a202c; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); color: white; padding: 40px 30px; text-align: center; position: relative;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">🎉 Witamy w Klubie!</h1>
            <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.9;">Klub Lepsze Życie</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 50px 40px;">
            <h2 style="color: #16a34a; font-size: 28px; font-weight: 600; margin-bottom: 25px; border-bottom: 3px solid #16a34a; padding-bottom: 15px;">Cześć {{user_name}}!</h2>
            
            <p style="font-size: 18px; margin-bottom: 25px; color: #2d3748;">Dziękujemy za dołączenie do <strong>Klubu Lepsze Życie</strong>! Jesteśmy podekscytowani, że będziesz częścią naszej społeczności.</p>
            
            <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 1px solid #bbf7d0; border-radius: 12px; padding: 30px; margin: 30px 0;">
                <h3 style="color: #15803d; font-size: 22px; font-weight: 600; margin-top: 0; margin-bottom: 20px;">🔑 Twoje dane logowania:</h3>
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #bbf7d0;">
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #15803d; min-width: 120px; margin-right: 16px;">📧 Email:</span>
                        <span style="color: #2d3748; flex: 1; font-size: 16px; font-weight: 500;">{{user_email}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #15803d; min-width: 120px; margin-right: 16px;">🔐 Hasło:</span>
                        <span style="color: #15803d; flex: 1; font-size: 18px; font-weight: 700; letter-spacing: 1px;">{{temporary_password}}</span>
                    </div>
                </div>
            </div>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #92400e; font-size: 16px;">⚠️ Ważne: Zalecamy zmianę hasła po pierwszym zalogowaniu.</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{login_url}}" style="display: inline-block; background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); color: white; padding: 18px 36px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 18px; box-shadow: 0 4px 12px rgba(22, 163, 74, 0.3);">Zaloguj się teraz</a>
            </div>
            
            <p style="font-size: 16px; margin: 30px 0; color: #2d3748;">Jeśli masz jakiekolwiek pytania, nie wahaj się z nami skontaktować.</p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0; color: #64748b;">
            <div style="font-size: 20px; font-weight: 700; color: #16a34a; margin-bottom: 16px;">Klub Lepsze Życie</div>
            <p style="margin: 8px 0; font-size: 14px;">Dziękujemy za bycie częścią naszej społeczności!</p>
            <p style="margin: 8px 0; font-size: 14px;">W razie pytań skontaktuj się z nami: <a href="mailto:kontakt@klublepszezycie.pl" style="color: #16a34a; text-decoration: none;">kontakt@klublepszezycie.pl</a></p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <a href="{{unsubscribe_url}}" style="color: #64748b; text-decoration: underline; font-size: 12px; margin: 0 8px;">Zrezygnuj z członkostwa</a> |
                <a href="{{delete_account_url}}" style="color: #dc2626; text-decoration: underline; font-size: 12px; margin: 0 8px;">Usuń konto</a>
            </div>
        </div>
    </div>
</body>
</html>'''

def create_enhanced_event_reminder_5min_template():
    """Ulepszony szablon przypomnienia 5 min z lepszym wyeksponowaniem czasu"""
    return '''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Przypomnienie: {{event_title}} za 5 minut!</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; color: #1a202c; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; padding: 40px 30px; text-align: center; position: relative;">
            <h1 style="margin: 0; font-size: 36px; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">⚡ ZA 5 MINUT!</h1>
            <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.9;">{{event_title}}</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 50px 40px;">
            <h2 style="color: #dc2626; font-size: 28px; font-weight: 600; margin-bottom: 25px; border-bottom: 3px solid #dc2626; padding-bottom: 15px;">Ostatni dzwonek!</h2>
            
            <p style="font-size: 18px; margin-bottom: 25px; color: #2d3748;">Cześć <strong>{{user_name}}</strong>!</p>
            
            <p style="font-size: 18px; margin-bottom: 30px; color: #2d3748;">Wydarzenie zaczyna się za <strong style="color: #dc2626; font-size: 20px;">5 minut</strong>!</p>
            
            <div style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border: 1px solid #fecaca; border-radius: 12px; padding: 30px; margin: 30px 0;">
                <h3 style="color: #dc2626; font-size: 24px; font-weight: 600; margin-top: 0; margin-bottom: 20px;">{{event_title}}</h3>
                
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #fecaca;">
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #dc2626; min-width: 120px; margin-right: 16px;">📅 Data:</span>
                        <span style="color: #dc2626; flex: 1; font-size: 18px; font-weight: 700;">{{event_date}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #dc2626; min-width: 120px; margin-right: 16px;">🕐 Godzina:</span>
                        <span style="color: #dc2626; flex: 1; font-size: 20px; font-weight: 700;">{{event_time}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #dc2626; min-width: 120px; margin-right: 16px;">📍 Lokalizacja:</span>
                        <span style="color: #2d3748; flex: 1; font-size: 16px; font-weight: 500;">{{event_location}}</span>
                    </div>
                </div>
            </div>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #92400e; font-size: 16px;">Nie przegap tego wydarzenia! Kliknij poniżej, aby dołączyć:</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{event_url}}" style="display: inline-block; background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; padding: 18px 36px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 18px; box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);">DOŁĄCZ TERAZ</a>
            </div>
            
            <p style="font-size: 18px; margin: 30px 0; color: #2d3748; text-align: center;">
                <strong style="color: #dc2626;">🎉 Czas na świetną zabawę!</strong><br>
                Życzymy Ci wspaniałego czasu!
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0; color: #64748b;">
            <div style="font-size: 20px; font-weight: 700; color: #dc2626; margin-bottom: 16px;">Klub Lepsze Życie</div>
            <p style="margin: 8px 0; font-size: 14px;">Dziękujemy za bycie częścią naszej społeczności!</p>
            <p style="margin: 8px 0; font-size: 14px;">W razie pytań skontaktuj się z nami: <a href="mailto:kontakt@klublepszezycie.pl" style="color: #dc2626; text-decoration: none;">kontakt@klublepszezycie.pl</a></p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <a href="{{unsubscribe_url}}" style="color: #64748b; text-decoration: underline; font-size: 12px; margin: 0 8px;">Zrezygnuj z członkostwa</a> |
                <a href="{{delete_account_url}}" style="color: #dc2626; text-decoration: underline; font-size: 12px; margin: 0 8px;">Usuń konto</a>
            </div>
        </div>
    </div>
</body>
</html>'''

def create_enhanced_event_registration_template():
    """Ulepszony szablon rejestracji z granatowym kolorem"""
    return '''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rejestracja potwierdzona</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; color: #1a202c; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); color: white; padding: 40px 30px; text-align: center; position: relative;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">✅ Rejestracja potwierdzona</h1>
            <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.9;">Klub Lepsze Życie</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 50px 40px;">
            <p style="font-size: 18px; margin-bottom: 25px; color: #2d3748;">Cześć <strong>{{user_name}}</strong>!</p>
            
            <p style="font-size: 18px; margin-bottom: 30px; color: #2d3748;">Twoja rejestracja na wydarzenie została pomyślnie potwierdzona!</p>
            
            <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 1px solid #bfdbfe; border-radius: 12px; padding: 30px; margin: 30px 0;">
                <h3 style="color: #1e3a8a; font-size: 24px; font-weight: 600; margin-top: 0; margin-bottom: 20px;">{{event_title}}</h3>
                
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #bfdbfe;">
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #1e3a8a; min-width: 120px; margin-right: 16px;">📅 Data:</span>
                        <span style="color: #1e3a8a; flex: 1; font-size: 18px; font-weight: 700;">{{event_date}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #1e3a8a; min-width: 120px; margin-right: 16px;">🕐 Godzina:</span>
                        <span style="color: #1e3a8a; flex: 1; font-size: 18px; font-weight: 700;">{{event_time}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #1e3a8a; min-width: 120px; margin-right: 16px;">📍 Lokalizacja:</span>
                        <span style="color: #2d3748; flex: 1; font-size: 16px; font-weight: 500;">{{event_location}}</span>
                    </div>
                </div>
            </div>
            
            <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #15803d; font-size: 16px;">🎉 Gratulacje! Jesteś już zarejestrowany na to wydarzenie.</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{event_url}}" style="display: inline-block; background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%); color: white; padding: 18px 36px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 18px; box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);">Zobacz szczegóły wydarzenia</a>
            </div>
            
            <p style="font-size: 16px; margin: 30px 0; color: #2d3748;">Do zobaczenia na wydarzeniu!</p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0; color: #64748b;">
            <div style="font-size: 20px; font-weight: 700; color: #1e3a8a; margin-bottom: 16px;">Klub Lepsze Życie</div>
            <p style="margin: 8px 0; font-size: 14px;">Dziękujemy za bycie częścią naszej społeczności!</p>
            <p style="margin: 8px 0; font-size: 14px;">W razie pytań skontaktuj się z nami: <a href="mailto:kontakt@klublepszezycie.pl" style="color: #1e3a8a; text-decoration: none;">kontakt@klublepszezycie.pl</a></p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <a href="{{unsubscribe_url}}" style="color: #64748b; text-decoration: underline; font-size: 12px; margin: 0 8px;">Zrezygnuj z członkostwa</a> |
                <a href="{{delete_account_url}}" style="color: #dc2626; text-decoration: underline; font-size: 12px; margin: 0 8px;">Usuń konto</a>
            </div>
        </div>
    </div>
</body>
</html>'''

def update_templates():
    """Aktualizuje wybrane szablony z lepszym wyeksponowaniem"""
    app = create_app()
    with app.app_context():
        print("🎨 Aktualizuję szablony z lepszym wyeksponowaniem kluczowych informacji...")
        
        # Mapowanie szablonów do aktualizacji
        updates = [
            {
                'name': 'welcome',
                'html_content': create_enhanced_welcome_template(),
                'description': 'Ulepszony szablon powitalny z lepszym wyeksponowaniem danych logowania'
            },
            {
                'name': 'event_reminder_5min',
                'html_content': create_enhanced_event_reminder_5min_template(),
                'description': 'Ulepszony szablon przypomnienia 5min z lepszym wyeksponowaniem czasu'
            },
            {
                'name': 'event_registration',
                'html_content': create_enhanced_event_registration_template(),
                'description': 'Ulepszony szablon rejestracji z granatowym kolorem'
            }
        ]
        
        updated_count = 0
        
        for update in updates:
            template = EmailTemplate.query.filter_by(name=update['name']).first()
            if template:
                template.html_content = update['html_content']
                template.description = update['description']
                db.session.commit()
                print(f"✅ {update['name']}: {update['description']}")
                updated_count += 1
            else:
                print(f"❌ {update['name']}: Szablon nie znaleziony")
        
        print(f"\n🎉 Zaktualizowano {updated_count} szablonów!")
        
        # Wyślij testowe emaile
        email_service = EmailService()
        
        print(f"📧 Wysyłam testowe emaile na codeitpy@gmail.com...")
        
        for update in updates:
            try:
                test_context = {
                    'user_name': 'Test User',
                    'user_email': 'test@example.com',
                    'event_title': 'Test Event',
                    'event_date': '2024-12-31',
                    'event_time': '18:00',
                    'event_location': 'Online - Zoom',
                    'event_url': 'https://zoom.us/j/123456789',
                    'temporary_password': 'TempPass123!',
                    'login_url': 'https://klublepszezycie.pl/login'
                }
                
                success, message = email_service.send_template_email(
                    to_email='codeitpy@gmail.com',
                    template_name=update['name'],
                    context=test_context,
                    to_name='Test User',
                    use_queue=False
                )
                
                if success:
                    print(f"✅ {update['name']}: Wysłano test")
                else:
                    print(f"❌ {update['name']}: {message}")
                    
            except Exception as e:
                print(f"❌ {update['name']}: Błąd - {str(e)}")
        
        print(f"\n🎉 Ulepszone szablony wysłane!")
        print("📧 Sprawdź skrzynkę codeitpy@gmail.com - kluczowe informacje powinny być lepiej wyeksponowane!")

if __name__ == '__main__':
    update_templates()
