#!/usr/bin/env python3
"""
Skrypt do naprawy grup wydarzeń - ustawia event_id dla grup które go nie mają
"""
import os
import sys
from datetime import datetime

# Dodaj ścieżkę do aplikacji
sys.path.append(os.path.dirname(__file__))

def fix_event_groups():
    """Naprawia grupy wydarzeń - ustawia event_id"""
    try:
        from app import create_app, db
        from app.models import UserGroup, EventSchedule
        
        print(f"🔧 [{datetime.now()}] === NAPRAWIAM GRUPY WYDARZEŃ ===")
        
        # Utwórz kontekst aplikacji
        app = create_app()
        with app.app_context():
            # Znajdź wszystkie grupy event_based bez event_id
            groups_without_event_id = UserGroup.query.filter_by(
                group_type='event_based',
                event_id=None
            ).all()
            
            print(f"📊 Znaleziono {len(groups_without_event_id)} grup bez event_id")
            
            fixed_count = 0
            
            for group in groups_without_event_id:
                print(f"🔍 Sprawdzam grupę: {group.name}")
                
                # Spróbuj znaleźć wydarzenie po nazwie grupy
                # Format: "Wydarzenie: {event_title}"
                if group.name.startswith("Wydarzenie: "):
                    event_title = group.name.replace("Wydarzenie: ", "")
                    
                    # Znajdź wydarzenie po tytule
                    event = EventSchedule.query.filter_by(title=event_title).first()
                    
                    if event:
                        group.event_id = event.id
                        fixed_count += 1
                        print(f"  ✅ Ustawiono event_id={event.id} dla grupy '{group.name}'")
                    else:
                        print(f"  ❌ Nie znaleziono wydarzenia dla grupy '{group.name}'")
                else:
                    print(f"  ⚠️ Grupa '{group.name}' nie ma standardowej nazwy")
            
            # Commit changes
            db.session.commit()
            
            print(f"✅ [{datetime.now()}] Naprawiono {fixed_count} grup")
            
            return True
            
    except Exception as e:
        error_msg = f"Błąd naprawy grup: {str(e)}"
        print(f"❌ [{datetime.now()}] {error_msg}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_event_groups()
    sys.exit(0 if success else 1)
