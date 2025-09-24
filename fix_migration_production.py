#!/usr/bin/env python3
"""
Skrypt do naprawy migracji na serwerze produkcyjnym
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

def fix_migration():
    """Naprawia migrację na serwerze produkcyjnym"""
    
    # Pobierz URL bazy danych z zmiennych środowiskowych
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Brak DATABASE_URL w zmiennych środowiskowych")
        return False
    
    try:
        # Połącz się z bazą danych
        engine = create_engine(database_url)
        
        with engine.connect() as connection:
            # Sprawdź czy kolumny już istnieją
            try:
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'email_queue' 
                    AND column_name IN ('content_hash', 'duplicate_check_key')
                """))
                existing_columns = [row[0] for row in result]
                print(f"🔍 Istniejące kolumny: {existing_columns}")
                
                # Dodaj brakujące kolumny
                if 'content_hash' not in existing_columns:
                    print("➕ Dodawanie kolumny content_hash...")
                    connection.execute(text("""
                        ALTER TABLE email_queue 
                        ADD COLUMN content_hash VARCHAR(64)
                    """))
                    connection.commit()
                    print("✅ Kolumna content_hash dodana")
                
                if 'duplicate_check_key' not in existing_columns:
                    print("➕ Dodawanie kolumny duplicate_check_key...")
                    connection.execute(text("""
                        ALTER TABLE email_queue 
                        ADD COLUMN duplicate_check_key VARCHAR(255)
                    """))
                    connection.commit()
                    print("✅ Kolumna duplicate_check_key dodana")
                
                # Wypełnij content_hash dla istniejących rekordów
                print("🔄 Wypełnianie content_hash dla istniejących rekordów...")
                connection.execute(text("""
                    UPDATE email_queue 
                    SET content_hash = MD5(CONCAT(recipient_email, '|', subject, '|', COALESCE(html_content, ''), '|', COALESCE(text_content, '')))
                    WHERE content_hash IS NULL
                """))
                connection.commit()
                print("✅ content_hash wypełniony")
                
                # Zmień content_hash na NOT NULL
                print("🔧 Zmiana content_hash na NOT NULL...")
                connection.execute(text("""
                    ALTER TABLE email_queue 
                    ALTER COLUMN content_hash SET NOT NULL
                """))
                connection.commit()
                print("✅ content_hash ustawiony jako NOT NULL")
                
                # Sprawdź czy indeksy już istnieją i dodaj brakujące
                try:
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS ix_email_queue_content_hash 
                        ON email_queue (content_hash)
                    """))
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS ix_email_queue_duplicate_check_key 
                        ON email_queue (duplicate_check_key)
                    """))
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS ix_email_queue_duplicate_pending 
                        ON email_queue (recipient_email, subject, status)
                    """))
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS ix_email_queue_campaign_duplicate 
                        ON email_queue (recipient_email, campaign_id, content_hash)
                    """))
                    connection.execute(text("""
                        CREATE INDEX IF NOT EXISTS ix_email_queue_custom_key 
                        ON email_queue (duplicate_check_key)
                    """))
                    connection.commit()
                    print("✅ Indeksy dodane")
                    
                except ProgrammingError as e:
                    print(f"⚠️ Niektóre indeksy mogą już istnieć: {e}")
                
                print("\n🎉 Migracja naprawiona pomyślnie!")
                print("\n📋 Następne kroki:")
                print("1. Oznacz migrację jako zastosowaną:")
                print("   flask db stamp 3b231ed058fc")
                print("2. Sprawdź status migracji:")
                print("   flask db current")
                print("3. Uruchom aplikację ponownie")
                
                return True
                
            except ProgrammingError as e:
                print(f"❌ Błąd podczas sprawdzania kolumn: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Błąd połączenia z bazą danych: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Naprawianie migracji na serwerze produkcyjnym...")
    success = fix_migration()
    sys.exit(0 if success else 1)
