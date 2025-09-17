"""
Social Media API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import SocialLink, db
from app.utils.auth import admin_required
import logging

social_api_bp = Blueprint('social_api', __name__)

@social_api_bp.route('/social', methods=['GET', 'POST'])
@login_required
def api_social():
    """Social media links API"""
    if request.method == 'GET':
        try:
            social_links = SocialLink.query.order_by(SocialLink.order.asc()).all()
            return jsonify({
                'success': True,
                'social_links': [{
                    'id': link.id,
                    'platform': link.platform,
                    'url': link.url,
                    'icon': link.icon,
                    'order': link.order,
                    'is_active': link.is_active,
                    'created_at': link.created_at.isoformat() if link.created_at else None
                } for link in social_links]
            })
        except Exception as e:
            logging.error(f"Error getting social links: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            social_link = SocialLink(
                platform=data['platform'],
                url=data['url'],
                icon=data.get('icon', ''),
                order=data.get('order', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(social_link)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Social link created successfully',
                'social_link': {
                    'id': social_link.id,
                    'platform': social_link.platform,
                    'url': social_link.url,
                    'icon': social_link.icon,
                    'order': social_link.order,
                    'is_active': social_link.is_active
                }
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating social link: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@social_api_bp.route('/social/<int:link_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_social_link(link_id):
    """Individual social link API"""
    social_link = SocialLink.query.get_or_404(link_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'social_link': {
                    'id': social_link.id,
                    'platform': social_link.platform,
                    'url': social_link.url,
                    'icon': social_link.icon,
                    'order': social_link.order,
                    'is_active': social_link.is_active,
                    'created_at': social_link.created_at.isoformat() if social_link.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'platform' in data:
                social_link.platform = data['platform']
            if 'url' in data:
                social_link.url = data['url']
            if 'icon' in data:
                social_link.icon = data['icon']
            if 'order' in data:
                social_link.order = data['order']
            if 'is_active' in data:
                social_link.is_active = data['is_active']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Social link updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(social_link)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Social link deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with social link {link_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@social_api_bp.route('/social/bulk-delete', methods=['DELETE'])
@login_required
@admin_required
def api_social_bulk_delete():
    """Bulk delete social links"""
    try:
        data = request.get_json()
        link_ids = data.get('link_ids', [])
        
        if not link_ids:
            return jsonify({'success': False, 'message': 'No social links selected'}), 400
        
        deleted_count = 0
        for link_id in link_ids:
            social_link = SocialLink.query.get(link_id)
            if social_link:
                db.session.delete(social_link)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} social links'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting social links: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@social_api_bp.route('/social/public', methods=['GET'])
def api_social_public():
    """Get active social links for public use"""
    try:
        social_links = SocialLink.query.filter_by(is_active=True).order_by(SocialLink.order.asc()).all()
        return jsonify({
            'success': True,
            'social_links': [{
                'id': link.id,
                'platform': link.platform,
                'url': link.url,
                'icon': link.icon,
                'order': link.order
            } for link in social_links]
        })
    except Exception as e:
        logging.error(f"Error getting public social links: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
