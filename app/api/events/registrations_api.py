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
        event_id = user.event_id
        email = user.email
        
        # Reset user account type
        user.account_type = 'user'
        user.event_id = None
        db.session.commit()
        
        # Asynchronicznie synchronizuj grupę wydarzenia
        try:
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            
            # Wywołaj asynchroniczną synchronizację grupy wydarzenia
            success, message = group_manager.async_sync_event_group(event_id)
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
        
        # Store event IDs for group synchronization
        event_ids = set()
        for user in users:
            if user.event_id:
                event_ids.add(user.event_id)
        
        # Reset user account types
        deleted_count = 0
        for user in users:
            user.account_type = 'user'
            user.event_id = None
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
