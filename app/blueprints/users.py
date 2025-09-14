"""
Users Management Blueprint
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
@login_required
def index():
    """Users management page"""
    try:
        # Pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Filter parameters
        name_filter = request.args.get('name', '').strip()
        email_filter = request.args.get('email', '').strip()
        role_filter = request.args.get('role', '').strip()
        status_filter = request.args.get('status', '').strip()
        club_member_filter = request.args.get('club_member', '').strip()
        
        # Build query with filters
        query = User.query
        
        # Apply filters
        if name_filter:
            query = query.filter(User.name.ilike(f'%{name_filter}%'))
        
        if email_filter:
            query = query.filter(User.email.ilike(f'%{email_filter}%'))
        
        if role_filter:
            if role_filter == 'admin':
                query = query.filter((User.role == 'admin') | (User.is_admin == True))
            else:
                query = query.filter(User.role == role_filter)
        
        if status_filter:
            if status_filter == 'active':
                query = query.filter(User.is_active == True)
            elif status_filter == 'inactive':
                query = query.filter(User.is_active == False)
            elif status_filter == 'never_logged':
                query = query.filter(User.last_login.is_(None))
        
        if club_member_filter:
            club_member_bool = club_member_filter.lower() == 'true'
            query = query.filter(User.club_member == club_member_bool)
        
        # Get users with pagination
        users_pagination = query.order_by(User.created_at.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        users = users_pagination.items
        
        # Get statistics for all users (not just current page)
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(is_admin=True).count()
        never_logged_users = User.query.filter(User.last_login.is_(None)).count()
        
        # Check if we're editing a specific user
        edit_user_email = request.args.get('edit_user')
        edit_user = None
        if edit_user_email:
            edit_user = User.query.filter_by(email=edit_user_email).first()
        
        # Prepare filter info for template
        active_filters = {
            'name': name_filter,
            'email': email_filter,
            'role': role_filter,
            'status': status_filter,
            'club_member': club_member_filter
        }
        
        # Count active filters
        active_filters_count = sum(1 for value in active_filters.values() if value)
        
        return render_template('admin/users.html', 
                             users=users, 
                             edit_user=edit_user,
                             pagination=users_pagination,
                             active_filters=active_filters,
                             active_filters_count=active_filters_count,
                             stats={
                                 'total_users': total_users,
                                 'active_users': active_users,
                                 'admin_users': admin_users,
                                 'never_logged_users': never_logged_users
                             })
    except Exception as e:
        flash(f'Błąd podczas ładowania użytkowników: {str(e)}', 'error')
        return render_template('admin/users.html', 
                             users=[], 
                             edit_user=None, 
                             pagination=None, 
                             stats={
                                 'total_users': 0,
                                 'active_users': 0,
                                 'admin_users': 0,
                                 'never_logged_users': 0
                             })

@users_bp.route('/users/groups')
@login_required
def groups():
    """User groups management page"""
    return render_template('admin/user_groups.html')

@users_bp.route('/users/registrations')
@login_required
def registrations():
    """User registrations management page"""
    return render_template('admin/registrations.html')

