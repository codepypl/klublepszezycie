#!/usr/bin/env python3
"""
Skrypt do wysyłania testowych e-maili z szablonami.
"""

from app import create_app
from app.services.email_service import EmailService
import sys


def send_test_email(template_name, recipient_email, test_data=None):
    """Wysyła testowy e-mail z szablonem"""
    
    app = create_app()
    with app.app_context():
        print(f'📧 Wysyłanie testowego e-maila...')
        print(f'📋 Szablon: {template_name}')
        print(f'📮 Odbiorca: {recipient_email}')
        
        # Domyślne dane testowe
        if not test_data:
            test_data = {
                'user_name': 'Test User',
                'event_title': 'Test Event',
                'event_date': '2024-12-31',
                'event_time': '18:00',
                'event_location': 'Online - Zoom',
                'event_url': 'https://zoom.us/j/123456789',
                'request_id': 'REQ-12345',
                'session_id': 'SESS-67890',
                'severity': 'Medium',
                'unsubscribe_url': 'https://example.com/unsubscribe',
                'delete_account_url': 'https://example.com/delete-account'
            }
        
        print(f'📊 Dane testowe:')
        for key, value in test_data.items():
            print(f'   - {key}: {value}')
        
        # Wyślij e-mail
        email_service = EmailService()
        
        try:
            success, message = email_service.send_template_email(
                to_email=recipient_email,
                template_name=template_name,
                context=test_data,
                to_name=test_data.get('user_name', 'Test User'),
                use_queue=False  # Wyślij natychmiast, bez kolejki
            )
            
            if success:
                print(f'✅ E-mail wysłany pomyślnie!')
                print(f'📝 Wiadomość: {message}')
            else:
                print(f'❌ Błąd wysyłania e-maila: {message}')
                
        except Exception as e:
            print(f'❌ Błąd podczas wysyłania: {str(e)}')


def list_available_templates():
    """Wyświetla dostępne szablony"""
    
    app = create_app()
    with app.app_context():
        from app.models import EmailTemplate
        
        templates = EmailTemplate.query.filter_by(is_active=True).all()
        
        print('📋 Dostępne szablony:')
        for template in templates:
            print(f'   - {template.name}: {template.subject}')
        
        return [template.name for template in templates]


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('❌ Nieprawidłowa liczba argumentów.')
        print('Użycie: python send_test_email.py <template_name> <recipient_email>')
        print()
        print('Dostępne szablony:')
        list_available_templates()
        sys.exit(1)
    
    template_name = sys.argv[1]
    recipient_email = sys.argv[2]
    
    # Sprawdź czy szablon istnieje
    app = create_app()
    with app.app_context():
        from app.models import EmailTemplate
        
        template = EmailTemplate.query.filter_by(name=template_name, is_active=True).first()
        if not template:
            print(f'❌ Szablon "{template_name}" nie istnieje lub jest nieaktywny.')
            print('Dostępne szablony:')
            list_available_templates()
            sys.exit(1)
    
    send_test_email(template_name, recipient_email)
