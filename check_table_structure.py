#!/usr/bin/env python3
"""
Skrypt do sprawdzenia struktury tabeli user_history na serwerze produkcyjnym
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from .env file
load_dotenv()

def check_table_structure():
    """Sprawdza strukturę tabeli user_history"""
    
    # Pobierz URL bazy danych z zmiennych środowiskowych
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Błąd: Zmienna środowiskowa DATABASE_URL nie jest ustawiona")
        return False
    
    try:
        # Połącz z bazą danych
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("🔍 Sprawdzanie struktury tabeli user_history...")
            
            # Sprawdź czy tabela istnieje
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'user_history'
                );
            """)).scalar()
            
            if not result:
                print("❌ Tabela user_history nie istnieje")
                return False
            
            print("✅ Tabela user_history istnieje")
            
            # Sprawdź kolumny w tabeli
            columns_result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' 
                AND table_name = 'user_history'
                ORDER BY ordinal_position;
            """)).fetchall()
            
            print(f"\n📋 Kolumny w tabeli user_history ({len(columns_result)}):")
            for col in columns_result:
                print(f"   - {col[0]} ({col[1]}) - nullable: {col[2]}, default: {col[3]}")
            
            # Sprawdź czy kolumny z migracji już istnieją
            existing_columns = [col[0] for col in columns_result]
            
            migration_columns = [
                'registration_type',
                'was_club_member', 
                'registration_date',
                'participation_date',
                'status',
                'notes'
            ]
            
            print(f"\n🔍 Sprawdzanie kolumn z migracji:")
            for col in migration_columns:
                if col in existing_columns:
                    print(f"   ✅ {col} - już istnieje")
                else:
                    print(f"   ❌ {col} - nie istnieje")
            
            # Sprawdź constraint'y
            constraints_result = conn.execute(text("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints
                WHERE table_schema = 'public' 
                AND table_name = 'user_history';
            """)).fetchall()
            
            print(f"\n📋 Constraint'y w tabeli user_history ({len(constraints_result)}):")
            for constraint in constraints_result:
                print(f"   - {constraint[0]} ({constraint[1]})")
            
            # Sprawdź indeksy
            indexes_result = conn.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'user_history';
            """)).fetchall()
            
            print(f"\n📋 Indeksy w tabeli user_history ({len(indexes_result)}):")
            for index in indexes_result:
                print(f"   - {index[0]}: {index[1]}")
            
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ Błąd bazy danych: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Sprawdzanie struktury tabeli user_history na serwerze produkcyjnym...")
    print()
    
    if check_table_structure():
        print("\n✅ Sprawdzanie zakończone pomyślnie")
    else:
        print("\n❌ Sprawdzanie zakończone z błędami")
        sys.exit(1)
