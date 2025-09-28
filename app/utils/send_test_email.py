#!/usr/bin/env python3
"""
Skrypt do wysyłania testowych e-maili z szablonami.
Pobiera aktualne szablony z bazy EmailTemplate i pozwala na wysłanie wszystkich lub jednego konkretnego.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app import create_app
from app.services.email_service import EmailService
from app.models import EmailTemplate
import argparse


def get_test_data_for_template(template_name, template_type):
    """Generuje odpowiednie dane testowe dla danego typu szablonu"""
    
    # Pobierz BASE_URL z .env
    import os
    from dotenv import load_dotenv
    load_dotenv()
    base_url = os.getenv('BASE_URL', 'https://klublepszezycie.pl')
    
    # Podstawowe dane dla wszystkich szablonów
    base_data = {
        'user_name': 'Jan Kowalski',
        'user_email': 'jan.kowalski@example.com',
        'login_url': f'{base_url}/login',
        'unsubscribe_url': f'{base_url}/unsubscribe?token=test_token',
        'delete_account_url': f'{base_url}/delete-account?token=test_token'
    }
    
    # Dane specyficzne dla typów szablonów
    if template_type == 'welcome':
        return {
            **base_data,
            'temporary_password': 'TempPass123!'
        }
    
    elif template_type == 'event_reminder':
        return {
            **base_data,
            'event_title': 'Warsztat: Efektywne zarządzanie czasem',
            'event_datetime': '2024-12-31 18:00',
            'event_date': '2024-12-31',
            'event_time': '18:00',
            'event_location': 'Online - Zoom',
            'event_description': 'Praktyczny warsztat o technikach zarządzania czasem',
            'event_url': f'{base_url}/events/123'
        }
    
    elif template_type == 'registration_confirmation':
        return {
            **base_data,
            'event_title': 'Warsztat: Efektywne zarządzanie czasem',
            'event_date': '2024-12-31',
            'event_time': '18:00',
            'event_location': 'Online - Zoom',
            'event_url': f'{base_url}/events/123'
        }
    
    elif template_type == 'password_reset':
        return {
            **base_data,
            'reset_code': 'ABC123XYZ',
            'reset_url': f'{base_url}/reset-password?token=test_token'
        }
    
    elif template_type == 'admin_notification':
        return {
            **base_data,
            'notification_type': 'Nowa rejestracja',
            'notification_message': 'Użytkownik Jan Kowalski zarejestrował się na platformę',
            'notification_date': '2024-12-31 15:30',
            'additional_info': 'IP: 192.168.1.100, Przeglądarka: Chrome'
        }
    
    elif template_type == 'system':
        return {
            **base_data,
            'alert_message': 'Wykryto podejrzaną aktywność na koncie',
            'alert_date': '2024-12-31 16:45',
            'ip_address': '192.168.1.100',
            'location': 'Warszawa, Polska',
            'password_reset_url': f'{base_url}/reset-password?token=test_token'
        }
    
    # Domyślne dane dla nieznanych typów
    return base_data


def send_test_email(template_name, recipient_email, test_data=None):
    """Wysyła testowy e-mail z szablonem pobranym z bazy EmailTemplate"""
    
    app = create_app()
    with app.app_context():
        print(f'📧 Wysyłanie testowego e-maila...')
        print(f'📋 Szablon: {template_name}')
        print(f'📮 Odbiorca: {recipient_email}')
        
        # Pobierz aktualny szablon z bazy
        template = EmailTemplate.query.filter_by(name=template_name, is_active=True).first()
        if not template:
            print(f'❌ Szablon "{template_name}" nie istnieje lub jest nieaktywny.')
            return False
        
        print(f'📄 Typ szablonu: {template.template_type}')
        print(f'📝 Temat: {template.subject}')
        
        # Generuj dane testowe na podstawie typu szablonu
        if not test_data:
            test_data = get_test_data_for_template(template_name, template.template_type)
        
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
                return True
            else:
                print(f'❌ Błąd wysyłania e-maila: {message}')
                return False
                
        except Exception as e:
            print(f'❌ Błąd podczas wysyłania: {str(e)}')
            return False


def send_all_templates(recipient_email):
    """Wysyła wszystkie dostępne szablony jako testowe e-maile"""
    
    app = create_app()
    with app.app_context():
        templates = EmailTemplate.query.filter_by(is_active=True).all()
        
        if not templates:
            print('❌ Brak dostępnych szablonów.')
            return False
        
        print(f'📧 Wysyłanie wszystkich {len(templates)} szablonów...')
        print(f'📮 Odbiorca: {recipient_email}')
        print('=' * 60)
        
        success_count = 0
        failed_count = 0
        
        for i, template in enumerate(templates, 1):
            print(f'\n📧 [{i}/{len(templates)}] Wysyłanie: {template.name}')
            print(f'📄 Typ: {template.template_type}')
            print(f'📝 Temat: {template.subject}')
            
            success = send_test_email(template.name, recipient_email)
            
            if success:
                success_count += 1
                print(f'✅ Wysłano pomyślnie')
            else:
                failed_count += 1
                print(f'❌ Błąd wysyłania')
            
            print('-' * 40)
        
        print(f'\n🎉 Podsumowanie:')
        print(f'✅ Wysłano pomyślnie: {success_count}')
        print(f'❌ Błędy: {failed_count}')
        print(f'📊 Razem: {len(templates)}')
        
        return success_count > 0


def list_available_templates():
    """Wyświetla dostępne szablony"""
    
    app = create_app()
    with app.app_context():
        templates = EmailTemplate.query.filter_by(is_active=True).all()
        
        print('📋 Dostępne szablony:')
        for template in templates:
            print(f'   - {template.name} ({template.template_type}): {template.subject}')
        
        return [template.name for template in templates]


def main():
    """Główna funkcja skryptu"""
    parser = argparse.ArgumentParser(
        description='Wysyła testowe e-maile z szablonami pobranymi z bazy EmailTemplate',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady użycia:
  python send_test_email.py --all test@example.com
  python send_test_email.py --template welcome test@example.com
  python send_test_email.py --list
  python send_test_email.py --template event_reminder_5min test@example.com
        """
    )
    
    parser.add_argument('--template', '-t', 
                       help='Nazwa szablonu do wysłania')
    parser.add_argument('--all', '-a', action='store_true',
                       help='Wyślij wszystkie dostępne szablony')
    parser.add_argument('--list', '-l', action='store_true',
                       help='Wyświetl listę dostępnych szablonów')
    parser.add_argument('recipient_email', nargs='?',
                       help='Adres e-mail odbiorcy')
    
    args = parser.parse_args()
    
    # Wyświetl listę szablonów
    if args.list:
        list_available_templates()
        return
    
    # Sprawdź czy podano adres e-mail
    if not args.recipient_email:
        print('❌ Musisz podać adres e-mail odbiorcy.')
        print('Użyj --help aby zobaczyć opcje.')
        sys.exit(1)
    
    # Wyślij wszystkie szablony
    if args.all:
        send_all_templates(args.recipient_email)
        return
    
    # Wyślij konkretny szablon
    if args.template:
        app = create_app()
        with app.app_context():
            template = EmailTemplate.query.filter_by(name=args.template, is_active=True).first()
            if not template:
                print(f'❌ Szablon "{args.template}" nie istnieje lub jest nieaktywny.')
                print('Dostępne szablony:')
                list_available_templates()
                sys.exit(1)
        
        send_test_email(args.template, args.recipient_email)
        return
    
    # Jeśli nie podano żadnej opcji
    print('❌ Musisz podać --template <nazwa> lub --all')
    print('Użyj --help aby zobaczyć opcje.')
    sys.exit(1)


if __name__ == '__main__':
    main()
