#!/usr/bin/env python3
"""
Skrypt do wyczyszczenia kolejki emaili
Usuwa wszystkie emaile z kolejki oprócz wysłanych (zachowuje historię)
"""

import os
import sys
from datetime import datetime

# Dodaj ścieżkę do aplikacji
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db, EmailQueue

def clear_email_queue(force=False):
    """Wyczyszczenie kolejki emaili"""
    print(f"[{datetime.now()}] 🗑️  Rozpoczynanie czyszczenia kolejki emaili...")
    
    try:
        # Utwórz aplikację
        app = create_app()
        
        with app.app_context():
            # Policz emaile przed usunięciem
            total_before = EmailQueue.query.count()
            pending_before = EmailQueue.query.filter_by(status='pending').count()
            failed_before = EmailQueue.query.filter_by(status='failed').count()
            processing_before = EmailQueue.query.filter_by(status='processing').count()
            sent_before = EmailQueue.query.filter_by(status='sent').count()
            
            print(f"📊 Statystyki przed czyszczeniem:")
            print(f"   Łącznie: {total_before}")
            print(f"   Oczekujące (pending): {pending_before}")
            print(f"   Nieudane (failed): {failed_before}")
            print(f"   Przetwarzane (processing): {processing_before}")
            print(f"   Wysłane (sent): {sent_before}")
            
            if total_before == 0:
                print("✅ Kolejka emaili jest już pusta!")
                return
            
            # Potwierdzenie (tylko jeśli nie force)
            if not force:
                print(f"\n⚠️  UWAGA: Zostanie usunięte {pending_before + failed_before + processing_before} emaili")
                print(f"📋 Zostanie zachowane {sent_before} wysłanych emaili jako historia")
                
                confirm = input("\nCzy na pewno chcesz wyczyścić kolejkę? (tak/nie): ").lower().strip()
                
                if confirm not in ['tak', 't', 'yes', 'y']:
                    print("❌ Anulowano czyszczenie kolejki")
                    return
            else:
                print(f"\n⚡ FORCE MODE: Usuwanie {pending_before + failed_before + processing_before} emaili bez potwierdzenia")
                print(f"📋 Zostanie zachowane {sent_before} wysłanych emaili jako historia")
            
            # Usuń wszystkie emaile oprócz wysłanych
            deleted_count = EmailQueue.query.filter(
                EmailQueue.status.in_(['pending', 'failed', 'processing'])
            ).delete(synchronize_session=False)
            
            db.session.commit()
            
            print(f"\n✅ Sukces! Usunięto {deleted_count} emaili z kolejki")
            print(f"📋 Zachowano {sent_before} wysłanych emaili jako historia")
            
            # Sprawdź wynik
            remaining_count = EmailQueue.query.count()
            print(f"📊 Pozostało w kolejce: {remaining_count} emaili")
            
    except Exception as e:
        print(f"❌ Błąd podczas czyszczenia kolejki: {str(e)}")
        if 'db' in locals():
            db.session.rollback()
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Wyczyszczenie kolejki emaili')
    parser.add_argument('--force', action='store_true', 
                       help='Wymuś czyszczenie bez potwierdzenia')
    parser.add_argument('--dry-run', action='store_true',
                       help='Tylko pokaż co zostanie usunięte, nie usuwaj')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - tylko podgląd, nic nie zostanie usunięte")
        # Tylko pokaż statystyki
        app = create_app()
        with app.app_context():
            total_before = EmailQueue.query.count()
            pending_before = EmailQueue.query.filter_by(status='pending').count()
            failed_before = EmailQueue.query.filter_by(status='failed').count()
            processing_before = EmailQueue.query.filter_by(status='processing').count()
            sent_before = EmailQueue.query.filter_by(status='sent').count()
            
            print(f"📊 Statystyki kolejki emaili:")
            print(f"   Łącznie: {total_before}")
            print(f"   Oczekujące (pending): {pending_before}")
            print(f"   Nieudane (failed): {failed_before}")
            print(f"   Przetwarzane (processing): {processing_before}")
            print(f"   Wysłane (sent): {sent_before}")
            
            if total_before > 0:
                to_delete = pending_before + failed_before + processing_before
                print(f"\n🗑️  Zostałoby usunięte: {to_delete} emaili")
                print(f"📋 Zostałoby zachowane: {sent_before} wysłanych emaili")
            else:
                print("✅ Kolejka emaili jest pusta!")
    else:
        clear_email_queue(force=args.force)
