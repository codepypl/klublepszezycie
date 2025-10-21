#!/usr/bin/env python3
"""
Skrypt do naprawy długości tokenów w password_reset_tokens
Przygotowuje dane przed migracją
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app import create_app, db
from sqlalchemy import text

def fix_token_length():
    """Naprawia długość tokenów w password_reset_tokens"""
    app = create_app()
    
    with app.app_context():
        try:
            # Sprawdź aktualną długość tokenów
            result = db.session.execute(text("""
                SELECT 
                    LENGTH(token) as token_length,
                    COUNT(*) as count
                FROM password_reset_tokens 
                GROUP BY LENGTH(token)
                ORDER BY token_length
            """)).fetchall()
            
            print("Aktualne długości tokenów:")
            for row in result:
                print(f"  {row.token_length} znaków: {row.count} tokenów")
            
            # Sprawdź czy są tokeny dłuższe niż 36 znaków
            long_tokens = db.session.execute(text("""
                SELECT id, token, LENGTH(token) as token_length
                FROM password_reset_tokens 
                WHERE LENGTH(token) > 36
                LIMIT 10
            """)).fetchall()
            
            if long_tokens:
                print(f"\nZnaleziono {len(long_tokens)} tokenów dłuższych niż 36 znaków:")
                for row in long_tokens:
                    print(f"  ID: {row.id}, Długość: {row.token_length}, Token: {row.token[:50]}...")
                
                # Opcja 1: Skróć tokeny do 36 znaków (zachowaj pierwsze 36)
                print("\nOpcja 1: Skracanie tokenów do 36 znaków...")
                response = input("Czy chcesz skrócić tokeny? (y/N): ")
                
                if response.lower() == 'y':
                    db.session.execute(text("""
                        UPDATE password_reset_tokens 
                        SET token = LEFT(token, 36)
                        WHERE LENGTH(token) > 36
                    """))
                    db.session.commit()
                    print("✅ Tokeny zostały skrócone do 36 znaków")
                else:
                    print("❌ Anulowano skracanie tokenów")
                    
                    # Opcja 2: Usuń tokeny dłuższe niż 36 znaków
                    print("\nOpcja 2: Usuwanie tokenów dłuższych niż 36 znaków...")
                    response2 = input("Czy chcesz usunąć te tokeny? (y/N): ")
                    
                    if response2.lower() == 'y':
                        deleted = db.session.execute(text("""
                            DELETE FROM password_reset_tokens 
                            WHERE LENGTH(token) > 36
                        """))
                        db.session.commit()
                        print(f"✅ Usunięto {deleted.rowcount} tokenów")
                    else:
                        print("❌ Anulowano usuwanie tokenów")
                        print("⚠️  Migracja nie będzie działać z tokenami dłuższymi niż 36 znaków")
                        return False
            else:
                print("✅ Wszystkie tokeny mają długość <= 36 znaków")
            
            # Sprawdź końcowy stan
            result_after = db.session.execute(text("""
                SELECT 
                    LENGTH(token) as token_length,
                    COUNT(*) as count
                FROM password_reset_tokens 
                GROUP BY LENGTH(token)
                ORDER BY token_length
            """)).fetchall()
            
            print("\nStan po naprawie:")
            for row in result_after:
                print(f"  {row.token_length} znaków: {row.count} tokenów")
            
            return True
            
        except Exception as e:
            print(f"❌ Błąd: {e}")
            return False

if __name__ == "__main__":
    print("🔧 Skrypt naprawy długości tokenów w password_reset_tokens")
    print("=" * 60)
    
    success = fix_token_length()
    
    if success:
        print("\n✅ Skrypt zakończony pomyślnie")
        print("Możesz teraz uruchomić: flask db upgrade")
    else:
        print("\n❌ Skrypt zakończony z błędami")
        sys.exit(1)
