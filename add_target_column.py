#!/usr/bin/env python3
"""
Skrypt do dodania kolumny 'target' do tabeli social_links (PostgreSQL)
Uruchom na serwerze: python add_target_column.py
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe
load_dotenv()

def get_database_url():
    """Pobiera URL bazy danych z zmiennych środowiskowych"""
    # Sprawdź różne możliwe nazwy zmiennych
    db_url = os.getenv('DATABASE_URL') or os.getenv('DEV_DATABASE_URL') or os.getenv('TEST_DATABASE_URL')
    
    if not db_url:
        print("❌ Błąd: Nie znaleziono DATABASE_URL w zmiennych środowiskowych")
        print("Sprawdź czy plik .env istnieje i zawiera DATABASE_URL")
        return None
    
    return db_url

def add_target_column():
    """Dodaje kolumnę target do tabeli social_links"""
    
    # Pobierz URL bazy danych
    db_url = get_database_url()
    if not db_url:
        return False
    
    try:
        # Połączenie z bazą danych PostgreSQL
        engine = create_engine(db_url)
        conn = engine.connect()
        
        print("=== DODAWANIE KOLUMNY 'target' DO TABELI social_links (PostgreSQL) ===")
        
        # Sprawdź czy kolumna target już istnieje
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'social_links' AND column_name = 'target'
        """))
        
        target_exists = result.fetchone() is not None
        
        if target_exists:
            print("✅ Kolumna 'target' już istnieje!")
            return True
        
        # Pobierz listę obecnych kolumn
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'social_links'
            ORDER BY ordinal_position
        """))
        
        columns = [row[0] for row in result.fetchall()]
        print(f"Obecne kolumny: {', '.join(columns)}")
        
        # Dodaj kolumnę target
        print("➕ Dodawanie kolumny 'target'...")
        conn.execute(text("""
            ALTER TABLE social_links 
            ADD COLUMN target VARCHAR(20) DEFAULT '_blank'
        """))
        
        # Zatwierdź zmiany
        conn.commit()
        
        # Sprawdź wynik
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'social_links'
            ORDER BY ordinal_position
        """))
        
        columns_after = [row[0] for row in result.fetchall()]
        print(f"✅ Kolumny po zmianie: {', '.join(columns_after)}")
        
        if 'target' in columns_after:
            print("🎉 Kolumna 'target' została pomyślnie dodana!")
            
            # Sprawdź ile rekordów jest w tabeli
            result = conn.execute(text("SELECT COUNT(*) FROM social_links"))
            count = result.fetchone()[0]
            print(f"📊 Liczba rekordów w tabeli: {count}")
            
            return True
        else:
            print("❌ Błąd: Kolumna 'target' nie została dodana!")
            return False
            
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def verify_changes():
    """Sprawdza czy zmiany zostały poprawnie zastosowane"""
    
    # Pobierz URL bazy danych
    db_url = get_database_url()
    if not db_url:
        return False
    
    try:
        engine = create_engine(db_url)
        conn = engine.connect()
        
        print("\n=== WERYFIKACJA ZMIAN ===")
        
        # Sprawdź strukturę tabeli
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'social_links'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        
        print("Struktura tabeli social_links:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        # Sprawdź przykładowe dane
        result = conn.execute(text("SELECT id, platform, url, target FROM social_links LIMIT 3"))
        records = result.fetchall()
        
        if records:
            print(f"\nPrzykładowe rekordy:")
            for record in records:
                print(f"  ID: {record[0]}, Platform: {record[1]}, URL: {record[2]}, Target: {record[3]}")
        else:
            print("\nBrak rekordów w tabeli social_links")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Błąd podczas weryfikacji: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Uruchamianie skryptu dodawania kolumny 'target'...")
    
    success = add_target_column()
    
    if success:
        verify_changes()
        print("\n✅ Skrypt zakończony pomyślnie!")
        print("Teraz możesz używać pola 'target' w social linkach.")
    else:
        print("\n❌ Skrypt zakończony z błędami!")
        print("Sprawdź logi powyżej i spróbuj ponownie.")
