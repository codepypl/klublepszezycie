"""
User Groups Controller
"""
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.user_groups_model import UserGroup, UserGroupMember
from app.models.events_model import EventSchedule
from app.models.user_model import User
import json

class UserGroupsController:
    
    @staticmethod
    @login_required
    def index():
        """Lista grup użytkowników"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            pagination = UserGroup.query.order_by(UserGroup.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            # Get events for filter
            events = EventSchedule.query.order_by(EventSchedule.event_date.desc()).limit(20).all()
            
            return render_template('admin/user_groups.html', 
                                 groups=pagination.items,
                                 pagination=pagination,
                                 events=events)
            
        except Exception as e:
            flash(f'Błąd ładowania grup: {str(e)}', 'error')
            return render_template('admin/user_groups.html', groups=[], pagination=None, events=[])
    
    @staticmethod
    @login_required
    def create():
        """Tworzenie nowej grupy"""
        try:
            data = request.form
            
            # Validate required fields
            if not data.get('name'):
                flash('Nazwa grupy jest wymagana', 'error')
                return redirect(url_for('user_groups.index'))
            
            # Check if group with same name exists
            existing_group = UserGroup.query.filter_by(name=data['name']).first()
            if existing_group:
                flash('Grupa o tej nazwie już istnieje', 'error')
                return redirect(url_for('user_groups.index'))
            
            # Create new group
            group = UserGroup(
                name=data['name'],
                description=data.get('description', ''),
                group_type=data.get('group_type', 'manual'),
                event_id=data.get('event_id') if data.get('event_id') else None,
                criteria=data.get('criteria'),
                is_active=data.get('is_active') == 'on'
            )
            
            db.session.add(group)
            db.session.commit()
            
            flash('Grupa utworzona pomyślnie', 'success')
            return redirect(url_for('user_groups.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Błąd tworzenia grupy: {str(e)}', 'error')
            return redirect(url_for('user_groups.index'))
    
    @staticmethod
    @login_required
    def update(group_id):
        """Aktualizacja grupy"""
        try:
            group = UserGroup.query.get(group_id)
            if not group:
                flash('Grupa nie istnieje', 'error')
                return redirect(url_for('user_groups.index'))
            
            data = request.form
            
            # Update fields
            group.name = data.get('name', group.name)
            group.description = data.get('description', group.description)
            group.group_type = data.get('group_type', group.group_type)
            group.event_id = data.get('event_id') if data.get('event_id') else None
            group.criteria = data.get('criteria', group.criteria)
            group.is_active = data.get('is_active') == 'on'
            
            db.session.commit()
            
            flash('Grupa zaktualizowana pomyślnie', 'success')
            return redirect(url_for('user_groups.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Błąd aktualizacji grupy: {str(e)}', 'error')
            return redirect(url_for('user_groups.index'))
    
    @staticmethod
    @login_required
    def delete(group_id):
        """Usuwanie grupy"""
        try:
            group = UserGroup.query.get(group_id)
            if not group:
                flash('Grupa nie istnieje', 'error')
                return redirect(url_for('user_groups.index'))
            
            # Check if group is default (cannot be deleted)
            default_groups = ['club_members']
            if group.group_type in default_groups:
                flash('Nie można usunąć grupy domyślnej', 'error')
                return redirect(url_for('user_groups.index'))
            
            db.session.delete(group)
            db.session.commit()
            
            flash('Grupa usunięta pomyślnie', 'success')
            return redirect(url_for('user_groups.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Błąd usuwania grupy: {str(e)}', 'error')
            return redirect(url_for('user_groups.index'))
    
    @staticmethod
    @login_required
    def view(group_id):
        """Szczegóły grupy"""
        try:
            group = UserGroup.query.get(group_id)
            if not group:
                flash('Grupa nie istnieje', 'error')
                return redirect(url_for('user_groups.index'))
            
            # Get event info
            event_info = None
            if group.event_id and group.event:
                event_info = {
                    'id': group.event.id,
                    'title': group.event.title,
                    'event_date': group.event.event_date
                }
            
            # Get members
            members = []
            for member in group.members:
                member_data = {
                    'id': member.id,
                    'member_type': member.member_type,
                    'is_active': member.is_active,
                    'joined_at': member.joined_at
                }
                
                if member.user:
                    member_data.update({
                        'user_id': member.user.id,
                        'email': member.user.email,
                        'name': member.user.first_name or member.user.email
                    })
                else:
                    member_data.update({
                        'email': member.email,
                        'name': member.name
                    })
                
                members.append(member_data)
            
            return render_template('admin/user_group_details.html', 
                                 group=group,
                                 event_info=event_info,
                                 members=members)
            
        except Exception as e:
            flash(f'Błąd ładowania grupy: {str(e)}', 'error')
            return redirect(url_for('user_groups.index'))
    
    @staticmethod
    @login_required
    def add_member(group_id):
        """Dodawanie członka do grupy"""
        try:
            group = UserGroup.query.get(group_id)
            if not group:
                flash('Grupa nie istnieje', 'error')
                return redirect(url_for('user_groups.view', group_id=group_id))
            
            data = request.form
            user_id = data.get('user_id')
            email = data.get('email')
            name = data.get('name')
            
            if not user_id and not email:
                flash('Musisz podać user_id lub email', 'error')
                return redirect(url_for('user_groups.view', group_id=group_id))
            
            # Check if member already exists
            if user_id:
                existing = UserGroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
            else:
                existing = UserGroupMember.query.filter_by(group_id=group_id, email=email).first()
            
            if existing:
                flash('Użytkownik już jest w tej grupie', 'error')
                return redirect(url_for('user_groups.view', group_id=group_id))
            
            # Create new member
            member = UserGroupMember(
                group_id=group_id,
                user_id=user_id,
                email=email,
                name=name,
                member_type='user' if user_id else 'external'
            )
            
            db.session.add(member)
            
            # Update member count
            group.member_count = group.members.count()
            
            db.session.commit()
            
            flash('Członek dodany pomyślnie', 'success')
            return redirect(url_for('user_groups.view', group_id=group_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Błąd dodawania członka: {str(e)}', 'error')
            return redirect(url_for('user_groups.view', group_id=group_id))
    
    @staticmethod
    @login_required
    def remove_member(group_id, member_id):
        """Usuwanie członka z grupy"""
        try:
            member = UserGroupMember.query.filter_by(id=member_id, group_id=group_id).first()
            if not member:
                flash('Członek nie istnieje', 'error')
                return redirect(url_for('user_groups.view', group_id=group_id))
            
            group = member.group
            db.session.delete(member)
            
            # Update member count
            group.member_count = group.members.count()
            
            db.session.commit()
            
            flash('Członek usunięty pomyślnie', 'success')
            return redirect(url_for('user_groups.view', group_id=group_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Błąd usuwania członka: {str(e)}', 'error')
            return redirect(url_for('user_groups.view', group_id=group_id))
