"""
Users API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import User, UserGroup, db
from app.utils.auth_utils import admin_required_api, login_required_api
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
            if 'club_member' in data:
                user.club_member = data['club_member']
            if 'role' in data:
                user.role = data['role']
            
            # Obsługa nowego hasła
            new_password = None
            if 'password' in data and data['password']:
                from werkzeug.security import generate_password_hash
                new_password = data['password']
                user.password_hash = generate_password_hash(new_password)
            
            db.session.commit()
            
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
            db.session.delete(user)
            db.session.commit()
            
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
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} users'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting users: {str(e)}")
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
                    'username': user.username,
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
                    'username': user.username,
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
