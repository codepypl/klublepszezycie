"""
Blog business logic controller
"""
from flask import request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, BlogCategory, BlogPost, BlogTag, BlogComment, User
from datetime import datetime
import re
import logging

def slugify(text):
    """Convert text to URL-friendly slug"""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text

class BlogController:
    """Blog business logic controller"""
    
    @staticmethod
    def get_blog_posts(page=1, per_page=10, category_slug=None, tag_slug=None, search=None):
        """Get blog posts with filters"""
        try:
            # Get published posts
            posts_query = BlogPost.query.filter_by(status='published').order_by(BlogPost.published_at.desc())
            
            # Filter by category if specified
            if category_slug:
                category = BlogCategory.query.filter_by(slug=category_slug, is_active=True).first()
                if category:
                    posts_query = posts_query.join(BlogPost.categories).filter(BlogCategory.id == category.id)
                else:
                    return {
                        'success': False,
                        'error': 'Kategoria nie została znaleziona',
                        'posts': None,
                        'categories': [],
                        'tags': []
                    }
            
            # Filter by tag if specified
            if tag_slug:
                tag = BlogTag.query.filter_by(slug=tag_slug, is_active=True).first()
                if tag:
                    posts_query = posts_query.join(BlogPost.tags).filter(BlogTag.id == tag.id)
                else:
                    return {
                        'success': False,
                        'error': 'Tag nie został znaleziony',
                        'posts': None,
                        'categories': [],
                        'tags': []
                    }
            
            # Search functionality
            if search:
                posts_query = posts_query.filter(
                    BlogPost.title.ilike(f'%{search}%') |
                    BlogPost.content.ilike(f'%{search}%') |
                    BlogPost.excerpt.ilike(f'%{search}%')
                )
            
            # Paginate
            posts = posts_query.paginate(page=page, per_page=per_page, error_out=False)
            
            # Get categories and tags for sidebar
            categories = BlogCategory.query.filter_by(is_active=True).order_by(BlogCategory.title).all()
            tags = BlogTag.query.filter_by(is_active=True).order_by(BlogTag.name).all()
            
            return {
                'success': True,
                'posts': posts,
                'categories': categories,
                'tags': tags,
                'search': search,
                'category_slug': category_slug,
                'tag_slug': tag_slug
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'posts': None,
                'categories': [],
                'tags': []
            }
    
    @staticmethod
    def get_blog_post(slug):
        """Get single blog post"""
        try:
            post = BlogPost.query.filter_by(slug=slug, status='published').first()
            if not post:
                return {
                    'success': False,
                    'error': 'Post nie został znaleziony',
                    'post': None,
                    'related_posts': []
                }
            
            # Get related posts (same category)
            related_posts = []
            if post.categories:
                category_ids = [cat.id for cat in post.categories]
                related_posts = BlogPost.query.filter(
                    BlogPost.id != post.id,
                    BlogPost.status == 'published',
                    BlogPost.categories.any(BlogCategory.id.in_(category_ids))
                ).order_by(BlogPost.published_at.desc()).limit(3).all()
            
            return {
                'success': True,
                'post': post,
                'related_posts': related_posts
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'post': None,
                'related_posts': []
            }
    
    @staticmethod
    def create_blog_comment(post_id, name, email, content, parent_id=None):
        """Create blog comment with user tracking"""
        try:
            from app.utils.user_info import get_user_info
            
            post = BlogPost.query.get(post_id)
            if not post:
                return {
                    'success': False,
                    'error': 'Post nie został znaleziony'
                }
            
            # Get user information
            user_info = get_user_info()
            
            comment = BlogComment(
                post_id=post_id,
                parent_id=parent_id,
                author_name=name,
                author_email=email,
                content=content,
                ip_address=user_info['ip_address'],
                user_agent=user_info['user_agent'],
                browser=user_info['browser'],
                operating_system=user_info['operating_system'],
                location_country=user_info['location_country'],
                location_city=user_info['location_city'],
                is_approved=False
            )
            
            db.session.add(comment)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Komentarz został dodany i oczekuje na zatwierdzenie',
                'comment_id': comment.id
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_admin_posts(page=1, per_page=20, status=None, search=None):
        """Get posts for admin panel"""
        try:
            query = BlogPost.query
            
            if status:
                query = query.filter_by(status=status)
            
            if search:
                query = query.filter(
                    BlogPost.title.ilike(f'%{search}%') |
                    BlogPost.content.ilike(f'%{search}%')
                )
            
            posts = query.order_by(BlogPost.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'success': True,
                'posts': posts
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'posts': None
            }
    
    @staticmethod
    def create_blog_post(title, content, excerpt, status, category_ids, tag_ids, featured_image=None):
        """Create new blog post"""
        try:
            # Generate slug
            slug = slugify(title)
            
            # Check if slug exists
            counter = 1
            original_slug = slug
            while BlogPost.query.filter_by(slug=slug).first():
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            post = BlogPost(
                title=title,
                slug=slug,
                content=content,
                excerpt=excerpt,
                status=status,
                featured_image=featured_image,
                author_id=current_user.id
            )
            
            if status == 'published':
                post.published_at = datetime.utcnow()
            
            db.session.add(post)
            db.session.flush()
            
            # Add categories
            if category_ids:
                categories = BlogCategory.query.filter(BlogCategory.id.in_(category_ids)).all()
                post.categories = categories
            
            # Add tags
            if tag_ids:
                tags = BlogTag.query.filter(BlogTag.id.in_(tag_ids)).all()
                post.tags = tags
            
            db.session.commit()
            
            return {
                'success': True,
                'post': post,
                'message': 'Post został utworzony'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_blog_post(post_id, title, content, excerpt, status, category_ids, tag_ids, featured_image=None):
        """Update blog post"""
        try:
            post = BlogPost.query.get(post_id)
            if not post:
                return {
                    'success': False,
                    'error': 'Post nie został znaleziony'
                }
            
            post.title = title
            post.content = content
            post.excerpt = excerpt
            post.status = status
            if featured_image:
                post.featured_image = featured_image
            
            # Update slug if title changed
            new_slug = slugify(title)
            if new_slug != post.slug:
                counter = 1
                original_slug = new_slug
                while BlogPost.query.filter(BlogPost.slug == new_slug, BlogPost.id != post_id).first():
                    new_slug = f"{original_slug}-{counter}"
                    counter += 1
                post.slug = new_slug
            
            if status == 'published' and not post.published_at:
                post.published_at = datetime.utcnow()
            
            # Update categories
            if category_ids:
                categories = BlogCategory.query.filter(BlogCategory.id.in_(category_ids)).all()
                post.categories = categories
            else:
                post.categories = []
            
            # Update tags
            if tag_ids:
                tags = BlogTag.query.filter(BlogTag.id.in_(tag_ids)).all()
                post.tags = tags
            else:
                post.tags = []
            
            db.session.commit()
            
            return {
                'success': True,
                'post': post,
                'message': 'Post został zaktualizowany'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def delete_blog_post(post_id):
        """Delete blog post"""
        try:
            post = BlogPost.query.get(post_id)
            if not post:
                return {
                    'success': False,
                    'error': 'Post nie został znaleziony'
                }
            
            db.session.delete(post)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Post został usunięty'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_categories():
        """Get all categories"""
        try:
            categories = BlogCategory.query.filter_by(is_active=True).order_by(BlogCategory.title).all()
            return {
                'success': True,
                'categories': categories
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'categories': []
            }
    
    @staticmethod
    def get_tags():
        """Get all tags"""
        try:
            tags = BlogTag.query.filter_by(is_active=True).order_by(BlogTag.name).all()
            return {
                'success': True,
                'tags': tags
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'tags': []
            }
    
    @staticmethod
    def search_posts(query, page=1, per_page=10):
        """Search blog posts"""
        try:
            return BlogController.get_blog_posts(page=page, per_page=per_page, search=query)
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'posts': None
            }
    
    @staticmethod
    def get_blog_comments(page=1, per_page=20, status=None):
        """Get blog comments for admin panel"""
        try:
            from sqlalchemy.orm import joinedload
            
            query = BlogComment.query.options(joinedload(BlogComment.post))
            
            if status == 'approved':
                query = query.filter_by(is_approved=True)
            elif status == 'pending':
                query = query.filter_by(is_approved=False)
            elif status == 'spam':
                query = query.filter_by(is_spam=True)
            
            comments = query.order_by(BlogComment.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'success': True,
                'comments': comments
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'comments': None
            }
    
    @staticmethod
    def get_post_comments(post_id, approved_only=True):
        """Get comments for a specific post with replies"""
        try:
            query = BlogComment.query.filter_by(post_id=post_id)
            
            if approved_only:
                query = query.filter_by(is_approved=True)
            
            # Get only top-level comments (no parent)
            comments = query.filter(BlogComment.parent_id.is_(None)).order_by(BlogComment.created_at.asc()).all()
            
            return {
                'success': True,
                'comments': comments
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'comments': []
            }
