#!/usr/bin/env python3
"""
Skrypt do naprawy problematycznej migracji na serwerze produkcyjnym
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def fix_migration():
    """Naprawia problematyczną migrację"""
    
    # Pobierz URL bazy danych z zmiennych środowiskowych
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Błąd: Zmienna środowiskowa DATABASE_URL nie jest ustawiona")
        return False
    
    try:
        # Połącz z bazą danych
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("🔧 Naprawianie problematycznej migracji...")
            
            # Sprawdź czy kolumny już istnieją
            columns_result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = 'user_history'
                ORDER BY ordinal_position;
            """)).fetchall()
            
            existing_columns = [col[0] for col in columns_result]
            print(f"📋 Istniejące kolumny: {existing_columns}")
            
            # Sprawdź które kolumny z migracji już istnieją
            migration_columns = [
                'registration_type',
                'was_club_member', 
                'registration_date',
                'participation_date',
                'status',
                'notes'
            ]
            
            existing_migration_columns = [col for col in migration_columns if col in existing_columns]
            missing_migration_columns = [col for col in migration_columns if col not in existing_columns]
            
            print(f"✅ Kolumny już istniejące: {existing_migration_columns}")
            print(f"❌ Brakujące kolumny: {missing_migration_columns}")
            
            # Jeśli wszystkie kolumny już istnieją, oznacza to że migracja została częściowo zastosowana
            if len(existing_migration_columns) == len(migration_columns):
                print("🔍 Wszystkie kolumny z migracji już istnieją - sprawdzanie czy migracja została zastosowana...")
                
                # Sprawdź czy migracja została oznaczone jako zastosowana
                migration_result = conn.execute(text("""
                    SELECT version_num FROM alembic_version;
                """)).scalar()
                
                print(f"📋 Obecna wersja migracji: {migration_result}")
                
                if migration_result == "af25e20522fc":
                    print("✅ Migracja af25e20522fc została już zastosowana")
                    return True
                else:
                    print("⚠️ Migracja nie została oznaczona jako zastosowana - oznaczamy ręcznie...")
                    
                    # Oznacz migrację jako zastosowaną
                    conn.execute(text("""
                        UPDATE alembic_version SET version_num = 'af25e20522fc';
                    """))
                    conn.commit()
                    
                    print("✅ Migracja af25e20522fc została oznaczona jako zastosowana")
                    return True
            
            # Jeśli niektóre kolumny brakują, dodaj je ręcznie
            elif missing_migration_columns:
                print(f"🔧 Dodawanie brakujących kolumn: {missing_migration_columns}")
                
                # Dodaj brakujące kolumny
                for col in missing_migration_columns:
                    if col == 'registration_type':
                        conn.execute(text("ALTER TABLE user_history ADD COLUMN registration_type VARCHAR(20) NOT NULL DEFAULT 'registration';"))
                    elif col == 'was_club_member':
                        conn.execute(text("ALTER TABLE user_history ADD COLUMN was_club_member BOOLEAN NOT NULL DEFAULT false;"))
                    elif col == 'registration_date':
                        conn.execute(text("ALTER TABLE user_history ADD COLUMN registration_date TIMESTAMP;"))
                    elif col == 'participation_date':
                        conn.execute(text("ALTER TABLE user_history ADD COLUMN participation_date TIMESTAMP;"))
                    elif col == 'status':
                        conn.execute(text("ALTER TABLE user_history ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'registered';"))
                    elif col == 'notes':
                        conn.execute(text("ALTER TABLE user_history ADD COLUMN notes TEXT;"))
                    
                    print(f"   ✅ Dodano kolumnę: {col}")
                
                conn.commit()
                
                # Usuń domyślne wartości
                for col in missing_migration_columns:
                    if col in ['registration_type', 'was_club_member', 'status']:
                        conn.execute(text(f"ALTER TABLE user_history ALTER COLUMN {col} DROP DEFAULT;"))
                
                conn.commit()
                
                print("✅ Wszystkie brakujące kolumny zostały dodane")
                
                # Sprawdź czy trzeba dodać constraint'y i indeksy
                print("🔍 Sprawdzanie constraint'ów i indeksów...")
                
                # Sprawdź czy unique constraint już istnieje
                constraint_exists = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.table_constraints
                        WHERE table_schema = 'public' 
                        AND table_name = 'user_history'
                        AND constraint_name = '_unique_user_event_history'
                    );
                """)).scalar()
                
                if not constraint_exists:
                    print("🔧 Dodawanie unique constraint...")
                    conn.execute(text("""
                        ALTER TABLE user_history 
                        ADD CONSTRAINT _unique_user_event_history 
                        UNIQUE (user_id, event_id);
                    """))
                    print("   ✅ Dodano unique constraint")
                
                # Sprawdź czy indeks już istnieje
                index_exists = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM pg_indexes
                        WHERE tablename = 'user_history'
                        AND indexname = 'ix_user_history_registration_date'
                    );
                """)).scalar()
                
                if not index_exists:
                    print("🔧 Dodawanie indeksu...")
                    conn.execute(text("""
                        CREATE INDEX ix_user_history_registration_date 
                        ON user_history (registration_date);
                    """))
                    print("   ✅ Dodano indeks")
                
                conn.commit()
                
                # Oznacz migrację jako zastosowaną
                conn.execute(text("""
                    UPDATE alembic_version SET version_num = 'af25e20522fc';
                """))
                conn.commit()
                
                print("✅ Migracja af25e20522fc została oznaczona jako zastosowana")
                return True
            
            else:
                print("✅ Wszystkie kolumny już istnieją")
                return True
            
    except SQLAlchemyError as e:
        print(f"❌ Błąd bazy danych: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 Naprawianie problematycznej migracji na serwerze produkcyjnym...")
    print()
    
    if fix_migration():
        print("\n✅ Naprawa zakończona pomyślnie")
        print("\n📋 Następne kroki:")
        print("1. Uruchom: flask db upgrade")
        print("2. Sprawdź czy wszystkie migracje zostały zastosowane")
    else:
        print("\n❌ Naprawa zakończona z błędami")
        sys.exit(1)
