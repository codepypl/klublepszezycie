#!/usr/bin/env python3
"""
Skrypt migracji - dodanie statusu 'archiwalne' do wydarzeń
"""
import os
import sys
from datetime import datetime

# Dodaj ścieżkę do aplikacji
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, EventSchedule

def main():
    """Główna funkcja migracji"""
    print(f"[{datetime.now()}] Rozpoczynanie migracji - dodanie statusu 'archiwalne'...")
    
    try:
        # Utwórz aplikację
        app = create_app()
        
        with app.app_context():
            # Dodaj kolumnę is_archived
            print("Dodawanie kolumny is_archived...")
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE event_schedule ADD COLUMN is_archived BOOLEAN DEFAULT FALSE"))
                conn.commit()
            print("✅ Kolumna is_archived dodana")
            
            # Zarchiwizuj wydarzenia, które się już zakończyły
            print("Archiwizowanie zakończonych wydarzeń...")
            events = EventSchedule.query.filter_by(is_archived=False).all()
            archived_count = 0
            
            for event in events:
                if event.is_ended():
                    event.archive()
                    archived_count += 1
                    print(f"  - Zarchiwizowano: {event.title} ({event.event_date})")
            
            # Zapisz zmiany
            db.session.commit()
            print(f"✅ Zarchiwizowano {archived_count} wydarzeń")
            
            print(f"[{datetime.now()}] ✅ Migracja zakończona pomyślnie")
            
    except Exception as e:
        print(f"[{datetime.now()}] ❌ Błąd migracji: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
