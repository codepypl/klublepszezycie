"""
Events Registrations API - registration management
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import EventSchedule, User, db
from app.utils.auth_utils import admin_required, admin_required_api
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create Registrations API blueprint
registrations_api_bp = Blueprint('events_registrations_main_api', __name__)

@registrations_api_bp.route('/registrations/<int:registration_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_registration(registration_id):
    """Delete event registration"""
    try:
        user = User.query.get(registration_id)
        if not user or user.account_type != 'event_registration':
            return jsonify({
                'success': False,
                'message': 'Rejestracja nie została znaleziona'
            }), 404
        
        # Store data before deletion for group cleanup
        # Get user's event registrations
        from app.models import EventRegistration
        registrations = EventRegistration.query.filter_by(
            user_id=user.id,
            is_active=True
        ).all()
        
        if not registrations:
            return jsonify({'success': False, 'message': 'Brak aktywnych rejestracji'}), 404
        
        # Unregister from all events
        for reg in registrations:
            reg.is_active = False
        
        email = user.email
        
        # Reset user account type
        user.account_type = 'user'
        db.session.commit()
        
        # Asynchronicznie synchronizuj grupy wszystkich wydarzeń dla tego użytkownika
        try:
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            
            # Synchronizuj grupy dla każdego wydarzenia
            for reg in registrations:
                success, message = group_manager.async_sync_event_group(reg.event_id)
            if success:
                logger.info(f"✅ Zsynchronizowano grupę wydarzenia po usunięciu rejestracji")
            else:
                logger.warning(f"⚠️ Błąd synchronizacji grupy wydarzenia: {message}")
        except Exception as e:
            logger.warning(f"⚠️ Błąd synchronizacji grupy wydarzenia: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Rejestracja została usunięta pomyślnie'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania rejestracji: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@registrations_api_bp.route('/bulk-delete/registrations', methods=['POST'])
@login_required
@admin_required_api
def bulk_delete_registrations():
    """Bulk delete event registrations"""
    try:
        data = request.get_json()
        registration_ids = data.get('registration_ids', data.get('ids', []))
        
        if not registration_ids:
            return jsonify({
                'success': False,
                'message': 'Brak rejestracji do usunięcia'
            }), 400
        
        # Get users to delete
        users = User.query.filter(
            User.id.in_(registration_ids),
            User.account_type == 'event_registration'
        ).all()
        
        if not users:
            return jsonify({
                'success': False,
                'message': 'Nie znaleziono rejestracji do usunięcia'
            }), 404
        
        # Store event IDs for group synchronization and unregister users
        from app.models import EventRegistration
        event_ids = set()
        deleted_count = 0
        
        for user in users:
            # Get user's event registrations
            user_registrations = EventRegistration.query.filter_by(
                user_id=user.id,
                is_active=True
            ).all()
            
            # Collect event IDs and deactivate registrations
            for reg in user_registrations:
                event_ids.add(reg.event_id)
                reg.is_active = False
            
            user.account_type = 'user'
            deleted_count += 1
        
        db.session.commit()
        
        # Synchronize groups for affected events
        try:
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            
            for event_id in event_ids:
                success, message = group_manager.async_sync_event_group(event_id)
                if success:
                    logger.info(f"✅ Zsynchronizowano grupę wydarzenia {event_id}")
                else:
                    logger.warning(f"⚠️ Błąd synchronizacji grupy wydarzenia {event_id}: {message}")
        except Exception as e:
            logger.warning(f"⚠️ Błąd synchronizacji grup wydarzeń: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} rejestracji'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd masowego usuwania rejestracji: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
