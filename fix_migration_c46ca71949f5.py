#!/usr/bin/env python3
"""
Naprawiona wersja migracji c46ca71949f5
Bezpiecznie obsługuje tokeny dłuższe niż 36 znaków
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app import create_app, db
from sqlalchemy import text

def fix_migration():
    """Naprawia migrację c46ca71949f5"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Naprawianie migracji c46ca71949f5...")
            
            # 1. Sprawdź czy tabela password_reset_tokens istnieje
            result = db.session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'password_reset_tokens'
                )
            """)).scalar()
            
            if not result:
                print("✅ Tabela password_reset_tokens nie istnieje - pomijam")
                return True
            
            # 2. Sprawdź aktualną długość kolumny token
            column_info = db.session.execute(text("""
                SELECT character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'password_reset_tokens' 
                AND column_name = 'token'
            """)).scalar()
            
            print(f"📊 Aktualna długość kolumny token: {column_info}")
            
            # 3. Sprawdź czy są tokeny dłuższe niż 36 znaków
            long_tokens_count = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM password_reset_tokens 
                WHERE LENGTH(token) > 36
            """)).scalar()
            
            print(f"📊 Tokeny dłuższe niż 36 znaków: {long_tokens_count}")
            
            if long_tokens_count > 0:
                print("⚠️  Znaleziono tokeny dłuższe niż 36 znaków")
                
                # Opcja 1: Skróć tokeny do 36 znaków
                print("🔧 Skracanie tokenów do 36 znaków...")
                db.session.execute(text("""
                    UPDATE password_reset_tokens 
                    SET token = LEFT(token, 36)
                    WHERE LENGTH(token) > 36
                """))
                db.session.commit()
                print("✅ Tokeny zostały skrócone")
            
            # 4. Teraz bezpiecznie zmień typ kolumny
            if column_info != 36:
                print("🔧 Zmienianie typu kolumny token na VARCHAR(36)...")
                
                # Usuń istniejące indeksy i ograniczenia
                try:
                    db.session.execute(text("DROP INDEX IF EXISTS ix_password_reset_tokens_token"))
                    db.session.execute(text("ALTER TABLE password_reset_tokens DROP CONSTRAINT IF EXISTS password_reset_tokens_token_key"))
                except Exception as e:
                    print(f"⚠️  Ostrzeżenie przy usuwaniu indeksów: {e}")
                
                # Zmień typ kolumny
                db.session.execute(text("""
                    ALTER TABLE password_reset_tokens 
                    ALTER COLUMN token TYPE VARCHAR(36)
                """))
                
                # Utwórz nowy indeks
                db.session.execute(text("""
                    CREATE UNIQUE INDEX ix_password_reset_tokens_token 
                    ON password_reset_tokens (token)
                """))
                
                db.session.commit()
                print("✅ Kolumna token została zmieniona na VARCHAR(36)")
            else:
                print("✅ Kolumna token już ma długość 36 znaków")
            
            # 5. Sprawdź końcowy stan
            final_length = db.session.execute(text("""
                SELECT character_maximum_length 
                FROM information_schema.columns 
                WHERE table_name = 'password_reset_tokens' 
                AND column_name = 'token'
            """)).scalar()
            
            print(f"✅ Końcowa długość kolumny token: {final_length}")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("🔧 Naprawianie migracji c46ca71949f5")
    print("=" * 50)
    
    success = fix_migration()
    
    if success:
        print("\n✅ Migracja naprawiona pomyślnie")
        print("Możesz teraz uruchomić: flask db upgrade")
    else:
        print("\n❌ Błąd podczas naprawiania migracji")
        sys.exit(1)
