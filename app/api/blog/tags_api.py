"""
Blog Tags API - tag management
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import BlogTag, db
from app.utils.auth_utils import admin_required, admin_required_api
import logging

logger = logging.getLogger(__name__)

# Create Tags API blueprint
tags_api_bp = Blueprint('blog_tags_api', __name__)

@tags_api_bp.route('/blog/tags/all', methods=['GET'])
@login_required
def get_all_tags():
    """Get all blog tags"""
    try:
        tags = BlogTag.query.filter_by(is_active=True).order_by(BlogTag.name).all()
        
        return jsonify({
            'success': True,
            'tags': [{
                'id': tag.id,
                'name': tag.name,
                'slug': tag.slug,
                'description': tag.description,
                'posts_count': tag.posts_count
            } for tag in tags]
        })
    except Exception as e:
        logger.error(f"❌ Błąd pobierania tagów: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@tags_api_bp.route('/blog/tags', methods=['GET'])
@login_required
def get_tags():
    """Get blog tags with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        tags = BlogTag.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'tags': [{
                'id': tag.id,
                'name': tag.name,
                'slug': tag.slug,
                'description': tag.description,
                'posts_count': tag.posts_count,
                'created_at': tag.created_at.isoformat() if tag.created_at else None
            } for tag in tags.items],
            'pagination': {
                'page': tags.page,
                'pages': tags.pages,
                'per_page': tags.per_page,
                'total': tags.total,
                'has_next': tags.has_next,
                'has_prev': tags.has_prev
            }
        })
    except Exception as e:
        logger.error(f"❌ Błąd pobierania tagów: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@tags_api_bp.route('/blog/tags', methods=['POST'])
@login_required
@admin_required_api
def create_tag():
    """Create new blog tag"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'Nazwa tagu jest wymagana'
            }), 400
        
        tag = BlogTag(
            name=data['name'],
            slug=data.get('slug', ''),
            description=data.get('description', ''),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(tag)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tag został dodany pomyślnie',
            'tag': {
                'id': tag.id,
                'name': tag.name,
                'slug': tag.slug,
                'description': tag.description
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd tworzenia tagu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@tags_api_bp.route('/blog/tags/<int:tag_id>', methods=['GET'])
@login_required
def get_tag(tag_id):
    """Get single blog tag"""
    try:
        tag = BlogTag.query.get_or_404(tag_id)
        
        return jsonify({
            'success': True,
            'tag': {
                'id': tag.id,
                'name': tag.name,
                'slug': tag.slug,
                'description': tag.description,
                'is_active': tag.is_active,
                'posts_count': tag.posts_count,
                'created_at': tag.created_at.isoformat() if tag.created_at else None,
                'updated_at': tag.updated_at.isoformat() if tag.updated_at else None
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania tagu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@tags_api_bp.route('/blog/tags/<int:tag_id>', methods=['PUT'])
@login_required
@admin_required_api
def update_tag(tag_id):
    """Update blog tag"""
    try:
        tag = BlogTag.query.get_or_404(tag_id)
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            tag.name = data['name']
        if 'slug' in data:
            tag.slug = data['slug']
        if 'description' in data:
            tag.description = data['description']
        if 'is_active' in data:
            tag.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tag został zaktualizowany'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd aktualizacji tagu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@tags_api_bp.route('/blog/tags/<int:tag_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_tag(tag_id):
    """Delete blog tag"""
    try:
        logger.info(f"🔍 Attempting to delete tag {tag_id}")
        logger.info(f"🔍 Current user: {current_user.email if current_user.is_authenticated else 'Not authenticated'}")
        logger.info(f"🔍 User is admin: {current_user.is_admin_role() if current_user.is_authenticated else 'N/A'}")
        
        tag = BlogTag.query.get_or_404(tag_id)
        
        logger.info(f"🔍 Tag found: {tag.name}, posts_count: {tag.posts_count}")
        
        # Check if tag has posts
        if tag.posts_count > 0:
            logger.warning(f"⚠️ Cannot delete tag {tag_id} - has {tag.posts_count} posts")
            return jsonify({
                'success': False,
                'message': f'Nie można usunąć tagu "{tag.name}" - jest przypisany do {tag.posts_count} postów'
            }), 400
        
        logger.info(f"✅ Deleting tag {tag_id}: {tag.name}")
        db.session.delete(tag)
        db.session.commit()
        
        logger.info(f"✅ Tag {tag_id} deleted successfully")
        return jsonify({
            'success': True,
            'message': f'Tag "{tag.name}" został usunięty'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania tagu {tag_id}: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': str(e)}), 500

@tags_api_bp.route('/blog/admin/tags/bulk-delete', methods=['POST'])
@login_required
@admin_required_api
def bulk_delete_tags():
    """Bulk delete blog tags"""
    try:
        data = request.get_json()
        tag_ids = data.get('tag_ids', [])
        
        if not tag_ids:
            return jsonify({
                'success': False,
                'message': 'Brak tagów do usunięcia'
            }), 400
        
        deleted_count = 0
        for tag_id in tag_ids:
            tag = BlogTag.query.get(tag_id)
            if tag:
                # Check if tag can be deleted
                if tag.posts_count == 0:
                    db.session.delete(tag)
                    deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {deleted_count} tagów'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd masowego usuwania tagów: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
