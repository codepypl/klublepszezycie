"""
User Groups Routes
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required
from app.blueprints.user_groups_controller import UserGroupsController

user_groups_bp = Blueprint('user_groups', __name__)

@user_groups_bp.route('/admin/user-groups')
@login_required
def index():
    """Lista grup użytkowników"""
    return UserGroupsController.index()

@user_groups_bp.route('/admin/user-groups/create', methods=['GET', 'POST'])
@login_required
def create():
    """Tworzenie nowej grupy"""
    if request.method == 'POST':
        return UserGroupsController.create()
    else:
        from app.models.events_model import EventSchedule
        events = EventSchedule.query.order_by(EventSchedule.event_date.desc()).limit(20).all()
        return render_template('admin/user_group_form.html', group=None, events=events)

@user_groups_bp.route('/admin/user-groups/<int:group_id>')
@login_required
def view(group_id):
    """Szczegóły grupy"""
    return UserGroupsController.view(group_id)

@user_groups_bp.route('/admin/user-groups/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(group_id):
    """Edycja grupy"""
    if request.method == 'POST':
        return UserGroupsController.update(group_id)
    else:
        from app.models.user_groups_model import UserGroup
        from app.models.events_model import EventSchedule
        
        group = UserGroup.query.get(group_id)
        if not group:
            flash('Grupa nie istnieje', 'error')
            return redirect(url_for('user_groups.index'))
        
        events = EventSchedule.query.order_by(EventSchedule.event_date.desc()).limit(20).all()
        return render_template('admin/user_group_form.html', group=group, events=events)

@user_groups_bp.route('/admin/user-groups/<int:group_id>/delete', methods=['POST'])
@login_required
def delete(group_id):
    """Usuwanie grupy"""
    return UserGroupsController.delete(group_id)

@user_groups_bp.route('/admin/user-groups/<int:group_id>/members/add', methods=['POST'])
@login_required
def add_member(group_id):
    """Dodawanie członka do grupy"""
    return UserGroupsController.add_member(group_id)

@user_groups_bp.route('/admin/user-groups/<int:group_id>/members/<int:member_id>/remove', methods=['POST'])
@login_required
def remove_member(group_id, member_id):
    """Usuwanie członka z grupy"""
    return UserGroupsController.remove_member(group_id, member_id)
