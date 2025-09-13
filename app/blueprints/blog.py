"""
Blog blueprint - full-featured blog system
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import db, BlogCategory, BlogPost, BlogTag, BlogComment, BlogPostImage, User
from datetime import datetime
import re
import logging

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text

blog_bp = Blueprint('blog', __name__, url_prefix='/blog')

@blog_bp.route('/')
def index():
    """Blog homepage - list of posts"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get published posts
    posts_query = BlogPost.query.filter_by(status='published').order_by(BlogPost.published_at.desc())
    
    # Filter by category if specified
    category_slug = request.args.get('category')
    if category_slug:
        category = BlogCategory.query.filter_by(slug=category_slug, is_active=True).first()
        if category:
            posts_query = posts_query.join(BlogPost.categories).filter(BlogCategory.id == category.id)
        else:
            flash('Kategoria nie została znaleziona', 'error')
            return redirect(url_for('blog.index'))
    
    # Filter by tag if specified
    tag_slug = request.args.get('tag')
    if tag_slug:
        tag = BlogTag.query.filter_by(slug=tag_slug, is_active=True).first()
        if tag:
            posts_query = posts_query.join(BlogPost.tags).filter(BlogTag.id == tag.id)
        else:
            flash('Tag nie został znaleziony', 'error')
            return redirect(url_for('blog.index'))
    
    # Search functionality
    search = request.args.get('search')
    if search:
        posts_query = posts_query.filter(
            db.or_(
                BlogPost.title.contains(search),
                BlogPost.content.contains(search),
                BlogPost.excerpt.contains(search)
            )
        )
    
    posts = posts_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get categories for sidebar
    categories = BlogCategory.query.filter_by(is_active=True, parent_id=None).order_by(BlogCategory.sort_order).all()
    
    # Get popular tags
    popular_tags = BlogTag.query.filter_by(is_active=True).order_by(BlogTag.name).limit(10).all()
    
    # Get recent posts
    recent_posts = BlogPost.query.filter_by(status='published').order_by(BlogPost.published_at.desc()).limit(5).all()
    
    # Get all database data dynamically (includes footer_settings, active_social_links, menu_items)
    from app.blueprints.public import get_database_data
    db_data = get_database_data()
    
    return render_template('blog/index.html',
                         posts=posts,
                         categories=categories,
                         popular_tags=popular_tags,
                         recent_posts=recent_posts,
                         current_category=category_slug,
                         current_tag=tag_slug,
                         search_query=search,
                         **db_data)

@blog_bp.route('/post/<slug>')
def post_detail(slug):
    """Single blog post detail"""
    post = BlogPost.query.filter_by(slug=slug, status='published').first_or_404()
    
    # Get approved comments
    comments = post.comments.filter_by(is_approved=True).order_by(BlogComment.created_at.desc()).all()
    
    # Get post images
    images = BlogPostImage.query.filter_by(post_id=post.id).order_by(BlogPostImage.order.asc()).all()
    
    # Get related posts
    related_posts = post.related_posts
    
    # Get categories for sidebar
    categories = BlogCategory.query.filter_by(is_active=True, parent_id=None).order_by(BlogCategory.sort_order).all()
    
    # Get popular tags
    popular_tags = BlogTag.query.filter_by(is_active=True).order_by(BlogTag.name).limit(10).all()
    
    # Get all database data dynamically (includes footer_settings, active_social_links, menu_items)
    from app.blueprints.public import get_database_data
    db_data = get_database_data()
    
    return render_template('blog/post_detail.html',
                         post=post,
                         comments=comments,
                         images=images,
                         related_posts=related_posts,
                         categories=categories,
                         popular_tags=popular_tags,
                         **db_data)

@blog_bp.route('/category/<slug>')
def category_detail(slug):
    """Category detail page"""
    category = BlogCategory.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get posts in this category and subcategories
    category_ids = [category.id]
    for child in category.children:
        if child.is_active:
            category_ids.append(child.id)
    
    posts = BlogPost.query.join(BlogPost.categories).filter(
        BlogCategory.id.in_(category_ids),
        BlogPost.status == 'published'
    ).order_by(BlogPost.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get categories for sidebar
    categories = BlogCategory.query.filter_by(is_active=True, parent_id=None).order_by(BlogCategory.sort_order).all()
    
    # Get popular tags
    popular_tags = BlogTag.query.filter_by(is_active=True).order_by(BlogTag.name).limit(10).all()
    
    # Get all database data dynamically (includes footer_settings, active_social_links, menu_items)
    from app.blueprints.public import get_database_data
    db_data = get_database_data()
    
    return render_template('blog/category_detail.html',
                         category=category,
                         posts=posts,
                         categories=categories,
                         popular_tags=popular_tags,
                         **db_data)

@blog_bp.route('/tag/<slug>')
def tag_detail(slug):
    """Tag detail page"""
    tag = BlogTag.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    posts = BlogPost.query.join(BlogPost.tags).filter(
        BlogTag.id == tag.id,
        BlogPost.status == 'published'
    ).order_by(BlogPost.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get categories for sidebar
    categories = BlogCategory.query.filter_by(is_active=True, parent_id=None).order_by(BlogCategory.sort_order).all()
    
    # Get popular tags
    popular_tags = BlogTag.query.filter_by(is_active=True).order_by(BlogTag.name).limit(10).all()
    
    # Get all database data dynamically (includes footer_settings, active_social_links, menu_items)
    from app.blueprints.public import get_database_data
    db_data = get_database_data()
    
    return render_template('blog/tag_detail.html',
                         tag=tag,
                         posts=posts,
                         categories=categories,
                         popular_tags=popular_tags,
                         **db_data)

@blog_bp.route('/comment', methods=['POST'])
def add_comment():
    """Add comment to blog post"""
    try:
        data = request.get_json()
        
        post_id = data.get('post_id')
        author_name = data.get('author_name', '').strip()
        author_email = data.get('author_email', '').strip()
        author_website = data.get('author_website', '').strip()
        content = data.get('content', '').strip()
        
        # Validation
        if not post_id or not author_name or not author_email or not content:
            return jsonify({'success': False, 'message': 'Wszystkie pola są wymagane'}), 400
        
        # Check if post exists and allows comments
        post = BlogPost.query.get(post_id)
        if not post or not post.allow_comments:
            return jsonify({'success': False, 'message': 'Komentarze są wyłączone dla tego artykułu'}), 400
        
        # Create comment
        comment = BlogComment(
            post_id=post_id,
            author_name=author_name,
            author_email=author_email,
            author_website=author_website,
            content=content,
            is_approved=False  # Require moderation
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Komentarz został dodany i oczekuje na moderację'
        })
        
    except Exception as e:
        logging.error(f"Error adding comment: {str(e)}")
        return jsonify({'success': False, 'message': 'Wystąpił błąd podczas dodawania komentarza'}), 500

@blog_bp.route('/search')
def search():
    """Search blog posts"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return redirect(url_for('blog.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    posts = BlogPost.query.filter(
        BlogPost.status == 'published',
        db.or_(
            BlogPost.title.contains(query),
            BlogPost.content.contains(query),
            BlogPost.excerpt.contains(query)
        )
    ).order_by(BlogPost.published_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get categories for sidebar
    categories = BlogCategory.query.filter_by(is_active=True, parent_id=None).order_by(BlogCategory.sort_order).all()
    
    # Get popular tags
    popular_tags = BlogTag.query.filter_by(is_active=True).order_by(BlogTag.name).limit(10).all()
    
    # Get all database data dynamically (includes footer_settings, active_social_links, menu_items)
    from app.blueprints.public import get_database_data
    db_data = get_database_data()
    
    return render_template('blog/search.html',
                         posts=posts,
                         query=query,
                         categories=categories,
                         popular_tags=popular_tags,
                         **db_data)

# Admin routes for blog management

@blog_bp.route('/admin/posts', methods=['GET', 'POST'])
@login_required
def admin_posts():
    """Blog posts management"""
    if not current_user.is_admin:
        flash('Brak uprawnień do tej strony', 'error')
        return redirect(url_for('public.index'))
    
    if request.method == 'POST':
        # Handle form submission
        try:
            data = request.form.to_dict()
            
            # Convert string values to appropriate types
            if 'allow_comments' in data:
                data['allow_comments'] = data['allow_comments'] == 'on'
            else:
                data['allow_comments'] = False
            
            # Validation
            if not data.get('title') or not data.get('slug') or not data.get('content'):
                flash('Tytuł, slug i treść są wymagane', 'error')
                return redirect(url_for('blog.admin_posts'))
            
            # Check if slug already exists
            existing = BlogPost.query.filter_by(slug=data['slug']).first()
            if existing:
                flash('Artykuł z tym slug już istnieje', 'error')
                return redirect(url_for('blog.admin_posts'))
            
            # Create post
            post = BlogPost(
                title=data['title'],
                slug=data['slug'],
                excerpt=data.get('excerpt', ''),
                content=data['content'],
                status=data.get('status', 'draft'),
                allow_comments=data.get('allow_comments', True),
                author_id=current_user.id
            )
            
            # Set published_at if status is published
            if data.get('status') == 'published':
                post.published_at = datetime.utcnow()
            
            db.session.add(post)
            db.session.commit()
            
            # Handle categories
            if 'categories' in data and data['categories']:
                category_ids = [int(id) for id in data['categories'] if id]
                categories = BlogCategory.query.filter(BlogCategory.id.in_(category_ids)).all()
                post.categories = categories
            
            # Handle tags
            if 'tags' in data and data['tags']:
                tag_names = [tag.strip() for tag in data['tags'].split(',') if tag.strip()]
                for tag_name in tag_names:
                    tag = BlogTag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = BlogTag(name=tag_name, slug=slugify(tag_name))
                        db.session.add(tag)
                    post.tags.append(tag)
            
            db.session.commit()
            
            flash('Artykuł został utworzony pomyślnie', 'success')
            return redirect(url_for('blog.admin_posts'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Błąd podczas tworzenia artykułu: {str(e)}', 'error')
            return redirect(url_for('blog.admin_posts'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    posts = BlogPost.query.order_by(BlogPost.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get categories for the form
    categories = BlogCategory.query.filter_by(is_active=True).order_by(BlogCategory.title).all()
    
    return render_template('blog/admin/posts.html', posts=posts, categories=categories)

@blog_bp.route('/admin/categories', methods=['GET', 'POST'])
@login_required
def admin_categories():
    """Blog categories management"""
    if not current_user.is_admin:
        flash('Brak uprawnień do tej strony', 'error')
        return redirect(url_for('public.index'))
    
    if request.method == 'POST':
        # Handle form submission
        try:
            data = request.form.to_dict()
            
            # Convert string values to appropriate types
            if 'is_active' in data:
                data['is_active'] = data['is_active'] == 'on'
            if 'sort_order' in data:
                try:
                    data['sort_order'] = int(data['sort_order'])
                except (ValueError, TypeError):
                    data['sort_order'] = 0
            if 'parent_id' in data and not data['parent_id']:
                data['parent_id'] = None
            
            # Validation
            if not data.get('title') or not data.get('slug'):
                flash('Nazwa i slug są wymagane', 'error')
                return redirect(url_for('blog.admin_categories'))
            
            # Check if slug already exists
            existing = BlogCategory.query.filter_by(slug=data['slug']).first()
            if existing:
                flash('Kategoria z tym slug już istnieje', 'error')
                return redirect(url_for('blog.admin_categories'))
            
            # Create category
            category = BlogCategory(
                title=data['title'],
                slug=data['slug'],
                description=data.get('description', ''),
                parent_id=data.get('parent_id'),
                sort_order=data.get('sort_order', 0),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(category)
            db.session.commit()
            
            flash('Kategoria została utworzona pomyślnie', 'success')
            return redirect(url_for('blog.admin_categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Błąd podczas tworzenia kategorii: {str(e)}', 'error')
            return redirect(url_for('blog.admin_categories'))
    
    # Pagination for categories
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    categories = BlogCategory.query.order_by(BlogCategory.sort_order).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('blog/admin/categories.html', categories=categories)

@blog_bp.route('/admin/tags')
@login_required
def admin_tags():
    """Blog tags management"""
    if not current_user.is_admin:
        flash('Brak uprawnień do tej strony', 'error')
        return redirect(url_for('public.index'))
    
    tags = BlogTag.query.order_by(BlogTag.name).all()
    return render_template('blog/admin/tags.html', tags=tags)

@blog_bp.route('/admin/comments')
@login_required
def admin_comments():
    """Blog comments management"""
    if not current_user.is_admin:
        flash('Brak uprawnień do tej strony', 'error')
        return redirect(url_for('public.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    comments = BlogComment.query.order_by(BlogComment.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('blog/admin/comments.html', comments=comments)

# API endpoints for admin panel
@blog_bp.route('/admin/api/categories')
@login_required
def api_categories():
    """API endpoint for blog categories"""
    if not current_user.is_admin:
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        categories = BlogCategory.query.filter_by(is_active=True).order_by(BlogCategory.sort_order).all()
        categories_data = []
        
        for category in categories:
            categories_data.append({
                'id': category.id,
                'title': category.title,
                'slug': category.slug,
                'full_path': category.full_path,
                'posts_count': category.posts_count,
                'parent_id': category.parent_id,
                'created_at': category.created_at.isoformat() if category.created_at else None
            })
        
        return jsonify({
            'success': True,
            'categories': categories_data
        })
    except Exception as e:
        logging.error(f"Error fetching blog categories: {str(e)}")
        return jsonify({'error': str(e)}), 500

@blog_bp.route('/admin/api/posts')
@login_required
def api_posts():
    """API endpoint for blog posts"""
    if not current_user.is_admin:
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        posts = BlogPost.query.order_by(BlogPost.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        posts_data = []
        for post in posts.items:
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'excerpt': post.excerpt,
                'content': post.content,
                'status': post.status,
                'featured_image': post.featured_image,
                'author_name': post.author.name or post.author.email,
                'published_at': post.published_at.isoformat() if post.published_at else None,
                'created_at': post.created_at.isoformat() if post.created_at else None,
                'categories': [{'id': cat.id, 'title': cat.title} for cat in post.categories],
                'tags': [{'id': tag.id, 'name': tag.name} for tag in post.tags],
                'comments_count': post.comments_count
            })
        
        return jsonify({
            'success': True,
            'posts': posts_data,
            'pagination': {
                'current_page': posts.page,
                'total_pages': posts.pages,
                'total': posts.total,
                'per_page': posts.per_page
            }
        })
    except Exception as e:
        logging.error(f"Error fetching blog posts: {str(e)}")
        return jsonify({'error': str(e)}), 500



@blog_bp.route('/test-meta')
def test_meta():
    """Test meta tags page"""
    return render_template('test_meta.html')

@blog_bp.route('/test-image')
def test_image():
    """Test if images are accessible"""
    from flask import send_from_directory
    return send_from_directory('static', 'images/hero/hero-bg.jpg')

@blog_bp.route('/debug/meta/<slug>')
def debug_meta(slug):
    """Debug meta tags for a blog post"""
    post = BlogPost.query.filter_by(slug=slug, status='published').first_or_404()
    
    # Get absolute URLs
    base_url = request.host_url.rstrip('/')
    
    # Featured image URL
    if post.featured_image:
        if post.featured_image.startswith('http'):
            image_url = post.featured_image
        else:
            image_url = f"{base_url}{url_for('static', filename=post.featured_image)}"
    else:
        image_url = f"{base_url}{url_for('static', filename='images/hero/hero-bg.jpg')}"
    
    return render_template('blog/meta_test.html', post=post, image_url=image_url)

@blog_bp.route('/debug/meta/<slug>/json')
def debug_meta_json(slug):
    """Debug meta tags for a blog post (JSON)"""
    post = BlogPost.query.filter_by(slug=slug, status='published').first_or_404()
    
    # Get absolute URLs
    base_url = request.host_url.rstrip('/')
    
    # Featured image URL
    if post.featured_image:
        if post.featured_image.startswith('http'):
            image_url = post.featured_image
        else:
            image_url = f"{base_url}{url_for('static', filename=post.featured_image)}"
    else:
        image_url = f"{base_url}{url_for('static', filename='images/hero/hero-bg.jpg')}"
    
    # Meta data
    meta_data = {
        'title': post.meta_title or post.title,
        'description': post.meta_description or (post.excerpt or post.content[:160]),
        'url': request.url,
        'image': image_url,
        'site_name': current_app.config.get('SITE_NAME', 'Klub Lepsze Życie'),
        'author': post.author.name or post.author.email,
        'published_at': post.published_at.isoformat() if post.published_at else None,
        'categories': [cat.title for cat in post.categories],
        'tags': [tag.name for tag in post.tags]
    }
    
    return jsonify(meta_data)

@blog_bp.route('/admin/api/categories/<int:category_id>', methods=['PUT', 'DELETE'])
@login_required
def api_category(category_id):
    """Update or delete blog category"""
    if not current_user.is_admin:
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        category = BlogCategory.query.get_or_404(category_id)
        
        if request.method == 'PUT':
            data = request.get_json()
            
            # Update fields
            if 'title' in data:
                category.title = data['title']
            if 'slug' in data:
                # Check if new slug already exists (excluding current category)
                existing = BlogCategory.query.filter(
                    BlogCategory.slug == data['slug'],
                    BlogCategory.id != category_id
                ).first()
                if existing:
                    return jsonify({'error': 'Kategoria z tym slug już istnieje'}), 400
                category.slug = data['slug']
            if 'description' in data:
                category.description = data['description']
            if 'parent_id' in data:
                category.parent_id = data['parent_id'] if data['parent_id'] else None
            if 'sort_order' in data:
                category.sort_order = data['sort_order']
            if 'is_active' in data:
                category.is_active = data['is_active']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Kategoria została zaktualizowana',
                'category': {
                    'id': category.id,
                    'title': category.title,
                    'slug': category.slug,
                    'full_path': category.full_path
                }
            })
        
        elif request.method == 'DELETE':
            # Check if category has posts
            if category.posts_count > 0:
                return jsonify({'error': 'Nie można usunąć kategorii, która ma artykuły'}), 400
            
            # Check if category has children
            if category.children:
                return jsonify({'error': 'Nie można usunąć kategorii, która ma podkategorie'}), 400
            
            db.session.delete(category)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Kategoria została usunięta'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error managing category: {str(e)}")
        return jsonify({'error': str(e)}), 500
