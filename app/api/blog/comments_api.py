"""
Blog Comments API - comment management
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import BlogComment, BlogPost, User, db
from app.utils.auth_utils import admin_required, admin_required_api
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create Comments API blueprint
comments_api_bp = Blueprint('blog_comments_api', __name__)

@comments_api_bp.route('/blog/comments', methods=['GET'])
@login_required
def get_comments():
    """Get blog comments with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        post_id = request.args.get('post_id', type=int)
        status = request.args.get('status', '', type=str)
        
        query = BlogComment.query
        
        if post_id:
            query = query.filter_by(post_id=post_id)
        
        if status == 'approved':
            query = query.filter_by(is_approved=True)
        elif status == 'pending':
            query = query.filter_by(is_approved=False)
        
        comments = query.order_by(BlogComment.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'comments': [{
                'id': comment.id,
                'author_name': comment.author_name,
                'author_email': comment.author_email,
                'content': comment.content,
                'is_approved': comment.is_approved,
                'is_spam': comment.is_spam,
                'moderation_reason': comment.moderation_reason,
                'moderated_by': comment.moderated_by,
                'moderated_at': comment.moderated_at.isoformat() if comment.moderated_at else None,
                'ip_address': comment.ip_address,
                'browser': comment.browser,
                'operating_system': comment.operating_system,
                'location_country': comment.location_country,
                'location_city': comment.location_city,
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
                'post': {
                    'id': comment.post.id,
                    'title': comment.post.title
                } if comment.post else None,
                'moderator': {
                    'id': comment.moderator.id,
                    'name': comment.moderator.first_name
                } if comment.moderator else None
            } for comment in comments.items],
            'pagination': {
                'page': comments.page,
                'pages': comments.pages,
                'per_page': comments.per_page,
                'total': comments.total,
                'has_next': comments.has_next,
                'has_prev': comments.has_prev
            }
        })
    except Exception as e:
        logger.error(f"❌ Błąd pobierania komentarzy: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@comments_api_bp.route('/blog/comments', methods=['POST'])
@login_required
def create_comment():
    """Create new blog comment"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['post_id', 'author_name', 'author_email', 'content']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Pole {field} jest wymagane'
                }), 400
        
        # Check if post exists
        post = BlogPost.query.get(data['post_id'])
        if not post:
            return jsonify({
                'success': False,
                'message': 'Post nie został znaleziony'
            }), 404
        
        # Create comment
        comment = BlogComment(
            post_id=data['post_id'],
            author_name=data['author_name'],
            author_email=data['author_email'],
            content=data['content'],
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            is_approved=False  # Comments need moderation by default
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Komentarz został dodany i oczekuje na moderację',
            'comment_id': comment.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd tworzenia komentarza: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@comments_api_bp.route('/blog/comments/<int:comment_id>', methods=['GET'])
@login_required
def get_comment(comment_id):
    """Get single blog comment"""
    try:
        comment = BlogComment.query.get_or_404(comment_id)
        
        return jsonify({
            'success': True,
            'comment': {
                'id': comment.id,
                'author_name': comment.author_name,
                'author_email': comment.author_email,
                'content': comment.content,
                'is_approved': comment.is_approved,
                'is_spam': comment.is_spam,
                'moderation_reason': comment.moderation_reason,
                'moderated_by': comment.moderated_by,
                'moderated_at': comment.moderated_at.isoformat() if comment.moderated_at else None,
                'ip_address': comment.ip_address,
                'browser': comment.browser,
                'operating_system': comment.operating_system,
                'location_country': comment.location_country,
                'location_city': comment.location_city,
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
                'post': {
                    'id': comment.post.id,
                    'title': comment.post.title
                } if comment.post else None,
                'moderator': {
                    'id': comment.moderator.id,
                    'name': comment.moderator.first_name
                } if comment.moderator else None
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania komentarza: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@comments_api_bp.route('/blog/comments/<int:comment_id>', methods=['PUT'])
@login_required
@admin_required_api
def update_comment(comment_id):
    """Update blog comment"""
    try:
        comment = BlogComment.query.get_or_404(comment_id)
        data = request.get_json()
        
        # Update fields
        if 'author_name' in data:
            comment.author_name = data['author_name']
        if 'author_email' in data:
            comment.author_email = data['author_email']
        if 'content' in data:
            comment.content = data['content']
        if 'is_approved' in data:
            comment.is_approved = data['is_approved']
        if 'is_spam' in data:
            comment.is_spam = data['is_spam']
        if 'moderation_reason' in data:
            comment.moderation_reason = data['moderation_reason']
        
        # Update moderation info
        comment.moderated_by = current_user.id
        comment.moderated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Komentarz został zaktualizowany'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd aktualizacji komentarza: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@comments_api_bp.route('/blog/comments/<int:comment_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_comment(comment_id):
    """Delete blog comment"""
    try:
        comment = BlogComment.query.get_or_404(comment_id)
        
        db.session.delete(comment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Komentarz został usunięty'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania komentarza: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@comments_api_bp.route('/blog/comments/<int:comment_id>/approve', methods=['POST'])
@login_required
@admin_required_api
def approve_comment(comment_id):
    """Approve blog comment"""
    try:
        comment = BlogComment.query.get_or_404(comment_id)
        
        comment.is_approved = True
        comment.is_spam = False
        comment.moderated_by = current_user.id
        comment.moderated_at = datetime.utcnow()
        comment.moderation_reason = 'Approved'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Komentarz został zatwierdzony'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd zatwierdzania komentarza: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@comments_api_bp.route('/blog/comments/<int:comment_id>/reject', methods=['POST'])
@login_required
@admin_required_api
def reject_comment(comment_id):
    """Reject blog comment"""
    try:
        comment = BlogComment.query.get_or_404(comment_id)
        
        comment.is_approved = False
        comment.moderated_by = current_user.id
        comment.moderated_at = datetime.utcnow()
        comment.moderation_reason = 'Rejected'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Komentarz został odrzucony'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd odrzucania komentarza: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@comments_api_bp.route('/blog/comments/<int:comment_id>/spam', methods=['POST'])
@login_required
@admin_required_api
def mark_comment_spam(comment_id):
    """Mark blog comment as spam"""
    try:
        comment = BlogComment.query.get_or_404(comment_id)
        
        comment.is_spam = True
        comment.is_approved = False
        comment.moderated_by = current_user.id
        comment.moderated_at = datetime.utcnow()
        comment.moderation_reason = 'Marked as spam'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Komentarz został oznaczony jako spam'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd oznaczania komentarza jako spam: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@comments_api_bp.route('/blog/comments/bulk-delete', methods=['POST'])
@login_required
@admin_required_api
def bulk_delete_comments():
    """Bulk delete blog comments"""
    try:
        data = request.get_json()
        comment_ids = data.get('comment_ids', [])
        
        if not comment_ids:
            return jsonify({
                'success': False,
                'message': 'Brak komentarzy do usunięcia'
            }), 400
        
        comments = BlogComment.query.filter(BlogComment.id.in_(comment_ids)).all()
        
        for comment in comments:
            db.session.delete(comment)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {len(comments)} komentarzy'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd masowego usuwania komentarzy: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500




