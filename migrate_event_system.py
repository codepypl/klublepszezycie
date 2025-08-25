#!/usr/bin/env python3
"""
Skrypt migracyjny dla systemu zapisów na wydarzenia i powiadomień
Dodaje nowe tabele: event_registrations, event_notifications, event_recipient_groups
"""

import sqlite3
import sys
import os

def check_database_exists(db_path):
    """Sprawdza czy baza danych istnieje"""
    if not os.path.exists(db_path):
        print(f"❌ Baza danych nie istnieje: {db_path}")
        return False
    return True

def create_event_registrations_table(cursor):
    """Tworzy tabelę event_registrations"""
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(120) NOT NULL,
                phone VARCHAR(20),
                status VARCHAR(20) DEFAULT 'confirmed',
                wants_club_news BOOLEAN DEFAULT 0,
                notification_preferences TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES event_schedule (id)
            )
        """)
        print("✅ Tabela event_registrations utworzona/istnieje")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia tabeli event_registrations: {e}")
        return False

def create_event_notifications_table(cursor):
    """Tworzy tabelę event_notifications"""
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                notification_type VARCHAR(20) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                scheduled_at TIMESTAMP NOT NULL,
                sent_at TIMESTAMP,
                subject VARCHAR(200),
                template_name VARCHAR(100),
                recipient_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES event_schedule (id)
            )
        """)
        print("✅ Tabela event_notifications utworzona/istnieje")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia tabeli event_notifications: {e}")
        return False

def create_event_recipient_groups_table(cursor):
    """Tworzy tabelę event_recipient_groups"""
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_recipient_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                group_type VARCHAR(20) NOT NULL,
                criteria_config TEXT,
                member_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES event_schedule (id)
            )
        """)
        print("✅ Tabela event_recipient_groups utworzona/istnieje")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia tabeli event_recipient_groups: {e}")
        return False

def create_indexes(cursor):
    """Tworzy indeksy dla lepszej wydajności"""
    try:
        # Indeksy dla event_registrations
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_registrations_event_id ON event_registrations(event_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_registrations_email ON event_registrations(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_registrations_status ON event_registrations(status)")
        
        # Indeksy dla event_notifications
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_notifications_event_id ON event_notifications(event_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_notifications_type ON event_notifications(notification_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_notifications_status ON event_notifications(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_notifications_scheduled ON event_notifications(scheduled_at)")
        
        # Indeksy dla event_recipient_groups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_recipient_groups_event_id ON event_recipient_groups(event_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_recipient_groups_type ON event_recipient_groups(group_type)")
        
        print("✅ Indeksy utworzone/istnieją")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia indeksów: {e}")
        return False

def rollback_migration(cursor):
    """Cofa migrację - usuwa utworzone tabele"""
    try:
        print("🔄 Cofanie migracji...")
        
        cursor.execute("DROP TABLE IF EXISTS event_recipient_groups")
        cursor.execute("DROP TABLE IF EXISTS event_notifications")
        cursor.execute("DROP TABLE IF EXISTS event_registrations")
        
        print("✅ Migracja cofnięta - tabele usunięte")
        return True
    except Exception as e:
        print(f"❌ Błąd podczas cofania migracji: {e}")
        return False

def main():
    """Główna funkcja migracji"""
    print("🚀 Rozpoczynam migrację systemu zapisów na wydarzenia...")
    
    # Sprawdź argumenty
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        print("🔄 Tryb cofania migracji")
        rollback_mode = True
    else:
        rollback_mode = False
    
    # Ścieżka do bazy danych
    db_path = 'klublepszezycie.db'
    
    if not check_database_exists(db_path):
        sys.exit(1)
    
    try:
        # Połącz z bazą danych
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        if rollback_mode:
            # Tryb cofania
            success = rollback_migration(cursor)
        else:
            # Tryb migracji
            print("📋 Tworzę nowe tabele...")
            
            success = True
            success &= create_event_registrations_table(cursor)
            success &= create_event_notifications_table(cursor)
            success &= create_event_recipient_groups_table(cursor)
            
            if success:
                print("📋 Tworzę indeksy...")
                success &= create_indexes(cursor)
        
        if success:
            # Zatwierdź zmiany
            conn.commit()
            print("✅ Migracja zakończona pomyślnie!")
            
            if not rollback_mode:
                print("\n📊 Podsumowanie utworzonych tabel:")
                print("   • event_registrations - zapisy na wydarzenia")
                print("   • event_notifications - harmonogram powiadomień")
                print("   • event_recipient_groups - grupy odbiorców")
                print("\n🔧 Następne kroki:")
                print("   1. Uruchom aplikację")
                print("   2. W panelu admina -> Szablony E-mail -> 'Utwórz Domyślne Szablony'")
                print("   3. W panelu admina -> Harmonogram E-maili -> 'Utwórz Harmonogramy Wydarzeń'")
        else:
            print("❌ Migracja nie powiodła się")
            conn.rollback()
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Błąd podczas migracji: {e}")
        if 'conn' in locals():
            conn.rollback()
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
