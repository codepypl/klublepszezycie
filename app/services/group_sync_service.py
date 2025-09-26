"""
Group Sync Service - automatyczna synchronizacja grup w czasie rzeczywistym
"""
from sqlalchemy import event
from app.models import db, User, UserGroup, UserGroupMember
from app.services.group_manager import GroupManager
import threading

# Thread-local storage for tracking changes
_local = threading.local()

# Flag to disable automatic sync for API operations
_auto_sync_disabled = threading.local()

# Throttling mechanism - last sync time
import time
_last_sync_time = time.time()
SYNC_THROTTLE_SECONDS = 30  # Minimum 30 seconds between syncs

class GroupSyncService:
    """Serwis automatycznej synchronizacji grup"""
    
    @staticmethod
    def setup_event_listeners():
        """Konfiguruje event listeners dla automatycznej synchronizacji"""
        
        @event.listens_for(db.session, 'before_flush')
        def before_flush(session, flush_context, instances):
            """Zbieranie informacji o zmianach przed flush"""
            try:
                # Store changes in thread-local storage
                if not hasattr(_local, 'pending_changes'):
                    _local.pending_changes = {'new': [], 'modified': [], 'deleted': []}
                
                # Collect changes
                for obj in session.new:
                    if isinstance(obj, User):
                        _local.pending_changes['new'].append(obj)
                
                for obj in session.dirty:
                    if isinstance(obj, User):
                        _local.pending_changes['modified'].append(obj)
                
                for obj in session.deleted:
                    if isinstance(obj, User):
                        _local.pending_changes['deleted'].append(obj)
            except Exception as e:
                print(f"❌ Błąd w before_flush listener: {str(e)}")
        
        @event.listens_for(db.session, 'after_commit')
        def after_commit(session):
            """Automatyczna synchronizacja po commit"""
            try:
                # Check if automatic sync is disabled for this operation
                if hasattr(_auto_sync_disabled, 'disabled') and _auto_sync_disabled.disabled:
                    print("⏸️ Automatyczna synchronizacja wyłączona dla tej operacji")
                    return
                
                # Check throttling - don't sync too often
                current_time = time.time()
                global _last_sync_time
                if current_time - _last_sync_time < SYNC_THROTTLE_SECONDS:
                    print(f"⏸️ Synchronizacja throttled - ostatnia synchronizacja {int(current_time - _last_sync_time)}s temu")
                    return
                
                if hasattr(_local, 'pending_changes'):
                    changes = _local.pending_changes
                    
                    # Check if there are any changes to process
                    has_changes = any(changes.get(key, []) for key in ['new', 'modified', 'deleted'])
                    if not has_changes:
                        return
                    
                    # Update last sync time
                    _last_sync_time = current_time
                    
                    # Process new users
                    for user in changes['new']:
                        print(f"🔄 Automatyczna synchronizacja: nowy użytkownik {user.email}")
                        GroupSyncService._sync_after_user_change(user)
                    
                    # Process modified users
                    for user in changes['modified']:
                        print(f"🔄 Automatyczna synchronizacja: użytkownik zaktualizowany {user.email}")
                        GroupSyncService._sync_after_user_change(user)
                    
                    # Process deleted users
                    for user in changes['deleted']:
                        print(f"🔄 Automatyczna synchronizacja: użytkownik usunięty {user.email}")
                        GroupSyncService._sync_after_user_delete(user)
                    
                    # Clear pending changes
                    _local.pending_changes = {'new': [], 'modified': [], 'deleted': []}
            except Exception as e:
                print(f"❌ Błąd w after_commit listener: {str(e)}")
        
        print("✅ Event listeners dla automatycznej synchronizacji grup zostały skonfigurowane")
    
    @staticmethod
    def _sync_after_user_change(user):
        """Synchronizacja po zmianie użytkownika"""
        try:
            # Wyłącz automatyczną synchronizację podczas synchronizacji
            GroupSyncService.disable_auto_sync_for_operation()
            
            # Use a new session for synchronization
            from flask import current_app
            with current_app.app_context():
                group_manager = GroupManager()
                
                # Synchronizuj grupę członków klubu
                if user.club_member:
                    success, message = group_manager.sync_club_members_group()
                    if success:
                        print(f"✅ Zsynchronizowano grupę członków klubu: {message}")
                    else:
                        print(f"❌ Błąd synchronizacji grupy członków klubu: {message}")
                
                # Synchronizuj grupy wydarzeń
                success, message = group_manager.sync_event_groups()
                if success:
                    print(f"✅ Zsynchronizowano grupy wydarzeń: {message}")
                else:
                    print(f"❌ Błąd synchronizacji grup wydarzeń: {message}")
                    
        except Exception as e:
            print(f"❌ Błąd automatycznej synchronizacji grup: {str(e)}")
        finally:
            # Włącz automatyczną synchronizację z powrotem
            GroupSyncService.enable_auto_sync_for_operation()
    
    @staticmethod
    def _sync_after_user_delete(user):
        """Synchronizacja po usunięciu użytkownika"""
        try:
            # Wyłącz automatyczną synchronizację podczas synchronizacji
            GroupSyncService.disable_auto_sync_for_operation()
            
            # Use a new session for synchronization
            from flask import current_app
            with current_app.app_context():
                group_manager = GroupManager()
                
                # Synchronizuj grupę członków klubu
                success, message = group_manager.sync_club_members_group()
                if success:
                    print(f"✅ Zsynchronizowano grupę członków klubu po usunięciu: {message}")
                else:
                    print(f"❌ Błąd synchronizacji grupy członków klubu po usunięciu: {message}")
                
                # Synchronizuj grupy wydarzeń
                success, message = group_manager.sync_event_groups()
                if success:
                    print(f"✅ Zsynchronizowano grupy wydarzeń po usunięciu: {message}")
                else:
                    print(f"❌ Błąd synchronizacji grup wydarzeń po usunięciu: {message}")
                    
        except Exception as e:
            print(f"❌ Błąd automatycznej synchronizacji grup po usunięciu: {str(e)}")
        finally:
            # Włącz automatyczną synchronizację z powrotem
            GroupSyncService.enable_auto_sync_for_operation()
    
    @staticmethod
    def enable_auto_sync():
        """Włącza automatyczną synchronizację grup"""
        GroupSyncService.setup_event_listeners()
        print("🚀 Automatyczna synchronizacja grup została włączona")
    
    @staticmethod
    def disable_auto_sync():
        """Wyłącza automatyczną synchronizację grup"""
        # Usuń event listeners
        event.remove(db.session, 'before_flush')
        event.remove(db.session, 'after_commit')
        print("⏹️  Automatyczna synchronizacja grup została wyłączona")
    
    @staticmethod
    def disable_auto_sync_for_operation():
        """Wyłącza automatyczną synchronizację dla bieżącej operacji"""
        _auto_sync_disabled.disabled = True
        print("⏸️ Automatyczna synchronizacja wyłączona dla bieżącej operacji")
    
    @staticmethod
    def enable_auto_sync_for_operation():
        """Włącza automatyczną synchronizację dla bieżącej operacji"""
        _auto_sync_disabled.disabled = False
        print("▶️ Automatyczna synchronizacja włączona dla bieżącej operacji")
