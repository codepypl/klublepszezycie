"""
Menu API endpoints
"""
from flask import Blueprint, request, jsonify
from app.models import MenuItem, db
from app.utils.auth_utils import admin_required_api, login_required_api
import logging

menu_api_bp = Blueprint('menu_api', __name__)

@menu_api_bp.route('/menu', methods=['GET', 'POST', 'DELETE'])
@login_required_api
def api_menu():
    """Menu API"""
    if request.method == 'GET':
        try:
            menu_items = MenuItem.query.order_by(MenuItem.order.asc()).all()
            return jsonify({
                'success': True,
                'menu_items': [{
                    'id': item.id,
                    'title': item.title,
                    'url': item.url,
                    'blog_url': item.blog_url,
                    'blog': item.blog,
                    'order': item.order,
                    'is_active': item.is_active,
                    'created_at': item.created_at.isoformat() if item.created_at else None
                } for item in menu_items]
            })
        except Exception as e:
            logging.error(f"Error getting menu items: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            menu_item = MenuItem(
                title=data['title'],
                url=data.get('url', ''),
                blog_url=data.get('blog_url', ''),
                blog=data.get('blog', False),
                order=data.get('order', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(menu_item)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Menu item created successfully',
                'menu_item': {
                    'id': menu_item.id,
                    'title': menu_item.title,
                    'url': menu_item.url,
                    'blog_url': menu_item.blog_url,
                    'blog': menu_item.blog,
                    'order': menu_item.order,
                    'is_active': menu_item.is_active
                }
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating menu item: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'DELETE':
        try:
            data = request.get_json()
            menu_item_ids = data.get('menu_item_ids', data.get('ids', []))
            
            if not menu_item_ids:
                return jsonify({'success': False, 'message': 'No menu items selected'}), 400
            
            deleted_count = 0
            for menu_item_id in menu_item_ids:
                menu_item = MenuItem.query.get(menu_item_id)
                if menu_item:
                    db.session.delete(menu_item)
                    deleted_count += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Successfully deleted {deleted_count} menu items'
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error bulk deleting menu items: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@menu_api_bp.route('/menu/<int:item_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required_api
def api_menu_item(item_id):
    """Individual menu item API"""
    menu_item = MenuItem.query.get_or_404(item_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'menu_item': {
                    'id': menu_item.id,
                    'title': menu_item.title,
                    'url': menu_item.url,
                    'blog_url': menu_item.blog_url,
                    'blog': menu_item.blog,
                    'order': menu_item.order,
                    'is_active': menu_item.is_active,
                    'created_at': menu_item.created_at.isoformat() if menu_item.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'title' in data:
                menu_item.title = data['title']
            if 'url' in data:
                menu_item.url = data['url']
            if 'blog_url' in data:
                menu_item.blog_url = data['blog_url']
            if 'blog' in data:
                menu_item.blog = data['blog']
            if 'order' in data:
                menu_item.order = data['order']
            if 'is_active' in data:
                menu_item.is_active = data['is_active']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Menu item updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(menu_item)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Menu item deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with menu item {item_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@menu_api_bp.route('/bulk-delete/menu', methods=['POST'])
@login_required_api
@admin_required_api
def api_bulk_delete_menu():
    """Bulk delete menu items"""
    try:
        data = request.get_json()
        menu_item_ids = data.get('menu_item_ids', data.get('ids', []))
        
        if not menu_item_ids:
            return jsonify({'success': False, 'message': 'No menu items selected'}), 400
        
        deleted_count = 0
        for menu_item_id in menu_item_ids:
            menu_item = MenuItem.query.get(menu_item_id)
            if menu_item:
                db.session.delete(menu_item)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} menu items'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting menu items: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
