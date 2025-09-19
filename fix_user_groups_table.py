#!/usr/bin/env python3
"""
Skrypt do naprawy tabeli user_groups na serwerze produkcyjnym
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from .env file
load_dotenv()

def fix_user_groups_table():
    """Naprawia tabelę user_groups dodając brakujące kolumny"""
    
    # Pobierz URL bazy danych z zmiennych środowiskowych
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Błąd: Zmienna środowiskowa DATABASE_URL nie jest ustawiona")
        return False
    
    try:
        # Połącz z bazą danych
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("🔧 Naprawianie tabeli user_groups...")
            
            # Sprawdź czy tabela user_groups istnieje
            table_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_groups'
                );
            """)).scalar()
            
            if not table_exists:
                print("❌ Tabela user_groups nie istnieje")
                return False
            
            print("✅ Tabela user_groups istnieje")
            
            # Sprawdź kolumny w tabeli user_groups
            columns_result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = 'user_groups'
                ORDER BY ordinal_position;
            """)).fetchall()
            
            existing_columns = [col[0] for col in columns_result]
            print(f"📋 Istniejące kolumny w tabeli user_groups: {existing_columns}")
            
            # Sprawdź które kolumny z migracji już istnieją
            required_columns = {
                'event_id': 'INTEGER',
                'criteria': 'TEXT',
                'is_active': 'BOOLEAN NOT NULL DEFAULT true',
                'member_count': 'INTEGER NOT NULL DEFAULT 0',
                'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                'updated_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            }
            
            missing_columns = []
            for col_name, col_definition in required_columns.items():
                if col_name not in existing_columns:
                    missing_columns.append((col_name, col_definition))
                    print(f"❌ Brakuje kolumny: {col_name}")
                else:
                    print(f"✅ Kolumna istnieje: {col_name}")
            
            if not missing_columns:
                print("✅ Wszystkie wymagane kolumny już istnieją")
                return True
            
            print(f"\n🔧 Dodawanie brakujących kolumn: {[col[0] for col in missing_columns]}")
            
            # Dodaj brakujące kolumny
            for col_name, col_definition in missing_columns:
                try:
                    sql = f"ALTER TABLE user_groups ADD COLUMN {col_name} {col_definition};"
                    print(f"   🔧 Wykonywanie: {sql}")
                    conn.execute(text(sql))
                    print(f"   ✅ Dodano kolumnę: {col_name}")
                except Exception as e:
                    print(f"   ❌ Błąd dodawania kolumny {col_name}: {str(e)}")
                    return False
            
            conn.commit()
            print("✅ Wszystkie brakujące kolumny zostały dodane")
            
            # Sprawdź czy trzeba dodać foreign key constraints
            print("\n🔍 Sprawdzanie foreign key constraints...")
            
            # Sprawdź czy constraint dla event_id już istnieje
            event_id_constraint_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.table_constraints
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_groups'
                    AND constraint_name = 'user_groups_event_id_fkey'
                );
            """)).scalar()
            
            if not event_id_constraint_exists and 'event_id' in existing_columns:
                print("🔧 Dodawanie foreign key constraint dla event_id...")
                try:
                    conn.execute(text("""
                        ALTER TABLE user_groups 
                        ADD CONSTRAINT user_groups_event_id_fkey 
                        FOREIGN KEY (event_id) REFERENCES event_schedule(id);
                    """))
                    print("   ✅ Dodano foreign key constraint dla event_id")
                except Exception as e:
                    print(f"   ⚠️ Nie można dodać foreign key constraint dla event_id: {str(e)}")
            
            conn.commit()
            
            # Sprawdź czy trzeba zaktualizować istniejące dane
            print("\n🔍 Sprawdzanie istniejących danych...")
            
            # Sprawdź ile grup ma puste is_active
            empty_is_active = conn.execute(text("""
                SELECT COUNT(*) FROM user_groups 
                WHERE is_active IS NULL;
            """)).scalar()
            
            if empty_is_active > 0:
                print(f"🔧 Aktualizowanie is_active dla {empty_is_active} grup...")
                conn.execute(text("""
                    UPDATE user_groups 
                    SET is_active = true 
                    WHERE is_active IS NULL;
                """))
                print("   ✅ Zaktualizowano is_active")
            
            # Sprawdź ile grup ma puste member_count
            empty_member_count = conn.execute(text("""
                SELECT COUNT(*) FROM user_groups 
                WHERE member_count IS NULL;
            """)).scalar()
            
            if empty_member_count > 0:
                print(f"🔧 Aktualizowanie member_count dla {empty_member_count} grup...")
                conn.execute(text("""
                    UPDATE user_groups 
                    SET member_count = 0 
                    WHERE member_count IS NULL;
                """))
                print("   ✅ Zaktualizowano member_count")
            
            # Sprawdź czy trzeba zaktualizować created_at i updated_at
            empty_timestamps = conn.execute(text("""
                SELECT COUNT(*) FROM user_groups 
                WHERE created_at IS NULL OR updated_at IS NULL;
            """)).scalar()
            
            if empty_timestamps > 0:
                print(f"🔧 Aktualizowanie timestampów dla {empty_timestamps} grup...")
                conn.execute(text("""
                    UPDATE user_groups 
                    SET created_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE created_at IS NULL OR updated_at IS NULL;
                """))
                print("   ✅ Zaktualizowano timestampy")
            
            # Sprawdź czy trzeba zaktualizować criteria dla grup wydarzeń
            event_groups_without_criteria = conn.execute(text("""
                SELECT COUNT(*) FROM user_groups 
                WHERE group_type = 'event_based' AND (criteria IS NULL OR criteria = '');
            """)).scalar()
            
            if event_groups_without_criteria > 0:
                print(f"🔧 Aktualizowanie criteria dla {event_groups_without_criteria} grup wydarzeń...")
                
                # Zaktualizuj criteria dla grup wydarzeń na podstawie event_id
                conn.execute(text("""
                    UPDATE user_groups 
                    SET criteria = CONCAT('{"event_id": ', event_id, '}')
                    WHERE group_type = 'event_based' 
                    AND (criteria IS NULL OR criteria = '')
                    AND event_id IS NOT NULL;
                """))
                print("   ✅ Zaktualizowano criteria dla grup wydarzeń")
            
            conn.commit()
            
            print("\n✅ Naprawa tabeli user_groups zakończona pomyślnie")
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ Błąd bazy danych: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Naprawianie tabeli user_groups na serwerze produkcyjnym...")
    print()
    
    if fix_user_groups_table():
        print("\n✅ Naprawa zakończona pomyślnie")
        print("\n📋 Następne kroki:")
        print("1. Uruchom: flask db upgrade")
        print("2. Sprawdź czy aplikacja działa poprawnie")
        print("3. Sprawdź logi aplikacji")
    else:
        print("\n❌ Naprawa zakończona z błędami")
        sys.exit(1)

