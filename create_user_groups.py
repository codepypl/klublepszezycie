#!/usr/bin/env python3
"""
Skrypt do tworzenia podstawowych grup użytkowników
"""
import os
import sys
from datetime import datetime

# Dodaj ścieżkę do aplikacji
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, UserGroup, UserGroupMember, User

def create_groups():
    """Tworzy podstawowe grupy użytkowników"""
    groups = [
        {
            'name': 'Członkowie klubu',
            'description': 'Grupa członków klubu Lepsze Życie',
            'group_type': 'club_members'
        },
        {
            'name': 'Wszyscy użytkownicy',
            'description': 'Grupa wszystkich zarejestrowanych użytkowników',
            'group_type': 'all_users'
        }
    ]
    
    created = 0
    for group_data in groups:
        # Sprawdź czy grupa już istnieje
        existing = UserGroup.query.filter_by(name=group_data['name']).first()
        
        if not existing:
            group = UserGroup(
                name=group_data['name'],
                description=group_data['description'],
                group_type=group_data['group_type'],
                is_active=True
            )
            
            db.session.add(group)
            created += 1
            print(f"✅ Utworzono grupę: {group_data['name']}")
        else:
            print(f"⚠️  Grupa już istnieje: {group_data['name']}")
    
    db.session.commit()
    
    # Dodaj użytkowników do grup
    add_users_to_groups()
    
    print(f"\n🎉 Utworzono {created} nowych grup użytkowników")

def add_users_to_groups():
    """Dodaje użytkowników do odpowiednich grup"""
    try:
        # Grupa "Wszyscy użytkownicy"
        all_users_group = UserGroup.query.filter_by(name='Wszyscy użytkownicy').first()
        if all_users_group:
            # Pobierz wszystkich aktywnych użytkowników
            users = User.query.filter_by(is_active=True).all()
            
            for user in users:
                # Sprawdź czy już jest w grupie
                existing = UserGroupMember.query.filter_by(
                    group_id=all_users_group.id,
                    user_id=user.id
                ).first()
                
                if not existing:
                    member = UserGroupMember(
                        group_id=all_users_group.id,
                        user_id=user.id,
                        email=user.email,
                        name=user.name
                    )
                    db.session.add(member)
            
            # Aktualizuj liczbę członków
            all_users_group.member_count = UserGroupMember.query.filter_by(
                group_id=all_users_group.id, 
                is_active=True
            ).count()
            
            print(f"✅ Dodano {all_users_group.member_count} użytkowników do grupy 'Wszyscy użytkownicy'")
        
        # Grupa "Członkowie klubu"
        club_members_group = UserGroup.query.filter_by(name='Członkowie klubu').first()
        if club_members_group:
            # Pobierz wszystkich członków klubu
            club_members = User.query.filter_by(club_member=True, is_active=True).all()
            
            for user in club_members:
                # Sprawdź czy już jest w grupie
                existing = UserGroupMember.query.filter_by(
                    group_id=club_members_group.id,
                    user_id=user.id
                ).first()
                
                if not existing:
                    member = UserGroupMember(
                        group_id=club_members_group.id,
                        user_id=user.id,
                        email=user.email,
                        name=user.name
                    )
                    db.session.add(member)
            
            # Aktualizuj liczbę członków
            club_members_group.member_count = UserGroupMember.query.filter_by(
                group_id=club_members_group.id, 
                is_active=True
            ).count()
            
            print(f"✅ Dodano {club_members_group.member_count} użytkowników do grupy 'Członkowie klubu'")
        
        db.session.commit()
        
    except Exception as e:
        print(f"❌ Błąd dodawania użytkowników do grup: {str(e)}")

def main():
    """Główna funkcja"""
    print("Tworzenie podstawowych grup użytkowników...")
    
    try:
        app = create_app()
        
        with app.app_context():
            create_groups()
            
    except Exception as e:
        print(f"❌ Błąd: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()




