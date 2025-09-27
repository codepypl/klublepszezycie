#!/usr/bin/env python3
"""
Tworzy profesjonalne szablony email od nowa, pasujące do stylistyki strony
"""

from app import create_app
from app.models.email_model import EmailTemplate
from app.services.email_service import EmailService
from app.models import db

def create_welcome_template():
    """Szablon powitalny"""
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
                    <p style="margin: 10px 0; font-size: 16px;"><strong>Email:</strong> {{user_email}}</p>
                    <p style="margin: 10px 0; font-size: 16px;"><strong>Hasło tymczasowe:</strong> {{temporary_password}}</p>
                </div>
            </div>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #92400e;">⚠️ Ważne: Zalecamy zmianę hasła po pierwszym zalogowaniu.</p>
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

def create_event_reminder_5min_template():
    """Szablon przypomnienia 5 minut przed wydarzeniem"""
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
            <h1 style="margin: 0; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">⚡ Ostatni dzwonek!</h1>
            <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.9;">Przypomnienie o wydarzeniu (5 min)</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 50px 40px;">
            <h2 style="color: #dc2626; font-size: 28px; font-weight: 600; margin-bottom: 25px; border-bottom: 3px solid #dc2626; padding-bottom: 15px;">Przypomnienie o wydarzeniu</h2>
            
            <p style="font-size: 18px; margin-bottom: 25px; color: #2d3748;">Cześć <strong>{{user_name}}</strong>!</p>
            
            <p style="font-size: 18px; margin-bottom: 30px; color: #2d3748;">Przypominamy o nadchodzącym wydarzeniu:</p>
            
            <div style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border: 1px solid #fecaca; border-radius: 12px; padding: 30px; margin: 30px 0;">
                <h3 style="color: #dc2626; font-size: 24px; font-weight: 600; margin-top: 0; margin-bottom: 20px;">{{event_title}}</h3>
                
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #fecaca;">
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #dc2626; min-width: 120px; margin-right: 16px;">📅 Data:</span>
                        <span style="color: #2d3748; flex: 1;">{{event_date}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #dc2626; min-width: 120px; margin-right: 16px;">🕐 Godzina:</span>
                        <span style="color: #2d3748; flex: 1;">{{event_time}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #dc2626; min-width: 120px; margin-right: 16px;">📍 Lokalizacja:</span>
                        <span style="color: #2d3748; flex: 1;">{{event_location}}</span>
                    </div>
                </div>
            </div>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #92400e;">Nie przegap tego wydarzenia! Kliknij poniżej, aby dołączyć:</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{event_url}}" style="display: inline-block; background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; padding: 18px 36px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 18px; box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);">Dołącz do wydarzenia</a>
            </div>
            
            <p style="font-size: 18px; margin: 30px 0; color: #2d3748; text-align: center;">
                <strong>🎉 Czas na świetną zabawę!</strong><br>
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

def create_event_registration_template():
    """Szablon potwierdzenia rejestracji na wydarzenie"""
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
        <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: white; padding: 40px 30px; text-align: center; position: relative;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">✅ Rejestracja potwierdzona</h1>
            <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.9;">Klub Lepsze Życie</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 50px 40px;">
            <p style="font-size: 18px; margin-bottom: 25px; color: #2d3748;">Cześć <strong>{{user_name}}</strong>!</p>
            
            <p style="font-size: 18px; margin-bottom: 30px; color: #2d3748;">Twoja rejestracja na wydarzenie została pomyślnie potwierdzona!</p>
            
            <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 1px solid #bfdbfe; border-radius: 12px; padding: 30px; margin: 30px 0;">
                <h3 style="color: #2563eb; font-size: 24px; font-weight: 600; margin-top: 0; margin-bottom: 20px;">{{event_title}}</h3>
                
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #bfdbfe;">
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #2563eb; min-width: 120px; margin-right: 16px;">📅 Data:</span>
                        <span style="color: #2d3748; flex: 1;">{{event_date}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #2563eb; min-width: 120px; margin-right: 16px;">🕐 Godzina:</span>
                        <span style="color: #2d3748; flex: 1;">{{event_time}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #2563eb; min-width: 120px; margin-right: 16px;">📍 Lokalizacja:</span>
                        <span style="color: #2d3748; flex: 1;">{{event_location}}</span>
                    </div>
                </div>
            </div>
            
            <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #15803d;">🎉 Gratulacje! Jesteś już zarejestrowany na to wydarzenie.</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{event_url}}" style="display: inline-block; background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: white; padding: 18px 36px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 18px; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);">Zobacz szczegóły wydarzenia</a>
            </div>
            
            <p style="font-size: 16px; margin: 30px 0; color: #2d3748;">Do zobaczenia na wydarzeniu!</p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0; color: #64748b;">
            <div style="font-size: 20px; font-weight: 700; color: #2563eb; margin-bottom: 16px;">Klub Lepsze Życie</div>
            <p style="margin: 8px 0; font-size: 14px;">Dziękujemy za bycie częścią naszej społeczności!</p>
            <p style="margin: 8px 0; font-size: 14px;">W razie pytań skontaktuj się z nami: <a href="mailto:kontakt@klublepszezycie.pl" style="color: #2563eb; text-decoration: none;">kontakt@klublepszezycie.pl</a></p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <a href="{{unsubscribe_url}}" style="color: #64748b; text-decoration: underline; font-size: 12px; margin: 0 8px;">Zrezygnuj z członkostwa</a> |
                <a href="{{delete_account_url}}" style="color: #dc2626; text-decoration: underline; font-size: 12px; margin: 0 8px;">Usuń konto</a>
            </div>
        </div>
    </div>
</body>
</html>'''

def create_password_reset_template():
    """Szablon resetowania hasła"""
    return '''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resetowanie hasła - Klub Lepsze Życie</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; color: #1a202c; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 40px 30px; text-align: center; position: relative;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">🔐 Resetowanie hasła</h1>
            <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.9;">Klub Lepsze Życie</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 50px 40px;">
            <h2 style="color: #f59e0b; font-size: 28px; font-weight: 600; margin-bottom: 25px; border-bottom: 3px solid #f59e0b; padding-bottom: 15px;">Resetowanie hasła</h2>
            
            <p style="font-size: 18px; margin-bottom: 25px; color: #2d3748;">Cześć <strong>{{user_name}}</strong>!</p>
            
            <p style="font-size: 18px; margin-bottom: 30px; color: #2d3748;">Otrzymaliśmy prośbę o resetowanie hasła do Twojego konta w Klubie Lepsze Życie.</p>
            
            <div style="background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); border: 1px solid #fed7aa; border-radius: 12px; padding: 30px; margin: 30px 0;">
                <h3 style="color: #d97706; font-size: 22px; font-weight: 600; margin-top: 0; margin-bottom: 20px;">🔑 Twoje nowe hasło:</h3>
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #fed7aa; text-align: center;">
                    <p style="margin: 0; font-size: 20px; font-weight: 600; color: #d97706; letter-spacing: 2px;">{{temporary_password}}</p>
                </div>
            </div>
            
            <div style="background: #fef2f2; border-left: 4px solid #dc2626; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #b91c1c;">⚠️ Ważne: Po zalogowaniu zalecamy zmianę hasła na własne.</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{login_url}}" style="display: inline-block; background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; padding: 18px 36px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 18px; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);">Zaloguj się teraz</a>
            </div>
            
            <p style="font-size: 16px; margin: 30px 0; color: #2d3748;">Jeśli nie prosiłeś o resetowanie hasła, zignoruj ten email.</p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0; color: #64748b;">
            <div style="font-size: 20px; font-weight: 700; color: #f59e0b; margin-bottom: 16px;">Klub Lepsze Życie</div>
            <p style="margin: 8px 0; font-size: 14px;">Dziękujemy za bycie częścią naszej społeczności!</p>
            <p style="margin: 8px 0; font-size: 14px;">W razie pytań skontaktuj się z nami: <a href="mailto:kontakt@klublepszezycie.pl" style="color: #f59e0b; text-decoration: none;">kontakt@klublepszezycie.pl</a></p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <a href="{{unsubscribe_url}}" style="color: #64748b; text-decoration: underline; font-size: 12px; margin: 0 8px;">Zrezygnuj z członkostwa</a> |
                <a href="{{delete_account_url}}" style="color: #dc2626; text-decoration: underline; font-size: 12px; margin: 0 8px;">Usuń konto</a>
            </div>
        </div>
    </div>
</body>
</html>'''

def create_admin_notification_template():
    """Szablon powiadomienia admin o nowym użytkowniku"""
    return '''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nowa osoba dołączyła do klubu - {{user_name}}</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; color: #1a202c; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%); color: white; padding: 40px 30px; text-align: center; position: relative;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">📋 Nowy członek klubu</h1>
            <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.9;">Klub Lepsze Życie</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 50px 40px;">
            <h2 style="color: #7c3aed; font-size: 28px; font-weight: 600; margin-bottom: 25px; border-bottom: 3px solid #7c3aed; padding-bottom: 15px;">Powiadomienie administracyjne</h2>
            
            <p style="font-size: 18px; margin-bottom: 30px; color: #2d3748;">Do klubu dołączyła nowa osoba:</p>
            
            <div style="background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%); border: 1px solid #e9d5ff; border-radius: 12px; padding: 30px; margin: 30px 0;">
                <h3 style="color: #7c3aed; font-size: 24px; font-weight: 600; margin-top: 0; margin-bottom: 20px;">👤 {{user_name}}</h3>
                
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #e9d5ff;">
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #7c3aed; min-width: 120px; margin-right: 16px;">📧 Email:</span>
                        <span style="color: #2d3748; flex: 1;">{{user_email}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #7c3aed; min-width: 120px; margin-right: 16px;">📅 Data dołączenia:</span>
                        <span style="color: #2d3748; flex: 1;">{{registration_date}}</span>
                    </div>
                </div>
            </div>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #92400e;">Nowy członek czeka na akceptację przez administratora.</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{admin_panel_url}}" style="display: inline-block; background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%); color: white; padding: 18px 36px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 18px; box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);">Przejdź do panelu admin</a>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0; color: #64748b;">
            <div style="font-size: 20px; font-weight: 700; color: #7c3aed; margin-bottom: 16px;">Klub Lepsze Życie</div>
            <p style="margin: 8px 0; font-size: 14px;">System powiadomień administracyjnych</p>
            <p style="margin: 8px 0; font-size: 14px;">W razie pytań skontaktuj się z nami: <a href="mailto:kontakt@klublepszezycie.pl" style="color: #7c3aed; text-decoration: none;">kontakt@klublepszezycie.pl</a></p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <a href="{{unsubscribe_url}}" style="color: #64748b; text-decoration: underline; font-size: 12px; margin: 0 8px;">Zrezygnuj z członkostwa</a> |
                <a href="{{delete_account_url}}" style="color: #dc2626; text-decoration: underline; font-size: 12px; margin: 0 8px;">Usuń konto</a>
            </div>
        </div>
    </div>
</body>
</html>'''

def create_admin_message_template():
    """Szablon wiadomości od administratora"""
    return '''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wiadomość od administratora - Klub Lepsze Życie</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; color: #1a202c; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #059669 0%, #047857 100%); color: white; padding: 40px 30px; text-align: center; position: relative;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">📢 Wiadomość od administratora</h1>
            <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.9;">Klub Lepsze Życie</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 50px 40px;">
            <h2 style="color: #059669; font-size: 28px; font-weight: 600; margin-bottom: 25px; border-bottom: 3px solid #059669; padding-bottom: 15px;">{{message_subject}}</h2>
            
            <p style="font-size: 18px; margin-bottom: 25px; color: #2d3748;">Cześć <strong>{{user_name}}</strong>!</p>
            
            <div style="background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); border: 1px solid #a7f3d0; border-radius: 12px; padding: 30px; margin: 30px 0;">
                <h3 style="color: #059669; font-size: 22px; font-weight: 600; margin-top: 0; margin-bottom: 20px;">📝 Treść wiadomości:</h3>
                
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #a7f3d0; font-size: 16px; line-height: 1.7;">
                    {{message_content}}
                </div>
            </div>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #92400e;">Jeśli masz pytania, odpowiedz na ten email lub skontaktuj się z nami bezpośrednio.</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{contact_url}}" style="display: inline-block; background: linear-gradient(135deg, #059669 0%, #047857 100%); color: white; padding: 18px 36px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 18px; box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3);">Skontaktuj się z nami</a>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0; color: #64748b;">
            <div style="font-size: 20px; font-weight: 700; color: #059669; margin-bottom: 16px;">Klub Lepsze Życie</div>
            <p style="margin: 8px 0; font-size: 14px;">Dziękujemy za bycie częścią naszej społeczności!</p>
            <p style="margin: 8px 0; font-size: 14px;">W razie pytań skontaktuj się z nami: <a href="mailto:kontakt@klublepszezycie.pl" style="color: #059669; text-decoration: none;">kontakt@klublepszezycie.pl</a></p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <a href="{{unsubscribe_url}}" style="color: #64748b; text-decoration: underline; font-size: 12px; margin: 0 8px;">Zrezygnuj z członkostwa</a> |
                <a href="{{delete_account_url}}" style="color: #dc2626; text-decoration: underline; font-size: 12px; margin: 0 8px;">Usuń konto</a>
            </div>
        </div>
    </div>
</body>
</html>'''

def create_comment_moderation_template():
    """Szablon powiadomienia o komentarzu do moderacji"""
    return '''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nowy komentarz wymaga moderacji - {{post_title}}</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; color: #1a202c; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%); color: white; padding: 40px 30px; text-align: center; position: relative;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">🔔 Komentarz do moderacji</h1>
            <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.9;">Klub Lepsze Życie</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 50px 40px;">
            <h2 style="color: #ea580c; font-size: 28px; font-weight: 600; margin-bottom: 25px; border-bottom: 3px solid #ea580c; padding-bottom: 15px;">Nowy komentarz czeka na akceptację</h2>
            
            <div style="background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%); border: 1px solid #fdba74; border-radius: 12px; padding: 30px; margin: 30px 0;">
                <h3 style="color: #ea580c; font-size: 24px; font-weight: 600; margin-top: 0; margin-bottom: 20px;">📝 {{post_title}}</h3>
                
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #fdba74; margin-bottom: 20px;">
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #ea580c; min-width: 120px; margin-right: 16px;">👤 Autor:</span>
                        <span style="color: #2d3748; flex: 1;">{{comment_author}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #ea580c; min-width: 120px; margin-right: 16px;">📧 Email:</span>
                        <span style="color: #2d3748; flex: 1;">{{comment_email}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #ea580c; min-width: 120px; margin-right: 16px;">📅 Data:</span>
                        <span style="color: #2d3748; flex: 1;">{{comment_date}}</span>
                    </div>
                </div>
                
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #fdba74;">
                    <h4 style="color: #ea580c; font-size: 18px; font-weight: 600; margin-top: 0; margin-bottom: 15px;">💬 Treść komentarza:</h4>
                    <div style="font-size: 16px; line-height: 1.7; color: #2d3748;">{{comment_content}}</div>
                </div>
            </div>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #92400e;">Komentarz czeka na Twoją akceptację przed publikacją.</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{moderation_url}}" style="display: inline-block; background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%); color: white; padding: 18px 36px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 18px; box-shadow: 0 4px 12px rgba(234, 88, 12, 0.3);">Przejdź do moderacji</a>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0; color: #64748b;">
            <div style="font-size: 20px; font-weight: 700; color: #ea580c; margin-bottom: 16px;">Klub Lepsze Życie</div>
            <p style="margin: 8px 0; font-size: 14px;">System moderacji komentarzy</p>
            <p style="margin: 8px 0; font-size: 14px;">W razie pytań skontaktuj się z nami: <a href="mailto:kontakt@klublepszezycie.pl" style="color: #ea580c; text-decoration: none;">kontakt@klublepszezycie.pl</a></p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <a href="{{unsubscribe_url}}" style="color: #64748b; text-decoration: underline; font-size: 12px; margin: 0 8px;">Zrezygnuj z członkostwa</a> |
                <a href="{{delete_account_url}}" style="color: #dc2626; text-decoration: underline; font-size: 12px; margin: 0 8px;">Usuń konto</a>
            </div>
        </div>
    </div>
</body>
</html>'''

def create_event_reminder_24h_template():
    """Szablon przypomnienia 24h przed wydarzeniem"""
    return '''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Przypomnienie: wydarzenie już jutro!</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; color: #1a202c; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%); color: white; padding: 40px 30px; text-align: center; position: relative;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">📅 Jutro już wydarzenie!</h1>
            <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.9;">Przypomnienie o wydarzeniu (24h)</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 50px 40px;">
            <h2 style="color: #0891b2; font-size: 28px; font-weight: 600; margin-bottom: 25px; border-bottom: 3px solid #0891b2; padding-bottom: 15px;">Przypomnienie o wydarzeniu</h2>
            
            <p style="font-size: 18px; margin-bottom: 25px; color: #2d3748;">Cześć <strong>{{user_name}}</strong>!</p>
            
            <p style="font-size: 18px; margin-bottom: 30px; color: #2d3748;">Przypominamy o nadchodzącym wydarzeniu:</p>
            
            <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 1px solid #7dd3fc; border-radius: 12px; padding: 30px; margin: 30px 0;">
                <h3 style="color: #0891b2; font-size: 24px; font-weight: 600; margin-top: 0; margin-bottom: 20px;">{{event_title}}</h3>
                
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #7dd3fc;">
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #0891b2; min-width: 120px; margin-right: 16px;">📅 Data:</span>
                        <span style="color: #2d3748; flex: 1;">{{event_date}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #0891b2; min-width: 120px; margin-right: 16px;">🕐 Godzina:</span>
                        <span style="color: #2d3748; flex: 1;">{{event_time}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #0891b2; min-width: 120px; margin-right: 16px;">📍 Lokalizacja:</span>
                        <span style="color: #2d3748; flex: 1;">{{event_location}}</span>
                    </div>
                </div>
            </div>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #92400e;">Nie zapomnij o jutrzejszym wydarzeniu! Przygotuj się na świetną zabawę.</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{event_url}}" style="display: inline-block; background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%); color: white; padding: 18px 36px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 18px; box-shadow: 0 4px 12px rgba(8, 145, 178, 0.3);">Zobacz szczegóły wydarzenia</a>
            </div>
            
            <p style="font-size: 18px; margin: 30px 0; color: #2d3748; text-align: center;">
                <strong>🎉 Do zobaczenia jutro!</strong><br>
                Życzymy Ci wspaniałego czasu!
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0; color: #64748b;">
            <div style="font-size: 20px; font-weight: 700; color: #0891b2; margin-bottom: 16px;">Klub Lepsze Życie</div>
            <p style="margin: 8px 0; font-size: 14px;">Dziękujemy za bycie częścią naszej społeczności!</p>
            <p style="margin: 8px 0; font-size: 14px;">W razie pytań skontaktuj się z nami: <a href="mailto:kontakt@klublepszezycie.pl" style="color: #0891b2; text-decoration: none;">kontakt@klublepszezycie.pl</a></p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <a href="{{unsubscribe_url}}" style="color: #64748b; text-decoration: underline; font-size: 12px; margin: 0 8px;">Zrezygnuj z członkostwa</a> |
                <a href="{{delete_account_url}}" style="color: #dc2626; text-decoration: underline; font-size: 12px; margin: 0 8px;">Usuń konto</a>
            </div>
        </div>
    </div>
</body>
</html>'''

def create_event_reminder_1h_template():
    """Szablon przypomnienia 1h przed wydarzeniem"""
    return '''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Przypomnienie: {{event_title}} za 1 godzinę!</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; color: #1a202c; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #be185d 0%, #9d174d 100%); color: white; padding: 40px 30px; text-align: center; position: relative;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">🚨 Za godzinę!</h1>
            <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.9;">Przypomnienie o wydarzeniu (1h)</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 50px 40px;">
            <h2 style="color: #be185d; font-size: 28px; font-weight: 600; margin-bottom: 25px; border-bottom: 3px solid #be185d; padding-bottom: 15px;">Przypomnienie o wydarzeniu</h2>
            
            <p style="font-size: 18px; margin-bottom: 25px; color: #2d3748;">Cześć <strong>{{user_name}}</strong>!</p>
            
            <p style="font-size: 18px; margin-bottom: 30px; color: #2d3748;">Przypominamy o nadchodzącym wydarzeniu:</p>
            
            <div style="background: linear-gradient(135deg, #fdf2f8 0%, #fce7f3 100%); border: 1px solid #f9a8d4; border-radius: 12px; padding: 30px; margin: 30px 0;">
                <h3 style="color: #be185d; font-size: 24px; font-weight: 600; margin-top: 0; margin-bottom: 20px;">{{event_title}}</h3>
                
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #f9a8d4;">
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #be185d; min-width: 120px; margin-right: 16px;">📅 Data:</span>
                        <span style="color: #2d3748; flex: 1;">{{event_date}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #be185d; min-width: 120px; margin-right: 16px;">🕐 Godzina:</span>
                        <span style="color: #2d3748; flex: 1;">{{event_time}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #be185d; min-width: 120px; margin-right: 16px;">📍 Lokalizacja:</span>
                        <span style="color: #2d3748; flex: 1;">{{event_location}}</span>
                    </div>
                </div>
            </div>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #92400e;">Wydarzenie zaczyna się za godzinę! Przygotuj się i nie przegap.</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{event_url}}" style="display: inline-block; background: linear-gradient(135deg, #be185d 0%, #9d174d 100%); color: white; padding: 18px 36px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 18px; box-shadow: 0 4px 12px rgba(190, 24, 93, 0.3);">Dołącz do wydarzenia</a>
            </div>
            
            <p style="font-size: 18px; margin: 30px 0; color: #2d3748; text-align: center;">
                <strong>🎉 Czas na świetną zabawę!</strong><br>
                Życzymy Ci wspaniałego czasu!
            </p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0; color: #64748b;">
            <div style="font-size: 20px; font-weight: 700; color: #be185d; margin-bottom: 16px;">Klub Lepsze Życie</div>
            <p style="margin: 8px 0; font-size: 14px;">Dziękujemy za bycie częścią naszej społeczności!</p>
            <p style="margin: 8px 0; font-size: 14px;">W razie pytań skontaktuj się z nami: <a href="mailto:kontakt@klublepszezycie.pl" style="color: #be185d; text-decoration: none;">kontakt@klublepszezycie.pl</a></p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <a href="{{unsubscribe_url}}" style="color: #64748b; text-decoration: underline; font-size: 12px; margin: 0 8px;">Zrezygnuj z członkostwa</a> |
                <a href="{{delete_account_url}}" style="color: #dc2626; text-decoration: underline; font-size: 12px; margin: 0 8px;">Usuń konto</a>
            </div>
        </div>
    </div>
</body>
</html>'''

def create_admin_password_set_template():
    """Szablon informujący o ustawieniu hasła przez admin"""
    return '''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nowe hasło zostało ustawione - Klub Lepsze Życie</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; color: #1a202c; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #4338ca 0%, #3730a3 100%); color: white; padding: 40px 30px; text-align: center; position: relative;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">🔐 Hasło zostało ustawione</h1>
            <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.9;">Klub Lepsze Życie</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 50px 40px;">
            <h2 style="color: #4338ca; font-size: 28px; font-weight: 600; margin-bottom: 25px; border-bottom: 3px solid #4338ca; padding-bottom: 15px;">Nowe hasło zostało ustawione</h2>
            
            <p style="font-size: 18px; margin-bottom: 25px; color: #2d3748;">Cześć <strong>{{user_name}}</strong>!</p>
            
            <p style="font-size: 18px; margin-bottom: 30px; color: #2d3748;">Administrator ustawił nowe hasło do Twojego konta w Klubie Lepsze Życie.</p>
            
            <div style="background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%); border: 1px solid #c7d2fe; border-radius: 12px; padding: 30px; margin: 30px 0;">
                <h3 style="color: #4338ca; font-size: 22px; font-weight: 600; margin-top: 0; margin-bottom: 20px;">🔑 Twoje nowe dane logowania:</h3>
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #c7d2fe;">
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #4338ca; min-width: 120px; margin-right: 16px;">📧 Email:</span>
                        <span style="color: #2d3748; flex: 1;">{{user_email}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #4338ca; min-width: 120px; margin-right: 16px;">🔐 Hasło:</span>
                        <span style="color: #2d3748; flex: 1;">{{new_password}}</span>
                    </div>
                </div>
            </div>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #92400e;">⚠️ Ważne: Po pierwszym zalogowaniu zalecamy zmianę hasła na własne.</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{login_url}}" style="display: inline-block; background: linear-gradient(135deg, #4338ca 0%, #3730a3 100%); color: white; padding: 18px 36px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 18px; box-shadow: 0 4px 12px rgba(67, 56, 202, 0.3);">Zaloguj się teraz</a>
            </div>
            
            <p style="font-size: 16px; margin: 30px 0; color: #2d3748;">Jeśli masz jakiekolwiek pytania, nie wahaj się z nami skontaktować.</p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0; color: #64748b;">
            <div style="font-size: 20px; font-weight: 700; color: #4338ca; margin-bottom: 16px;">Klub Lepsze Życie</div>
            <p style="margin: 8px 0; font-size: 14px;">Dziękujemy za bycie częścią naszej społeczności!</p>
            <p style="margin: 8px 0; font-size: 14px;">W razie pytań skontaktuj się z nami: <a href="mailto:kontakt@klublepszezycie.pl" style="color: #4338ca; text-decoration: none;">kontakt@klublepszezycie.pl</a></p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <a href="{{unsubscribe_url}}" style="color: #64748b; text-decoration: underline; font-size: 12px; margin: 0 8px;">Zrezygnuj z członkostwa</a> |
                <a href="{{delete_account_url}}" style="color: #dc2626; text-decoration: underline; font-size: 12px; margin: 0 8px;">Usuń konto</a>
            </div>
        </div>
    </div>
</body>
</html>'''

def create_security_alert_template():
    """Szablon alertu bezpieczeństwa"""
    return '''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚨 Alert Bezpieczeństwa - {{server_name}}</title>
</head>
<body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f8fafc; color: #1a202c; line-height: 1.6;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; padding: 40px 30px; text-align: center; position: relative;">
            <h1 style="margin: 0; font-size: 32px; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">🚨 Alert Bezpieczeństwa</h1>
            <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.9;">{{server_name}}</p>
        </div>
        
        <!-- Content -->
        <div style="padding: 50px 40px;">
            <h2 style="color: #dc2626; font-size: 28px; font-weight: 600; margin-bottom: 25px; border-bottom: 3px solid #dc2626; padding-bottom: 15px;">Wykryto podejrzaną aktywność</h2>
            
            <p style="font-size: 18px; margin-bottom: 25px; color: #2d3748;">Cześć <strong>{{user_name}}</strong>!</p>
            
            <p style="font-size: 18px; margin-bottom: 30px; color: #2d3748;">Nasz system bezpieczeństwa wykrył podejrzaną aktywność na Twoim koncie.</p>
            
            <div style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); border: 1px solid #fecaca; border-radius: 12px; padding: 30px; margin: 30px 0;">
                <h3 style="color: #dc2626; font-size: 22px; font-weight: 600; margin-top: 0; margin-bottom: 20px;">🔍 Szczegóły alertu:</h3>
                
                <div style="background: white; border-radius: 8px; padding: 20px; border: 1px solid #fecaca;">
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #dc2626; min-width: 120px; margin-right: 16px;">🆔 ID żądania:</span>
                        <span style="color: #2d3748; flex: 1;">{{request_id}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #dc2626; min-width: 120px; margin-right: 16px;">🆔 ID sesji:</span>
                        <span style="color: #2d3748; flex: 1;">{{session_id}}</span>
                    </div>
                    <div style="display: flex; margin-bottom: 12px; align-items: center;">
                        <span style="font-weight: 600; color: #dc2626; min-width: 120px; margin-right: 16px;">⚠️ Poziom:</span>
                        <span style="color: #2d3748; flex: 1;">{{severity}}</span>
                    </div>
                </div>
            </div>
            
            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 20px; margin: 25px 0; border-radius: 0 8px 8px 0;">
                <p style="margin: 0; font-weight: 600; color: #92400e;">Jeśli to nie Ty wykonałeś tę aktywność, natychmiast zmień hasło!</p>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <a href="{{login_url}}" style="display: inline-block; background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; padding: 18px 36px; text-decoration: none; border-radius: 10px; font-weight: 600; font-size: 18px; box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);">Zmień hasło</a>
            </div>
            
            <p style="font-size: 16px; margin: 30px 0; color: #2d3748;">Jeśli masz pytania dotyczące bezpieczeństwa, skontaktuj się z nami.</p>
        </div>
        
        <!-- Footer -->
        <div style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0; color: #64748b;">
            <div style="font-size: 20px; font-weight: 700; color: #dc2626; margin-bottom: 16px;">Klub Lepsze Życie</div>
            <p style="margin: 8px 0; font-size: 14px;">Bezpieczeństwo Twojego konta jest dla nas priorytetem.</p>
            <p style="margin: 8px 0; font-size: 14px;">W razie pytań skontaktuj się z nami: <a href="mailto:kontakt@klublepszezycie.pl" style="color: #dc2626; text-decoration: none;">kontakt@klublepszezycie.pl</a></p>
            
            <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                <a href="{{unsubscribe_url}}" style="color: #64748b; text-decoration: underline; font-size: 12px; margin: 0 8px;">Zrezygnuj z członkostwa</a> |
                <a href="{{delete_account_url}}" style="color: #dc2626; text-decoration: underline; font-size: 12px; margin: 0 8px;">Usuń konto</a>
            </div>
        </div>
    </div>
</body>
</html>'''

def create_all_templates():
    """Tworzy wszystkie profesjonalne szablony od nowa"""
    app = create_app()
    with app.app_context():
        # Najpierw usuń logi emaili, które referencują szablony
        from app.models.email_model import EmailLog
        EmailLog.query.delete()
        db.session.commit()
        print("🗑️ Usunięto logi emaili")
        
        # Potem usuń wszystkie istniejące szablony
        EmailTemplate.query.delete()
        db.session.commit()
        print("🗑️ Usunięto wszystkie stare szablony")
        
        # Mapowanie szablonów - 11 profesjonalnych szablonów
        templates_data = [
            {
                'name': 'welcome',
                'subject': 'Witamy w Klubie Lepsze Życie!',
                'html_content': create_welcome_template(),
                'text_content': '''Witamy w Klubie Lepsze Życie! 🌟

Cześć {{user_name}}

Dziękujemy za dołączenie do Klubu Lepsze Życie!

🔑 Twoje dane logowania:
Email: {{user_email}}
Hasło tymczasowe: {{temporary_password}}

⚠️ Ważne: Zalecamy zmianę hasła po pierwszym zalogowaniu.

Zaloguj się: {{login_url}}

Jeśli masz jakiekolwiek pytania, nie wahaj się z nami skontaktować.

© 2025 Klub Lepsze Życie. Wszystkie prawa zastrzeżone.
Kontakt: kontakt@klublepszezycie.pl

Zrezygnuj z członkostwa: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
                'description': 'Szablon powitalny dla nowych członków klubu'
            },
            {
                'name': 'event_reminder_5min',
                'subject': 'Przypomnienie: {{event_title}} za 5 minut! ⚡',
                'html_content': create_event_reminder_5min_template(),
                'text_content': '''Przypomnienie o wydarzeniu za 5 minut! ⚡

Cześć {{user_name}}!

Przypominamy o nadchodzącym wydarzeniu:

{{event_title}}
Data: {{event_date}}
Godzina: {{event_time}}
Lokalizacja: {{event_location}}

Nie przegap tego wydarzenia! Dołącz: {{event_url}}

🎉 Czas na świetną zabawę!
Życzymy Ci wspaniałego czasu!

© 2025 Klub Lepsze Życie. Wszystkie prawa zastrzeżone.
Kontakt: kontakt@klublepszezycie.pl

Zrezygnuj z członkostwa: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
                'description': 'Przypomnienie 5 minut przed wydarzeniem'
            },
            {
                'name': 'event_registration',
                'subject': 'Potwierdzenie rejestracji na wydarzenie',
                'html_content': create_event_registration_template(),
                'text_content': '''Rejestracja potwierdzona ✅

Cześć {{user_name}}!

Twoja rejestracja na wydarzenie została pomyślnie potwierdzona!

{{event_title}}
Data: {{event_date}}
Godzina: {{event_time}}
Lokalizacja: {{event_location}}

🎉 Gratulacje! Jesteś już zarejestrowany na to wydarzenie.

Zobacz szczegóły: {{event_url}}

Do zobaczenia na wydarzeniu!

© 2025 Klub Lepsze Życie. Wszystkie prawa zastrzeżone.
Kontakt: kontakt@klublepszezycie.pl

Zrezygnuj z członkostwa: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
                'description': 'Potwierdzenie rejestracji na wydarzenie'
            },
            {
                'name': 'password_reset',
                'subject': 'Resetowanie hasła - Klub Lepsze Życie',
                'html_content': create_password_reset_template(),
                'text_content': '''Resetowanie hasła 🔐

Cześć {{user_name}}!

Otrzymaliśmy prośbę o resetowanie hasła do Twojego konta.

🔑 Twoje nowe hasło: {{temporary_password}}

⚠️ Ważne: Po zalogowaniu zalecamy zmianę hasła na własne.

Zaloguj się: {{login_url}}

Jeśli nie prosiłeś o resetowanie hasła, zignoruj ten email.

© 2025 Klub Lepsze Życie. Wszystkie prawa zastrzeżone.
Kontakt: kontakt@klublepszezycie.pl

Zrezygnuj z członkostwa: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
                'description': 'Resetowanie hasła użytkownika'
            },
            {
                'name': 'security_alert',
                'subject': '🚨 Alert Bezpieczeństwa - {{server_name}}',
                'html_content': create_security_alert_template(),
                'text_content': '''Alert Bezpieczeństwa 🚨

Cześć {{user_name}}!

Nasz system bezpieczeństwa wykrył podejrzaną aktywność na Twoim koncie.

🔍 Szczegóły alertu:
ID żądania: {{request_id}}
ID sesji: {{session_id}}
Poziom: {{severity}}

⚠️ Jeśli to nie Ty wykonałeś tę aktywność, natychmiast zmień hasło!

Zmień hasło: {{login_url}}

Jeśli masz pytania dotyczące bezpieczeństwa, skontaktuj się z nami.

© 2025 Klub Lepsze Życie. Wszystkie prawa zastrzeżone.
Kontakt: kontakt@klublepszezycie.pl

Zrezygnuj z członkostwa: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
                'description': 'Alert bezpieczeństwa systemu'
            },
            {
                'name': 'admin_notification',
                'subject': 'Nowa osoba dołączyła do klubu - {{user_name}}',
                'html_content': create_admin_notification_template(),
                'text_content': '''Nowy członek klubu 📋

Do klubu dołączyła nowa osoba:

👤 {{user_name}}
📧 Email: {{user_email}}
📅 Data dołączenia: {{registration_date}}

Nowy członek czeka na akceptację przez administratora.

Przejdź do panelu admin: {{admin_panel_url}}

© 2025 Klub Lepsze Życie. Wszystkie prawa zastrzeżone.
Kontakt: kontakt@klublepszezycie.pl

Zrezygnuj z członkostwa: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
                'description': 'Powiadomienie admin o nowym użytkowniku'
            },
            {
                'name': 'admin_message',
                'subject': 'Wiadomość od administratora - Klub Lepsze Życie',
                'html_content': create_admin_message_template(),
                'text_content': '''Wiadomość od administratora 📢

Cześć {{user_name}}!

{{message_subject}}

📝 Treść wiadomości:
{{message_content}}

Jeśli masz pytania, odpowiedz na ten email lub skontaktuj się z nami bezpośrednio.

Skontaktuj się z nami: {{contact_url}}

© 2025 Klub Lepsze Życie. Wszystkie prawa zastrzeżone.
Kontakt: kontakt@klublepszezycie.pl

Zrezygnuj z członkostwa: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
                'description': 'Wiadomość od administratora do użytkowników'
            },
            {
                'name': 'comment_moderation',
                'subject': 'Nowy komentarz wymaga moderacji - {{post_title}}',
                'html_content': create_comment_moderation_template(),
                'text_content': '''Komentarz do moderacji 🔔

Nowy komentarz czeka na akceptację:

📝 {{post_title}}
👤 Autor: {{comment_author}}
📧 Email: {{comment_email}}
📅 Data: {{comment_date}}

💬 Treść komentarza:
{{comment_content}}

Komentarz czeka na Twoją akceptację przed publikacją.

Przejdź do moderacji: {{moderation_url}}

© 2025 Klub Lepsze Życie. Wszystkie prawa zastrzeżone.
Kontakt: kontakt@klublepszezycie.pl

Zrezygnuj z członkostwa: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
                'description': 'Powiadomienie o komentarzu do moderacji'
            },
            {
                'name': 'event_reminder_24h',
                'subject': 'Przypomnienie: wydarzenie już jutro!',
                'html_content': create_event_reminder_24h_template(),
                'text_content': '''Jutro już wydarzenie! 📅

Cześć {{user_name}}!

Przypominamy o nadchodzącym wydarzeniu:

{{event_title}}
Data: {{event_date}}
Godzina: {{event_time}}
Lokalizacja: {{event_location}}

Nie zapomnij o jutrzejszym wydarzeniu! Przygotuj się na świetną zabawę.

Zobacz szczegóły: {{event_url}}

🎉 Do zobaczenia jutro!
Życzymy Ci wspaniałego czasu!

© 2025 Klub Lepsze Życie. Wszystkie prawa zastrzeżone.
Kontakt: kontakt@klublepszezycie.pl

Zrezygnuj z członkostwa: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
                'description': 'Przypomnienie 24h przed wydarzeniem'
            },
            {
                'name': 'event_reminder_1h',
                'subject': 'Przypomnienie: {{event_title}} za 1 godzinę!',
                'html_content': create_event_reminder_1h_template(),
                'text_content': '''Za godzinę! 🚨

Cześć {{user_name}}!

Przypominamy o nadchodzącym wydarzeniu:

{{event_title}}
Data: {{event_date}}
Godzina: {{event_time}}
Lokalizacja: {{event_location}}

Wydarzenie zaczyna się za godzinę! Przygotuj się i nie przegap.

Dołącz do wydarzenia: {{event_url}}

🎉 Czas na świetną zabawę!
Życzymy Ci wspaniałego czasu!

© 2025 Klub Lepsze Życie. Wszystkie prawa zastrzeżone.
Kontakt: kontakt@klublepszezycie.pl

Zrezygnuj z członkostwa: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
                'description': 'Przypomnienie 1h przed wydarzeniem'
            },
            {
                'name': 'admin_password_set',
                'subject': 'Nowe hasło zostało ustawione - Klub Lepsze Życie',
                'html_content': create_admin_password_set_template(),
                'text_content': '''Hasło zostało ustawione 🔐

Cześć {{user_name}}!

Administrator ustawił nowe hasło do Twojego konta w Klubie Lepsze Życie.

🔑 Twoje nowe dane logowania:
📧 Email: {{user_email}}
🔐 Hasło: {{new_password}}

⚠️ Ważne: Po pierwszym zalogowaniu zalecamy zmianę hasła na własne.

Zaloguj się: {{login_url}}

Jeśli masz jakiekolwiek pytania, nie wahaj się z nami skontaktować.

© 2025 Klub Lepsze Życie. Wszystkie prawa zastrzeżone.
Kontakt: kontakt@klublepszezycie.pl

Zrezygnuj z członkostwa: {{unsubscribe_url}}
Usuń konto: {{delete_account_url}}''',
                'description': 'Informacja o ustawieniu hasła przez administratora'
            }
        ]
        
        print(f"🎨 Tworzę {len(templates_data)} profesjonalnych szablonów...")
        
        for template_data in templates_data:
            template = EmailTemplate(
                name=template_data['name'],
                subject=template_data['subject'],
                html_content=template_data['html_content'],
                text_content=template_data['text_content'],
                description=template_data['description'],
                template_type='html',
                is_active=True,
                is_default=True
            )
            db.session.add(template)
            print(f"✅ {template_data['name']}: {template_data['subject']}")
        
        db.session.commit()
        print(f"\n🎉 Utworzono {len(templates_data)} profesjonalnych szablonów!")
        
        # Wyślij wszystkie szablony do testu
        email_service = EmailService()
        
        print(f"📧 Wysyłam {len(templates_data)} testowych emaili na codeitpy@gmail.com...")
        
        for template_data in templates_data:
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
                    'login_url': 'https://klublepszezycie.pl/login',
                    'server_name': 'Test Server',
                    'request_id': 'REQ-12345',
                    'session_id': 'SESS-67890',
                    'severity': 'Medium',
                    'registration_date': '2024-12-27',
                    'admin_panel_url': 'https://klublepszezycie.pl/admin',
                    'message_subject': 'Test Message Subject',
                    'message_content': 'To jest testowa wiadomość od administratora. Sprawdza czy szablon działa poprawnie.',
                    'contact_url': 'https://klublepszezycie.pl/contact',
                    'post_title': 'Test Post Title',
                    'comment_author': 'Test Commenter',
                    'comment_email': 'commenter@example.com',
                    'comment_date': '2024-12-27',
                    'comment_content': 'To jest testowy komentarz, który czeka na moderację.',
                    'moderation_url': 'https://klublepszezycie.pl/admin/comments',
                    'new_password': 'NewAdminPass123!'
                }
                
                success, message = email_service.send_template_email(
                    to_email='codeitpy@gmail.com',
                    template_name=template_data['name'],
                    context=test_context,
                    to_name='Test User',
                    use_queue=False
                )
                
                if success:
                    print(f"✅ {template_data['name']}: {template_data['subject']}")
                else:
                    print(f"❌ {template_data['name']}: {message}")
                    
            except Exception as e:
                print(f"❌ {template_data['name']}: Błąd - {str(e)}")
        
        print(f"\n🎉 Wysłano wszystkie testowe emaile!")
        print("📧 Sprawdź skrzynkę codeitpy@gmail.com - emaile powinny mieć profesjonalne style!")

if __name__ == '__main__':
    create_all_templates()
