#!/usr/bin/env python3
"""
Script to initialize default email schedules
"""

import psycopg2
import json
from datetime import datetime
from dotenv import load_dotenv
from config import DevelopmentConfig

load_dotenv()

def create_default_schedules(cursor):
    """Create default email schedules"""
    try:
        # 1. Email powitalny - gdy konto użytkownika zostanie aktywowane
        cursor.execute("""
        INSERT INTO email_schedules (name, description, template_id, trigger_type, trigger_conditions, recipient_type, send_type, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            'Email powitalny',
            'Automatyczny email powitalny wysyłany gdy konto użytkownika zostanie aktywowane przez administratora',
            12,  # ID szablonu powitalnego
            'user_activation',
            json.dumps({'event': 'user_activation'}),
            'user',
            'immediate',
            'active'
        ))
        print("✅ Utworzono harmonogram: Email powitalny")
        
        # 2. Email dla administratora o nowych rejestracjach
        cursor.execute("""
        INSERT INTO email_schedules (name, description, template_id, trigger_type, trigger_conditions, recipient_type, send_type, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            'Powiadomienie admina o rejestracji',
            'Email wysyłany do administratora gdy ktoś zarejestruje się na wydarzenie z zgodą na newsletter',
            14,  # ID szablonu powiadomienia admina
            'event_registration',
            json.dumps({'event': 'event_registration', 'newsletter_consent': True}),
            'admin',
            'immediate',
            'active'
        ))
        print("✅ Utworzono harmonogram: Powiadomienie admina o rejestracji")
        
        # 3. Przypomnienie o wydarzeniu - 24h przed
        cursor.execute("""
        INSERT INTO email_schedules (name, description, template_id, trigger_type, trigger_conditions, recipient_type, send_type, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            'Przypomnienie o wydarzeniu - 24h przed',
            'Przypomnienie o wydarzeniu wysyłane 24h przed do osób zapisanych na wydarzenie',
            9,  # ID szablonu przypomnienia 24h
            'event_reminder',
            json.dumps({'timing': '24h_before', 'event_type': 'all'}),
            'group',
            'scheduled',
            'active'
        ))
        print("✅ Utworzono harmonogram: Przypomnienie o wydarzeniu - 24h przed")
        
        # 4. Przypomnienie o wydarzeniu - 1h przed
        cursor.execute("""
        INSERT INTO email_schedules (name, description, template_id, trigger_type, trigger_conditions, recipient_type, send_type, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            'Przypomnienie o wydarzeniu - 1h przed',
            'Przypomnienie o wydarzeniu wysyłane 1h przed do osób zapisanych na wydarzenie',
            10,  # ID szablonu przypomnienia 1h
            'event_reminder',
            json.dumps({'timing': '1h_before', 'event_type': 'all'}),
            'group',
            'scheduled',
            'active'
        ))
        print("✅ Utworzono harmonogram: Przypomnienie o wydarzeniu - 1h przed")
        
        # 5. Przypomnienie o wydarzeniu - 5min przed
        cursor.execute("""
        INSERT INTO email_schedules (name, description, template_id, trigger_type, trigger_conditions, recipient_type, send_type, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            'Przypomnienie o wydarzeniu - 5min przed',
            'Przypomnienie o wydarzeniu wysyłane 5min przed do osób zapisanych na wydarzenie',
            11,  # ID szablonu przypomnienia 5min
            'event_reminder',
            json.dumps({'timing': '5min_before', 'event_type': 'all'}),
            'group',
            'scheduled',
            'active'
        ))
        print("✅ Utworzono harmonogram: Przypomnienie o wydarzeniu - 5min przed")
        
        return 5
        
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia harmonogramów: {e}")
        return 0

def main():
    """Main function"""
    print("🚀 Inicjalizacja domyślnych harmonogramów emaili...")
    print("=" * 60)
    
    # PostgreSQL connection parameters
    config = DevelopmentConfig()
    db_params = {
        'host': config.DB_HOST,
        'port': config.DB_PORT,
        'database': config.DB_NAME,
        'user': config.DB_USER,
        'password': config.DB_PASSWORD
    }
    
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        print("📊 Połączono z bazą PostgreSQL")
        print(f"   Host: {db_params['host']}:{db_params['port']}")
        print(f"   Database: {db_params['database']}")
        print(f"   User: {db_params['user']}")
        
        # Create default schedules
        print("\n📅 Tworzenie domyślnych harmonogramów...")
        schedules_created = create_default_schedules(cursor)
        
        # Commit changes
        conn.commit()
        
        print(f"\n🎉 Inicjalizacja zakończona pomyślnie!")
        print(f"📋 Utworzono harmonogramów: {schedules_created}")
        
        print("\n📋 Utworzone harmonogramy:")
        print("   • Email powitalny (user_activation)")
        print("   • Powiadomienie admina o rejestracji (event_registration)")
        print("   • Przypomnienie o wydarzeniu - 24h przed (event_reminder)")
        print("   • Przypomnienie o wydarzeniu - 1h przed (event_reminder)")
        print("   • Przypomnienie o wydarzeniu - 5min przed (event_reminder)")
        
        print("\n✨ System harmonogramów jest gotowy do użycia!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Błąd podczas inicjalizacji: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔌 Połączenie z bazą danych zamknięte")

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
