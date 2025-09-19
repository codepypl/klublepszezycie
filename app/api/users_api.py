"""
Users API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import User, UserGroup, db
from app.utils.auth_utils import admin_required_api, login_required_api
from app.blueprints.users_controller import UsersController
import logging

users_api_bp = Blueprint('users_api', __name__)

@users_api_bp.route('/users', methods=['GET'])
@login_required
def api_users():
    """Get all users with pagination and search"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '', type=str)
        
        query = User.query
        
        if search:
            query = query.filter(
                db.or_(
                    User.first_name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                )
            )
        
        users = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'users': [{
                'id': user.id,
                'first_name': user.first_name,
                'email': user.email,
                'phone': user.phone,
                'is_active': user.is_active,
                'event_id': user.event_id,
                'group_id': user.group_id,
                'account_type': user.account_type,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            } for user in users.items],
            'pagination': {
                'page': users.page,
                'pages': users.pages,
                'per_page': users.per_page,
                'total': users.total,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        })
    except Exception as e:
        logging.error(f"Error getting users: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@users_api_bp.route('/users/for-event-group/<int:event_id>', methods=['GET'])
@login_required
def api_users_for_event_group(event_id):
    """Get users suitable for adding to event group (non-club members registered for other events)"""
    try:
        search = request.args.get('search', '', type=str)
        
        # Get users who:
        # 1. Are NOT club members (club_member=False)
        # 2. Are registered for events (account_type='event_registration')
        # 3. Are NOT registered for the current event being edited
        query = User.query.filter(
            User.club_member == False,
            User.account_type == 'event_registration',
            User.event_id != event_id
        )
        
        if search:
            query = query.filter(
                db.or_(
                    User.first_name.ilike(f'%{search}%'),
                    User.email.ilike(f'%{search}%')
                )
            )
        
        users = query.all()
        
        return jsonify({
            'success': True,
            'users': [{
                'id': user.id,
                'first_name': user.first_name,
                'email': user.email,
                'phone': user.phone,
                'event_id': user.event_id,
                'account_type': user.account_type
            } for user in users]
        })
    except Exception as e:
        logging.error(f"Error getting users for event group: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@users_api_bp.route('/search-users', methods=['GET'])
@login_required
def api_search_users():
    """Search users by name or email"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'success': True, 'users': []})
        
        users = User.query.filter(
            db.or_(
                User.first_name.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%')
            )
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'users': [{
                'id': user.id,
                'first_name': user.first_name,
                'email': user.email,
                'phone': user.phone,
                'is_active': user.is_active
            } for user in users]
        })
    except Exception as e:
        logging.error(f"Error searching users: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@users_api_bp.route('/user/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_user(user_id):
    """Individual user API"""
    try:
        user = User.query.get_or_404(user_id)
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'email': user.email,
                    'phone': user.phone,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'email' in data:
                user.email = data['email']
            if 'phone' in data:
                user.phone = data['phone']
            if 'is_active' in data:
                user.is_active = data['is_active']
            # Store old club_member status for group management
            old_club_member = user.club_member
            
            if 'club_member' in data:
                user.club_member = data['club_member']
            if 'role' in data:
                user.role = data['role']
            if 'account_type' in data:
                user.account_type = data['account_type']
            
            # Obsługa nowego hasła
            new_password = None
            if 'password' in data and data['password']:
                from werkzeug.security import generate_password_hash
                new_password = data['password']
                user.password_hash = generate_password_hash(new_password)
            
            db.session.commit()
            
            # Update groups if club_member status changed
            if 'club_member' in data and old_club_member != data['club_member']:
                from app.services.group_manager import GroupManager
                group_manager = GroupManager()
                
                if data['club_member']:
                    # User became club member - add to club group
                    print(f"🔍 Dodawanie użytkownika {user.email} do grupy członków klubu")
                    success, message = group_manager.add_user_to_club_members(user.id)
                    if success:
                        print(f"✅ Użytkownik {user.email} dodany do grupy członków klubu")
                    else:
                        print(f"❌ Błąd dodawania do grupy członków klubu: {message}")
                else:
                    # User is no longer club member - remove from club group and all event groups
                    print(f"🔍 Usuwanie użytkownika {user.email} z grupy członków klubu")
                    
                    # Remove from club group
                    success, message = group_manager.remove_user_from_club_members(user.id)
                    if success:
                        print(f"✅ Użytkownik {user.email} usunięty z grupy członków klubu")
                    else:
                        print(f"❌ Błąd usuwania z grupy członków klubu: {message}")
                    
                    # Synchronizuj wszystkie grupy wydarzeń
                    success, message = group_manager.sync_event_groups()
                    if success:
                        print(f"✅ Zsynchronizowano wszystkie grupy wydarzeń po zmianie statusu członka klubu dla {user.email}")
                    else:
                        print(f"❌ Błąd synchronizacji grup wydarzeń: {message}")
                
                # Dodatkowa synchronizacja grupy członków klubu dla pewności
                success, message = group_manager.sync_club_members_group()
                if success:
                    print(f"✅ Zsynchronizowano grupę członków klubu po zmianie statusu dla {user.email}")
                else:
                    print(f"❌ Błąd synchronizacji grupy członków klubu: {message}")
            
            # Wyślij email z nowym hasłem jeśli zostało ustawione
            if new_password:
                try:
                    from app.services.email_service import EmailService
                    from app.utils.timezone_utils import get_local_now
                    import os
                    
                    email_service = EmailService()
                    
                    # Przygotuj kontekst emaila
                    base_url = os.getenv('BASE_URL', 'https://klublepszezycie.pl')
                    login_url = f"{base_url}/login"
                    unsubscribe_url = f"{base_url}/unsubscribe"
                    delete_account_url = f"{base_url}/delete-account"
                    
                    context = {
                        'user_name': user.first_name or 'Użytkowniku',
                        'new_password': new_password,
                        'login_url': login_url,
                        'unsubscribe_url': unsubscribe_url,
                        'delete_account_url': delete_account_url
                    }
                    
                    # Wyślij email
                    email_service.send_template_email(
                        to_email=user.email,
                        template_name='admin_password_set',
                        context=context,
                        to_name=user.first_name or 'Użytkowniku'
                    )
                    
                except Exception as email_error:
                    # Nie przerywaj operacji jeśli email się nie wyśle
                    print(f"Błąd wysyłania emaila z nowym hasłem: {str(email_error)}")
            
            return jsonify({
                'success': True,
                'message': 'User updated successfully'
            })
        
        elif request.method == 'DELETE':
            # Store user info before deletion for group synchronization
            user_email = user.email
            user_id = user.id
            
            # Delete user from database
            db.session.delete(user)
            db.session.commit()
            
            # Synchronize groups after user deletion
            try:
                from app.services.group_manager import GroupManager
                group_manager = GroupManager()
                
                # Synchronize club members group
                success, message = group_manager.sync_club_members_group()
                if success:
                    print(f"✅ Zsynchronizowano grupę członków klubu po usunięciu użytkownika {user_email}")
                else:
                    print(f"❌ Błąd synchronizacji grupy członków klubu: {message}")
                
                # Synchronize event groups
                success, message = group_manager.sync_event_groups()
                if success:
                    print(f"✅ Zsynchronizowano grupy wydarzeń po usunięciu użytkownika {user_email}")
                else:
                    print(f"❌ Błąd synchronizacji grup wydarzeń: {message}")
                    
            except Exception as sync_error:
                print(f"❌ Błąd synchronizacji grup po usunięciu użytkownika {user_email}: {str(sync_error)}")
            
            return jsonify({
                'success': True,
                'message': 'User deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with user {user_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@users_api_bp.route('/user-groups', methods=['GET', 'POST'])
@login_required
def api_user_groups():
    """User groups API"""
    if request.method == 'GET':
        try:
            groups = UserGroup.query.all()
            return jsonify({
                'success': True,
                'groups': [{
                    'id': group.id,
                    'name': group.name,
                    'description': group.description,
                    'created_at': group.created_at.isoformat() if group.created_at else None
                } for group in groups]
            })
        except Exception as e:
            logging.error(f"Error getting user groups: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            group = UserGroup(
                name=data['name'],
                description=data.get('description', '')
            )
            
            db.session.add(group)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'User group created successfully',
                'group': {
                    'id': group.id,
                    'name': group.name,
                    'description': group.description
                }
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating user group: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@users_api_bp.route('/user-groups/<int:group_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_user_group(group_id):
    """Specific user group API"""
    group = UserGroup.query.get_or_404(group_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'group': {
                    'id': group.id,
                    'name': group.name,
                    'description': group.description,
                    'created_at': group.created_at.isoformat() if group.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'name' in data:
                group.name = data['name']
            if 'description' in data:
                group.description = data['description']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'User group updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(group)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'User group deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with user group {group_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@users_api_bp.route('/bulk-delete/users', methods=['POST'])
@admin_required_api
def api_bulk_delete_users():
    """Bulk delete users"""
    try:
        data = request.get_json()
        logging.info(f"Bulk delete users request data: {data}")
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        user_ids = data.get('user_ids', data.get('ids', []))
        
        if not user_ids:
            return jsonify({'success': False, 'message': 'No users selected'}), 400
        
        deleted_count = 0
        deleted_users = []  # Store user info for group synchronization
        
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user:
                # Store user info before deletion
                deleted_users.append({
                    'id': user.id,
                    'email': user.email,
                    'club_member': user.club_member
                })
                db.session.delete(user)
                deleted_count += 1
        
        db.session.commit()
        
        # Synchronize groups after bulk deletion
        if deleted_users:
            try:
                from app.services.group_manager import GroupManager
                group_manager = GroupManager()
                
                # Synchronize club members group
                success, message = group_manager.sync_club_members_group()
                if success:
                    print(f"✅ Zsynchronizowano grupę członków klubu po bulk delete ({deleted_count} użytkowników)")
                else:
                    print(f"❌ Błąd synchronizacji grupy członków klubu: {message}")
                
                # Synchronize event groups
                success, message = group_manager.sync_event_groups()
                if success:
                    print(f"✅ Zsynchronizowano grupy wydarzeń po bulk delete ({deleted_count} użytkowników)")
                else:
                    print(f"❌ Błąd synchronizacji grup wydarzeń: {message}")
                    
            except Exception as sync_error:
                print(f"❌ Błąd synchronizacji grup po bulk delete: {str(sync_error)}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} users'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting users: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@users_api_bp.route('/bulk-edit/users', methods=['POST'])
@admin_required_api
def api_bulk_edit_users():
    """Bulk edit users"""
    try:
        data = request.get_json()
        logging.info(f"Bulk edit users request data: {data}")
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        user_ids = data.get('user_ids', data.get('ids', []))
        
        if not user_ids:
            return jsonify({'success': False, 'message': 'No users selected'}), 400
        
        # Get edit parameters
        club_member = data.get('club_member')
        is_active = data.get('is_active')
        account_type = data.get('account_type')
        
        # Check if at least one parameter is provided
        if club_member is None and is_active is None and account_type is None:
            return jsonify({'success': False, 'message': 'No changes specified'}), 400
        
        updated_count = 0
        updated_users = []  # Store user info for group synchronization
        
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user:
                # Don't allow editing admin users
                if user.is_admin_role():
                    continue
                
                user_updated = False
                
                # Update club membership
                if club_member is not None:
                    if club_member == 'true':
                        user.club_member = True
                    elif club_member == 'false':
                        user.club_member = False
                    user_updated = True
                
                # Update account status
                if is_active is not None:
                    if is_active == 'true':
                        user.is_active = True
                    elif is_active == 'false':
                        user.is_active = False
                    user_updated = True
                
                # Update account type
                if account_type is not None and account_type != '':
                    user.account_type = account_type
                    user_updated = True
                
                if user_updated:
                    updated_users.append({
                        'id': user.id,
                        'email': user.email,
                        'club_member': user.club_member,
                        'is_active': user.is_active,
                        'account_type': user.account_type
                    })
                    updated_count += 1
        
        db.session.commit()
        
        # Synchronize groups after bulk edit
        if updated_users:
            try:
                from app.services.group_manager import GroupManager
                group_manager = GroupManager()
                
                # Synchronize club members group
                success, message = group_manager.sync_club_members_group()
                if success:
                    print(f"✅ Zsynchronizowano grupę członków klubu po bulk edit ({updated_count} użytkowników)")
                else:
                    print(f"❌ Błąd synchronizacji grupy członków klubu: {message}")
                
                # Synchronize event groups
                success, message = group_manager.sync_event_groups()
                if success:
                    print(f"✅ Zsynchronizowano grupy wydarzeń po bulk edit")
                else:
                    print(f"❌ Błąd synchronizacji grup wydarzeń: {message}")
                    
            except Exception as sync_error:
                print(f"❌ Błąd podczas synchronizacji grup po bulk edit: {str(sync_error)}")
        
        return jsonify({
            'success': True,
            'message': f'Zaktualizowano {updated_count} użytkowników',
            'updated_count': updated_count,
            'updated_users': updated_users
        })
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk editing users: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@users_api_bp.route('/bulk-delete/user-groups', methods=['POST'])
@admin_required_api
def api_bulk_delete_user_groups():
    """Bulk delete user groups"""
    try:
        data = request.get_json()
        group_ids = data.get('group_ids', data.get('ids', []))
        
        if not group_ids:
            return jsonify({'success': False, 'message': 'No groups selected'}), 400
        
        deleted_count = 0
        for group_id in group_ids:
            group = UserGroup.query.get(group_id)
            if group:
                db.session.delete(group)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} user groups'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting user groups: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@users_api_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def api_profile():
    """User profile API - get and update current user profile"""
    try:
        if request.method == 'GET':
            # Get current user profile
            user = current_user
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'name': user.first_name,
                    'first_name': user.first_name,
                    'username': user.first_name,
                    'email': user.email,
                    'phone': user.phone,
                    'club_member': user.club_member,
                    'is_active': user.is_active,
                    'role': user.role,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
            })
        
        elif request.method == 'PUT':
            # Update current user profile
            user = current_user
            data = request.get_json()
            
            if not data:
                return jsonify({'success': False, 'message': 'No data provided'}), 400
            
            # Update user fields
            if 'first_name' in data:
                user.first_name = data['first_name'].strip() if data['first_name'] else None
            if 'email' in data:
                user.email = data['email'].strip()
            if 'phone' in data:
                user.phone = data['phone'].strip() if data['phone'] else None
            if 'club_member' in data:
                old_club_member = user.club_member
                user.club_member = bool(data['club_member'])
                
                # Synchronize club members group if status changed
                if old_club_member != user.club_member:
                    from app.services.group_manager import GroupManager
                    group_manager = GroupManager()
                    group_manager.sync_club_members_group()
            
            # Validate email if provided
            if 'email' in data and user.email:
                from app.utils.validation_utils import validate_email
                if not validate_email(user.email):
                    return jsonify({'success': False, 'message': 'Nieprawidłowy format adresu e-mail'}), 400
                
                # Check if email is already taken by another user
                existing_user = User.query.filter(User.email == user.email, User.id != user.id).first()
                if existing_user:
                    return jsonify({'success': False, 'message': 'Adres e-mail jest już używany przez innego użytkownika'}), 400
            
            # Validate phone if provided
            if 'phone' in data and user.phone:
                from app.utils.validation_utils import validate_phone
                if not validate_phone(user.phone):
                    return jsonify({'success': False, 'message': 'Nieprawidłowy format numeru telefonu'}), 400
            
            # Save changes
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Profil został zaktualizowany',
                'user': {
                    'id': user.id,
                    'name': user.first_name,
                    'first_name': user.first_name,
                    'username': user.first_name,
                    'email': user.email,
                    'phone': user.phone,
                    'club_member': user.club_member,
                    'is_active': user.is_active,
                    'role': user.role,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in profile API: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@users_api_bp.route('/users/profile/<int:user_id>', methods=['GET'])
@login_required
def api_user_profile(user_id):
    """Get user profile with event history"""
    try:
        result = UsersController.get_user_profile(user_id)
        
        if result['success']:
            user = result['user']
            event_history = result['event_history']
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'email': user.email,
                    'phone': user.phone,
                    'club_member': user.club_member,
                    'account_type': user.account_type,
                    'event_id': user.event_id,
                    'group_id': user.group_id,
                    'is_active': user.is_active,
                    'role': user.role,
                    'created_at': user.created_at.strftime('%Y-%m-%dT%H:%M:%S%z') if user.created_at else None,
                    'last_login': user.last_login.strftime('%Y-%m-%dT%H:%M:%S%z') if user.last_login else None
                },
                'event_history': event_history
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 404
    
    except Exception as e:
        logging.error(f"Error in user profile API: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
