"""
Users API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import User, UserGroup, db
from app.utils.auth_utils import admin_required
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
                    User.last_name.ilike(f'%{search}%'),
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
                'last_name': user.last_name,
                'email': user.email,
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
                User.last_name.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%')
            )
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'users': [{
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
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
                    'last_name': user.last_name,
                    'email': user.email,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'email' in data:
                user.email = data['email']
            if 'is_active' in data:
                user.is_active = data['is_active']
            
            db.session.commit()
            
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
@login_required
@admin_required
def api_bulk_delete_users():
    """Bulk delete users"""
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        
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
@login_required
@admin_required
def api_bulk_delete_user_groups():
    """Bulk delete user groups"""
    try:
        data = request.get_json()
        group_ids = data.get('group_ids', [])
        
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
                    'name': user.name,
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
            if 'name' in data:
                user.name = data['name'].strip() if data['name'] else None
            if 'email' in data:
                user.email = data['email'].strip()
            if 'phone' in data:
                user.phone = data['phone'].strip() if data['phone'] else None
            if 'club_member' in data:
                user.club_member = bool(data['club_member'])
            
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
                    'name': user.name,
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
