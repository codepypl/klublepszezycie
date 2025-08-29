#!/usr/bin/env python3
"""
Script to remove old email system tables
Removes legacy tables that are no longer needed
"""

import psycopg2
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def remove_old_tables(cursor):
    """Remove old email system tables"""
    old_tables = [
        'email_recipient_groups',
        'event_recipient_groups',
        'custom_email_campaigns'
    ]
    
    removed_tables = []
    
    for table in old_tables:
        try:
            # Check if table exists
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            """, (table,))
            
            if cursor.fetchone():
                # Drop table
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                removed_tables.append(table)
                print(f"✅ Usunięto tabelę: {table}")
            else:
                print(f"ℹ️ Tabela {table} nie istnieje")
        except Exception as e:
            print(f"❌ Błąd podczas usuwania tabeli {table}: {e}")
    
    return removed_tables

def remove_new_tables(cursor):
    """Remove new tables to recreate them with correct column names"""
    new_tables = [
        'event_email_schedules',
        'email_automation_logs',
        'email_automations',
        'email_campaigns',
        'user_group_members',
        'user_groups',
        'email_schedules'
    ]
    
    removed_tables = []
    
    for table in new_tables:
        try:
            # Check if table exists
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = %s
            """, (table,))
            
            if cursor.fetchone():
                # Drop table
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                removed_tables.append(table)
                print(f"✅ Usunięto tabelę: {table}")
            else:
                print(f"ℹ️ Tabela {table} nie istnieje")
        except Exception as e:
            print(f"❌ Błąd podczas usuwania tabeli {table}: {e}")
    
    return removed_tables

def remove_old_indexes(cursor):
    """Remove old indexes"""
    old_indexes = [
        'idx_email_recipient_groups_event_id',
        'idx_email_recipient_groups_type'
    ]
    
    removed_indexes = []
    
    for index in old_indexes:
        try:
            cursor.execute(f"DROP INDEX IF EXISTS {index}")
            removed_indexes.append(index)
            print(f"✅ Usunięto indeks: {index}")
        except Exception as e:
            print(f"❌ Błąd podczas usuwania indeksu {index}: {e}")
    
    return removed_indexes

def main():
    """Main function to remove old tables"""
    print("🗑️ Usuwanie starych tabel systemu mailingu...")
    print("=" * 60)
    
    # PostgreSQL connection parameters from config.py
    from config import config
from config import DevelopmentConfig
    
    # Użyj DevelopmentConfig (domyślna konfiguracja)
    dev_config = DevelopmentConfig()
    
    db_params = {
        'host': dev_config.DB_HOST,
        'port': dev_config.DB_PORT,
        'database': dev_config.DB_NAME,
        'user': dev_config.DB_USER,
        'password': dev_config.DB_PASSWORD
    }
    
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        print("📊 Połączono z bazą PostgreSQL")
        print(f"   Host: {db_params['host']}:{db_params['port']}")
        print(f"   Database: {db_params['database']}")
        print(f"   User: {db_params['user']}")
        
        # Remove old tables
        print("\n🗑️ Usuwanie starych tabel...")
        removed_tables = remove_old_tables(cursor)
        
        # Remove new tables to recreate them with correct column names
        print("\n🗑️ Usuwanie nowych tabel (do ponownego utworzenia)...")
        removed_new_tables = remove_new_tables(cursor)
        
        # Remove old indexes
        print("\n🗑️ Usuwanie starych indeksów...")
        removed_indexes = remove_old_indexes(cursor)
        
        # Commit changes
        conn.commit()
        
        print(f"\n🎉 Usuwanie zakończone pomyślnie!")
        print(f"📋 Usunięte tabele: {len(removed_tables)}")
        print(f"📋 Usunięte indeksy: {len(removed_indexes)}")
        
        if removed_tables:
            print("\n🗑️ Usunięte tabele:")
            for table in removed_tables:
                print(f"   • {table}")
        
        if removed_indexes:
            print("\n🗑️ Usunięte indeksy:")
            for index in removed_indexes:
                print(f"   • {index}")
        
        print("\n✨ Stary system mailingu został całkowicie usunięty!")
        print("🆕 Nowy system jest jedynym aktywnym systemem")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Błąd podczas usuwania starych tabel: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔌 Połączenie z bazą danych zamknięte")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
