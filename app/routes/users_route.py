"""
Users routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.blueprints.users_controller import UsersController

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
@login_required
def index():
    """Users management page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    name_filter = request.args.get('name', '').strip()
    email_filter = request.args.get('email', '').strip()
    account_type_filter = request.args.get('account_type', '').strip()
    status_filter = request.args.get('status', '').strip()
    club_member_filter = request.args.get('club_member', '').strip()
    event_filter = request.args.get('event', '').strip()
    group_filter = request.args.get('group', '').strip()
    edit_user_id = request.args.get('edit_user', '').strip()
    
    data = UsersController.get_users(
        page=page,
        per_page=per_page,
        name_filter=name_filter,
        email_filter=email_filter,
        account_type_filter=account_type_filter,
        status_filter=status_filter,
        club_member_filter=club_member_filter,
        event_filter=event_filter,
        group_filter=group_filter
    )
    
    if not data['success']:
        flash(f'Błąd: {data["error"]}', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Calculate active filters count
    active_filters_count = 0
    if name_filter:
        active_filters_count += 1
    if email_filter:
        active_filters_count += 1
    if account_type_filter:
        active_filters_count += 1
    if status_filter:
        active_filters_count += 1
    if club_member_filter:
        active_filters_count += 1
    if event_filter:
        active_filters_count += 1
    if group_filter:
        active_filters_count += 1
    
    # Get user for editing if edit_user_id is provided
    edit_user = None
    if edit_user_id:
        try:
            edit_user_data = UsersController.get_user(int(edit_user_id))
            if edit_user_data['success']:
                edit_user = edit_user_data['user']
        except (ValueError, TypeError):
            pass
    
    # Get events and groups for filters
    from app.models import EventSchedule, UserGroup
    events = EventSchedule.query.filter_by(is_active=True).order_by(EventSchedule.title).all()
    groups = UserGroup.query.filter_by(is_active=True).order_by(UserGroup.name).all()
    
    return render_template('admin/users.html', 
                         users=data['users'],
                         pagination=data.get('pagination'),
                         stats=data.get('stats'),
                         active_filters_count=active_filters_count,
                         name_filter=name_filter,
                         email_filter=email_filter,
                         account_type_filter=account_type_filter,
                         status_filter=status_filter,
                         club_member_filter=club_member_filter,
                         event_filter=event_filter,
                         group_filter=group_filter,
                         events=events,
                         groups=groups,
                         edit_user=edit_user)

@users_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new user"""
    if request.method == 'POST':
        name = request.form.get('first_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', 'user')
        is_active = request.form.get('is_active') == 'on'
        
        result = UsersController.create_user(name, email, phone, role, is_active)
        
        if result['success']:
            flash(result['message'], 'success')
            if result['password']:
                flash(f'Wygenerowane hasło: {result["password"]}', 'info')
            return redirect(url_for('users.index'))
        else:
            flash(result['error'], 'error')
    
    return render_template('admin/user_create.html')


@users_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
def delete(user_id):
    """Delete user"""
    result = UsersController.delete_user(user_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('users.index'))

@users_bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@login_required
def toggle_status(user_id):
    """Toggle user status"""
    result = UsersController.toggle_user_status(user_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('users.index'))

@users_bp.route('/users/reset-password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    """Reset user password"""
    result = UsersController.reset_user_password(user_id)
    
    if result['success']:
        flash(f'{result["message"]}. Nowe hasło: {result["password"]}', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('users.index'))

@users_bp.route('/users/groups/<int:user_id>')
@login_required
def user_groups(user_id):
    """User groups management"""
    data = UsersController.get_user_groups(user_id)
    
    if not data['success']:
        flash(data['error'], 'error')
        return redirect(url_for('users.index'))
    
    # Get all available groups
    from app.models import UserGroup
    all_groups = UserGroup.query.all()
    
    return render_template('admin/user_groups.html', 
                         user_id=user_id, 
                         user_groups=data['groups'], 
                         all_groups=all_groups)

@users_bp.route('/users/add-to-group/<int:user_id>/<int:group_id>', methods=['POST'])
@login_required
def add_to_group(user_id, group_id):
    """Add user to group"""
    result = UsersController.add_user_to_group(user_id, group_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('users.user_groups', user_id=user_id))

@users_bp.route('/users/remove-from-group/<int:user_id>/<int:group_id>', methods=['POST'])
@login_required
def remove_from_group(user_id, group_id):
    """Remove user from group"""
    result = UsersController.remove_user_from_group(user_id, group_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('users.user_groups', user_id=user_id))

@users_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('user/profile.html', user=current_user)