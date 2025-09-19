#!/usr/bin/env python3
"""
Skrypt do sprawdzenia stanu migracji na serwerze produkcyjnym
"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables from .env file
load_dotenv()

def check_migrations():
    """Sprawdza stan migracji na serwerze produkcyjnym"""
    
    # Pobierz URL bazy danych z zmiennych środowiskowych
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ Błąd: Zmienna środowiskowa DATABASE_URL nie jest ustawiona")
        return False
    
    try:
        # Połącz z bazą danych
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            print("🔍 Sprawdzanie stanu migracji na serwerze produkcyjnym...")
            
            # Sprawdź obecną wersję migracji
            try:
                current_version = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
                print(f"📋 Obecna wersja migracji: {current_version}")
            except Exception as e:
                print(f"❌ Błąd pobierania wersji migracji: {str(e)}")
                return False
            
            # Sprawdź wszystkie migracje w historii
            try:
                migrations_result = conn.execute(text("""
                    SELECT version_num, is_current 
                    FROM alembic_version 
                    ORDER BY version_num;
                """)).fetchall()
                
                print(f"\n📋 Historia migracji ({len(migrations_result)}):")
                for migration in migrations_result:
                    status = "✅ AKTYWNA" if migration[1] else "📝 HISTORIA"
                    print(f"   - {migration[0]} {status}")
                    
            except Exception as e:
                print(f"⚠️ Nie można pobrać historii migracji: {str(e)}")
            
            # Sprawdź strukturę kluczowych tabel
            print(f"\n🔍 Sprawdzanie struktury kluczowych tabel...")
            
            key_tables = ['users', 'user_history', 'user_logs', 'stats', 'user_groups']
            
            for table_name in key_tables:
                try:
                    # Sprawdź czy tabela istnieje
                    table_exists = conn.execute(text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = '{table_name}'
                        );
                    """)).scalar()
                    
                    if table_exists:
                        # Sprawdź kolumny
                        columns_result = conn.execute(text(f"""
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_schema = 'public' 
                            AND table_name = '{table_name}'
                            ORDER BY ordinal_position;
                        """)).fetchall()
                        
                        columns = [col[0] for col in columns_result]
                        print(f"   ✅ {table_name}: {len(columns)} kolumn - {columns}")
                    else:
                        print(f"   ❌ {table_name}: Tabela nie istnieje")
                        
                except Exception as e:
                    print(f"   ⚠️ {table_name}: Błąd sprawdzania - {str(e)}")
            
            # Sprawdź kluczowe kolumny w tabeli users
            print(f"\n🔍 Sprawdzanie kluczowych kolumn w tabeli users...")
            
            try:
                users_columns_result = conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                    ORDER BY ordinal_position;
                """)).fetchall()
                
                users_columns = [col[0] for col in users_columns_result]
                
                required_columns = ['account_type', 'event_id', 'group_id']
                missing_columns = [col for col in required_columns if col not in users_columns]
                
                if missing_columns:
                    print(f"   ❌ Brakujące kolumny: {missing_columns}")
                    print(f"   💡 Uruchom: python fix_users_table.py")
                else:
                    print(f"   ✅ Wszystkie wymagane kolumny istnieją")
                    
            except Exception as e:
                print(f"   ❌ Błąd sprawdzania kolumn users: {str(e)}")
            
            # Sprawdź dane w tabelach
            print(f"\n🔍 Sprawdzanie danych w kluczowych tabelach...")
            
            try:
                users_count = conn.execute(text("SELECT COUNT(*) FROM users;")).scalar()
                print(f"   📊 users: {users_count} rekordów")
                
                user_history_count = conn.execute(text("SELECT COUNT(*) FROM user_history;")).scalar()
                print(f"   📊 user_history: {user_history_count} rekordów")
                
                user_logs_count = conn.execute(text("SELECT COUNT(*) FROM user_logs;")).scalar()
                print(f"   📊 user_logs: {user_logs_count} rekordów")
                
                stats_count = conn.execute(text("SELECT COUNT(*) FROM stats;")).scalar()
                print(f"   📊 stats: {stats_count} rekordów")
                
                user_groups_count = conn.execute(text("SELECT COUNT(*) FROM user_groups;")).scalar()
                print(f"   📊 user_groups: {user_groups_count} rekordów")
                
            except Exception as e:
                print(f"   ⚠️ Błąd sprawdzania danych: {str(e)}")
            
            return True
            
    except SQLAlchemyError as e:
        print(f"❌ Błąd bazy danych: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Nieoczekiwany błąd: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 Sprawdzanie stanu migracji na serwerze produkcyjnym...")
    print()
    
    if check_migrations():
        print("\n✅ Sprawdzanie zakończone pomyślnie")
    else:
        print("\n❌ Sprawdzanie zakończone z błędami")
        sys.exit(1)
