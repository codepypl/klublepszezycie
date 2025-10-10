"""
Skrypt testowy dla Mailgun API

Sprawdza czy:
1. Credentials są poprawne
2. API odpowiada
3. Email faktycznie się wysyła
4. Możesz sprawdzić logi w Mailgun dashboard

Użycie:
    python app/utils/test_mailgun.py your-email@example.com
"""
import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import create_app


def test_mailgun_direct(recipient_email: str):
    """Test bezpośredni przez Mailgun API"""
    
    print("\n" + "="*80)
    print("TEST MAILGUN API - Bezpośredni")
    print("="*80 + "\n")
    
    # Pobierz credentials
    app = create_app()
    
    with app.app_context():
        api_key = os.getenv('MAILGUN_API_KEY')
        domain = os.getenv('MAILGUN_DOMAIN', 'klublepszezycie.pl').strip('"')
        from_email = os.getenv('MAILGUN_FROM_EMAIL', f'noreply@{domain}')
        
        # Check EU region
        mail_server = os.getenv('MAIL_SERVER', '')
        if 'eu.mailgun.org' in mail_server:
            api_url = f"https://api.eu.mailgun.net/v3/{domain}/messages"
        else:
            api_url = f"https://api.mailgun.net/v3/{domain}/messages"
        
        print("📋 Konfiguracja:")
        print(f"   API Key: {'*' * (len(api_key) - 4) + api_key[-4:] if api_key else 'BRAK'}")
        print(f"   Domain: {domain}")
        print(f"   API URL: {api_url}")
        print(f"   From Email: {from_email}")
        print()
        
        if not api_key:
            print("❌ BŁĄD: Brak MAILGUN_API_KEY w zmiennych środowiskowych!")
            return False
        
        # Przygotuj dane testowe
        data = {
            'from': f'Klub Lepsze Życie <{from_email}>',
            'to': recipient_email,
            'subject': 'Test Mailgun - Klub Lepsze Życie',
            'text': 'To jest testowa wiadomość z systemu Klub Lepsze Życie.\n\nJeśli otrzymałeś ten email, oznacza to że Mailgun działa poprawnie!',
            'html': '''
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>Test Mailgun</h2>
                    <p>To jest testowa wiadomość z systemu <strong>Klub Lepsze Życie</strong>.</p>
                    <p>Jeśli otrzymałeś ten email, oznacza to że Mailgun działa poprawnie! ✅</p>
                    <hr>
                    <p style="font-size: 12px; color: #666;">
                        Wysłano przez: Mailgun API<br>
                        Domain: ''' + domain + '''
                    </p>
                </body>
                </html>
            '''
        }
        
        print("📤 Wysyłam testowy email...")
        print(f"   Do: {recipient_email}")
        print(f"   Temat: {data['subject']}")
        print()
        
        try:
            response = requests.post(
                api_url,
                auth=('api', api_key),
                data=data,
                timeout=30
            )
            
            print("📬 Response od Mailgun:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            print()
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    message_id = response_data.get('id', 'unknown')
                    
                    print("✅ EMAIL WYSŁANY POMYŚLNIE!")
                    print(f"   Message ID: {message_id}")
                    print()
                    print("📋 Co dalej?")
                    print("   1. Sprawdź swoją skrzynkę email (także spam)")
                    print("   2. Sprawdź Mailgun Dashboard -> Logs")
                    print(f"   3. Szukaj Message ID: {message_id}")
                    print()
                    print("⚠️ UWAGA: Jeśli używasz Mailgun Sandbox:")
                    print(f"   - Dodaj {recipient_email} jako 'Authorized Recipient' w Mailgun Dashboard")
                    print("   - Sandbox wysyła tylko do zweryfikowanych adresów")
                    print()
                    
                    return True
                except Exception as e:
                    print(f"⚠️ Nie można parsować JSON: {e}")
                    return True
            else:
                print(f"❌ BŁĄD: {response.status_code}")
                print(f"   Response: {response.text}")
                print()
                
                # Podpowiedzi na podstawie błędu
                if response.status_code == 401:
                    print("💡 Podpowiedź: Błąd autoryzacji (401)")
                    print("   - Sprawdź czy MAILGUN_API_KEY jest poprawny")
                    print("   - Klucz powinien zaczynać się od 'key-' lub być w formacie długiego tokena")
                elif response.status_code == 404:
                    print("💡 Podpowiedź: Nie znaleziono (404)")
                    print("   - Sprawdź czy MAILGUN_DOMAIN jest poprawny")
                    print(f"   - Aktualny domain: {domain}")
                elif 'Sandbox' in response.text or 'authorized' in response.text.lower():
                    print("💡 Podpowiedź: Problem z Sandbox")
                    print("   - Dodaj recipient do 'Authorized Recipients' w Mailgun Dashboard")
                    print("   - LUB zmień plan na płatny aby wysyłać do wszystkich")
                
                return False
                
        except requests.exceptions.Timeout:
            print("❌ TIMEOUT: Mailgun API nie odpowiada")
            print("   - Sprawdź połączenie internetowe")
            print("   - Sprawdź czy firewall nie blokuje requestów")
            return False
            
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False


def test_mailgun_provider(recipient_email: str):
    """Test przez nasz MailgunProvider"""
    
    print("\n" + "="*80)
    print("TEST MAILGUN PROVIDER - Przez aplikację")
    print("="*80 + "\n")
    
    app = create_app()
    
    with app.app_context():
        from app.services.email_v2.providers.mailgun import MailgunProvider
        import logging
        
        # Skonfiguruj logging
        logger = logging.getLogger('test_mailgun')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)
        
        # Utwórz providera
        provider = MailgunProvider({})
        provider.set_logger(logger)
        
        print("📤 Wysyłam testowy email przez MailgunProvider...")
        print()
        
        success, message = provider.send_email(
            to_email=recipient_email,
            subject='Test Mailgun Provider - Klub Lepsze Życie',
            html_content='''
                <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2>Test Mailgun Provider</h2>
                    <p>To jest testowa wiadomość wysłana przez <strong>MailgunProvider</strong>.</p>
                    <p>Jeśli otrzymałeś ten email, oznacza to że system działa poprawnie! ✅</p>
                </body>
                </html>
            ''',
            text_content='To jest testowa wiadomość z MailgunProvider.\n\nJeśli otrzymałeś ten email, system działa poprawnie!'
        )
        
        print()
        print(f"📬 Wynik: success={success}")
        print(f"   Message: {message}")
        print()
        
        if success:
            print("✅ EMAIL WYSŁANY POMYŚLNIE PRZEZ PROVIDER!")
            return True
        else:
            print(f"❌ BŁĄD PROVIDERA: {message}")
            return False


def main():
    if len(sys.argv) < 2:
        print("""
Użycie:
    python app/utils/test_mailgun.py <recipient_email>
    
Przykład:
    python app/utils/test_mailgun.py jan.kowalski@example.com
        """)
        sys.exit(1)
    
    recipient_email = sys.argv[1]
    
    print("\n" + "="*80)
    print("MAILGUN TEST SUITE")
    print("="*80)
    print(f"\nOdbiorca testowy: {recipient_email}")
    
    # Test 1: Bezpośredni API
    test1_success = test_mailgun_direct(recipient_email)
    
    # Test 2: Przez Provider
    test2_success = test_mailgun_provider(recipient_email)
    
    # Podsumowanie
    print("\n" + "="*80)
    print("PODSUMOWANIE")
    print("="*80 + "\n")
    print(f"Test 1 (Bezpośredni API): {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Test 2 (MailgunProvider):  {'✅ PASS' if test2_success else '❌ FAIL'}")
    print()
    
    if test1_success and test2_success:
        print("🎉 Wszystkie testy przeszły pomyślnie!")
        print("   System powinien teraz poprawnie wysyłać emaile.")
    elif test1_success:
        print("⚠️ API działa, ale Provider ma problem")
        print("   Sprawdź logi aplikacji dla więcej szczegółów")
    else:
        print("❌ API nie działa - sprawdź credentials w .env")
        print("\n📋 Sprawdź:")
        print("   1. MAILGUN_API_KEY")
        print("   2. MAILGUN_DOMAIN")
        print("   3. Czy konto Mailgun jest aktywne")
        print("   4. Czy nie używasz sandbox mode bez authorized recipients")


if __name__ == '__main__':
    main()

