#!/usr/bin/env python3
"""
Skrypt migracyjny dla tabeli event_schedule
Dodaje brakujące kolumny: hero_background i hero_background_type
"""

import os
import sys
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Boolean
from sqlalchemy.exc import OperationalError

# Dodaj ścieżkę do katalogu projektu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config

def run_migration():
    """Uruchamia migrację bazy danych"""
    print("🚀 Uruchamianie migracji dla tabeli event_schedule...")
    
    try:
        # Utwórz połączenie z bazą danych
        db_url = config['development'].SQLALCHEMY_DATABASE_URI
        engine = create_engine(db_url)
        
        # Sprawdź połączenie
        with engine.connect() as conn:
            print("✅ Połączenie z bazą danych ustanowione")
            
            # Sprawdź czy tabela event_schedule istnieje
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'event_schedule'
                );
            """))
            
            if not result.scalar():
                print("❌ Tabela event_schedule nie istnieje!")
                print("   Uruchom najpierw aplikację, aby utworzyć tabele.")
                return False
            
            print("✅ Tabela event_schedule istnieje")
            
            # Sprawdź czy kolumna hero_background istnieje
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'event_schedule' 
                    AND column_name = 'hero_background'
                );
            """))
            
            if result.scalar():
                print("✅ Kolumna hero_background już istnieje")
            else:
                print("➕ Dodawanie kolumny hero_background...")
                conn.execute(text("""
                    ALTER TABLE event_schedule 
                    ADD COLUMN hero_background VARCHAR(500);
                """))
                print("✅ Kolumna hero_background została dodana")
            
            # Sprawdź czy kolumna hero_background_type istnieje
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'event_schedule' 
                    AND column_name = 'hero_background_type'
                );
            """))
            
            if result.scalar():
                print("✅ Kolumna hero_background_type już istnieje")
            else:
                print("➕ Dodawanie kolumny hero_background_type...")
                conn.execute(text("""
                    ALTER TABLE event_schedule 
                    ADD COLUMN hero_background_type VARCHAR(20) DEFAULT 'image';
                """))
                print("✅ Kolumna hero_background_type została dodana")
            
            # Zatwierdź zmiany
            conn.commit()
            print("✅ Zmiany zostały zatwierdzone")
            
            # Sprawdź finalną strukturę tabeli
            print("\n📋 Struktura tabeli event_schedule:")
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'event_schedule'
                ORDER BY ordinal_position;
            """))
            
            for row in result:
                print(f"   {row.column_name}: {row.data_type} (nullable: {row.is_nullable}, default: {row.column_default})")
            
            print("\n🎉 Migracja zakończona pomyślnie!")
            return True
            
    except OperationalError as e:
        print(f"❌ Błąd bazy danych: {e}")
        return False
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {e}")
        return False

def rollback_migration():
    """Cofa migrację (usuwa dodane kolumny)"""
    print("🔄 Cofanie migracji...")
    
    try:
        db_url = config['development'].SQLALCHEMY_DATABASE_URI
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Usuń kolumnę hero_background_type
            try:
                conn.execute(text("ALTER TABLE event_schedule DROP COLUMN IF EXISTS hero_background_type;"))
                print("✅ Kolumna hero_background_type została usunięta")
            except Exception as e:
                print(f"⚠️  Błąd podczas usuwania hero_background_type: {e}")
            
            # Usuń kolumnę hero_background
            try:
                conn.execute(text("ALTER TABLE event_schedule DROP COLUMN IF EXISTS hero_background;"))
                print("✅ Kolumna hero_background została usunięta")
            except Exception as e:
                print(f"⚠️  Błąd podczas usuwania hero_background: {e}")
            
            conn.commit()
            print("✅ Rollback zakończony")
            
    except Exception as e:
        print(f"❌ Błąd podczas rollback: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback_migration()
    else:
        success = run_migration()
        if not success:
            sys.exit(1)
