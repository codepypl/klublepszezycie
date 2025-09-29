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
            # Find all active events that are published and not archived
            all_events = EventSchedule.query.filter(
                EventSchedule.is_active == True,
                EventSchedule.is_published == True,
                EventSchedule.is_archived == False
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
                
                # Check for orphaned groups from already archived events
                print("🔍 Sprawdzam osierocone grupy z zarchiwizowanych wydarzeń...")
                cleanup_orphaned_groups()
                return True
            
            # Archive each ended event
            archived_count = 0
            total_members_removed = 0
            total_groups_deleted = 0
            
            for event in ended_events:
                print(f"🏁 Archiwizuję: {event.title} (ID: {event.id})")
                
                # Find event groups by criteria JSON field
                import json
                event_groups = []
                
                # Search by event_id in criteria field
                all_event_groups = UserGroup.query.filter_by(group_type='event_based').all()
                for group in all_event_groups:
                    if group.criteria:
                        try:
                            criteria = json.loads(group.criteria)
                            if criteria.get('event_id') == event.id:
                                event_groups.append(group)
                        except json.JSONDecodeError:
                            pass
                
                print(f"  🔍 Znaleziono {len(event_groups)} grup dla wydarzenia {event.id} w criteria")
                
                # Also check by event_id field if it exists
                event_groups_by_id = UserGroup.query.filter_by(
                    event_id=event.id,
                    group_type='event_based'
                ).all()
                
                # Add groups found by event_id field (avoid duplicates)
                for group in event_groups_by_id:
                    if group not in event_groups:
                        event_groups.append(group)
                
                print(f"  🔍 Łącznie {len(event_groups)} grup dla wydarzenia {event.id}")
                
                # Debug: show all groups
                for group in event_groups:
                    print(f"    - Grupa: {group.name} (ID: {group.id}, event_id: {group.event_id}, criteria: {group.criteria})")
                
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

def cleanup_orphaned_groups():
    """Czyści osierocone grupy z zarchiwizowanych wydarzeń"""
    try:
        from app import create_app, db
        from app.models import EventSchedule, UserGroup, UserGroupMember
        import json
        
        print(f"🧹 [{datetime.now()}] === CZYSZCZENIE OSIEROCONYCH GRUP ===")
        
        # Utwórz kontekst aplikacji
        app = create_app()
        with app.app_context():
            # Find all archived events
            archived_events = EventSchedule.query.filter_by(is_archived=True).all()
            archived_event_ids = [event.id for event in archived_events]
            
            print(f"🔍 Znaleziono {len(archived_event_ids)} zarchiwizowanych wydarzeń")
            
            # Find groups for archived events
            orphaned_groups = []
            
            # Search by criteria field
            all_event_groups = UserGroup.query.filter_by(group_type='event_based').all()
            for group in all_event_groups:
                if group.criteria:
                    try:
                        criteria = json.loads(group.criteria)
                        event_id = criteria.get('event_id')
                        if event_id in archived_event_ids:
                            orphaned_groups.append(group)
                    except json.JSONDecodeError:
                        pass
            
            # Search by event_id field
            for event_id in archived_event_ids:
                groups_by_id = UserGroup.query.filter_by(
                    event_id=event_id,
                    group_type='event_based'
                ).all()
                for group in groups_by_id:
                    if group not in orphaned_groups:
                        orphaned_groups.append(group)
            
            print(f"🔍 Znaleziono {len(orphaned_groups)} osieroconych grup")
            
            # Clean up orphaned groups
            total_members_removed = 0
            total_groups_deleted = 0
            
            for group in orphaned_groups:
                print(f"🗑️ Czyszczę osieroconą grupę: {group.name} (ID: {group.id})")
                
                # Remove members
                members_count = UserGroupMember.query.filter_by(
                    group_id=group.id,
                    is_active=True
                ).count()
                
                if members_count > 0:
                    UserGroupMember.query.filter_by(
                        group_id=group.id,
                        is_active=True
                    ).delete(synchronize_session=False)
                    total_members_removed += members_count
                    print(f"  👥 Usunięto {members_count} członków")
                
                # Delete group
                db.session.delete(group)
                total_groups_deleted += 1
                print(f"  ✅ Grupa usunięta")
            
            if total_groups_deleted > 0:
                db.session.commit()
                print(f"✅ Usunięto {total_groups_deleted} osieroconych grup i {total_members_removed} członków")
            else:
                print("ℹ️ Brak osieroconych grup do usunięcia")
                
            return True
                
    except Exception as e:
        print(f"❌ Błąd czyszczenia osieroconych grup: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = archive_ended_events()
    sys.exit(0 if success else 1)
