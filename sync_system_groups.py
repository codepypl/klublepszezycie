#!/usr/bin/env python3
"""
Skrypt do synchronizacji grup systemowych
Synchronizuje grupy 'Wszyscy użytkownicy' i 'Członkowie klubu' z aktualnymi danymi użytkowników
"""

import sys
import os

# Dodaj ścieżkę do aplikacji
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.group_manager import GroupManager

def main():
    """Główna funkcja synchronizacji"""
    print("🔄 Synchronizacja grup systemowych...")
    print("=" * 50)
    
    # Utwórz aplikację
    app = create_app()
    
    with app.app_context():
        try:
            # Utwórz menedżera grup
            group_manager = GroupManager()
            
            # Synchronizuj wszystkie grupy systemowe
            success, message = group_manager.sync_system_groups()
            
            if success:
                print("✅ Synchronizacja zakończona pomyślnie!")
                print(f"📊 Wyniki: {message}")
            else:
                print("❌ Błąd synchronizacji!")
                print(f"🚨 Szczegóły: {message}")
                return 1
                
        except Exception as e:
            print(f"❌ Błąd krytyczny: {str(e)}")
            return 1
    
    print("=" * 50)
    print("🎉 Synchronizacja zakończona!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


