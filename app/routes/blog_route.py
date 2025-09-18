"""
Blog routes
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app.blueprints.blog_controller import BlogController

blog_bp = Blueprint('blog', __name__, url_prefix='/blog')

@blog_bp.route('/')
def index():
    """Blog homepage - list of posts"""
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('category')
    tag_slug = request.args.get('tag')
    search = request.args.get('search')
    
    data = BlogController.get_blog_posts(
        page=page, 
        category_slug=category_slug, 
        tag_slug=tag_slug, 
        search=search
    )
    
    if not data['success']:
        flash(data['error'], 'error')
        return redirect(url_for('blog.index'))
    
    # Get all database data dynamically (includes footer_settings, active_social_links, menu_items)
    from app.blueprints.public_controller import PublicController
    db_data = PublicController.get_database_data()
    
    return render_template('blog/index.html', 
                         posts=data['posts'], 
                         categories=data['categories'], 
                         tags=data['tags'],
                         search=data['search'],
                         category_slug=data['category_slug'],
                         tag_slug=data['tag_slug'],
                         **db_data)

@blog_bp.route('/<slug>')
def post_detail(slug):
    """Blog post detail page"""
    data = BlogController.get_blog_post(slug)
    
    if not data['success']:
        flash(data['error'], 'error')
        return redirect(url_for('blog.index'))
    
    post = data['post']
    related_posts = data['related_posts']
    
    # Get comments for this post
    comments_data = BlogController.get_post_comments(post.id, approved_only=True)
    comments = comments_data['comments'] if comments_data['success'] else []
    
    # Get categories and tags for sidebar
    categories_data = BlogController.get_categories()
    tags_data = BlogController.get_tags()
    
    categories = categories_data['categories'] if categories_data['success'] else []
    popular_tags = tags_data['tags'] if tags_data['success'] else []
    
    # Get all database data dynamically
    from app.blueprints.public_controller import PublicController
    db_data = PublicController.get_database_data()
    
    return render_template('blog/post_detail.html',
                         post=post,
                         comments=comments,
                         related_posts=related_posts,
                         categories=categories,
                         popular_tags=popular_tags,
                         **db_data)

@blog_bp.route('/category/<category_slug>/<post_slug>')
def post_detail_with_category(category_slug, post_slug):
    """Blog post detail page with category in URL"""
    data = BlogController.get_blog_post(post_slug)
    
    if not data['success']:
        flash(data['error'], 'error')
        return redirect(url_for('blog.index'))
    
    # Verify the category matches
    category = next((cat for cat in data['post'].categories if cat.slug == category_slug), None)
    if not category:
        # If category doesn't match, redirect to correct category
        if data['post'].categories:
            primary_category = data['post'].categories[0]
            return redirect(url_for('blog.post_detail_with_category', 
                                  category_slug=primary_category.slug, 
                                  post_slug=post_slug), code=301)
        else:
            return redirect(url_for('blog.post_detail', slug=post_slug), code=301)
    
    post = data['post']
    related_posts = data['related_posts']
    
    # Get comments for this post
    comments_data = BlogController.get_post_comments(post.id, approved_only=True)
    comments = comments_data['comments'] if comments_data['success'] else []
    
    # Get categories and tags for sidebar
    categories_data = BlogController.get_categories()
    tags_data = BlogController.get_tags()
    
    categories = categories_data['categories'] if categories_data['success'] else []
    popular_tags = tags_data['tags'] if tags_data['success'] else []
    
    # Get all database data dynamically
    from app.blueprints.public_controller import PublicController
    db_data = PublicController.get_database_data()
    
    return render_template('blog/post_detail.html',
                         post=post,
                         comments=comments,
                         related_posts=related_posts,
                         categories=categories,
                         popular_tags=popular_tags,
                         primary_category=category,
                         **db_data)

@blog_bp.route('/category/<slug>')
def category_detail(slug):
    """Category detail page"""
    page = request.args.get('page', 1, type=int)
    
    data = BlogController.get_blog_posts(page=page, category_slug=slug)
    
    if not data['success']:
        flash(data['error'], 'error')
        return redirect(url_for('blog.index'))
    
    # Get category info
    from app.models import BlogCategory
    category = BlogCategory.query.filter_by(slug=slug, is_active=True).first()
    
    # Get all database data dynamically
    from app.blueprints.public_controller import PublicController
    db_data = PublicController.get_database_data()
    
    return render_template('blog/category_detail.html',
                         posts=data['posts'],
                         categories=data['categories'],
                         tags=data['tags'],
                         category=category,
                         **db_data)

@blog_bp.route('/category/<parent_slug>/<child_slug>')
def category_hierarchy_detail(parent_slug, child_slug):
    """Category detail page with hierarchy in URL"""
    page = request.args.get('page', 1, type=int)
    
    # Get child category
    from app.models import BlogCategory
    child_category = BlogCategory.query.filter_by(slug=child_slug, is_active=True).first()
    
    if not child_category:
        flash('Kategoria nie została znaleziona', 'error')
        return redirect(url_for('blog.index'))
    
    # Verify parent relationship
    if not child_category.parent or child_category.parent.slug != parent_slug:
        # Redirect to correct URL
        if child_category.parent:
            return redirect(url_for('blog.category_hierarchy_detail', 
                                  parent_slug=child_category.parent.slug, 
                                  child_slug=child_slug), code=301)
        else:
            return redirect(url_for('blog.category_detail', slug=child_slug), code=301)
    
    data = BlogController.get_blog_posts(page=page, category_slug=child_slug)
    
    if not data['success']:
        flash(data['error'], 'error')
        return redirect(url_for('blog.index'))
    
    # Get all database data dynamically
    from app.blueprints.public_controller import PublicController
    db_data = PublicController.get_database_data()
    
    return render_template('blog/category_detail.html',
                         posts=data['posts'],
                         categories=data['categories'],
                         tags=data['tags'],
                         category=child_category,
                         parent_category=child_category.parent,
                         **db_data)

@blog_bp.route('/tag/<slug>')
def tag_detail(slug):
    """Tag detail page"""
    page = request.args.get('page', 1, type=int)
    
    data = BlogController.get_blog_posts(page=page, tag_slug=slug)
    
    if not data['success']:
        flash(data['error'], 'error')
        return redirect(url_for('blog.index'))
    
    # Get tag info
    from app.models import BlogTag
    tag = BlogTag.query.filter_by(slug=slug, is_active=True).first()
    
    # Get all database data dynamically
    from app.blueprints.public_controller import PublicController
    db_data = PublicController.get_database_data()
    
    return render_template('blog/tag_detail.html',
                         posts=data['posts'],
                         categories=data['categories'],
                         tags=data['tags'],
                         tag=tag,
                         **db_data)

@blog_bp.route('/search')
def search():
    """Search blog posts"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    if not query:
        flash('Wprowadź frazę do wyszukiwania', 'warning')
        return redirect(url_for('blog.index'))
    
    # Get search results from controller
    data = BlogController.search_posts(query, page)
    
    if not data['success']:
        flash(data['error'], 'error')
        return redirect(url_for('blog.index'))
    
    # Get all database data dynamically
    from app.blueprints.public_controller import PublicController
    db_data = PublicController.get_database_data()
    
    return render_template('blog/search.html', 
                         query=query,
                         posts=data['posts'], 
                         **db_data)

@blog_bp.route('/comment', methods=['POST'])
def add_comment():
    """Add comment to blog post"""
    try:
        # Check if request is JSON
        if request.is_json:
            data = request.get_json()
            post_id = data.get('post_id')
            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            content = data.get('content', '').strip()
            parent_id = data.get('parent_id')
        else:
            # Fallback to form data
            post_id = request.form.get('post_id', type=int)
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            content = request.form.get('content', '').strip()
            parent_id = request.form.get('parent_id', type=int)
        
        # Debug logging
        import logging
        logging.info(f"Comment data - post_id: {post_id}, name: '{name}', email: '{email}', content: '{content}'")
        
        # Convert post_id to int if it's a string
        if isinstance(post_id, str):
            try:
                post_id = int(post_id)
            except ValueError:
                post_id = None
        
        # Check if all required fields are present and not empty
        required_fields = [post_id, name, email, content]
        if not all(required_fields):
            missing_fields = []
            if not post_id:
                missing_fields.append('post_id')
            if not name:
                missing_fields.append('name')
            if not email:
                missing_fields.append('email')
            if not content:
                missing_fields.append('content')
            
            error_msg = f'Brakujące pola: {", ".join(missing_fields)}'
            logging.warning(f"Missing fields: {missing_fields}")
            
            if request.is_json:
                return jsonify({'success': False, 'message': error_msg})
            else:
                flash(error_msg, 'error')
                return redirect(request.referrer or url_for('blog.index'))
        
        result = BlogController.create_blog_comment(post_id, name, email, content, parent_id)
        
        if request.is_json:
            if result['success']:
                return jsonify({'success': True, 'message': result['message']})
            else:
                return jsonify({'success': False, 'message': result['error']})
        else:
            if result['success']:
                flash(result['message'], 'success')
            else:
                flash(f'Błąd: {result["error"]}', 'error')
            return redirect(request.referrer or url_for('blog.index'))
    
    except Exception as e:
        import logging
        logging.error(f"Error in add_comment: {str(e)}")
        if request.is_json:
            return jsonify({'success': False, 'message': f'Błąd serwera: {str(e)}'})
        else:
            flash(f'Błąd serwera: {str(e)}', 'error')
            return redirect(request.referrer or url_for('blog.index'))

# Admin routes for blog management
@blog_bp.route('/admin')
@login_required
def admin_index():
    """Blog admin dashboard"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    search = request.args.get('search')
    
    data = BlogController.get_admin_posts(page=page, status=status, search=search)
    
    if not data['success']:
        flash(f'Błąd: {data["error"]}', 'error')
        return redirect(url_for('blog.index'))
    
    return render_template('blog/admin/posts.html', posts=data['posts'])

@blog_bp.route('/admin/create', methods=['GET', 'POST'])
@login_required
def admin_create():
    """Create new blog post"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        status = request.form.get('status', 'draft')
        category_ids = request.form.getlist('categories', type=int)
        tag_ids = request.form.getlist('tags', type=int)
        featured_image = request.form.get('featured_image', '').strip()
        
        if not title or not content:
            flash('Tytuł i treść są wymagane', 'error')
        else:
            result = BlogController.create_blog_post(
                title, content, excerpt, status, category_ids, tag_ids, featured_image
            )
            
            if result['success']:
                flash(result['message'], 'success')
                return redirect(url_for('blog.admin_index'))
            else:
                flash(f'Błąd: {result["error"]}', 'error')
    
    # Get categories and tags for form
    categories_data = BlogController.get_categories()
    tags_data = BlogController.get_tags()
    
    categories = categories_data['categories'] if categories_data['success'] else []
    tags = tags_data['tags'] if tags_data['success'] else []
    
    return render_template('blog/admin/posts.html', categories=categories, tags=tags)

@blog_bp.route('/admin/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def admin_edit(post_id):
    """Edit blog post"""
    from app.models import BlogPost
    post = BlogPost.query.get_or_404(post_id)
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        excerpt = request.form.get('excerpt', '').strip()
        status = request.form.get('status', 'draft')
        category_ids = request.form.getlist('categories', type=int)
        tag_ids = request.form.getlist('tags', type=int)
        featured_image = request.form.get('featured_image', '').strip()
        
        if not title or not content:
            flash('Tytuł i treść są wymagane', 'error')
        else:
            result = BlogController.update_blog_post(
                post_id, title, content, excerpt, status, category_ids, tag_ids, featured_image
            )
            
            if result['success']:
                flash(result['message'], 'success')
                return redirect(url_for('blog.admin_index'))
            else:
                flash(f'Błąd: {result["error"]}', 'error')
    
    # Get categories and tags for form
    categories_data = BlogController.get_categories()
    tags_data = BlogController.get_tags()
    
    categories = categories_data['categories'] if categories_data['success'] else []
    tags = tags_data['tags'] if tags_data['success'] else []
    
    return render_template('blog/admin/posts.html', post=post, categories=categories, tags=tags)

@blog_bp.route('/admin/delete/<int:post_id>', methods=['POST'])
@login_required
def admin_delete(post_id):
    """Delete blog post"""
    result = BlogController.delete_blog_post(post_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(f'Błąd: {result["error"]}', 'error')
    
    return redirect(url_for('blog.admin_index'))

@blog_bp.route('/admin/categories')
@login_required
def admin_categories():
    """Blog categories management page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    data = BlogController.get_categories_paginated(page=page, per_page=per_page)
    
    if not data['success']:
        flash(f'Błąd: {data["error"]}', 'error')
        return redirect(url_for('blog.admin_index'))
    
    return render_template('blog/admin/categories.html', categories=data['categories'])

@blog_bp.route('/admin/tags')
@login_required
def admin_tags():
    """Blog tags management page"""
    data = BlogController.get_tags()
    
    if not data['success']:
        flash(f'Błąd: {data["error"]}', 'error')
        return redirect(url_for('blog.admin_index'))
    
    return render_template('blog/admin/tags.html', tags=data['tags'])

@blog_bp.route('/admin/comments')
@login_required
def admin_comments():
    """Blog comments management page"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', None)
    
    # Get comments from controller
    data = BlogController.get_blog_comments(page=page, status=status)
    
    if not data['success']:
        flash(data['error'], 'error')
        comments = None
    else:
        comments = data['comments']
    
    return render_template('blog/admin/comments.html', comments=comments)