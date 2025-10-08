"""
Blog Posts API - post management
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import BlogPost, BlogCategory, BlogTag, BlogComment, BlogPostImage, db
from app.utils.auth_utils import admin_required, admin_required_api
from app.utils.file_utils import cleanup_blog_post_files
import logging
import os
import json
import time
import shutil
from datetime import datetime
from app.utils.timezone_utils import get_local_now
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# Create Posts API blueprint
posts_api_bp = Blueprint('blog_posts_api', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@posts_api_bp.route('/blog/posts', methods=['GET'])
def get_blog_posts():
    """Get blog posts for public use"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        category_id = request.args.get('category_id', type=int)
        tag_id = request.args.get('tag_id', type=int)
        
        query = BlogPost.query.filter_by(status='published')
        
        if category_id:
            query = query.join(BlogPost.categories).filter(BlogCategory.id == category_id)
        
        if tag_id:
            query = query.join(BlogPost.tags).filter(BlogTag.id == tag_id)
        
        posts = query.order_by(BlogPost.published_at.desc().nulls_last()).paginate(
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
                'author': post.author.first_name if post.author else 'Unknown',
                'categories': [{'id': cat.id, 'title': cat.title, 'slug': cat.slug} for cat in post.categories],
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
        logger.error(f"❌ Błąd pobierania postów: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@posts_api_bp.route('/blog/admin/posts', methods=['GET'])
@login_required
@admin_required_api
def get_admin_posts():
    """Get blog posts for admin"""
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
            query = query.join(BlogPost.categories).filter(BlogCategory.id == category_id)
        
        if status == 'published':
            query = query.filter_by(status='published')
        elif status == 'draft':
            query = query.filter_by(status='draft')
        
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
                'status': post.status,
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'created_at': post.created_at.isoformat() if post.created_at else None,
                'author': post.author.first_name if post.author else 'Unknown',
                'categories': [{'id': cat.id, 'title': cat.title} for cat in post.categories],
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
        logger.error(f"❌ Błąd pobierania postów admin: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@posts_api_bp.route('/blog/admin/posts', methods=['POST'])
@login_required
@admin_required_api
def create_post():
    """Create new blog post"""
    try:
        # Handle both JSON and FormData
        if request.is_json:
            data = request.get_json()
        else:
            # Handle FormData
            data = request.form.to_dict()
            # Convert boolean fields
            if 'allow_comments' in data:
                data['allow_comments'] = data['allow_comments'] == 'true'
            if 'is_featured' in data:
                data['is_featured'] = data['is_featured'] == 'true'
            if 'social_facebook' in data:
                data['social_facebook'] = data['social_facebook'] == 'true'
            if 'social_twitter' in data:
                data['social_twitter'] = data['social_twitter'] == 'true'
            if 'social_linkedin' in data:
                data['social_linkedin'] = data['social_linkedin'] == 'true'
            if 'social_instagram' in data:
                data['social_instagram'] = data['social_instagram'] == 'true'
        
        # Validate required fields
        required_fields = ['title', 'content']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Pole {field} jest wymagane'
                }), 400
        
        # Create post
        status = data.get('status', 'draft')
        post = BlogPost(
            title=data['title'],
            content=data['content'],
            excerpt=data.get('excerpt', ''),
            author_id=current_user.id,
            meta_title=data.get('meta_title', ''),
            meta_description=data.get('meta_description', ''),
            status=status,
            is_featured=data.get('is_featured', False),
            allow_comments=data.get('allow_comments', True),
            social_facebook=data.get('social_facebook', False),
            social_twitter=data.get('social_twitter', False),
            social_linkedin=data.get('social_linkedin', False),
            social_instagram=data.get('social_instagram', False)
        )
        
        # Set published_at if creating as published
        if status == 'published':
            post.published_at = get_local_now()
            logger.info(f"✅ Post created as published at {post.published_at}")
        
        # Use slug from frontend or generate simple one if missing
        if data.get('slug'):
            post.slug = data['slug']
        else:
            # Fallback: simple slug generation
            import re
            slug = data['title'].lower()
            slug = re.sub(r'[^\w\s-]', '', slug)
            slug = re.sub(r'[-\s]+', '-', slug)
            slug = slug.strip('-')
            post.slug = slug
        
        # Handle featured image upload
        featured_image_url = data.get('featured_image', '')
        if 'featured_image' in request.files and request.files['featured_image'].filename:
            # Upload featured image file
            featured_image_file = request.files['featured_image']
            if allowed_file(featured_image_file.filename):
                filename = secure_filename(featured_image_file.filename)
                filename = f"{int(time.time())}_{filename}"
                
                # Create blog-specific upload folder structure: media/blog/{post_id}/featured/
                blog_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', 'temp_featured')
                os.makedirs(blog_upload_folder, exist_ok=True)
                
                file_path = os.path.join(blog_upload_folder, filename)
                featured_image_file.save(file_path)
                featured_image_url = f'/static/uploads/blog/temp_featured/{filename}'
                
                # Note: Thumbnail will be created when moving to final location
        
        post.featured_image = featured_image_url
        
        db.session.add(post)
        db.session.flush()  # Get the ID
        
        # Move featured image to proper directory if it was uploaded
        if featured_image_url.startswith('/static/uploads/blog/temp_featured/'):
            _move_featured_image_to_post_folder(post.id, featured_image_url, current_app)
        
        # Add categories
        if 'categories' in data and data['categories']:
            category_ids = data['categories']
            # Handle both string and list formats
            if isinstance(category_ids, str):
                try:
                    category_ids = json.loads(category_ids)
                except:
                    category_ids = [int(x.strip()) for x in category_ids.split(',') if x.strip()]
            categories = BlogCategory.query.filter(BlogCategory.id.in_(category_ids)).all()
            post.categories = categories
        
        # Add tags
        if 'tags' in data and data['tags']:
            tag_data = data['tags']
            # Handle both string and list formats
            if isinstance(tag_data, str):
                try:
                    tag_data = json.loads(tag_data)
                except:
                    tag_data = [x.strip() for x in tag_data.split(',') if x.strip()]
            
            tags = []
            for tag_item in tag_data:
                if isinstance(tag_item, str) and tag_item.strip():
                    # Frontend sends tag names, find or create tag
                    tag_name = tag_item.strip()
                    tag = BlogTag.query.filter_by(name=tag_name).first()
                    if not tag:
                        # Create new tag if it doesn't exist
                        import re
                        slug = re.sub(r'[^a-z0-9-]', '-', tag_item.lower())
                        slug = re.sub(r'-+', '-', slug).strip('-')
                        tag = BlogTag(name=tag_name, slug=slug)
                        db.session.add(tag)
                        db.session.flush()
                    tags.append(tag)
                elif isinstance(tag_item, int):
                    # Backend might send tag IDs
                    tag = BlogTag.query.get(tag_item)
                    if tag:
                        tags.append(tag)
            post.tags = tags
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Post został utworzony',
            'post_id': post.id
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd tworzenia postu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@posts_api_bp.route('/blog/admin/posts/<int:post_id>', methods=['GET'])
@login_required
@admin_required_api
def get_post(post_id):
    """Get single blog post"""
    try:
        post = BlogPost.query.get_or_404(post_id)
        
        return jsonify({
            'success': True,
            'post': {
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'content': post.content,
                'excerpt': post.excerpt,
                'status': post.status,
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'created_at': post.created_at.isoformat() if post.created_at else None,
                'updated_at': post.updated_at.isoformat() if post.updated_at else None,
                'author': post.author.first_name if post.author else 'Unknown',
                'featured_image': post.featured_image,
                'meta_title': post.meta_title,
                'meta_description': post.meta_description,
                'status': post.status,
                'categories': [{'id': cat.id, 'title': cat.title} for cat in post.categories],
                'tags': [{'id': tag.id, 'name': tag.name} for tag in post.tags]
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Błąd pobierania postu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@posts_api_bp.route('/blog/admin/posts/<int:post_id>', methods=['PUT'])
@login_required
@admin_required_api
def update_post(post_id):
    """Update blog post"""
    try:
        post = BlogPost.query.get_or_404(post_id)
        
        # Handle both JSON and FormData
        if request.is_json:
            data = request.get_json()
        else:
            # Handle FormData
            data = request.form.to_dict()
            # Convert boolean fields
            if 'allow_comments' in data:
                data['allow_comments'] = data['allow_comments'] == 'true'
            if 'is_featured' in data:
                data['is_featured'] = data['is_featured'] == 'true'
            if 'social_facebook' in data:
                data['social_facebook'] = data['social_facebook'] == 'true'
            if 'social_twitter' in data:
                data['social_twitter'] = data['social_twitter'] == 'true'
            if 'social_linkedin' in data:
                data['social_linkedin'] = data['social_linkedin'] == 'true'
            if 'social_instagram' in data:
                data['social_instagram'] = data['social_instagram'] == 'true'
        
        # Update fields
        if 'title' in data:
            post.title = data['title']
        if 'content' in data:
            post.content = data['content']
        if 'excerpt' in data:
            post.excerpt = data['excerpt']
        if 'status' in data:
            old_status = post.status
            post.status = data['status']
            
            # Set published_at when status changes to 'published'
            if data['status'] == 'published' and old_status != 'published':
                post.published_at = get_local_now()
                logger.info(f"✅ Post {post_id} published at {post.published_at}")
            elif data['status'] != 'published' and old_status == 'published':
                # Clear published_at when status changes from 'published' to something else
                post.published_at = None
                logger.info(f"✅ Post {post_id} unpublished")
        # Handle featured image upload
        if 'featured_image' in request.files and request.files['featured_image'].filename:
            # Upload featured image file
            featured_image_file = request.files['featured_image']
            if allowed_file(featured_image_file.filename):
                filename = secure_filename(featured_image_file.filename)
                filename = f"{int(time.time())}_{filename}"
                
                # Create post-specific upload folder structure: media/blog/{post_id}/featured/
                post_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', str(post_id), 'featured')
                os.makedirs(post_folder, exist_ok=True)
                
                file_path = os.path.join(post_folder, filename)
                featured_image_file.save(file_path)
                
                # Create thumbnail for featured image
                from app.utils.image_utils import create_featured_thumbnail
                thumbnail_result = create_featured_thumbnail(post_id, filename, current_app.config['UPLOAD_FOLDER'])
                
                if thumbnail_result['success']:
                    logger.info(f"✅ Featured image thumbnail created: {thumbnail_result['thumbnail_url']}")
                else:
                    logger.warning(f"⚠️ Failed to create featured image thumbnail: {thumbnail_result.get('error', 'Unknown error')}")
                
                post.featured_image = f'/static/uploads/blog/{post_id}/featured/{filename}'
        elif 'featured_image' in data:
            post.featured_image = data['featured_image']
        if 'meta_title' in data:
            post.meta_title = data['meta_title']
        if 'meta_description' in data:
            post.meta_description = data['meta_description']
        if 'slug' in data:
            post.slug = data['slug']
        if 'is_featured' in data:
            post.is_featured = data['is_featured']
        if 'allow_comments' in data:
            post.allow_comments = data['allow_comments']
        if 'social_facebook' in data:
            post.social_facebook = data['social_facebook']
        if 'social_twitter' in data:
            post.social_twitter = data['social_twitter']
        if 'social_linkedin' in data:
            post.social_linkedin = data['social_linkedin']
        if 'social_instagram' in data:
            post.social_instagram = data['social_instagram']
        
        # Update categories
        if 'categories' in data and data['categories']:
            category_ids = data['categories']
            # Handle both string and list formats
            if isinstance(category_ids, str):
                try:
                    category_ids = json.loads(category_ids)
                except:
                    category_ids = [int(x.strip()) for x in category_ids.split(',') if x.strip()]
            categories = BlogCategory.query.filter(BlogCategory.id.in_(category_ids)).all()
            post.categories = categories
        
        # Update tags
        if 'tags' in data and data['tags']:
            tag_data = data['tags']
            # Handle both string and list formats
            if isinstance(tag_data, str):
                try:
                    tag_data = json.loads(tag_data)
                except:
                    tag_data = [x.strip() for x in tag_data.split(',') if x.strip()]
            
            tags = []
            for tag_item in tag_data:
                if isinstance(tag_item, str) and tag_item.strip():
                    # Frontend sends tag names, find or create tag
                    tag_name = tag_item.strip()
                    tag = BlogTag.query.filter_by(name=tag_name).first()
                    if not tag:
                        # Create new tag if it doesn't exist
                        import re
                        slug = re.sub(r'[^a-z0-9-]', '-', tag_item.lower())
                        slug = re.sub(r'-+', '-', slug).strip('-')
                        tag = BlogTag(name=tag_name, slug=slug)
                        db.session.add(tag)
                        db.session.flush()
                    tags.append(tag)
                elif isinstance(tag_item, int):
                    # Backend might send tag IDs
                    tag = BlogTag.query.get(tag_item)
                    if tag:
                        tags.append(tag)
            post.tags = tags
        
        post.updated_at = get_local_now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Post został zaktualizowany'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd aktualizacji postu {post_id}: {e}", exc_info=True)
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Błąd aktualizacji: {str(e)}'}), 500

@posts_api_bp.route('/blog/admin/posts/<int:post_id>', methods=['DELETE'])
@login_required
@admin_required_api
def delete_post(post_id):
    """Delete blog post"""
    try:
        post = BlogPost.query.get_or_404(post_id)
        
        # Clean up files
        cleanup_blog_post_files(post)
        
        # Delete post
        db.session.delete(post)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Post został usunięty'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd usuwania postu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@posts_api_bp.route('/blog/admin/posts/bulk-delete', methods=['POST'])
@login_required
@admin_required_api
def bulk_delete_posts():
    """Bulk delete blog posts"""
    try:
        data = request.get_json()
        post_ids = data.get('post_ids', [])
        
        if not post_ids:
            return jsonify({
                'success': False,
                'message': 'Brak postów do usunięcia'
            }), 400
        
        posts = BlogPost.query.filter(BlogPost.id.in_(post_ids)).all()
        
        for post in posts:
            # Clean up files
            cleanup_blog_post_files(post)
            db.session.delete(post)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Usunięto {len(posts)} postów'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Błąd masowego usuwania postów: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

def _move_featured_image_to_post_folder(post_id, temp_url, app):
    """Move featured image from temp folder to post-specific folder"""
    try:
        
        # Extract filename from temp URL
        filename = os.path.basename(temp_url)
        
        # Source path (temp folder)
        temp_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'blog', 'temp_featured')
        source_path = os.path.join(temp_folder, filename)
        
        # Destination path (post-specific folder)
        post_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'blog', str(post_id), 'featured')
        os.makedirs(post_folder, exist_ok=True)
        dest_path = os.path.join(post_folder, filename)
        
        # Move file
        if os.path.exists(source_path):
            shutil.move(source_path, dest_path)
            
            # Create thumbnail for featured image
            from app.utils.image_utils import create_featured_thumbnail
            thumbnail_result = create_featured_thumbnail(post_id, filename, app.config['UPLOAD_FOLDER'])
            
            if thumbnail_result['success']:
                logger.info(f"✅ Featured image thumbnail created: {thumbnail_result['thumbnail_url']}")
            else:
                logger.warning(f"⚠️ Failed to create featured image thumbnail: {thumbnail_result.get('error', 'Unknown error')}")
            
            # Update post.featured_image URL
            post = BlogPost.query.get(post_id)
            if post:
                post.featured_image = f'/static/uploads/blog/{post_id}/featured/{filename}'
                db.session.commit()
                
            logger.info(f"✅ Moved featured image to: {dest_path}")
        else:
            logger.warning(f"⚠️ Source file not found: {source_path}")
            
    except Exception as e:
        logger.error(f"❌ Error moving featured image: {e}")

def _move_gallery_image_to_post_folder(post_id, temp_url, app):
    """Move gallery image from temp folder to post-specific folder"""
    try:
        
        # Extract filename from temp URL
        filename = os.path.basename(temp_url)
        
        # Source path (temp folder)
        temp_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'blog', 'temp_gallery')
        source_path = os.path.join(temp_folder, filename)
        
        # Destination path (post-specific folder)
        post_folder = os.path.join(app.config['UPLOAD_FOLDER'], 'blog', str(post_id), 'gallery')
        os.makedirs(post_folder, exist_ok=True)
        dest_path = os.path.join(post_folder, filename)
        
        # Move file
        if os.path.exists(source_path):
            shutil.move(source_path, dest_path)
            
            # Update image.image_url
            image = BlogPostImage.query.filter_by(image_url=temp_url).first()
            if image:
                image.image_url = f'/static/uploads/blog/{post_id}/gallery/{filename}'
                db.session.commit()
                
            logger.info(f"✅ Moved gallery image to: {dest_path}")
        else:
            logger.warning(f"⚠️ Source file not found: {source_path}")
            
    except Exception as e:
        logger.error(f"❌ Error moving gallery image: {e}")
