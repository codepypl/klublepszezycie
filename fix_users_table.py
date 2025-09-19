#!/usr/bin/env python3
"""
Skrypt do naprawy tabeli users na serwerze produkcyjnym
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from .env file
load_dotenv()

def fix_users_table():
    """Naprawia tabelę users dodając brakujące kolumny"""
    
    # Pobierz URL bazy danych z zmiennych środowiskowych
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Błąd: Zmienna środowiskowa DATABASE_URL nie jest ustawiona")
        return False
    
    try:
        # Połącz z bazą danych
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("🔧 Naprawianie tabeli users...")
            
            # Sprawdź czy tabela users istnieje
            table_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """)).scalar()
            
            if not table_exists:
                print("❌ Tabela users nie istnieje")
                return False
            
            print("✅ Tabela users istnieje")
            
            # Sprawdź kolumny w tabeli users
            columns_result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = 'users'
                ORDER BY ordinal_position;
            """)).fetchall()
            
            existing_columns = [col[0] for col in columns_result]
            print(f"📋 Istniejące kolumny w tabeli users: {existing_columns}")
            
            # Sprawdź które kolumny z migracji już istnieją
            required_columns = {
                'account_type': 'VARCHAR(50) NOT NULL DEFAULT \'user\'',
                'event_id': 'INTEGER',
                'group_id': 'INTEGER'
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
                    sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_definition};"
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
                    AND table_name = 'users'
                    AND constraint_name = 'users_event_id_fkey'
                );
            """)).scalar()
            
            if not event_id_constraint_exists and 'event_id' in existing_columns:
                print("🔧 Dodawanie foreign key constraint dla event_id...")
                try:
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD CONSTRAINT users_event_id_fkey 
                        FOREIGN KEY (event_id) REFERENCES event_schedule(id);
                    """))
                    print("   ✅ Dodano foreign key constraint dla event_id")
                except Exception as e:
                    print(f"   ⚠️ Nie można dodać foreign key constraint dla event_id: {str(e)}")
            
            # Sprawdź czy constraint dla group_id już istnieje
            group_id_constraint_exists = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.table_constraints
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                    AND constraint_name = 'users_group_id_fkey'
                );
            """)).scalar()
            
            if not group_id_constraint_exists and 'group_id' in existing_columns:
                print("🔧 Dodawanie foreign key constraint dla group_id...")
                try:
                    conn.execute(text("""
                        ALTER TABLE users 
                        ADD CONSTRAINT users_group_id_fkey 
                        FOREIGN KEY (group_id) REFERENCES user_groups(id);
                    """))
                    print("   ✅ Dodano foreign key constraint dla group_id")
                except Exception as e:
                    print(f"   ⚠️ Nie można dodać foreign key constraint dla group_id: {str(e)}")
            
            conn.commit()
            
            # Sprawdź czy trzeba zaktualizować istniejące dane
            print("\n🔍 Sprawdzanie istniejących danych...")
            
            # Sprawdź ile użytkowników ma puste account_type
            empty_account_type = conn.execute(text("""
                SELECT COUNT(*) FROM users 
                WHERE account_type IS NULL OR account_type = '';
            """)).scalar()
            
            if empty_account_type > 0:
                print(f"🔧 Aktualizowanie account_type dla {empty_account_type} użytkowników...")
                conn.execute(text("""
                    UPDATE users 
                    SET account_type = 'user' 
                    WHERE account_type IS NULL OR account_type = '';
                """))
                print("   ✅ Zaktualizowano account_type")
            
            # Sprawdź czy trzeba zaktualizować group_id dla członków klubu
            club_members_without_group = conn.execute(text("""
                SELECT COUNT(*) FROM users 
                WHERE club_member = true AND group_id IS NULL;
            """)).scalar()
            
            if club_members_without_group > 0:
                print(f"🔧 Aktualizowanie group_id dla {club_members_without_group} członków klubu...")
                
                # Znajdź ID grupy członków klubu
                club_group_id = conn.execute(text("""
                    SELECT id FROM user_groups 
                    WHERE name = 'Członkowie klubu' 
                    LIMIT 1;
                """)).scalar()
                
                if club_group_id:
                    conn.execute(text(f"""
                        UPDATE users 
                        SET group_id = {club_group_id} 
                        WHERE club_member = true AND group_id IS NULL;
                    """))
                    print(f"   ✅ Zaktualizowano group_id dla członków klubu (group_id = {club_group_id})")
                else:
                    print("   ⚠️ Nie znaleziono grupy 'Członkowie klubu'")
            
            conn.commit()
            
            print("\n✅ Naprawa tabeli users zakończona pomyślnie")
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ Błąd bazy danych: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Naprawianie tabeli users na serwerze produkcyjnym...")
    print()
    
    if fix_users_table():
        print("\n✅ Naprawa zakończona pomyślnie")
        print("\n📋 Następne kroki:")
        print("1. Uruchom: flask db upgrade")
        print("2. Sprawdź czy aplikacja działa poprawnie")
        print("3. Sprawdź logi aplikacji")
    else:
        print("\n❌ Naprawa zakończona z błędami")
        sys.exit(1)
