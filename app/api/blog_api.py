"""
Blog API endpoints
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import BlogPost, BlogCategory, BlogTag, BlogComment, BlogPostImage, db
from app.utils.auth_utils import admin_required, admin_required_api
from app.utils.file_utils import cleanup_blog_post_files
import logging
import os
import json
from datetime import datetime
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
                'parent_id': category.parent_id,
                'full_path': category.full_path
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
                query = query.join(BlogPost.categories).filter(BlogCategory.id == category_id)
            
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
            logging.error(f"Error getting admin blog posts: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            # Handle both JSON and FormData
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                # Handle FormData
                data = request.form.to_dict()
                
                # Parse JSON fields from FormData
                if data.get('categories'):
                    try:
                        data['categories'] = json.loads(data['categories'])
                    except (json.JSONDecodeError, TypeError):
                        data['categories'] = []
                
                if data.get('tags'):
                    try:
                        data['tags'] = json.loads(data['tags'])
                    except (json.JSONDecodeError, TypeError):
                        data['tags'] = []
                
                # Convert boolean fields
                # Don't override status if it's already set from form
                if 'status' not in data:
                    data['status'] = 'published' if data.get('is_published') == 'true' else 'draft'
                data['allow_comments'] = data.get('allow_comments') == 'true'
                
                # Handle featured_image file upload
                featured_image_url = data.get('featured_image', '')
                if 'featured_image' in request.files:
                    file = request.files['featured_image']
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        import time
                        filename = f"{int(time.time())}_{filename}"
                        
                        # Create blog-specific upload folder structure for featured images
                        # We'll use a temporary ID for new posts, will be updated after post creation
                        temp_id = data.get('temp_id', 'temp')
                        featured_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', 'article', temp_id, 'featured')
                        os.makedirs(featured_folder, exist_ok=True)
                        
                        file_path = os.path.join(featured_folder, filename)
                        file.save(file_path)
                        featured_image_url = f'/static/uploads/blog/article/{temp_id}/featured/{filename}'
            
            post = BlogPost(
                title=data['title'],
                slug=data.get('slug', ''),
                excerpt=data.get('excerpt', ''),
                content=data['content'],
                status=data.get('status', 'draft'),
                author_id=current_user.id,
                featured_image=featured_image_url,
                allow_comments=data.get('allow_comments', True)
            )
            
            if data.get('published_at'):
                post.published_at = data['published_at']
            elif data.get('status') == 'published' and not post.published_at:
                from datetime import datetime
                post.published_at = datetime.utcnow()
            
            # Add categories
            if data.get('categories') and len(data['categories']) > 0:
                categories = BlogCategory.query.filter(BlogCategory.id.in_(data['categories'])).all()
                post.categories = categories
            
            # Add tags - handle both tag names and IDs
            if data.get('tags') and len(data['tags']) > 0:
                tags = []
                for tag_data in data['tags']:
                    if isinstance(tag_data, str):
                        # Tag name provided, find or create tag
                        tag = BlogTag.query.filter_by(name=tag_data).first()
                        if not tag:
                            # Create new tag
                            tag = BlogTag(
                                name=tag_data,
                                slug=tag_data.lower().replace(' ', '-'),
                                is_active=True
                            )
                            db.session.add(tag)
                            db.session.flush()  # Flush to get the ID
                        tags.append(tag)
                    elif isinstance(tag_data, int):
                        # Tag ID provided, find by ID
                        tag = BlogTag.query.get(tag_data)
                        if tag:
                            tags.append(tag)
                post.tags = tags
            else:
                # Clear all tags if empty array or no tags provided
                post.tags = []
            
            db.session.add(post)
            db.session.commit()
            
            # Move files from temp folder to proper post folder if needed
            if featured_image_url and 'temp' in featured_image_url:
                new_featured_url = featured_image_url.replace('temp', str(post.id))
                new_featured_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', 'article', str(post.id), 'featured')
                old_featured_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', 'article', 'temp', 'featured')
                
                # Create new directory
                os.makedirs(new_featured_path, exist_ok=True)
                
                # Move file
                filename = os.path.basename(featured_image_url)
                old_file_path = os.path.join(old_featured_path, filename)
                new_file_path = os.path.join(new_featured_path, filename)
                
                if os.path.exists(old_file_path):
                    import shutil
                    shutil.move(old_file_path, new_file_path)
                    # Remove temp directory if empty
                    try:
                        os.rmdir(old_featured_path)
                        os.rmdir(os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', 'article', 'temp'))
                    except:
                        pass
                    
                    # Update post with correct URL
                    post.featured_image = new_featured_url
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
    # Check if user is still authenticated
    if not current_user.is_authenticated:
        return jsonify({
            'success': False,
            'message': 'Sesja wygasła. Zaloguj się ponownie.',
            'requires_login': True
        }), 401
    
    try:
        post = BlogPost.query.get(post_id)
        if not post:
            return jsonify({
                'success': False,
                'message': f'Post o ID {post_id} nie został znaleziony'
            }), 404
    except Exception as e:
        logging.error(f"Error querying post {post_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Błąd podczas wyszukiwania posta: {str(e)}'
        }), 500
    
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
                    'status': post.status,
                    'is_published': post.is_published,
                    'allow_comments': post.allow_comments,
                    'published_at': post.published_at.isoformat() if post.published_at else None,
                    'created_at': post.created_at.isoformat() if post.created_at else None,
                    'author_id': post.author_id,
                    'categories': [{'id': cat.id, 'title': cat.title} for cat in post.categories],
                    'featured_image': post.featured_image,
                    'tags': [{'id': tag.id, 'name': tag.name} for tag in post.tags]
                }
            })
        
        elif request.method == 'PUT':
            # Handle both JSON and FormData
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                # Handle FormData
                data = request.form.to_dict()
                
                # Parse JSON fields from FormData
                if data.get('categories'):
                    try:
                        data['categories'] = json.loads(data['categories'])
                    except (json.JSONDecodeError, TypeError):
                        data['categories'] = []
                
                if data.get('tags'):
                    try:
                        data['tags'] = json.loads(data['tags'])
                    except (json.JSONDecodeError, TypeError):
                        data['tags'] = []
                
                # Convert boolean fields
                # Don't override status if it's already set from form
                if 'status' not in data:
                    data['status'] = 'published' if data.get('is_published') == 'true' else 'draft'
                data['allow_comments'] = data.get('allow_comments') == 'true'
                
                # Handle featured_image file upload
                if 'featured_image' in request.files:
                    file = request.files['featured_image']
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        import time
                        filename = f"{int(time.time())}_{filename}"
                        
                        # Create blog-specific upload folder structure for featured images
                        featured_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', 'article', str(post_id), 'featured')
                        os.makedirs(featured_folder, exist_ok=True)
                        
                        file_path = os.path.join(featured_folder, filename)
                        file.save(file_path)
                        data['featured_image'] = f'/static/uploads/blog/article/{post_id}/featured/{filename}'
            
            if 'title' in data:
                post.title = data['title']
            if 'slug' in data:
                post.slug = data['slug']
            if 'excerpt' in data:
                post.excerpt = data['excerpt']
            if 'content' in data:
                post.content = data['content']
            if 'status' in data:
                post.status = data['status']
                # Set published_at when status changes to published
                if data['status'] == 'published' and not post.published_at:
                    from datetime import datetime
                    post.published_at = datetime.utcnow()
            if 'allow_comments' in data:
                post.allow_comments = data['allow_comments']
            # Update categories
            if 'categories' in data:
                if data['categories'] and len(data['categories']) > 0:
                    categories = BlogCategory.query.filter(BlogCategory.id.in_(data['categories'])).all()
                    post.categories = categories
                else:
                    post.categories = []
            # Don't allow changing author_id in updates
            if 'featured_image' in data:
                post.featured_image = data['featured_image']
            if 'published_at' in data:
                post.published_at = data['published_at']
            
            # Update tags - handle both tag names and IDs
            if 'tags' in data:
                if data['tags'] and len(data['tags']) > 0:
                    tags = []
                    for tag_data in data['tags']:
                        if isinstance(tag_data, str):
                            # Tag name provided, find or create tag
                            tag = BlogTag.query.filter_by(name=tag_data).first()
                            if not tag:
                                # Create new tag
                                tag = BlogTag(
                                    name=tag_data,
                                    slug=tag_data.lower().replace(' ', '-'),
                                    is_active=True
                                )
                                db.session.add(tag)
                                db.session.flush()  # Flush to get the ID
                            tags.append(tag)
                        elif isinstance(tag_data, int):
                            # Tag ID provided, find by ID
                            tag = BlogTag.query.get(tag_data)
                            if tag:
                                tags.append(tag)
                    post.tags = tags
                else:
                    post.tags = []
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Blog post updated successfully'
            })
        
        elif request.method == 'DELETE':
            # Clean up associated files before deleting the post
            cleanup_result = cleanup_blog_post_files(post)
            
            # Delete the post from database
            db.session.delete(post)
            db.session.commit()
            
            # Log cleanup results
            logging.info(f"Blog post {post_id} deleted. File cleanup: {cleanup_result}")
            
            return jsonify({
                'success': True,
                'message': 'Blog post deleted successfully',
                'files_cleaned': cleanup_result
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with blog post {post_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/admin/posts/bulk-delete', methods=['POST'])
@login_required
@admin_required_api
def api_blog_admin_posts_bulk_delete():
    """Bulk delete blog posts"""
    try:
        data = request.get_json()
        post_ids = data.get('post_ids', data.get('ids', []))
        
        if not post_ids:
            return jsonify({'success': False, 'message': 'No posts selected'}), 400
        
        deleted_count = 0
        cleanup_results = []
        
        for post_id in post_ids:
            post = BlogPost.query.get(post_id)
            if post:
                # Clean up associated files before deleting the post
                cleanup_result = cleanup_blog_post_files(post)
                cleanup_results.append({
                    'post_id': post_id,
                    'post_title': post.title,
                    'cleanup': cleanup_result
                })
                
                db.session.delete(post)
                deleted_count += 1
        
        db.session.commit()
        
        # Log cleanup results
        logging.info(f"Bulk deleted {deleted_count} blog posts. Cleanup results: {cleanup_results}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} blog posts',
            'cleanup_results': cleanup_results
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
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            pagination = BlogCategory.query.order_by(BlogCategory.title).paginate(
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
                is_active=data.get('is_active', True),
                sort_order=data.get('sort_order', 0)
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
@admin_required_api
def api_blog_admin_categories_bulk_delete():
    """Bulk delete blog categories"""
    try:
        data = request.get_json()
        category_ids = data.get('category_ids', data.get('ids', []))
        
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

@blog_api_bp.route('/blog/tags/all', methods=['GET'])
@login_required
def api_blog_tags_all():
    """Get all blog tags for selectors"""
    try:
        tags = BlogTag.query.filter_by(is_active=True).order_by(BlogTag.name).all()
        return jsonify({
            'success': True,
            'tags': [{
                'id': tag.id,
                'name': tag.name,
                'slug': tag.slug
            } for tag in tags]
        })
    except Exception as e:
        logging.error(f"Error getting all blog tags: {str(e)}")
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

@blog_api_bp.route('/blog/admin/tags/bulk-delete', methods=['POST'])
@login_required
@admin_required_api
def api_blog_tags_bulk_delete():
    """Bulk delete blog tags"""
    try:
        data = request.get_json()
        tag_ids = data.get('tag_ids', data.get('ids', []))
        
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

@blog_api_bp.route('/blog/comments', methods=['GET', 'POST'])
@login_required
def api_blog_comments():
    """Blog comments API"""
    if request.method == 'GET':
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
                        'name': comment.moderator.name
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
            logging.error(f"Error getting blog comments: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['post_id', 'author_name', 'author_email', 'content']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'success': False, 'message': f'Pole {field} jest wymagane'}), 400
            
            # Create comment using the controller
            from app.blueprints.blog_controller import BlogController
            result = BlogController.create_blog_comment(
                post_id=data['post_id'],
                name=data['author_name'],
                email=data['author_email'],
                content=data['content'],
                parent_id=data.get('parent_id')
            )
            
            if result['success']:
                # If it's a reply and should be auto-approved
                if data.get('parent_id') and data.get('is_approved', False):
                    comment = BlogComment.query.get(result['comment_id'])
                    if comment:
                        comment.is_approved = True
                        comment.moderated_by = current_user.id
                        comment.moderated_at = datetime.utcnow()
                        db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': result['message'],
                    'comment_id': result['comment_id']
                })
            else:
                return jsonify({'success': False, 'message': result['error']}), 400
                
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating blog comment: {str(e)}")
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
                    'is_spam': comment.is_spam,
                    'parent_id': comment.parent_id,
                    'ip_address': comment.ip_address,
                    'browser': comment.browser,
                    'operating_system': comment.operating_system,
                    'location_country': comment.location_country,
                    'location_city': comment.location_city,
                    'created_at': comment.created_at.isoformat() if comment.created_at else None,
                    'post_id': comment.post_id,
                    'post': {
                        'id': comment.post.id,
                        'title': comment.post.title,
                        'slug': comment.post.slug
                    } if comment.post else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'author_name' in data:
                comment.author_name = data['author_name']
            if 'author_email' in data:
                comment.author_email = data['author_email']
            # Content is not editable - remove from data if present
            if 'content' in data:
                del data['content']
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
        comment.moderated_by = current_user.id
        comment.moderated_at = datetime.utcnow()
        comment.moderation_reason = None  # Clear any previous reason
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Comment approved successfully'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error approving comment {comment_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/comments/<int:comment_id>/reject', methods=['POST'])
@login_required
@admin_required
def api_blog_comment_reject(comment_id):
    """Reject blog comment with reason"""
    comment = BlogComment.query.get_or_404(comment_id)
    
    try:
        data = request.get_json()
        reason = data.get('reason', '').strip()
        
        if not reason:
            return jsonify({'success': False, 'message': 'Uzasadnienie jest wymagane'}), 400
        
        comment.is_approved = False
        comment.moderated_by = current_user.id
        comment.moderated_at = datetime.utcnow()
        comment.moderation_reason = reason
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Comment rejected successfully'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error rejecting comment {comment_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/comments/<int:comment_id>/spam', methods=['POST'])
@login_required
@admin_required
def api_blog_comment_spam(comment_id):
    """Mark comment as spam"""
    comment = BlogComment.query.get_or_404(comment_id)
    
    try:
        data = request.get_json()
        reason = data.get('reason', 'Oznaczono jako spam').strip()
        
        comment.is_spam = True
        comment.is_approved = False
        comment.moderated_by = current_user.id
        comment.moderated_at = datetime.utcnow()
        comment.moderation_reason = reason
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Comment marked as spam successfully'
        })
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error marking comment {comment_id} as spam: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/comments/bulk-delete', methods=['POST'])
@login_required
@admin_required_api
def api_blog_comments_bulk_delete():
    """Bulk delete blog comments"""
    try:
        data = request.get_json()
        comment_ids = data.get('comment_ids', data.get('ids', []))
        
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
            
            # Create blog-specific upload folder structure
            blog_upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog')
            os.makedirs(blog_upload_folder, exist_ok=True)
            
            file_path = os.path.join(blog_upload_folder, filename)
            file.save(file_path)
            
            return jsonify({
                'success': True,
                'message': 'Image uploaded successfully',
                'filename': filename,
                'url': f'/static/uploads/blog/{filename}'
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
            images = BlogPostImage.query.filter_by(post_id=post_id, is_active=True).order_by(BlogPostImage.order.asc()).all()
            return jsonify({
                'success': True,
                'images': [{
                    'id': image.id,
                    'image_url': image.image_url,
                    'alt_text': image.alt_text,
                    'caption': image.caption,
                    'order': image.order,
                    'created_at': image.created_at.isoformat() if image.created_at else None
                } for image in images]
            })
        
        elif request.method == 'POST':
            # Handle both JSON and FormData
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                # Handle FormData
                data = request.form.to_dict()
                
                # Handle image file upload
                if 'image_file' in request.files:
                    file = request.files['image_file']
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        import time
                        filename = f"{int(time.time())}_{filename}"
                        
                        # Create blog-specific upload folder structure for gallery
                        gallery_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', 'article', str(post_id), 'gallery')
                        os.makedirs(gallery_folder, exist_ok=True)
                        
                        file_path = os.path.join(gallery_folder, filename)
                        file.save(file_path)
                        data['image_url'] = f'/static/uploads/blog/article/{post_id}/gallery/{filename}'
            
            # Validate required fields
            if not data.get('image_url'):
                return jsonify({'success': False, 'message': 'Image URL is required'}), 400
            
            image = BlogPostImage(
                post_id=post_id,
                image_url=data['image_url'],
                alt_text=data.get('alt_text', ''),
                caption=data.get('caption', ''),
                order=data.get('order', 0),
                is_active=True
            )
            
            db.session.add(image)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Image added successfully',
                'image': {
                    'id': image.id,
                    'image_url': image.image_url,
                    'alt_text': image.alt_text,
                    'caption': image.caption,
                    'order': image.order
                }
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with blog post images: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/admin/posts/<int:post_id>/images/<int:image_id>', methods=['PUT', 'DELETE'])
@login_required
def api_blog_post_image(post_id, image_id):
    """Individual blog post image API"""
    post = BlogPost.query.get_or_404(post_id)
    image = BlogPostImage.query.filter_by(id=image_id, post_id=post_id).first_or_404()
    
    try:
        if request.method == 'PUT':
            # Handle both JSON and FormData
            if request.content_type == 'application/json':
                data = request.get_json()
            else:
                # Handle FormData
                data = request.form.to_dict()
                
                # Handle image file upload
                if 'image_file' in request.files:
                    file = request.files['image_file']
                    if file and file.filename and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        import time
                        filename = f"{int(time.time())}_{filename}"
                        
                        # Create blog-specific upload folder structure for gallery
                        gallery_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'blog', 'article', str(post_id), 'gallery')
                        os.makedirs(gallery_folder, exist_ok=True)
                        
                        file_path = os.path.join(gallery_folder, filename)
                        file.save(file_path)
                        data['image_url'] = f'/static/uploads/blog/article/{post_id}/gallery/{filename}'
            
            # Update image fields
            if 'image_url' in data:
                image.image_url = data['image_url']
            if 'alt_text' in data:
                image.alt_text = data['alt_text']
            if 'caption' in data:
                image.caption = data['caption']
            if 'order' in data:
                image.order = data['order']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Image updated successfully',
                'image': {
                    'id': image.id,
                    'image_url': image.image_url,
                    'alt_text': image.alt_text,
                    'caption': image.caption,
                    'order': image.order
                }
            })
        
        elif request.method == 'DELETE':
            # Hard delete - actually delete the image from database and file system
            try:
                # Delete the file from storage
                if image.image_url:
                    logging.info(f"Attempting to delete image file: {image.image_url}")
                    
                    if image.image_url.startswith('/static/'):
                        # Remove leading / and use the path directly
                        relative_path = image.image_url[1:]  # Remove leading /
                        file_path = os.path.join(current_app.root_path, relative_path)
                        logging.info(f"Constructed file path: {file_path}")
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            logging.info(f"Successfully deleted image file: {file_path}")
                        else:
                            logging.warning(f"Image file does not exist: {file_path}")
                    elif image.image_url.startswith('static/'):
                        file_path = os.path.join(current_app.root_path, image.image_url)
                        logging.info(f"Constructed file path: {file_path}")
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            logging.info(f"Successfully deleted image file: {file_path}")
                        else:
                            logging.warning(f"Image file does not exist: {file_path}")
                    else:
                        logging.warning(f"Image URL does not start with /static/ or static/: {image.image_url}")
            except Exception as e:
                logging.error(f"Error deleting image file: {str(e)}")
                logging.error(f"Image URL: {image.image_url}")
            
            # Delete from database
            db.session.delete(image)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Zdjęcie zostało usunięte z galerii i serwera',
                'details': {
                    'image_url': image.image_url,
                    'file_deleted': True
                }
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with blog post image: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@blog_api_bp.route('/blog/admin/posts/<int:post_id>/featured-image', methods=['DELETE'])
@login_required
def api_blog_post_delete_featured_image(post_id):
    """Delete featured image from blog post"""
    post = BlogPost.query.get_or_404(post_id)
    
    try:
        if post.featured_image:
            featured_image_url = post.featured_image  # Store URL before deletion
            logging.info(f"Attempting to delete featured image: {featured_image_url}")
            
            # Delete the file from storage
            file_deleted = False
            try:
                if featured_image_url.startswith('/static/'):
                    # Remove leading / and use the path directly
                    relative_path = featured_image_url[1:]  # Remove leading /
                    file_path = os.path.join(current_app.root_path, relative_path)
                    logging.info(f"Constructed file path (with /): {file_path}")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        file_deleted = True
                        logging.info(f"Successfully deleted featured image file: {file_path}")
                    else:
                        logging.warning(f"File does not exist: {file_path}")
                elif featured_image_url.startswith('static/'):
                    file_path = os.path.join(current_app.root_path, featured_image_url)
                    logging.info(f"Constructed file path (without /): {file_path}")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        file_deleted = True
                        logging.info(f"Successfully deleted featured image file: {file_path}")
                    else:
                        logging.warning(f"File does not exist: {file_path}")
                else:
                    logging.warning(f"Featured image path does not start with /static/ or static/: {featured_image_url}")
            except Exception as e:
                logging.error(f"Error deleting featured image file: {str(e)}")
                logging.error(f"Featured image path: {featured_image_url}")
            
            # Clear the featured_image field
            post.featured_image = None
            db.session.commit()
            
            logging.info(f"Deleted featured image for post {post_id}")
            return jsonify({
                'success': True,
                'message': 'Zdjęcie główne zostało usunięte z artykułu i serwera',
                'details': {
                    'featured_image_url': featured_image_url,
                    'file_deleted': file_deleted
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Artykuł nie ma zdjęcia głównego'
            }), 400
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting featured image for post {post_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
