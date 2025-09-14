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
        
        # Get users with pagination
        users_pagination = User.query.order_by(User.created_at.desc()).paginate(
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
        
        return render_template('admin/users.html', 
                             users=users, 
                             edit_user=edit_user,
                             pagination=users_pagination,
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

