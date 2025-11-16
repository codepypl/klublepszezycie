"""
Social Media routes
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.blueprints.social_controller import SocialController

social_bp = Blueprint('social', __name__)

@social_bp.route('/social')
@login_required
def index():
    """Social media management page"""
    data = SocialController.get_social_links()
    
    if not data['success']:
        flash(f'Błąd: {data["error"]}', 'error')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/social.html', social_links=data['links'])

@social_bp.route('/social/create', methods=['POST'])
@login_required
def create():
    """Create new social media link"""
    try:
        data = request.get_json()
        
        platform = data.get('platform', '').strip()
        url = data.get('url', '').strip()
        icon = data.get('icon', '').strip() or data.get('icon_class', '').strip()  # Support both icon and icon_class
        target = data.get('target', '_blank')
        is_active = data.get('is_active', True)
        show_on_post_card = data.get('show_on_post_card', False)
        order = data.get('order', 0)
        
        result = SocialController.create_social_link(platform, url, icon, target, is_active, show_on_post_card, order)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'social_link': {
                    'id': result['link'].id,
                    'platform': result['link'].platform,
                    'url': result['link'].url,
                    'icon': getattr(result['link'], 'icon', ''),
                    'target': getattr(result['link'], 'target', '_blank'),
                    'is_active': result['link'].is_active,
                    'show_on_post_card': getattr(result['link'], 'show_on_post_card', False),
                    'order': result['link'].order
                }
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@social_bp.route('/social/edit/<int:link_id>', methods=['POST'])
@login_required
def edit(link_id):
    """Edit social media link"""
    try:
        data = request.get_json()
        
        platform = data.get('platform', '').strip()
        url = data.get('url', '').strip()
        icon = data.get('icon', '').strip() or data.get('icon_class', '').strip()  # Support both icon and icon_class
        target = data.get('target', '_blank')
        is_active = data.get('is_active', True)
        show_on_post_card = data.get('show_on_post_card', False)
        order = data.get('order', 0)
        
        result = SocialController.update_social_link(link_id, platform, url, icon, target, is_active, show_on_post_card, order)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'social_link': {
                    'id': result['link'].id,
                    'platform': result['link'].platform,
                    'url': result['link'].url,
                    'icon': getattr(result['link'], 'icon', ''),
                    'target': getattr(result['link'], 'target', '_blank'),
                    'is_active': result['link'].is_active,
                    'show_on_post_card': getattr(result['link'], 'show_on_post_card', False),
                    'order': result['link'].order
                }
            })
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@social_bp.route('/social/delete/<int:link_id>', methods=['POST'])
@login_required
def delete(link_id):
    """Delete social media link"""
    result = SocialController.delete_social_link(link_id)
    
    if result['success']:
        return jsonify({'success': True, 'message': result['message']})
    else:
        return jsonify({'error': result['error']}), 400

@social_bp.route('/social/toggle/<int:link_id>', methods=['POST'])
@login_required
def toggle_status(link_id):
    """Toggle social media link status"""
    result = SocialController.toggle_social_link_status(link_id)
    
    if result['success']:
        return jsonify({
            'success': True,
            'message': result['message'],
            'is_active': result['link'].is_active
        })
    else:
        return jsonify({'error': result['error']}), 400

@social_bp.route('/social/reorder', methods=['POST'])
@login_required
def reorder():
    """Reorder social media links"""
    try:
        data = request.get_json()
        link_orders = data.get('orders', {})
        
        result = SocialController.reorder_social_links(link_orders)
        
        if result['success']:
            return jsonify({'success': True, 'message': result['message']})
        else:
            return jsonify({'error': result['error']}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500