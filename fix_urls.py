#!/usr/bin/env python3
"""
Skrypt do naprawy URL-i w szablonach e-mail.
Zastępuje localhost:5000 na właściwą domenę.
"""

from app import create_app
from app.models import db, EmailTemplate
import os
import re


def fix_urls_in_templates():
    """Naprawia URL-e w szablonach e-mail"""
    
    app = create_app()
    with app.app_context():
        print('🔧 Naprawianie URL-i w szablonach e-mail...')
        
        # Pobierz BASE_URL z konfiguracji
        base_url = os.getenv('BASE_URL', 'https://klublepszezycie.pl')
        print(f'📡 Używam BASE_URL: {base_url}')
        
        # Pobierz wszystkie szablony
        templates = EmailTemplate.query.all()
        
        if not templates:
            print('❌ Nie znaleziono szablonów')
            return
        
        updated_count = 0
        
        for template in templates:
            print(f'\\n📝 Sprawdzam szablon: {template.name}')
            
            template_updated = False
            original_html = template.html_content
            
            # Zastąp localhost:5000 na BASE_URL
            if 'localhost:5000' in template.html_content:
                template.html_content = template.html_content.replace('localhost:5000', base_url)
                template_updated = True
                print(f'   - ✅ Zastąpiono localhost:5000 na {base_url}')
            
            # Zastąp http://localhost:5000 na BASE_URL
            if 'http://localhost:5000' in template.html_content:
                template.html_content = template.html_content.replace('http://localhost:5000', base_url)
                template_updated = True
                print(f'   - ✅ Zastąpiono http://localhost:5000 na {base_url}')
            
            # Zastąp https://localhost:5000 na BASE_URL
            if 'https://localhost:5000' in template.html_content:
                template.html_content = template.html_content.replace('https://localhost:5000', base_url)
                template_updated = True
                print(f'   - ✅ Zastąpiono https://localhost:5000 na {base_url}')
            
            # Sprawdź czy są inne localhost URL-e
            localhost_patterns = [
                r'http://localhost:\d+',
                r'https://localhost:\d+',
                r'localhost:\d+'
            ]
            
            for pattern in localhost_patterns:
                matches = re.findall(pattern, template.html_content)
                if matches:
                    for match in matches:
                        template.html_content = template.html_content.replace(match, base_url)
                        template_updated = True
                        print(f'   - ✅ Zastąpiono {match} na {base_url}')
            
            if template_updated:
                template.updated_at = db.func.now()
                updated_count += 1
                print(f'   - ✅ Zaktualizowano szablon {template.name}')
            else:
                print(f'   - ⏭️ Szablon {template.name} nie wymagał zmian')
        
        # Zatwierdź zmiany
        if updated_count > 0:
            db.session.commit()
            print(f'\\n✅ Pomyślnie zaktualizowano {updated_count} szablonów!')
        else:
            print('\\nℹ️ Żaden szablon nie wymagał aktualizacji')


def check_urls_in_templates():
    """Sprawdza URL-e w szablonach e-mail"""
    
    app = create_app()
    with app.app_context():
        print('🔍 Sprawdzanie URL-i w szablonach e-mail...')
        
        # Pobierz BASE_URL z konfiguracji
        base_url = os.getenv('BASE_URL', 'https://klublepszezycie.pl')
        print(f'📡 BASE_URL: {base_url}')
        
        # Pobierz wszystkie szablony
        templates = EmailTemplate.query.all()
        
        if not templates:
            print('❌ Nie znaleziono szablonów')
            return
        
        localhost_found = False
        
        for template in templates:
            print(f'\\n📋 {template.name}:')
            
            # Sprawdź localhost URL-e
            localhost_patterns = [
                'localhost:5000',
                'http://localhost:5000',
                'https://localhost:5000',
                'localhost:',
                'http://localhost:',
                'https://localhost:'
            ]
            
            found_patterns = []
            for pattern in localhost_patterns:
                if pattern in template.html_content:
                    found_patterns.append(pattern)
            
            if found_patterns:
                print(f'   - ❌ Znaleziono localhost URL-e: {", ".join(found_patterns)}')
                localhost_found = True
            else:
                print(f'   - ✅ Brak localhost URL-i')
            
            # Sprawdź czy ma BASE_URL
            if base_url in template.html_content:
                print(f'   - ✅ Ma BASE_URL: {base_url}')
            else:
                print(f'   - ⚠️ Brak BASE_URL: {base_url}')
        
        if localhost_found:
            print(f'\\n❌ Znaleziono localhost URL-e w szablonach - wymagana naprawa')
        else:
            print(f'\\n✅ Wszystkie szablony mają poprawne URL-e')


def test_unsubscribe_manager():
    """Testuje UnsubscribeManager"""
    
    app = create_app()
    with app.app_context():
        print('🧪 Testowanie UnsubscribeManager...')
        
        from app.services.unsubscribe_manager import unsubscribe_manager
        
        print(f'📡 BASE_URL w UnsubscribeManager: {unsubscribe_manager.base_url}')
        
        # Test generowania URL-i
        test_email = 'test@example.com'
        
        unsubscribe_url = unsubscribe_manager.get_unsubscribe_url(test_email)
        delete_url = unsubscribe_manager.get_delete_account_url(test_email)
        
        print(f'\\n🔗 Testowe URL-e:')
        print(f'   - Unsubscribe: {unsubscribe_url}')
        print(f'   - Delete account: {delete_url}')
        
        # Sprawdź czy zawierają localhost
        if 'localhost' in (unsubscribe_url or ''):
            print(f'\\n❌ Unsubscribe URL zawiera localhost!')
        else:
            print(f'\\n✅ Unsubscribe URL jest poprawny')
        
        if 'localhost' in (delete_url or ''):
            print(f'❌ Delete account URL zawiera localhost!')
        else:
            print(f'✅ Delete account URL jest poprawny')


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'check':
            check_urls_in_templates()
        elif sys.argv[1] == 'fix':
            fix_urls_in_templates()
        elif sys.argv[1] == 'test':
            test_unsubscribe_manager()
        else:
            print('❌ Nieznana komenda.')
            print('Dostępne komendy:')
            print('  - python fix_urls.py check    # Sprawdza URL-e w szablonach')
            print('  - python fix_urls.py fix      # Naprawia URL-e w szablonach')
            print('  - python fix_urls.py test     # Testuje UnsubscribeManager')
    else:
        check_urls_in_templates()
