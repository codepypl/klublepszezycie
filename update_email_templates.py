#!/usr/bin/env python3
"""
Skrypt do aktualizacji wszystkich szablonów email z nowymi linkami unsubscribe
"""
import sys
import os

# Dodaj ścieżkę do aplikacji
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.email_template_enricher import email_template_enricher

def main():
    """Aktualizuje wszystkie szablony email"""
    print("🔄 Aktualizacja szablonów email z linkami unsubscribe...")
    
    # Utwórz kontekst aplikacji
    app = create_app()
    
    with app.app_context():
        try:
            # Aktualizuj szablony
            success, message = email_template_enricher.update_existing_templates()
            
            if success:
                print(f"✅ {message}")
                print("🎉 Wszystkie szablony zostały zaktualizowane!")
            else:
                print(f"❌ {message}")
                return 1
                
        except Exception as e:
            print(f"❌ Błąd aktualizacji szablonów: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
