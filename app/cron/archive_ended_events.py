#!/usr/bin/env python3
"""
Skrypt do archiwizacji zakończonych wydarzeń
Uruchamiany przez Cron co 5 minut
"""
import os
import sys
from datetime import datetime

# Dodaj ścieżkę do aplikacji
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def archive_ended_events():
    """Archiwizuje zakończone wydarzenia i usuwa ich grupy"""
    try:
        from app import create_app, db
        from app.models import EventSchedule, UserGroup, UserGroupMember
        from app.utils.timezone_utils import get_local_now
        
        print(f"🏁 [{datetime.now()}] === ROZPOCZYNAM ARCHIWIZACJĘ WYDARZEŃ ===")
        
        # Utwórz kontekst aplikacji
        app = create_app()
        with app.app_context():
            # Find all active events
            all_events = EventSchedule.query.filter_by(
                is_active=True, 
                is_published=True, 
                is_archived=False
            ).all()
            
            print(f"📊 Znaleziono {len(all_events)} aktywnych wydarzeń do sprawdzenia")
            
            # Check which events are ended
            ended_events = []
            now = get_local_now().replace(tzinfo=None)
            
            for event in all_events:
                if event.is_ended():
                    ended_events.append(event)
                    print(f"⏰ Wydarzenie '{event.title}' (ID: {event.id}) jest zakończone")
                else:
                    print(f"🟢 Wydarzenie '{event.title}' (ID: {event.id}) jest jeszcze aktywne")
            
            if not ended_events:
                print("ℹ️ Brak wydarzeń do archiwizacji")
                return True
            
            # Archive each ended event
            archived_count = 0
            total_members_removed = 0
            total_groups_deleted = 0
            
            for event in ended_events:
                print(f"🏁 Archiwizuję: {event.title} (ID: {event.id})")
                
                # Find event groups - check all groups for this event
                event_groups = UserGroup.query.filter_by(
                    event_id=event.id,
                    group_type='event_based'
                ).all()
                
                print(f"  🔍 Znaleziono {len(event_groups)} grup dla wydarzenia {event.id}")
                
                # Debug: check all groups for this event (any type)
                all_groups_for_event = UserGroup.query.filter_by(event_id=event.id).all()
                print(f"  🔍 Wszystkich grup dla wydarzenia {event.id}: {len(all_groups_for_event)}")
                for group in all_groups_for_event:
                    print(f"    - Grupa: {group.name} (ID: {group.id}, type: {group.group_type})")
                
                # Remove members from groups
                for group in event_groups:
                    print(f"  📦 Przetwarzam grupę: {group.name} (ID: {group.id})")
                    
                    members_count = UserGroupMember.query.filter_by(
                        group_id=group.id,
                        is_active=True
                    ).count()
                    
                    print(f"    👥 Członków w grupie: {members_count}")
                    
                    if members_count > 0:
                        UserGroupMember.query.filter_by(
                            group_id=group.id,
                            is_active=True
                        ).delete(synchronize_session=False)
                        
                        total_members_removed += members_count
                        print(f"    ✅ Usunięto {members_count} członków z grupy '{group.name}'")
                    else:
                        print(f"    ℹ️ Grupa '{group.name}' nie ma członków")
                
                # Delete groups
                for group in event_groups:
                    print(f"  🗑️ Usuwam grupę: {group.name} (ID: {group.id})")
                    db.session.delete(group)
                    total_groups_deleted += 1
                    print(f"    ✅ Grupa '{group.name}' usunięta")
                
                # Archive event - set flags as requested
                event.is_published = False
                event.is_active = False
                event.is_archived = True
                archived_count += 1
                
                print(f"  📦 Wydarzenie zarchiwizowane (published=False, active=False, archived=True)")
            
            # Commit all changes
            db.session.commit()
            
            message = f"Zarchiwizowano {archived_count} wydarzeń. Usunięto {total_members_removed} członków z {total_groups_deleted} grup."
            print(f"✅ [{datetime.now()}] {message}")
            
            return True
            
    except Exception as e:
        error_msg = f"Błąd archiwizacji: {str(e)}"
        print(f"❌ [{datetime.now()}] {error_msg}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = archive_ended_events()
    sys.exit(0 if success else 1)
