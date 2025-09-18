"""
Group Manager - zarządzanie grupami użytkowników
"""
import json
from datetime import datetime
from app.models import db, UserGroup, UserGroupMember, User, EventSchedule, EventRegistration
from app.utils.timezone_utils import get_local_now

class GroupManager:
    """Menedżer grup użytkowników"""
    
    def create_event_group(self, event_id, event_title):
        """Tworzy grupę dla wydarzenia"""
        try:
            # Sprawdź czy grupa już istnieje
            existing_group = UserGroup.query.filter_by(
                name=f"Wydarzenie: {event_title}",
                group_type='event_based'
            ).first()
            
            if existing_group:
                return existing_group.id
            
            # Utwórz nową grupę
            group = UserGroup(
                name=f"Wydarzenie: {event_title}",
                description=f"Grupa uczestników wydarzenia: {event_title}",
                group_type='event_based',
                criteria=json.dumps({'event_id': event_id})
            )
            
            db.session.add(group)
            db.session.commit()
            
            return group.id
            
        except Exception as e:
            print(f"Błąd tworzenia grupy wydarzenia: {str(e)}")
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
            # Znajdź lub utwórz grupę członków
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
            
            for group in event_groups:
                try:
                    # Sprawdź czy criteria zawiera event_id
                    criteria = json.loads(group.criteria) if group.criteria else {}
                    event_id = criteria.get('event_id')
                    
                    if event_id:
                        # Sprawdź czy wydarzenie nadal istnieje
                        event = EventSchedule.query.get(event_id)
                        if not event:
                            orphaned_groups.append(group)
                except (json.JSONDecodeError, TypeError):
                    # Jeśli criteria jest nieprawidłowe, usuń grupę
                    orphaned_groups.append(group)
            
            # Usuń nieużywane grupy
            deleted_count = 0
            for group in orphaned_groups:
                # Usuń wszystkich członków
                UserGroupMember.query.filter_by(group_id=group.id).delete()
                
                # Usuń grupę
                db.session.delete(group)
                deleted_count += 1
                print(f"🗑️ Usunięto nieużywaną grupę: {group.name}")
            
            if deleted_count > 0:
                db.session.commit()
                return True, f"Usunięto {deleted_count} nieużywanych grup"
            else:
                return True, "Brak nieużywanych grup do usunięcia"
                
        except Exception as e:
            db.session.rollback()
            return False, f"Błąd czyszczenia grup: {str(e)}"
    
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
            
            # Pobierz obecnych członków grupy
            current_members = UserGroupMember.query.filter_by(group_id=group.id).all()
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
    
    def sync_system_groups(self):
        """Synchronizuje grupy systemowe"""
        try:
            # Synchronizuj tylko grupę członków klubu (wszyscy aktywni użytkownicy)
            success, message = self.sync_club_members_group()
            
            return success, message
            
        except Exception as e:
            return False, f"Błąd synchronizacji grup systemowych: {str(e)}"
    
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
                    registrations = EventRegistration.query.filter_by(event_id=event_id).all()
                    
                    for registration in registrations:
                        member = UserGroupMember(
                            group_id=group_id,
                            user_id=None,  # user_id field no longer exists in event_registrations
                            email=registration.email,
                            first_name=registration.first_name,
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

