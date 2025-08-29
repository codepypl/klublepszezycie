#!/usr/bin/env python3
"""
Migration script for user system updates:
- Add is_temporary_password field to users table
- Make username nullable
- Update existing users to have is_temporary_password = False
"""

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def migrate_user_system():
    """Migrate user system to new schema"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'klub'),
            user=os.getenv('DB_USER', 'shadi'),
            password=os.getenv('DB_PASSWORD', 'Das5ahec')
        )
        
        cursor = conn.cursor()
        
        print("🔄 Rozpoczynam migrację systemu użytkowników...")
        
        # Sprawdź czy kolumna is_temporary_password już istnieje
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'is_temporary_password'
        """)
        
        if cursor.fetchone():
            print("✅ Kolumna is_temporary_password już istnieje")
        else:
            # Dodaj kolumnę is_temporary_password
            print("➕ Dodaję kolumnę is_temporary_password...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN is_temporary_password BOOLEAN DEFAULT TRUE
            """)
            print("✅ Kolumna is_temporary_password została dodana")
        
        # Sprawdź czy kolumna username jest nullable
        cursor.execute("""
            SELECT is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'username'
        """)
        
        result = cursor.fetchone()
        if result and result[0] == 'YES':
            print("✅ Kolumna username jest już nullable")
        else:
            # Zmień kolumnę username na nullable
            print("🔄 Zmieniam kolumnę username na nullable...")
            cursor.execute("""
                ALTER TABLE users 
                ALTER COLUMN username DROP NOT NULL
            """)
            print("✅ Kolumna username jest teraz nullable")
        
        # Zaktualizuj istniejących użytkowników
        print("🔄 Aktualizuję istniejących użytkowników...")
        cursor.execute("""
            UPDATE users 
            SET is_temporary_password = FALSE 
            WHERE is_temporary_password IS NULL
        """)
        
        # Commit zmian
        conn.commit()
        print("✅ Migracja zakończona pomyślnie!")
        
        # Pokaż podsumowanie
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_temporary_password = TRUE")
        temp_password_users = cursor.fetchone()[0]
        
        print(f"📊 Podsumowanie:")
        print(f"   - Łącznie użytkowników: {users_count}")
        print(f"   - Z tymczasowym hasłem: {temp_password_users}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Błąd podczas migracji: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Uruchamiam migrację systemu użytkowników...")
    success = migrate_user_system()
    
    if success:
        print("🎉 Migracja zakończona pomyślnie!")
        exit(0)
    else:
        print("💥 Migracja nie powiodła się!")
        exit(1)
