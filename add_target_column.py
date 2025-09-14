#!/usr/bin/env python3
"""
Skrypt do dodania kolumny 'target' do tabeli social_links
Uruchom na serwerze: python add_target_column.py
"""

import sqlite3
import os

def add_target_column():
    """Dodaje kolumnę target do tabeli social_links"""
    
    # Ścieżka do bazy danych
    db_path = 'instance/klublepszezycie.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Błąd: Baza danych nie istnieje: {db_path}")
        return False
    
    try:
        # Połączenie z bazą danych
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== DODAWANIE KOLUMNY 'target' DO TABELI social_links ===")
        
        # Sprawdź czy kolumna target już istnieje
        cursor.execute("PRAGMA table_info(social_links)")
        columns = cursor.fetchall()
        
        column_names = [col[1] for col in columns]
        print(f"Obecne kolumny: {', '.join(column_names)}")
        
        if 'target' in column_names:
            print("✅ Kolumna 'target' już istnieje!")
            return True
        
        # Dodaj kolumnę target
        print("➕ Dodawanie kolumny 'target'...")
        cursor.execute("""
            ALTER TABLE social_links 
            ADD COLUMN target VARCHAR(20) DEFAULT '_blank'
        """)
        
        # Ustaw domyślną wartość dla istniejących rekordów
        print("🔄 Ustawianie domyślnej wartości '_blank' dla istniejących rekordów...")
        cursor.execute("""
            UPDATE social_links 
            SET target = '_blank' 
            WHERE target IS NULL
        """)
        
        # Zatwierdź zmiany
        conn.commit()
        
        # Sprawdź wynik
        cursor.execute("PRAGMA table_info(social_links)")
        columns_after = cursor.fetchall()
        column_names_after = [col[1] for col in columns_after]
        
        print(f"✅ Kolumny po zmianie: {', '.join(column_names_after)}")
        
        if 'target' in column_names_after:
            print("🎉 Kolumna 'target' została pomyślnie dodana!")
            
            # Sprawdź ile rekordów zostało zaktualizowanych
            cursor.execute("SELECT COUNT(*) FROM social_links")
            count = cursor.fetchone()[0]
            print(f"📊 Liczba rekordów w tabeli: {count}")
            
            return True
        else:
            print("❌ Błąd: Kolumna 'target' nie została dodana!")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Błąd SQLite: {e}")
        return False
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def verify_changes():
    """Sprawdza czy zmiany zostały poprawnie zastosowane"""
    
    db_path = 'instance/klublepszezycie.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n=== WERYFIKACJA ZMIAN ===")
        
        # Sprawdź strukturę tabeli
        cursor.execute("PRAGMA table_info(social_links)")
        columns = cursor.fetchall()
        
        print("Struktura tabeli social_links:")
        for col in columns:
            print(f"  - {col[1]}: {col[2]} (nullable: {not col[3]}, default: {col[4]})")
        
        # Sprawdź przykładowe dane
        cursor.execute("SELECT id, platform, url, target FROM social_links LIMIT 3")
        records = cursor.fetchall()
        
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
