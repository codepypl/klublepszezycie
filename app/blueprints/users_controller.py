"""
Users business logic controller
"""
from flask import request
from flask_login import login_required, current_user
from app.models import db, User, UserGroup, UserGroupMember, Stats
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

class UsersController:
    """Users business logic controller"""
    
    @staticmethod
    def get_users(page=1, per_page=10, name_filter='', email_filter='', account_type_filter='', status_filter='', club_member_filter='', event_filter='', group_filter=''):
        """Get users with pagination and filters"""
        try:
            query = User.query
            
            # Apply filters
            if name_filter:
                query = query.filter(User.first_name.ilike(f'%{name_filter}%'))
            
            if email_filter:
                query = query.filter(User.email.ilike(f'%{email_filter}%'))
            
            if account_type_filter:
                query = query.filter(User.account_type == account_type_filter)
            
            if status_filter:
                if status_filter == 'active':
                    query = query.filter(User.is_active == True)
                elif status_filter == 'inactive':
                    query = query.filter(User.is_active == False)
            
            if club_member_filter is not None and club_member_filter != '':
                if club_member_filter == 'true' or club_member_filter is True:
                    query = query.filter(User.club_member == True)
                elif club_member_filter == 'false' or club_member_filter is False:
                    query = query.filter(User.club_member == False)
            
            if event_filter:
                query = query.filter(User.event_id == event_filter)
            
            if group_filter:
                query = query.filter(User.group_id == group_filter)
            
            # Join with UserGroup to get group name
            users = query.join(UserGroup, User.group_id == UserGroup.id, isouter=True).order_by(User.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            # Get stats from central stats table
            total_users = Stats.get_total_users()
            active_users = Stats.get_active_users()
            admin_users = Stats.get_admin_users()
            event_registrations = Stats.get_total_registrations()
            
            club_members = 0
            club_group = UserGroup.query.filter_by(group_type='club_members').first()
            if club_group:
                club_members = UserGroupMember.query.filter_by(group_id=club_group.id, is_active=True).count()
            
            return {
                'success': True,
                'users': users.items,
                'pagination': {
                    'page': users.page,
                    'pages': users.pages,
                    'total': users.total,
                    'per_page': users.per_page
                },
                'stats': {
                    'total_users': total_users,
                    'active_users': active_users,
                    'admin_users': admin_users,
                    'event_registrations': event_registrations,
                    'club_members': club_members
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'users': None
            }
    
    @staticmethod
    def get_user(user_id):
        """Get single user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'Użytkownik nie został znaleziony',
                    'user': None
                }
            
            return {
                'success': True,
                'user': user
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'user': None
            }
    
    @staticmethod
    def create_user(name, email, phone, role='user', is_active=True, password=None):
        """Create new user"""
        try:
            if not all([name, email]):
                return {
                    'success': False,
                    'error': 'Imię i email są wymagane'
                }
            
            # Check if user already exists
            if User.query.filter_by(email=email).first():
                return {
                    'success': False,
                    'error': 'Użytkownik z tym emailem już istnieje'
                }
            
            # Generate password if not provided
            if not password:
                import secrets
                password = secrets.token_urlsafe(8)
            
            user = User(
                first_name=name,
                email=email,
                phone=phone,
                role=role,
                is_active=is_active,
                password_hash=generate_password_hash(password)
            )
            
            db.session.add(user)
            db.session.commit()
            
            return {
                'success': True,
                'user': user,
                'password': password if not password else None,
                'message': 'Użytkownik został utworzony pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_user(user_id, name, email, phone, role, is_active, account_type=None):
        """Update user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'Użytkownik nie został znaleziony'
                }
            
            # Check if email is taken by another user
            existing_user = User.query.filter(User.email == email, User.id != user_id).first()
            if existing_user:
                return {
                    'success': False,
                    'error': 'Email jest już używany przez innego użytkownika'
                }
            
            user.first_name = name
            user.email = email
            user.phone = phone
            user.role = role
            user.is_active = is_active
            if account_type:
                user.account_type = account_type
            
            db.session.commit()
            
            return {
                'success': True,
                'user': user,
                'message': 'Użytkownik został zaktualizowany pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def delete_user(user_id):
        """Delete user"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'Użytkownik nie został znaleziony'
                }
            
            # Don't allow deleting admin users
            if user.is_admin_role():
                return {
                    'success': False,
                    'error': 'Nie można usunąć użytkownika z rolą administratora'
                }
            
            # Don't allow deleting current user
            if user.id == current_user.id:
                return {
                    'success': False,
                    'error': 'Nie można usunąć własnego konta'
                }
            
            db.session.delete(user)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Użytkownik został usunięty pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def toggle_user_status(user_id):
        """Toggle user active status"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'Użytkownik nie został znaleziony'
                }
            
            # Don't allow deactivating admin users
            if user.is_admin_role() and user.is_active:
                return {
                    'success': False,
                    'error': 'Nie można deaktywować użytkownika z rolą administratora'
                }
            
            # Don't allow deactivating current user
            if user.id == current_user.id:
                return {
                    'success': False,
                    'error': 'Nie można deaktywować własnego konta'
                }
            
            user.is_active = not user.is_active
            db.session.commit()
            
            return {
                'success': True,
                'user': user,
                'message': f'Użytkownik został {"aktywowany" if user.is_active else "deaktywowany"}'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def reset_user_password(user_id):
        """Reset user password"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'Użytkownik nie został znaleziony'
                }
            
            # Generate new password
            import secrets
            new_password = secrets.token_urlsafe(8)
            
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            
            return {
                'success': True,
                'password': new_password,
                'message': 'Hasło zostało zresetowane pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_user_groups(user_id):
        """Get user groups"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'Użytkownik nie został znaleziony',
                    'groups': []
                }
            
            groups = UserGroupMember.query.filter_by(user_id=user_id).join(UserGroup).all()
            
            return {
                'success': True,
                'groups': groups
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'groups': []
            }
    
    @staticmethod
    def add_user_to_group(user_id, group_id):
        """Add user to group"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'Użytkownik nie został znaleziony'
                }
            
            group = UserGroup.query.get(group_id)
            if not group:
                return {
                    'success': False,
                    'error': 'Grupa nie została znaleziona'
                }
            
            # Check if user is already in group
            existing = UserGroupMember.query.filter_by(user_id=user_id, group_id=group_id).first()
            if existing:
                return {
                    'success': False,
                    'error': 'Użytkownik jest już w tej grupie'
                }
            
            member = UserGroupMember(user_id=user_id, group_id=group_id)
            db.session.add(member)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Użytkownik został dodany do grupy'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def remove_user_from_group(user_id, group_id):
        """Remove user from group"""
        try:
            member = UserGroupMember.query.filter_by(user_id=user_id, group_id=group_id).first()
            if not member:
                return {
                    'success': False,
                    'error': 'Użytkownik nie jest w tej grupie'
                }
            
            db.session.delete(member)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Użytkownik został usunięty z grupy'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_user_profile(user_id):
        """Get user profile with event history"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'Użytkownik nie został znaleziony'
                }
            
            # Get event history for this user from UserHistory
            from app.models import UserHistory, EventSchedule
            event_history = []

            # Get user event history entries
            history_entries = UserHistory.get_user_event_history(user.id)

            for entry in history_entries:
                event = EventSchedule.query.get(entry.event_id) if entry.event_id else None
                if event:
                    event_history.append({
                        'event_id': event.id,
                        'event_title': event.title,
                        'event_date': event.event_date,
                        'registration_date': entry.registration_date,
                        'participation_date': entry.participation_date,
                        'status': entry.status,
                        'was_club_member': entry.was_club_member,
                        'notes': entry.notes
                    })
            
            return {
                'success': True,
                'user': user,
                'event_history': event_history
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Błąd podczas pobierania profilu użytkownika: {str(e)}'
            }
    
    @staticmethod
    def create_event_registration_user(first_name, email, phone, event_id, group_id):
        """Create user from event registration"""
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                return {
                    'success': False,
                    'error': 'Użytkownik z tym emailem już istnieje',
                    'existing_user': existing_user
                }
            
            # Generate temporary password
            import secrets
            password = secrets.token_urlsafe(8)
            
            user = User(
                first_name=first_name,
                email=email,
                phone=phone,
                password_hash=generate_password_hash(password),
                account_type='event_registration',
                event_id=event_id,
                group_id=group_id,
                club_member=False,
                is_active=True,
                role='user'
            )
            
            db.session.add(user)
            db.session.commit()
            
            return {
                'success': True,
                'user': user,
                'password': password,
                'message': 'Użytkownik został utworzony z rejestracji na wydarzenie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
