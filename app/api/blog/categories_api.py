"""
Blog Categories API - category management
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import BlogCategory, db
from app.utils.auth_utils import admin_required, admin_required_api
import logging
from sqlalchemy.orm import joinedload

logger = logging.getLogger(__name__)

# Create Categories API blueprint
categories_api_bp = Blueprint('blog_categories_api', __name__)

@categories_api_bp.route('/blog/categories', methods=['GET'])
def get_blog_categories():
    """Get blog categories for public use"""
    try:
        categories = BlogCategory.query.filter_by(is_active=True).order_by(BlogCategory.title).all()
        return jsonify({
            'success': True,
            'categories': [{
                'id': category.id,
                'title': category.title,
                'slug': category.slug,
                'description': category.description,
                'parent_id': category.parent_id,
                'full_path': category.full_path
            } for category in categories]
        })
    except Exception as e:
        logger.error(f"❌ Błąd pobierania kategorii: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@categories_api_bp.route('/blog/admin/categories', methods=['GET'])
@login_required
@admin_required_api
def get_admin_categories():
    """Get blog categories for admin"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = BlogCategory.query.options(joinedload(BlogCategory.posts)).order_by(BlogCategory.title).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        categories = [{
            'id': category.id,
            'title': category.title,
            'slug': category.slug,
            'description': category.description,
            'parent_id': category.parent_id,
            'parent': {
                'id': category.parent.id,
                'title': category.parent.title
            } if category.parent else None,
            'is_active': category.is_active,
            'posts_count': category.posts_count,
            'posts': [{'id': post.id, 'title': post.title} for post in category.posts],
            'created_at': category.created_at.isoformat() if category.created_at else None
        } for category in pagination.items]
        
        return jsonify({
            'success': True,
            'categories': categories,
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'total': pagination.total,
                'per_page': pagination.per_page
            }
        })
    except Exception as e:
        logger.error(f"❌ Błąd pobierania kategorii admin: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@categories_api_bp.route('/blog/admin/categories', methods=['POST'])
@login_required
@admin_required_api
def create_category():
    """Create new blog category"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({
                'success': False,
                'message': 'Tytuł kategorii jest wymagany'
            }), 400
        
        category = BlogCategory(
            title=data['title'],
            slug=data.get('slug', ''),
            description=data.get('description', ''),
            parent_id=data.get('parent_id'),
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0)
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Kategoria została dodana pomyślnie',
            'category': {
                'id': category.id,
                'title': category.title,
                'slug': category.slug,
                'description': category.description,
                'parent_id': category.parent_id,
                'is_active': category.is_active
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd tworzenia kategorii: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@categories_api_bp.route('/blog/admin/categories/<int:category_id>', methods=['GET'])
@login_required
@admin_required_api
def get_category(category_id):
    """Get single blog category"""
    try:
        category = BlogCategory.query.get_or_404(category_id)
        
        return jsonify({
            'success': True,
            'category': {
                'id': category.id,
                'title': category.title,
                'slug': category.slug,
                'description': category.description,
                'parent_id': category.parent_id,
                'is_active': category.is_active,
                'sort_order': category.sort_order,
                'created_at': category.created_at.isoformat() if category.created_at else None,
                'updated_at': category.updated_at.isoformat() if category.updated_at else None,
                'posts_count': category.posts_count,
                'parent': {
                    'id': category.parent.id,
                    'title': category.parent.title
                } if category.parent else None
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania kategorii: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@categories_api_bp.route('/blog/admin/categories/<int:category_id>', methods=['PUT'])
@login_required
@admin_required_api
def update_category(category_id):
    """Update blog category"""
    try:
        category = BlogCategory.query.get_or_404(category_id)
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            category.title = data['title']
        if 'slug' in data:
            category.slug = data['slug']
        if 'description' in data:
            category.description = data['description']
        if 'parent_id' in data:
            category.parent_id = data['parent_id']
        if 'is_active' in data:
            category.is_active = data['is_active']
        if 'sort_order' in data:
            category.sort_order = data['sort_order']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Kategoria została zaktualizowana'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd aktualizacji kategorii: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@categories_api_bp.route('/blog/admin/categories/<int:category_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_category(category_id):
    """Delete blog category"""
    try:
        category = BlogCategory.query.get_or_404(category_id)
        
        # Check if category has posts
        if category.posts_count > 0:
            return jsonify({
                'success': False,
                'message': 'Nie można usunąć kategorii z postami'
            }), 400
        
        # Check if category has children
        children = BlogCategory.query.filter_by(parent_id=category_id).count()
        if children > 0:
            return jsonify({
                'success': False,
                'message': 'Nie można usunąć kategorii z podkategoriami'
            }), 400
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Kategoria została usunięta'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania kategorii: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@categories_api_bp.route('/blog/admin/categories/bulk-delete', methods=['POST'])
@login_required
@admin_required_api
def bulk_delete_categories():
    """Bulk delete blog categories"""
    try:
        data = request.get_json()
        category_ids = data.get('category_ids', [])
        
        if not category_ids:
            return jsonify({
                'success': False,
                'message': 'Brak kategorii do usunięcia'
            }), 400
        
        deleted_count = 0
        for category_id in category_ids:
            category = BlogCategory.query.get(category_id)
            if category:
                # Check if category can be deleted
                if category.posts_count == 0:
                    children = BlogCategory.query.filter_by(parent_id=category_id).count()
                    if children == 0:
                        db.session.delete(category)
                        deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} kategorii'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd masowego usuwania kategorii: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


