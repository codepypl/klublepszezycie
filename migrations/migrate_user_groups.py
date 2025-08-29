#!/usr/bin/env python3
"""
Migration script for new user groups system
Creates new tables for user groups, members, campaigns, and automations
"""

import psycopg2
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def create_user_groups_table(cursor):
    """Tworzy tabelę user_groups"""
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_groups (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            group_type VARCHAR(50) NOT NULL,
            criteria TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            member_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✅ Tabela user_groups utworzona/istnieje")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia tabeli user_groups: {e}")
        return False

def create_user_group_members_table(cursor):
    """Tworzy tabelę user_group_members"""
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_group_members (
            id SERIAL PRIMARY KEY,
            group_id INTEGER NOT NULL,
            member_type VARCHAR(50) NOT NULL,
            email VARCHAR(120) NOT NULL,
            name VARCHAR(100),
            member_metadata TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES user_groups (id) ON DELETE CASCADE
        )
        """)
        print("✅ Tabela user_group_members utworzona/istnieje")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia tabeli user_group_members: {e}")
        return False

def create_email_campaigns_table(cursor):
    """Tworzy tabelę email_campaigns"""
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_campaigns (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            subject VARCHAR(200) NOT NULL,
            html_content TEXT,
            text_content TEXT,
            recipient_groups TEXT,
            custom_emails TEXT,
            status VARCHAR(20) DEFAULT 'draft',
            send_type VARCHAR(20) DEFAULT 'immediate',
            scheduled_at TIMESTAMP,
            total_recipients INTEGER DEFAULT 0,
            sent_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP
        )
        """)
        print("✅ Tabela email_campaigns utworzona/istnieje")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia tabeli email_campaigns: {e}")
        return False

def create_email_automations_table(cursor):
    """Tworzy tabelę email_automations"""
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_automations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            automation_type VARCHAR(50) NOT NULL,
            template_id INTEGER,
            trigger_conditions TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id) REFERENCES email_templates (id)
        )
        """)
        print("✅ Tabela email_automations utworzona/istnieje")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia tabeli email_automations: {e}")
        return False

def create_email_automation_logs_table(cursor):
    """Tworzy tabelę email_automation_logs"""
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_automation_logs (
            id SERIAL PRIMARY KEY,
            automation_id INTEGER NOT NULL,
            execution_type VARCHAR(50) NOT NULL,
            recipient_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            status VARCHAR(20) DEFAULT 'running',
            details TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (automation_id) REFERENCES email_automations (id) ON DELETE CASCADE
        )
        """)
        print("✅ Tabela email_automation_logs utworzona/istnieje")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia tabeli email_automation_logs: {e}")
        return False

def create_email_schedules_table(cursor):
    """Tworzy tabelę email_schedules"""
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_schedules (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            template_id INTEGER NOT NULL,
            trigger_type VARCHAR(50) NOT NULL,
            trigger_conditions TEXT,
            recipient_type VARCHAR(20) NOT NULL,
            recipient_emails TEXT,
            recipient_group_id INTEGER,
            send_type VARCHAR(20) DEFAULT 'immediate',
            scheduled_at TIMESTAMP,
            status VARCHAR(20) DEFAULT 'active',
            last_sent TIMESTAMP,
            sent_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (template_id) REFERENCES email_templates (id),
            FOREIGN KEY (recipient_group_id) REFERENCES user_groups (id)
        )
        """)
        print("✅ Tabela email_schedules utworzona/istnieje")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia tabeli email_schedules: {e}")
        return False

def create_indexes(cursor):
    """Tworzy indeksy dla nowych tabel"""
    try:
        # Indeksy dla user_groups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_groups_type ON user_groups(group_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_groups_active ON user_groups(is_active)")
        
        # Indeksy dla user_group_members
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_group_members_group_id ON user_group_members(group_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_group_members_email ON user_group_members(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_group_members_active ON user_group_members(is_active)")
        
        # Indeksy dla email_campaigns
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_campaigns_status ON email_campaigns(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_campaigns_scheduled ON email_campaigns(scheduled_at)")
        
        # Indeksy dla email_automations
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_automations_type ON email_automations(automation_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_automations_active ON email_automations(is_active)")
        
        # Indeksy dla email_schedules
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_schedules_template_id ON email_schedules(template_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_schedules_trigger_type ON email_schedules(trigger_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_schedules_status ON email_schedules(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_email_schedules_scheduled ON email_schedules(scheduled_at)")
        
        print("✅ Indeksy utworzone/istnieją")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia indeksów: {e}")
        return False

def drop_tables(cursor):
    """Usuwa wszystkie nowe tabele (w przypadku rollback)"""
    try:
        cursor.execute("DROP TABLE IF EXISTS email_schedules")
        cursor.execute("DROP TABLE IF EXISTS email_automation_logs")
        cursor.execute("DROP TABLE IF EXISTS email_automations")
        cursor.execute("DROP TABLE IF EXISTS email_campaigns")
        cursor.execute("DROP TABLE IF EXISTS user_group_members")
        cursor.execute("DROP TABLE IF EXISTS user_groups")
        print("✅ Wszystkie nowe tabele zostały usunięte")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas usuwania tabel: {e}")
        return False

def migrate_existing_data(cursor):
    """Migracja danych została uproszczona - stary system został usunięty"""
    print("ℹ️ Stary system został usunięty - brak danych do migracji")
    return True

def main():
    """Główna funkcja migracji"""
    print("🚀 Rozpoczynam migrację systemu grup użytkowników...")
    print("=" * 50)
    
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
        # Połącz z bazą PostgreSQL
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        print("📊 Połączono z bazą PostgreSQL")
        print(f"   Host: {db_params['host']}:{db_params['port']}")
        print(f"   Database: {db_params['database']}")
        print(f"   User: {db_params['user']}")
        
        # Utwórz nowe tabele
        success = True
        success &= create_user_groups_table(cursor)
        success &= create_user_group_members_table(cursor)
        success &= create_email_campaigns_table(cursor)
        success &= create_email_automations_table(cursor)
        success &= create_email_automation_logs_table(cursor)
        success &= create_email_schedules_table(cursor)
        
        if success:
            # Utwórz indeksy
            success &= create_indexes(cursor)
            
            # Migruj istniejące dane
            success &= migrate_existing_data(cursor)
            
            if success:
                # Zatwierdź zmiany
                conn.commit()
                print("\n🎉 Migracja zakończona pomyślnie!")
                print("\n📋 Utworzone tabele:")
                print("   • user_groups - grupy użytkowników")
                print("   • user_group_members - członkowie grup")
                print("   • email_campaigns - kampanie emailowe")
                print("   • email_automations - automatyzacje emailowe")
                print("   • email_automation_logs - logi automatyzacji")
                print("   • email_schedules - harmonogramy emaili")
                print("\n✨ Nowy system mailingu jest gotowy do użycia!")
                print("🗑️ Stary system został całkowicie usunięty")
            else:
                print("\n❌ Migracja nie powiodła się!")
                conn.rollback()
        else:
            print("\n❌ Nie udało się utworzyć wszystkich tabel!")
            conn.rollback()
        
    except Exception as e:
        print(f"\n❌ Błąd podczas migracji: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()
            print("🔌 Połączenie z bazą danych zamknięte")
    
    return success

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        print("🔄 Rozpoczynam rollback migracji...")
        # Implementacja rollback
        print("ℹ️ Rollback nie jest jeszcze zaimplementowany")
    else:
        success = main()
        sys.exit(0 if success else 1)
