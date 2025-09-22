#!/usr/bin/env python3
"""
Skrypt do utworzenia tabeli śledzenia wysłanych przypomnień
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, EmailReminderSent

def main():
    """Utwórz tabelę EmailReminderSent"""
    print(f"[{datetime.now()}] 🔧 Tworzenie tabeli śledzenia wysłanych przypomnień...")
    
    try:
        app = create_app()
        with app.app_context():
            # Utwórz tabelę
            db.create_all()
            
            # Sprawdź czy tabela została utworzona
            result = db.engine.execute("SELECT COUNT(*) FROM email_reminders_sent")
            count = result.fetchone()[0]
            
            print(f"✅ Tabela 'email_reminders_sent' została utworzona")
            print(f"📊 Liczba rekordów w tabeli: {count}")
            
            # Sprawdź strukturę tabeli
            result = db.engine.execute("PRAGMA table_info(email_reminders_sent)")
            columns = result.fetchall()
            
            print(f"\n📋 Struktura tabeli:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"❌ Błąd: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
