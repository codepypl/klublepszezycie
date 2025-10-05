"""
User Groups API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app import db
from app.models.user_groups_model import UserGroup, UserGroupMember
from app.models.events_model import EventSchedule
from app.models.user_model import User
from sqlalchemy import desc
import json

user_groups_bp = Blueprint('user_groups_api', __name__)

@user_groups_bp.route('/user-groups', methods=['GET'])
@login_required
def get_user_groups():
    """Pobiera listę grup użytkowników"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = UserGroup.query.order_by(UserGroup.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Lista domyślnych grup (nie można ich usuwać)
        default_groups = ['club_members']
        
        group_list = []
        for group in pagination.items:
            # Get event info for event-based groups
            event_id = None
            event_title = None
            
            if group.group_type == 'event_based':
                if group.event_id:
                    event_id = group.event_id
                    if group.event:
                        event_title = group.event.title
                elif group.criteria:
                    try:
                        criteria = json.loads(group.criteria)
                        event_id = criteria.get('event_id')
                        if event_id:
                            event = EventSchedule.query.get(event_id)
                            if event:
                                event_title = event.title
                    except (json.JSONDecodeError, KeyError):
                        pass
            
            group_list.append({
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'group_type': group.group_type,
                'member_count': group.member_count,
                'is_active': group.is_active,
                'is_default': group.group_type in default_groups,
                'created_at': group.created_at.isoformat(),
                'event_id': event_id,
                'event_title': event_title
            })
        
        return jsonify({
            'success': True, 
            'groups': group_list,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': pagination.per_page
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@user_groups_bp.route('/user-groups', methods=['POST'])
@login_required
def create_user_group():
    """Tworzy nową grupę użytkowników"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'Nazwa grupy jest wymagana'}), 400
        
        # Check if group with same name exists
        existing_group = UserGroup.query.filter_by(name=data['name']).first()
        if existing_group:
            return jsonify({'success': False, 'error': 'Grupa o tej nazwie już istnieje'}), 400
        
        # Create new group
        group = UserGroup(
            name=data['name'],
            description=data.get('description', ''),
            group_type=data.get('group_type', 'manual'),
            event_id=data.get('event_id'),
            criteria=data.get('criteria'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(group)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Grupa utworzona pomyślnie',
            'group': {
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'group_type': group.group_type,
                'is_active': group.is_active
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@user_groups_bp.route('/user-groups/<int:group_id>', methods=['GET'])
@login_required
def get_user_group(group_id):
    """Pobiera szczegóły grupy użytkowników"""
    try:
        group = UserGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupa nie istnieje'}), 404
        
        # Get event info
        event_info = None
        if group.event_id and group.event:
            event_info = {
                'id': group.event.id,
                'title': group.event.title,
                'event_date': group.event.event_date.isoformat() if group.event.event_date else None
            }
        
        # Get members
        members = []
        for member in group.members.all():  # .all() bo members to dynamic query
            member_data = {
                'id': member.id,
                'member_type': member.member_type,
                'is_active': member.is_active,
                'joined_at': member.joined_at.isoformat() if member.joined_at else None
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
        
        return jsonify({
            'success': True,
            'group': {
                'id': group.id,
                'name': group.name,
                'description': group.description,
                'group_type': group.group_type,
                'member_count': group.member_count,
                'is_active': group.is_active,
                'created_at': group.created_at.isoformat(),
                'event_info': event_info,
                'members': members
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@user_groups_bp.route('/user-groups/<int:group_id>', methods=['PUT'])
@login_required
def update_user_group(group_id):
    """Aktualizuje grupę użytkowników"""
    try:
        group = UserGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupa nie istnieje'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            group.name = data['name']
        if 'description' in data:
            group.description = data['description']
        if 'group_type' in data:
            group.group_type = data['group_type']
        if 'event_id' in data:
            group.event_id = data['event_id']
        if 'criteria' in data:
            group.criteria = data['criteria']
        if 'is_active' in data:
            group.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Grupa zaktualizowana pomyślnie'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@user_groups_bp.route('/user-groups/<int:group_id>', methods=['DELETE'])
@login_required
def delete_user_group(group_id):
    """Usuwa grupę użytkowników"""
    try:
        group = UserGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupa nie istnieje'}), 404
        
        # Check if group is default (cannot be deleted)
        default_groups = ['club_members']
        if group.group_type in default_groups:
            return jsonify({'success': False, 'error': 'Nie można usunąć grupy domyślnej'}), 400
        
        db.session.delete(group)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Grupa usunięta pomyślnie'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@user_groups_bp.route('/user-groups/<int:group_id>/members', methods=['GET'])
@login_required
def get_group_members(group_id):
    """Pobiera członków grupy"""
    try:
        group = UserGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupa nie istnieje'}), 404
        
        members = []
        for member in group.members.all():  # .all() bo members to dynamic query
            member_data = {
                'id': member.id,
                'member_type': member.member_type,
                'is_active': member.is_active,
                'joined_at': member.joined_at.isoformat() if member.joined_at else None
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
        
        return jsonify({
            'success': True,
            'members': members
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@user_groups_bp.route('/user-groups/<int:group_id>/members', methods=['POST'])
@login_required
def add_group_member(group_id):
    """Dodaje członka do grupy"""
    try:
        group = UserGroup.query.get(group_id)
        if not group:
            return jsonify({'success': False, 'error': 'Grupa nie istnieje'}), 404
        
        data = request.get_json()
        user_id = data.get('user_id')
        email = data.get('email')
        name = data.get('name')
        
        if not user_id and not email:
            return jsonify({'success': False, 'error': 'Musisz podać user_id lub email'}), 400
        
        # Check if member already exists
        if user_id:
            existing = UserGroupMember.query.filter_by(group_id=group_id, user_id=user_id).first()
        else:
            existing = UserGroupMember.query.filter_by(group_id=group_id, email=email).first()
        
        if existing:
            return jsonify({'success': False, 'error': 'Użytkownik już jest w tej grupie'}), 400
        
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
        
        return jsonify({
            'success': True,
            'message': 'Członek dodany pomyślnie'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@user_groups_bp.route('/user-groups/<int:group_id>/members/<int:member_id>', methods=['DELETE'])
@login_required
def remove_group_member(group_id, member_id):
    """Usuwa członka z grupy"""
    try:
        member = UserGroupMember.query.filter_by(id=member_id, group_id=group_id).first()
        if not member:
            return jsonify({'success': False, 'error': 'Członek nie istnieje'}), 404
        
        group = member.group
        db.session.delete(member)
        
        # Update member count
        group.member_count = group.members.count()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Członek usunięty pomyślnie'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@user_groups_api_bp.route('/user-groups/cleanup-duplicates', methods=['POST'])
@login_required
@admin_required_api
def cleanup_duplicate_event_groups():
    """Usuwa duplikaty grup wydarzeń"""
    try:
        from app.services.group_manager import GroupManager
        group_manager = GroupManager()
        
        success, message = group_manager.cleanup_duplicate_event_groups()
        
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        logging.error(f"Error cleaning up duplicate event groups: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
