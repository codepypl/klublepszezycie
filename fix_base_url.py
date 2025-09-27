#!/usr/bin/env python3
"""
Skrypt do naprawy BASE_URL w .env na produkcji
"""

import os
import sys
from datetime import datetime

def fix_base_url():
    """Naprawia BASE_URL w pliku .env"""
    env_file = '.env'
    
    if not os.path.exists(env_file):
        print(f"❌ Nie znaleziono pliku {env_file}")
        return False
    
    print("🔧 Naprawiam BASE_URL w .env...")
    
    # Wczytaj zawartość pliku
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Znajdź i zastąp BASE_URL
    updated = False
    new_lines = []
    
    for line in lines:
        if line.startswith('BASE_URL='):
            old_value = line.strip()
            new_line = 'BASE_URL=https://klublepszezycie.pl\n'
            new_lines.append(new_line)
            print(f"   ✅ Zastąpiono: {old_value}")
            print(f"   ✅ Nowy: {new_line.strip()}")
            updated = True
        else:
            new_lines.append(line)
    
    if not updated:
        # Dodaj BASE_URL jeśli nie istnieje
        new_lines.append('BASE_URL=https://klublepszezycie.pl\n')
        print("   ✅ Dodano BASE_URL=https://klublepszezycie.pl")
        updated = True
    
    # Zapisz zaktualizowany plik
    if updated:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("✅ Plik .env został zaktualizowany")
        
        # Test nowej konfiguracji
        print("\\n🧪 Test nowej konfiguracji...")
        from dotenv import load_dotenv
        load_dotenv()
        
        base_url = os.getenv('BASE_URL')
        print(f"BASE_URL: {base_url}")
        
        if base_url == 'https://klublepszezycie.pl':
            print("✅ BASE_URL jest poprawny")
            
            # Test UnsubscribeManager
            try:
                from app import create_app
                app = create_app()
                with app.app_context():
                    from app.services.unsubscribe_manager import unsubscribe_manager
                    test_email = 'test@example.com'
                    unsubscribe_url = unsubscribe_manager.get_unsubscribe_url(test_email)
                    delete_account_url = unsubscribe_manager.get_delete_account_url(test_email)
                    
                    print(f"\\n📧 Test URL-e:")
                    print(f"Unsubscribe: {unsubscribe_url}")
                    print(f"Delete account: {delete_account_url}")
                    
                    if 'klublepszezycie.pl' in unsubscribe_url and 'klublepszezycie.pl' in delete_account_url:
                        print("✅ URL-e zawierają klublepszezycie.pl")
                        return True
                    else:
                        print("❌ URL-e nadal nie są poprawne")
                        return False
            except Exception as e:
                print(f"❌ Błąd testu: {e}")
                return False
        else:
            print(f"❌ BASE_URL nadal niepoprawny: {base_url}")
            return False
    else:
        print("❌ Nie udało się zaktualizować .env")
        return False

def main():
    """Główna funkcja"""
    print("🚀 Rozpoczynam naprawę BASE_URL...")
    print(f"📅 Czas: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    success = fix_base_url()
    
    print("-" * 50)
    if success:
        print("✅ BASE_URL został naprawiony pomyślnie!")
        print("📧 Teraz możesz uruchomić: uv run update_templates_klub_style.py")
    else:
        print("❌ Nie udało się naprawić BASE_URL")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

