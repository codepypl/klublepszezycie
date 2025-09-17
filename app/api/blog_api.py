"""
Blog API endpoints
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required
from app.models import BlogPost, BlogCategory, BlogTag, BlogComment, db
from app.utils.auth_utils import admin_required
import logging
import os
from werkzeug.utils import secure_filename

blog_api_bp = Blueprint('blog_api', __name__)

@blog_api_bp.route('/blog/categories', methods=['GET'])
def api_blog_categories():
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
                'parent_id': category.parent_id
            } for category in categories]
        })
    except Exception as e:
        logging.error(f"Error getting blog categories: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/posts', methods=['GET'])
def api_blog_posts():
    """Get blog posts for public use"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        category_id = request.args.get('category_id', type=int)
        tag_id = request.args.get('tag_id', type=int)
        
        query = BlogPost.query.filter_by(is_published=True)
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if tag_id:
            query = query.join(BlogPost.tags).filter(BlogTag.id == tag_id)
        
        posts = query.order_by(BlogPost.published_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'posts': [{
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'excerpt': post.excerpt,
                'content': post.content,
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'author': post.author.first_name + ' ' + post.author.last_name if post.author else 'Unknown',
                'category': {
                    'id': post.category.id,
                    'title': post.category.title,
                    'slug': post.category.slug
                } if post.category else None,
                'tags': [{'id': tag.id, 'name': tag.name, 'slug': tag.slug} for tag in post.tags],
                'featured_image': post.featured_image
            } for post in posts.items],
            'pagination': {
                'page': posts.page,
                'pages': posts.pages,
                'per_page': posts.per_page,
                'total': posts.total,
                'has_next': posts.has_next,
                'has_prev': posts.has_prev
            }
        })
    except Exception as e:
        logging.error(f"Error getting blog posts: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/admin/posts', methods=['GET', 'POST'])
@login_required
def api_blog_admin_posts():
    """Admin blog posts API"""
    if request.method == 'GET':
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            search = request.args.get('search', '', type=str)
            category_id = request.args.get('category_id', type=int)
            status = request.args.get('status', '', type=str)
            
            query = BlogPost.query
            
            if search:
                query = query.filter(
                    db.or_(
                        BlogPost.title.ilike(f'%{search}%'),
                        BlogPost.content.ilike(f'%{search}%')
                    )
                )
            
            if category_id:
                query = query.filter_by(category_id=category_id)
            
            if status == 'published':
                query = query.filter_by(is_published=True)
            elif status == 'draft':
                query = query.filter_by(is_published=False)
            
            posts = query.order_by(BlogPost.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return jsonify({
                'success': True,
                'posts': [{
                    'id': post.id,
                    'title': post.title,
                    'slug': post.slug,
                    'excerpt': post.excerpt,
                    'is_published': post.is_published,
                    'published_at': post.published_at.isoformat() if post.published_at else None,
                    'created_at': post.created_at.isoformat() if post.created_at else None,
                    'author': post.author.first_name + ' ' + post.author.last_name if post.author else 'Unknown',
                    'category': {
                        'id': post.category.id,
                        'title': post.category.title
                    } if post.category else None,
                    'tags': [{'id': tag.id, 'name': tag.name} for tag in post.tags],
                    'featured_image': post.featured_image
                } for post in posts.items],
                'pagination': {
                    'page': posts.page,
                    'pages': posts.pages,
                    'per_page': posts.per_page,
                    'total': posts.total,
                    'has_next': posts.has_next,
                    'has_prev': posts.has_prev
                }
            })
        except Exception as e:
            logging.error(f"Error getting admin blog posts: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            post = BlogPost(
                title=data['title'],
                slug=data.get('slug', ''),
                excerpt=data.get('excerpt', ''),
                content=data['content'],
                is_published=data.get('is_published', False),
                category_id=data.get('category_id'),
                author_id=data.get('author_id'),
                featured_image=data.get('featured_image', '')
            )
            
            if data.get('published_at'):
                post.published_at = data['published_at']
            
            # Add tags
            if data.get('tag_ids'):
                tags = BlogTag.query.filter(BlogTag.id.in_(data['tag_ids'])).all()
                post.tags = tags
            
            db.session.add(post)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Blog post created successfully',
                'post': {
                    'id': post.id,
                    'title': post.title,
                    'slug': post.slug,
                    'is_published': post.is_published
                }
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating blog post: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/admin/posts/<int:post_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_blog_admin_post(post_id):
    """Individual admin blog post API"""
    post = BlogPost.query.get_or_404(post_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'post': {
                    'id': post.id,
                    'title': post.title,
                    'slug': post.slug,
                    'excerpt': post.excerpt,
                    'content': post.content,
                    'is_published': post.is_published,
                    'published_at': post.published_at.isoformat() if post.published_at else None,
                    'created_at': post.created_at.isoformat() if post.created_at else None,
                    'author_id': post.author_id,
                    'category_id': post.category_id,
                    'featured_image': post.featured_image,
                    'tags': [{'id': tag.id, 'name': tag.name} for tag in post.tags]
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'title' in data:
                post.title = data['title']
            if 'slug' in data:
                post.slug = data['slug']
            if 'excerpt' in data:
                post.excerpt = data['excerpt']
            if 'content' in data:
                post.content = data['content']
            if 'is_published' in data:
                post.is_published = data['is_published']
            if 'category_id' in data:
                post.category_id = data['category_id']
            if 'author_id' in data:
                post.author_id = data['author_id']
            if 'featured_image' in data:
                post.featured_image = data['featured_image']
            if 'published_at' in data:
                post.published_at = data['published_at']
            
            # Update tags
            if 'tag_ids' in data:
                tags = BlogTag.query.filter(BlogTag.id.in_(data['tag_ids'])).all()
                post.tags = tags
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Blog post updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(post)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Blog post deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with blog post {post_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/admin/posts/bulk-delete', methods=['POST'])
@login_required
@admin_required
def api_blog_admin_posts_bulk_delete():
    """Bulk delete blog posts"""
    try:
        data = request.get_json()
        post_ids = data.get('post_ids', [])
        
        if not post_ids:
            return jsonify({'success': False, 'message': 'No posts selected'}), 400
        
        deleted_count = 0
        for post_id in post_ids:
            post = BlogPost.query.get(post_id)
            if post:
                db.session.delete(post)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} blog posts'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting blog posts: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/admin/categories', methods=['GET', 'POST'])
@login_required
def api_blog_admin_categories():
    """Admin blog categories API"""
    if request.method == 'GET':
        try:
            categories = BlogCategory.query.order_by(BlogCategory.title).all()
            return jsonify({
                'success': True,
                'categories': [{
                    'id': category.id,
                    'title': category.title,
                    'slug': category.slug,
                    'description': category.description,
                    'parent_id': category.parent_id,
                    'is_active': category.is_active,
                    'created_at': category.created_at.isoformat() if category.created_at else None
                } for category in categories]
            })
        except Exception as e:
            logging.error(f"Error getting blog categories: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            category = BlogCategory(
                title=data['title'],
                slug=data.get('slug', ''),
                description=data.get('description', ''),
                parent_id=data.get('parent_id'),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(category)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Blog category created successfully',
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
            logging.error(f"Error creating blog category: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/admin/categories/<int:category_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_blog_admin_category(category_id):
    """Individual admin blog category API"""
    category = BlogCategory.query.get_or_404(category_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'category': {
                    'id': category.id,
                    'title': category.title,
                    'slug': category.slug,
                    'description': category.description,
                    'parent_id': category.parent_id,
                    'is_active': category.is_active,
                    'created_at': category.created_at.isoformat() if category.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
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
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Blog category updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(category)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Blog category deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with blog category {category_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/admin/categories/bulk-delete', methods=['POST'])
@login_required
@admin_required
def api_blog_admin_categories_bulk_delete():
    """Bulk delete blog categories"""
    try:
        data = request.get_json()
        category_ids = data.get('category_ids', [])
        
        if not category_ids:
            return jsonify({'success': False, 'message': 'No categories selected'}), 400
        
        deleted_count = 0
        for category_id in category_ids:
            category = BlogCategory.query.get(category_id)
            if category:
                db.session.delete(category)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} blog categories'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting blog categories: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/tags', methods=['GET', 'POST'])
@login_required
def api_blog_tags():
    """Blog tags API"""
    if request.method == 'GET':
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
            logging.error(f"Error getting blog tags: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            tag = BlogTag(
                name=data['name'],
                slug=data.get('slug', ''),
                description=data.get('description', '')
            )
            
            db.session.add(tag)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Blog tag created successfully',
                'tag': {
                    'id': tag.id,
                    'name': tag.name,
                    'slug': tag.slug,
                    'description': tag.description
                }
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating blog tag: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/tags/<int:tag_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_blog_tag(tag_id):
    """Individual blog tag API"""
    tag = BlogTag.query.get_or_404(tag_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'tag': {
                    'id': tag.id,
                    'name': tag.name,
                    'slug': tag.slug,
                    'description': tag.description,
                    'created_at': tag.created_at.isoformat() if tag.created_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'name' in data:
                tag.name = data['name']
            if 'slug' in data:
                tag.slug = data['slug']
            if 'description' in data:
                tag.description = data['description']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Blog tag updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(tag)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Blog tag deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with blog tag {tag_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/tags/bulk-delete', methods=['POST'])
@login_required
@admin_required
def api_blog_tags_bulk_delete():
    """Bulk delete blog tags"""
    try:
        data = request.get_json()
        tag_ids = data.get('tag_ids', [])
        
        if not tag_ids:
            return jsonify({'success': False, 'message': 'No tags selected'}), 400
        
        deleted_count = 0
        for tag_id in tag_ids:
            tag = BlogTag.query.get(tag_id)
            if tag:
                db.session.delete(tag)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} blog tags'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting blog tags: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/comments', methods=['GET'])
@login_required
def api_blog_comments():
    """Blog comments API"""
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
                'created_at': comment.created_at.isoformat() if comment.created_at else None,
                'post': {
                    'id': comment.post.id,
                    'title': comment.post.title
                } if comment.post else None
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
        logging.error(f"Error getting blog comments: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/comments/<int:comment_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_blog_comment(comment_id):
    """Individual blog comment API"""
    comment = BlogComment.query.get_or_404(comment_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'comment': {
                    'id': comment.id,
                    'author_name': comment.author_name,
                    'author_email': comment.author_email,
                    'content': comment.content,
                    'is_approved': comment.is_approved,
                    'created_at': comment.created_at.isoformat() if comment.created_at else None,
                    'post_id': comment.post_id
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'author_name' in data:
                comment.author_name = data['author_name']
            if 'author_email' in data:
                comment.author_email = data['author_email']
            if 'content' in data:
                comment.content = data['content']
            if 'is_approved' in data:
                comment.is_approved = data['is_approved']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Blog comment updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(comment)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Blog comment deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with blog comment {comment_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/comments/<int:comment_id>/approve', methods=['POST'])
@login_required
@admin_required
def api_blog_comment_approve(comment_id):
    """Approve blog comment"""
    comment = BlogComment.query.get_or_404(comment_id)
    
    try:
        comment.is_approved = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Comment approved successfully'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error approving comment {comment_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/comments/bulk-delete', methods=['POST'])
@login_required
@admin_required
def api_blog_comments_bulk_delete():
    """Bulk delete blog comments"""
    try:
        data = request.get_json()
        comment_ids = data.get('comment_ids', [])
        
        if not comment_ids:
            return jsonify({'success': False, 'message': 'No comments selected'}), 400
        
        deleted_count = 0
        for comment_id in comment_ids:
            comment = BlogComment.query.get(comment_id)
            if comment:
                db.session.delete(comment)
                deleted_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} blog comments'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error bulk deleting blog comments: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/upload/image', methods=['POST'])
@login_required
def api_upload_image():
    """Upload image for blog posts"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No image file selected'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid conflicts
            import time
            filename = f"{int(time.time())}_{filename}"
            
            upload_folder = os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            
            return jsonify({
                'success': True,
                'message': 'Image uploaded successfully',
                'filename': filename,
                'url': f'/static/uploads/{filename}'
            })
        else:
            return jsonify({'success': False, 'message': 'Invalid file type'}), 400
    
    except Exception as e:
        logging.error(f"Error uploading image: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blog_api_bp.route('/blog/admin/posts/<int:post_id>/images', methods=['GET', 'POST'])
@login_required
def api_blog_post_images(post_id):
    """Blog post images API"""
    post = BlogPost.query.get_or_404(post_id)
    
    try:
        if request.method == 'GET':
            # This would need to be implemented based on your image storage model
            return jsonify({
                'success': True,
                'images': []
            })
        
        elif request.method == 'POST':
            # This would need to be implemented based on your image storage model
            return jsonify({
                'success': True,
                'message': 'Image added successfully'
            })
    
    except Exception as e:
        logging.error(f"Error with blog post images: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/admin/posts/<int:post_id>/images/<int:image_id>', methods=['PUT', 'DELETE'])
@login_required
def api_blog_post_image(post_id, image_id):
    """Individual blog post image API"""
    post = BlogPost.query.get_or_404(post_id)
    
    try:
        if request.method == 'PUT':
            # This would need to be implemented based on your image storage model
            return jsonify({
                'success': True,
                'message': 'Image updated successfully'
            })
        
        elif request.method == 'DELETE':
            # This would need to be implemented based on your image storage model
            return jsonify({
                'success': True,
                'message': 'Image deleted successfully'
            })
    
    except Exception as e:
        logging.error(f"Error with blog post image: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
