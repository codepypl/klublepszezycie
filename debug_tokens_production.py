#!/usr/bin/env python3
"""
Skrypt do debugowania tokenów na produkcji
"""

import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.email_service import EmailService
from app.models import EmailTemplate

def debug_tokens_on_production():
    """Debuguje tokeny na produkcji"""
    print("🔍 Debugowanie tokenów na produkcji...")
    print(f"📅 Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    app = create_app()
    with app.app_context():
        # 1. Sprawdź konfigurację BASE_URL
        print("1. Sprawdzenie konfiguracji BASE_URL:")
        from dotenv import load_dotenv
        load_dotenv()
        
        base_url = os.getenv('BASE_URL')
        print(f"   BASE_URL z .env: {base_url}")
        
        # 2. Sprawdź UnsubscribeManager
        print("\\n2. Sprawdzenie UnsubscribeManager:")
        from app.services.unsubscribe_manager import unsubscribe_manager
        print(f"   UnsubscribeManager.base_url: {unsubscribe_manager.base_url}")
        
        # 3. Test generowania tokenów
        print("\\n3. Test generowania tokenów:")
        test_email = 'test@klublepszezycie.pl'
        
        unsubscribe_url = unsubscribe_manager.get_unsubscribe_url(test_email)
        delete_account_url = unsubscribe_manager.get_delete_account_url(test_email)
        
        print(f"   Unsubscribe URL: {unsubscribe_url}")
        print(f"   Delete account URL: {delete_account_url}")
        
        # Sprawdź czy URL-e zawierają tokeny
        if unsubscribe_url and '/unsubscribe/' in unsubscribe_url:
            token_part = unsubscribe_url.split('/unsubscribe/')[-1]
            if len(token_part) > 50:  # Tokeny są długie
                print("   ✅ Unsubscribe URL ma token")
            else:
                print("   ❌ Unsubscribe URL nie ma tokenu lub token jest za krótki")
        else:
            print("   ❌ Unsubscribe URL nie zawiera ścieżki /unsubscribe/")
            
        if delete_account_url and '/delete-account/' in delete_account_url:
            token_part = delete_account_url.split('/delete-account/')[-1]
            if len(token_part) > 50:  # Tokeny są długie
                print("   ✅ Delete account URL ma token")
            else:
                print("   ❌ Delete account URL nie ma tokenu lub token jest za krótki")
        else:
            print("   ❌ Delete account URL nie zawiera ścieżki /delete-account/")
        
        # 4. Sprawdź szablon e-mail
        print("\\n4. Sprawdzenie szablonu e-mail:")
        template = EmailTemplate.query.filter_by(name='event_reminder_1h').first()
        
        if template:
            print(f"   Szablon: {template.name}")
            print(f"   Temat: {template.subject}")
            
            # Sprawdź czy szablon ma placeholdery
            if '{{unsubscribe_url}}' in template.html_content and '{{delete_account_url}}' in template.html_content:
                print("   ✅ Szablon ma placeholdery unsubscribe")
            else:
                print("   ❌ Szablon nie ma placeholderów unsubscribe")
                
            # Sprawdź czy szablon ma CSS
            if '<style>' in template.html_content:
                print("   ✅ Szablon ma CSS")
            else:
                print("   ❌ Szablon nie ma CSS")
        else:
            print("   ❌ Nie znaleziono szablonu event_reminder_1h")
        
        # 5. Test wysyłania e-maila
        print("\\n5. Test wysyłania e-maila:")
        email_service = EmailService()
        
        test_data = {
            'user_name': 'Test User',
            'event_title': 'Test Event - Debug Tokenów',
            'event_date': '2024-12-31',
            'event_time': '18:00',
            'event_location': 'Online - Zoom',
            'event_url': 'https://zoom.us/j/123456789'
        }
        
        # Pokaż HTML przed wysłaniem
        html_content = email_service._replace_variables(template.html_content, test_data)
        
        # Sprawdź EmailTemplateEnricher
        from app.services.email_template_enricher import EmailTemplateEnricher
        enricher = EmailTemplateEnricher()
        enriched = enricher.enrich_template_content(
            html_content=html_content,
            text_content=template.text_content or '',
            user_email=test_email
        )
        
        # Sprawdź czy URL-e w HTML mają tokeny
        import re
        unsubscribe_links = re.findall(r'href="([^"]*unsubscribe[^"]*)"', enriched['html_content'])
        delete_account_links = re.findall(r'href="([^"]*delete-account[^"]*)"', enriched['html_content'])
        
        print(f"   Znalezione linki unsubscribe: {len(unsubscribe_links)}")
        for link in unsubscribe_links:
            if len(link.split('/unsubscribe/')[-1]) > 50:
                print(f"   ✅ {link}")
            else:
                print(f"   ❌ {link}")
                
        print(f"   Znalezione linki delete account: {len(delete_account_links)}")
        for link in delete_account_links:
            if len(link.split('/delete-account/')[-1]) > 50:
                print(f"   ✅ {link}")
            else:
                print(f"   ❌ {link}")
        
        return True

def main():
    """Główna funkcja"""
    try:
        success = debug_tokens_on_production()
        print("\\n" + "=" * 50)
        if success:
            print("✅ Debugowanie zakończone")
        else:
            print("❌ Błąd podczas debugowania")
        return success
    except Exception as e:
        print(f"❌ Błąd: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

