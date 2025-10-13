"""
Group Manager - zarządzanie grupami użytkowników
"""
import json
from datetime import datetime
from app.models import db, UserGroup, UserGroupMember, User, EventSchedule
from app.utils.timezone_utils import get_local_now

class GroupManager:
    """Menedżer grup użytkowników"""
    
    def create_event_group(self, event_id, event_title):
        """Tworzy grupę dla wydarzenia"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Sprawdź czy grupa już istnieje dla tego event_id
            existing_group = UserGroup.query.filter_by(
                event_id=event_id,
                group_type='event_based'
            ).first()
            
            if existing_group:
                logger.info(f"✅ Grupa już istnieje dla wydarzenia {event_id}: {existing_group.name}")
                return existing_group.id
            
            # Podwójne sprawdzenie - czy nie ma grupy o tej samej nazwie
            group_name = f"Wydarzenie: {event_title}"
            existing_by_name = UserGroup.query.filter_by(
                name=group_name,
                group_type='event_based'
            ).first()
            
            if existing_by_name:
                logger.warning(f"⚠️ Znaleziono duplikat grupy o nazwie '{group_name}' dla wydarzenia {event_id}")
                # Zaktualizuj event_id w istniejącej grupie
                existing_by_name.event_id = event_id
                existing_by_name.criteria = json.dumps({'event_id': event_id})
                db.session.commit()
                logger.info(f"✅ Zaktualizowano event_id dla istniejącej grupy {existing_by_name.id}")
                return existing_by_name.id
            
            # Utwórz nową grupę
            group = UserGroup(
                name=f"Wydarzenie: {event_title}",
                description=f"Grupa uczestników wydarzenia: {event_title}",
                group_type='event_based',
                event_id=event_id,
                criteria=json.dumps({'event_id': event_id})
            )
            
            db.session.add(group)
            db.session.commit()
            
            logger.info(f"✅ Utworzono grupę {group.id} dla wydarzenia {event_id}: {event_title}")
            return group.id
            
        except Exception as e:
            logger.error(f"❌ Błąd tworzenia grupy wydarzenia {event_id}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def add_user_to_event_group(self, user_id, event_id):
        """Dodaje użytkownika do grupy wydarzenia"""
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, "Wydarzenie nie zostało znalezione"
            
            # Znajdź lub utwórz grupę
            group_id = self.create_event_group(event_id, event.title)
            if not group_id:
                return False, "Błąd tworzenia grupy"
            
            # Pobierz użytkownika
            user = User.query.get(user_id)
            if not user:
                return False, "Użytkownik nie został znaleziony"
            
            # Sprawdź czy już jest w grupie
            existing_member = UserGroupMember.query.filter_by(
                group_id=group_id,
                user_id=user_id
            ).first()
            
            if existing_member:
                return True, "Użytkownik już jest w grupie"
            
            # Dodaj do grupy
            member = UserGroupMember(
                group_id=group_id,
                user_id=user_id,
                email=user.email,
                name=user.first_name
            )
            
            db.session.add(member)
            
            # Aktualizuj liczbę członków
            group = UserGroup.query.get(group_id)
            group.member_count = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).count()
            
            db.session.commit()
            
            return True, "Użytkownik dodany do grupy"
            
        except Exception as e:
            return False, f"Błąd dodawania do grupy: {str(e)}"
    
    def add_user_to_all_users(self, user_id):
        """Dodaje użytkownika do grupy członków klubu (zastąpienie grupy wszystkich użytkowników)"""
        try:
            # Użyj grupy członków klubu zamiast grupy wszystkich użytkowników
            return self.add_user_to_club_members(user_id)
            
        except Exception as e:
            return False, f"Błąd dodawania do grupy członków klubu: {str(e)}"
    
    def add_user_to_club_members(self, user_id):
        """Dodaje użytkownika do grupy członków klubu"""
        try:
            # Znajdź grupę członków klubu (ID 19)
            group = UserGroup.query.get(19)
            
            # Fallback: jeśli grupa o ID 19 nie istnieje, szukaj po nazwie
            if not group:
                group = UserGroup.query.filter_by(
                    name="Członkowie klubu",
                    group_type='club_members'
                ).first()
            
            if not group:
                group = UserGroup(
                    name="Członkowie klubu",
                    description="Grupa członków klubu Lepsze Życie",
                    group_type='club_members'
                )
                db.session.add(group)
                db.session.commit()
            
            # Pobierz użytkownika
            user = User.query.get(user_id)
            if not user:
                return False, "Użytkownik nie został znaleziony"
            
            # Sprawdź czy już jest w grupie
            existing_member = UserGroupMember.query.filter_by(
                group_id=group.id,
                user_id=user_id
            ).first()
            
            if existing_member:
                return True, "Użytkownik już jest w grupie"
            
            # Dodaj do grupy
            member = UserGroupMember(
                group_id=group.id,
                user_id=user_id,
                email=user.email,
                name=user.first_name,
                member_type='user',
                is_active=True
            )
            
            db.session.add(member)
            
            # Aktualizuj liczbę członków
            group.member_count = UserGroupMember.query.filter_by(group_id=group.id, is_active=True).count()
            
            db.session.commit()
            
            return True, "Użytkownik dodany do grupy członków"
            
        except Exception as e:
            return False, f"Błąd dodawania do grupy członków: {str(e)}"
    
    def create_manual_group(self, name, description, user_ids):
        """Tworzy ręczną grupę użytkowników"""
        try:
            # Utwórz grupę
            group = UserGroup(
                name=name,
                description=description,
                group_type='manual'
            )
            
            db.session.add(group)
            db.session.commit()
            
            # Dodaj użytkowników
            added = 0
            for user_id in user_ids:
                user = User.query.get(user_id)
                if user:
                    member = UserGroupMember(
                        group_id=group.id,
                        user_id=user_id,
                        email=user.email,
                        name=user.first_name
                    )
                    db.session.add(member)
                    added += 1
            
            # Aktualizuj liczbę członków
            group.member_count = added
            
            db.session.commit()
            
            return True, f"Grupa utworzona z {added} użytkownikami"
            
        except Exception as e:
            return False, f"Błąd tworzenia grupy: {str(e)}"
    
    def cleanup_orphaned_groups(self):
        """Czyści nieużywane grupy wydarzeń (gdy wydarzenia nie istnieją)"""
        try:
            # Znajdź wszystkie grupy wydarzeń
            event_groups = UserGroup.query.filter_by(group_type='event_based').all()
            orphaned_groups = []
            
            print(f"🔍 Sprawdzam {len(event_groups)} grup wydarzeń pod kątem osieroconych grup...")
            
            for group in event_groups:
                is_orphaned = False
                orphan_reason = ""
                
                # Sprawdź 1: Czy grupa ma event_id w kolumnie event_id
                if group.event_id:
                    event = EventSchedule.query.get(group.event_id)
                    if not event:
                        is_orphaned = True
                        orphan_reason = f"event_id={group.event_id} nie istnieje"
                        print(f"  🚨 Grupa '{group.name}' (ID: {group.id}) - wydarzenie {group.event_id} nie istnieje")
                    elif not event.is_active:
                        is_orphaned = True
                        orphan_reason = f"event_id={group.event_id} jest nieaktywne"
                        print(f"  🚨 Grupa '{group.name}' (ID: {group.id}) - wydarzenie {group.event_id} jest nieaktywne")
                    else:
                        print(f"  ✅ Grupa '{group.name}' (ID: {group.id}) - wydarzenie {group.event_id} istnieje i jest aktywne")
                
                # Sprawdź 2: Czy criteria zawiera event_id (jeśli nie ma event_id w kolumnie)
                if not is_orphaned and group.criteria:
                    try:
                        criteria = json.loads(group.criteria)
                        event_id = criteria.get('event_id')
                        
                        if event_id:
                            event = EventSchedule.query.get(event_id)
                            if not event:
                                is_orphaned = True
                                orphan_reason = f"criteria.event_id={event_id} nie istnieje"
                                print(f"  🚨 Grupa '{group.name}' (ID: {group.id}) - wydarzenie {event_id} z criteria nie istnieje")
                            elif not event.is_active:
                                is_orphaned = True
                                orphan_reason = f"criteria.event_id={event_id} jest nieaktywne"
                                print(f"  🚨 Grupa '{group.name}' (ID: {group.id}) - wydarzenie {event_id} z criteria jest nieaktywne")
                            else:
                                print(f"  ✅ Grupa '{group.name}' (ID: {group.id}) - wydarzenie {event_id} z criteria istnieje i jest aktywne")
                    except (json.JSONDecodeError, TypeError):
                        # Jeśli criteria jest nieprawidłowe, usuń grupę
                        is_orphaned = True
                        orphan_reason = "nieprawidłowe criteria JSON"
                        print(f"  🚨 Grupa '{group.name}' (ID: {group.id}) - nieprawidłowe criteria JSON")
                
                if is_orphaned:
                    orphaned_groups.append((group, orphan_reason))
            
            print(f"🔍 Znaleziono {len(orphaned_groups)} osieroconych grup")
            
            # Usuń nieużywane grupy
            deleted_count = 0
            total_members_removed = 0
            
            for group, reason in orphaned_groups:
                print(f"🗑️ Usuwam osieroconą grupę: {group.name} (ID: {group.id}) - {reason}")
                
                # Policz członków przed usunięciem
                members_count = UserGroupMember.query.filter_by(
                    group_id=group.id,
                    is_active=True
                ).count()
                
                if members_count > 0:
                    # Usuń wszystkich członków
                    UserGroupMember.query.filter_by(group_id=group.id).delete()
                    total_members_removed += members_count
                    print(f"  👥 Usunięto {members_count} członków z grupy")
                
                # Usuń grupę
                db.session.delete(group)
                deleted_count += 1
                print(f"  ✅ Grupa usunięta")
            
            if deleted_count > 0:
                db.session.commit()
                return True, f"Usunięto {deleted_count} osieroconych grup i {total_members_removed} członków"
            else:
                return True, "Brak osieroconych grup do usunięcia"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Błąd czyszczenia grup: {str(e)}"
    
    def cleanup_event_groups(self, event_id):
        """Usuwa wszystkich członków z grup wydarzenia"""
        try:
            # Find all groups related to this event
            event_groups = UserGroup.query.filter_by(
                group_type='event_based'
            ).all()
            
            cleaned_groups = []
            
            for group in event_groups:
                try:
                    # Check if this group is related to the event
                    criteria = json.loads(group.criteria) if group.criteria else {}
                    group_event_id = criteria.get('event_id')
                    
                    if group_event_id == event_id:
                        # Remove all members from this group
                        UserGroupMember.query.filter_by(group_id=group.id).delete()
                        cleaned_groups.append(group.name)
                        print(f"🧹 Wyczyściono grupę: {group.name}")
                        
                except (json.JSONDecodeError, TypeError):
                    continue
            
            if cleaned_groups:
                db.session.commit()
                return True, f"Wyczyściono {len(cleaned_groups)} grup"
            else:
                return True, "Brak grup do wyczyszczenia"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Błąd czyszczenia grup wydarzenia: {str(e)}"
    
    def delete_event_groups(self, event_id):
        """Usuwa grupy wydarzenia z systemu"""
        try:
            # Find all groups related to this event
            event_groups = UserGroup.query.filter_by(
                group_type='event_based'
            ).all()
            
            deleted_groups = []
            
            for group in event_groups:
                try:
                    # Check if this group is related to the event
                    criteria = json.loads(group.criteria) if group.criteria else {}
                    group_event_id = criteria.get('event_id')
                    
                    if group_event_id == event_id:
                        # Delete the group
                        db.session.delete(group)
                        deleted_groups.append(group.name)
                        print(f"🗑️ Usunięto grupę: {group.name}")
                        
                except (json.JSONDecodeError, TypeError):
                    # If criteria is invalid, delete the group
                    db.session.delete(group)
                    deleted_groups.append(group.name)
                    print(f"🗑️ Usunięto grupę z nieprawidłowymi kryteriami: {group.name}")
            
            if deleted_groups:
                db.session.commit()
                return True, f"Usunięto {len(deleted_groups)} grup"
            else:
                return True, "Brak grup do usunięcia"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Błąd usuwania grup wydarzenia: {str(e)}"
    
    def sync_club_members_group(self):
        """Synchronizuje grupę 'Członkowie klubu' z aktywnymi członkami klubu"""
        try:
            # Znajdź lub utwórz grupę
            group = UserGroup.query.filter_by(
                name="Członkowie klubu",
                group_type='club_members'
            ).first()
            
            if not group:
                group = UserGroup(
                    name="Członkowie klubu",
                    description="Grupa członków klubu Lepsze Życie",
                    group_type='club_members'
                )
                db.session.add(group)
                db.session.commit()
            
            # Pobierz wszystkich członków klubu (club_member=True)
            club_members = User.query.filter_by(club_member=True, is_active=True).all()
            
            # Pobierz obecnych członków grupy (tylko aktywnych)
            current_members = UserGroupMember.query.filter_by(group_id=group.id, is_active=True).all()
            current_user_ids = {member.user_id for member in current_members}
            
            # Dodaj nowych członków klubu (którzy nie są jeszcze w grupie)
            new_members = []
            for user in club_members:
                if user.id not in current_user_ids:
                    member = UserGroupMember(
                        group_id=group.id,
                        user_id=user.id,
                        email=user.email,
                        name=user.first_name
                    )
                    db.session.add(member)
                    new_members.append(member)
            
            # Usuń użytkowników, którzy nie są już członkami klubu
            club_member_ids = {user.id for user in club_members}
            members_to_remove = [member for member in current_members 
                               if member.user_id not in club_member_ids]
            
            for member in members_to_remove:
                db.session.delete(member)
            
            # Aktualizuj liczbę członków
            group.member_count = len(club_members)
            
            db.session.commit()
            
            return True, f"Zsynchronizowano grupę 'Członkowie klubu' z {len(club_members)} członkami"
            
        except Exception as e:
            return False, f"Błąd synchronizacji grupy członków klubu: {str(e)}"
    
    def sync_event_groups(self):
        """Synchronizuje grupy wydarzeń z rejestracjami"""
        try:
            from app.models import EventSchedule, User
            
            # Pobierz wszystkie aktywne wydarzenia
            events = EventSchedule.query.filter_by(is_active=True).all()
            synced_groups = 0
            
            for event in events:
                group_name = f"Wydarzenie: {event.title}"
                
                # Znajdź lub utwórz grupę wydarzenia
                group = UserGroup.query.filter_by(
                    name=group_name,
                    group_type='event_based'
                ).first()
                
                if not group:
                    # Utwórz nową grupę
                    group = UserGroup(
                        name=group_name,
                        description=f"Grupa uczestników wydarzenia: {event.title}",
                        group_type='event_based',
                        criteria=json.dumps({'event_id': event.id})
                    )
                    db.session.add(group)
                    db.session.commit()
                    print(f"✅ Utworzono nową grupę: {group_name}")
                
                # Pobierz wszystkich zarejestrowanych na wydarzenie
                # Użyj tabeli event_registrations
                from app.models import EventRegistration
                registrations = EventRegistration.query.filter_by(
                    event_id=event.id,
                    is_active=True
                ).all()
                
                # Pobierz użytkowników z rejestracji
                user_ids = [reg.user_id for reg in registrations]
                registrations = User.query.filter(User.id.in_(user_ids)).all()
                
                # Pobierz obecnych członków grupy (tylko aktywnych)
                current_members = UserGroupMember.query.filter_by(group_id=group.id, is_active=True).all()
                current_emails = {member.email for member in current_members if member.email}
                
                # Pobierz unikalne emaile z rejestracji (usuń duplikaty)
                unique_registrations = {}
                for registration in registrations:
                    if registration.email:
                        # Użyj najnowszej rejestracji dla każdego emaila
                        if registration.email not in unique_registrations or registration.created_at > unique_registrations[registration.email].created_at:
                            unique_registrations[registration.email] = registration
                
                print(f"🔍 Grupa {group_name}: {len(registrations)} rejestracji, {len(unique_registrations)} unikalnych emaili")
                
                # Dodaj nowych członków
                new_members = []
                for email, registration in unique_registrations.items():
                    if email not in current_emails:
                        # Sprawdź czy użytkownik ma konto
                        user = User.query.filter_by(email=email).first()
                        
                        member = UserGroupMember(
                            group_id=group.id,
                            user_id=user.id if user else None,
                            email=email,
                            name=registration.first_name,
                            is_active=True
                        )
                        db.session.add(member)
                        new_members.append(member)
                        print(f"✅ Dodano {email} do grupy {group_name}")
                    else:
                        print(f"ℹ️ {email} już jest w grupie {group_name}")
                
                # Usuń członków, którzy nie są już zarejestrowani lub których konta zostały usunięte
                unique_emails = set(unique_registrations.keys())
                members_to_remove = []
                for member in current_members:
                    should_remove = False
                    reason = ""
                    
                    # Check if user account was deleted
                    if member.user_id:
                        user_exists = User.query.get(member.user_id)
                        if not user_exists:
                            should_remove = True
                            reason = "konto użytkownika zostało usunięte"
                    
                    # Check if user is no longer registered for this event
                    if member.email and member.email not in unique_emails:
                        should_remove = True
                        reason = "nie jest już zarejestrowany na wydarzenie"
                    
                    if should_remove:
                        member.is_active = False
                        members_to_remove.append(member)
                        print(f"✅ Usunięto {member.email or member.first_name} z grupy {group_name} ({reason})")
                
                # Aktualizuj liczbę członków
                group.member_count = UserGroupMember.query.filter_by(group_id=group.id, is_active=True).count()
                synced_groups += 1
            
            db.session.commit()
            return True, f"Zsynchronizowano {synced_groups} grup wydarzeń"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Błąd synchronizacji grup wydarzeń: {str(e)}"
    
    def sync_system_groups(self):
        """Synchronizuje grupy systemowe"""
        try:
            # Synchronizuj grupę członków klubu
            success1, message1 = self.sync_club_members_group()
            
            # Synchronizuj grupy wydarzeń
            success2, message2 = self.sync_event_groups()
            
            if success1 and success2:
                return True, f"{message1}. {message2}"
            elif success1:
                return True, f"{message1}. Błąd synchronizacji grup wydarzeń: {message2}"
            elif success2:
                return True, f"Błąd synchronizacji grupy członków: {message1}. {message2}"
            else:
                return False, f"Błąd synchronizacji: {message1}. {message2}"
            
        except Exception as e:
            return False, f"Błąd synchronizacji grup systemowych: {str(e)}"
    
    def async_sync_event_group(self, event_id):
        """Asynchronicznie synchronizuje grupę konkretnego wydarzenia"""
        try:
            from app.models import EventSchedule
            
            event = EventSchedule.query.get(event_id)
            if not event:
                print(f"❌ Wydarzenie {event_id} nie zostało znalezione")
                return False, "Wydarzenie nie zostało znalezione"
            
            group_name = f"Wydarzenie: {event.title}"
            
            # Znajdź grupę wydarzenia
            group = UserGroup.query.filter_by(
                name=group_name,
                group_type='event_based'
            ).first()
            
            if not group:
                print(f"❌ Grupa wydarzenia '{group_name}' nie została znaleziona - sprawdzam czy istnieje po event_id")
                # Sprawdź czy grupa istnieje po event_id
                group = UserGroup.query.filter_by(
                    event_id=event_id,
                    group_type='event_based'
                ).first()
                
                if not group:
                    print(f"❌ Grupa wydarzenia nie istnieje - tworzę nową grupę")
                    # Utwórz nową grupę wydarzenia
                    group = UserGroup(
                        name=group_name,
                        description=f"Grupa uczestników wydarzenia: {event.title}",
                        group_type='event_based',
                        event_id=event_id,
                        criteria=json.dumps({'event_id': event_id})
                    )
                    db.session.add(group)
                    db.session.commit()
                    print(f"✅ Utworzono nową grupę wydarzenia: {group_name}")
                else:
                    print(f"✅ Znaleziono grupę wydarzenia po event_id: {group.name}")
                    # Zaktualizuj nazwę jeśli się zmieniła
                    if group.name != group_name:
                        group.name = group_name
                        group.description = f"Grupa uczestników wydarzenia: {event.title}"
                        db.session.commit()
                        print(f"✅ Zaktualizowano nazwę grupy: {group_name}")
            
            # Pobierz wszystkich zarejestrowanych na wydarzenie przez EventRegistration
            from app.models import EventRegistration
            event_registrations = EventRegistration.query.filter_by(
                event_id=event_id,
                is_active=True
            ).all()
            
            # Pobierz użytkowników z rejestracji
            registrations = [reg.user for reg in event_registrations if reg.user]
            
            # Pobierz obecnych członków grupy (tylko aktywnych)
            current_members = UserGroupMember.query.filter_by(group_id=group.id, is_active=True).all()
            current_emails = {member.email for member in current_members if member.email}
            
            # Pobierz unikalne emaile z rejestracji (usuń duplikaty)
            unique_registrations = {}
            for registration in registrations:
                if registration.email:
                    # Użyj najnowszej rejestracji dla każdego emaila
                    if registration.email not in unique_registrations or registration.created_at > unique_registrations[registration.email].created_at:
                        unique_registrations[registration.email] = registration
            
            print(f"🔍 Znaleziono {len(registrations)} rejestracji, {len(unique_registrations)} unikalnych emaili")
            
            # Dodaj nowych członków
            new_members = []
            for email, registration in unique_registrations.items():
                if email not in current_emails:
                    # Sprawdź czy użytkownik ma konto
                    from app.models import User
                    user = User.query.filter_by(email=email).first()
                    
                    member = UserGroupMember(
                        group_id=group.id,
                        user_id=user.id if user else None,
                        email=email,
                        name=registration.first_name,
                        is_active=True
                    )
                    db.session.add(member)
                    new_members.append(member)
                    print(f"✅ Dodano {email} do grupy {group_name}")
                else:
                    print(f"ℹ️ {email} już jest w grupie {group_name}")
            
            # Usuń członków, którzy nie są już zarejestrowani
            unique_emails = set(unique_registrations.keys())
            members_to_remove = []
            for member in current_members:
                if member.email and member.email not in unique_emails:
                    member.is_active = False
                    members_to_remove.append(member)
                    print(f"✅ Usunięto {member.email or member.first_name} z grupy {group_name}")
            
            # Aktualizuj liczbę członków
            group.member_count = UserGroupMember.query.filter_by(group_id=group.id, is_active=True).count()
            
            db.session.commit()
            
            # Jeśli dodano nowych członków, zaplanuj dla nich przypomnienia
            if new_members:
                print(f"🔄 Planowanie przypomnień dla {len(new_members)} nowych członków grupy wydarzenia")
                try:
                    from app.services.email_v2 import EmailManager
                    email_manager = EmailManager()
                    
                    # Zaplanuj przypomnienia dla nowych członków
                    success, message = email_manager.send_event_reminders_for_new_members(event_id)
                    if success:
                        print(f"✅ Zaplanowano przypomnienia dla nowych członków: {message}")
                    else:
                        print(f"⚠️ Błąd planowania przypomnień dla nowych członków: {message}")
                except Exception as e:
                    print(f"❌ Błąd planowania przypomnień dla nowych członków: {e}")
            
            return True, f"Zsynchronizowano grupę wydarzenia {group_name}"
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Błąd synchronizacji grupy wydarzenia {event_id}: {str(e)}")
            return False, f"Błąd synchronizacji grupy wydarzenia: {str(e)}"
    
    def update_group_members(self, group_id):
        """Aktualizuje listę członków grupy na podstawie kryteriów"""
        try:
            group = UserGroup.query.get(group_id)
            if not group:
                return False, "Grupa nie została znaleziona"
            
            # Nie aktualizuj grup manual - są zarządzane ręcznie
            if group.group_type == 'manual':
                return True, "Grupa ręczna - nie wymaga synchronizacji"
            
            # Nie aktualizuj grupy club_members - ma własną logikę synchronizacji
            if group.group_type == 'club_members':
                return True, "Grupa członków klubu - synchronizowana przez sync_club_members_group"
            
            # Usuń wszystkich członków
            UserGroupMember.query.filter_by(group_id=group_id).delete()
            
            # Dodaj członków na podstawie kryteriów
            if group.group_type == 'event_based':
                criteria = json.loads(group.criteria) if group.criteria else {}
                event_id = criteria.get('event_id')
                
                if event_id:
                    # Pobierz wszystkich uczestników wydarzenia
                    registrations = User.query.filter_by(
                    event_id=event_id,
                    account_type='event_registration'
                ).all()
                    
                    for registration in registrations:
                        member = UserGroupMember(
                            group_id=group_id,
                            user_id=registration.id,  # registration.id is the user_id
                            email=registration.email,
                            name=registration.first_name,
                            member_type='external'  # All event registrations are external members
                        )
                        db.session.add(member)
            
            
            # Aktualizuj liczbę członków
            group.member_count = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).count()
            
            db.session.commit()
            
            return True, f"Grupa zaktualizowana z {group.member_count} członkami"
            
        except Exception as e:
            return False, f"Błąd aktualizacji grupy: {str(e)}"
    
    def get_group_members(self, group_id):
        """Pobiera listę członków grupy"""
        try:
            members = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).all()
            return True, members
        except Exception as e:
            return False, f"Błąd pobierania członków: {str(e)}"
    
    def remove_user_from_group(self, group_id, user_id):
        """Usuwa użytkownika z grupy"""
        try:
            member = UserGroupMember.query.filter_by(
                group_id=group_id,
                user_id=user_id
            ).first()
            
            if not member:
                return False, "Użytkownik nie jest w grupie"
            
            member.is_active = False
            db.session.commit()
            
            # Aktualizuj liczbę członków
            group = UserGroup.query.get(group_id)
            group.member_count = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).count()
            db.session.commit()
            
            return True, "Użytkownik usunięty z grupy"
            
        except Exception as e:
            return False, f"Błąd usuwania z grupy: {str(e)}"
    
    def remove_user_from_club_members(self, user_id):
        """Usuwa użytkownika z grupy członków klubu"""
        try:
            # Znajdź grupę członków klubu
            club_group = UserGroup.query.filter_by(group_type='club_members').first()
            if not club_group:
                return False, "Grupa członków klubu nie została znaleziona"
            
            # Usuń użytkownika z grupy
            return self.remove_user_from_group(club_group.id, user_id)
            
        except Exception as e:
            return False, f"Błąd usuwania z grupy członków klubu: {str(e)}"
    
    def delete_group(self, group_id):
        """Usuwa grupę"""
        try:
            group = UserGroup.query.get(group_id)
            if not group:
                return False, "Grupa nie została znaleziona"
            
            # Usuń wszystkich członków
            UserGroupMember.query.filter_by(group_id=group_id).delete()
            
            # Usuń grupę
            db.session.delete(group)
            db.session.commit()
            
            return True, "Grupa usunięta"
            
        except Exception as e:
            return False, f"Błąd usuwania grupy: {str(e)}"
    
    def add_email_to_event_group(self, email, name, event_id):
        """Dodaje email do grupy wydarzenia (bez konta użytkownika)"""
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                return False, "Wydarzenie nie zostało znalezione"
            
            # Znajdź lub utwórz grupę
            group_id = self.create_event_group(event_id, event.title)
            if not group_id:
                return False, "Błąd tworzenia grupy"
            
            # Sprawdź czy już jest w grupie
            existing_member = UserGroupMember.query.filter_by(
                group_id=group_id,
                email=email
            ).first()
            
            if existing_member:
                return True, "Email już jest w grupie wydarzenia"
            
            # Dodaj do grupy
            member = UserGroupMember(
                group_id=group_id,
                user_id=None,  # Brak konta użytkownika
                email=email,
                name=name,
                is_active=True
            )
            
            db.session.add(member)
            
            # Aktualizuj liczbę członków
            group = UserGroup.query.get(group_id)
            group.member_count = UserGroupMember.query.filter_by(group_id=group_id, is_active=True).count()
            
            db.session.commit()
            
            return True, "Email dodany do grupy wydarzenia"
            
        except Exception as e:
            return False, f"Błąd dodawania do grupy wydarzenia: {str(e)}"
    
    def remove_user_from_event_group(self, user_id, event_id):
        """Usuwa użytkownika z grupy wydarzenia"""
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                print(f"❌ Wydarzenie {event_id} nie zostało znalezione")
                return False, "Wydarzenie nie zostało znalezione"
            
            group_name = f"Wydarzenie: {event.title}"
            print(f"🔍 Szukam grupy: {group_name}")
            
            # Znajdź grupę wydarzenia
            group = UserGroup.query.filter_by(
                name=group_name,
                group_type='event_based'
            ).first()
            
            if not group:
                print(f"❌ Grupa wydarzenia '{group_name}' nie została znaleziona")
                # Sprawdź czy istnieją inne grupy dla tego wydarzenia
                all_event_groups = UserGroup.query.filter_by(group_type='event_based').all()
                print(f"🔍 Dostępne grupy wydarzeń: {[g.name for g in all_event_groups]}")
                
                # Jeśli grupa nie istnieje, to użytkownik prawdopodobnie nie był w grupie
                # Zwróć sukces, bo cel (usunięcie z grupy) został osiągnięty
                print(f"✅ Grupa nie istnieje - użytkownik {user_id} nie był w grupie wydarzenia {event_id}")
                return True, "Użytkownik nie był w grupie wydarzenia"
            
            print(f"✅ Znaleziono grupę: {group.name} (ID: {group.id})")
            
            # Usuń użytkownika z grupy
            return self.remove_user_from_group(group.id, user_id)
            
        except Exception as e:
            print(f"❌ Błąd usuwania z grupy wydarzenia: {str(e)}")
            return False, f"Błąd usuwania z grupy wydarzenia: {str(e)}"
    
    def remove_email_from_event_group(self, email, event_id):
        """Usuwa email z grupy wydarzenia (bez konta użytkownika)"""
        try:
            event = EventSchedule.query.get(event_id)
            if not event:
                print(f"❌ Wydarzenie {event_id} nie zostało znalezione")
                return False, "Wydarzenie nie zostało znalezione"
            
            group_name = f"Wydarzenie: {event.title}"
            print(f"🔍 Szukam grupy: {group_name}")
            
            # Znajdź grupę wydarzenia
            group = UserGroup.query.filter_by(
                name=group_name,
                group_type='event_based'
            ).first()
            
            if not group:
                print(f"❌ Grupa wydarzenia '{group_name}' nie została znaleziona")
                # Sprawdź czy istnieją inne grupy dla tego wydarzenia
                all_event_groups = UserGroup.query.filter_by(group_type='event_based').all()
                print(f"🔍 Dostępne grupy wydarzeń: {[g.name for g in all_event_groups]}")
                
                # Jeśli grupa nie istnieje, to email prawdopodobnie nie był w grupie
                # Zwróć sukces, bo cel (usunięcie z grupy) został osiągnięty
                print(f"✅ Grupa nie istnieje - email {email} nie był w grupie wydarzenia {event_id}")
                return True, "Email nie był w grupie wydarzenia"
            
            print(f"✅ Znaleziono grupę: {group.name} (ID: {group.id})")
            
            # Znajdź członka grupy po emailu
            member = UserGroupMember.query.filter_by(
                group_id=group.id,
                email=email
            ).first()
            
            if not member:
                print(f"❌ Email {email} nie jest w grupie wydarzenia {group.name}")
                return False, "Email nie jest w grupie wydarzenia"
            
            print(f"✅ Znaleziono członka: {email} w grupie {group.name}")
            
            # Usuń członka
            member.is_active = False
            db.session.commit()
            
            # Aktualizuj liczbę członków
            group.member_count = UserGroupMember.query.filter_by(group_id=group.id, is_active=True).count()
            db.session.commit()
            
            print(f"✅ Email {email} usunięty z grupy wydarzenia {group.name}")
            return True, "Email usunięty z grupy wydarzenia"
            
        except Exception as e:
            print(f"❌ Błąd usuwania z grupy wydarzenia: {str(e)}")
            return False, f"Błąd usuwania z grupy wydarzenia: {str(e)}"
    
    def cleanup_duplicate_event_groups(self):
        """Usuwa duplikaty grup wydarzeń"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            
            # Znajdź wszystkie grupy wydarzeń
            event_groups = UserGroup.query.filter_by(group_type='event_based').all()
            
            # Grupuj po event_id
            groups_by_event = {}
            for group in event_groups:
                if group.event_id:
                    if group.event_id not in groups_by_event:
                        groups_by_event[group.event_id] = []
                    groups_by_event[group.event_id].append(group)
            
            # Usuń duplikaty
            duplicates_removed = 0
            for event_id, groups in groups_by_event.items():
                if len(groups) > 1:
                    logger.warning(f"⚠️ Znaleziono {len(groups)} duplikatów grup dla wydarzenia {event_id}")
                    
                    # Zostaw pierwszą grupę, usuń pozostałe
                    main_group = groups[0]
                    for duplicate_group in groups[1:]:
                        # Przenieś członków do głównej grupy (tylko aktywnych)
                        members = UserGroupMember.query.filter_by(group_id=duplicate_group.id, is_active=True).all()
                        for member in members:
                            # Sprawdź czy członek już nie istnieje w głównej grupie
                            existing = UserGroupMember.query.filter_by(
                                group_id=main_group.id,
                                email=member.email
                            ).first()
                            if not existing:
                                member.group_id = main_group.id
                            else:
                                db.session.delete(member)
                        
                        db.session.delete(duplicate_group)
                        duplicates_removed += 1
                        logger.info(f"✅ Usunięto duplikat grupy {duplicate_group.id} dla wydarzenia {event_id}")
            
            db.session.commit()
            logger.info(f"✅ Usunięto {duplicates_removed} duplikatów grup wydarzeń")
            return True, f"Usunieto {duplicates_removed} duplikatów"
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Błąd usuwania duplikatów grup: {str(e)}")
            return False, f"Błąd: {str(e)}"

