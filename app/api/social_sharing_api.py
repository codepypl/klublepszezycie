"""
Social Media Sharing API endpoints
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.models import BlogPost, db
from app.utils.auth_utils import admin_required_api
import logging
import re
from urllib.parse import quote
import requests

social_sharing_api_bp = Blueprint('social_sharing_api', __name__)

def get_post_excerpt(post, max_length=100):
    """Get excerpt from blog post (first 100 characters)"""
    if post.excerpt:
        return post.excerpt[:max_length] + ('...' if len(post.excerpt) > max_length else '')
    
    # Remove HTML tags and get first 100 characters
    clean_content = re.sub(r'<[^>]+>', '', post.content)
    return clean_content[:max_length] + ('...' if len(clean_content) > max_length else '')

def get_post_thumbnail_url(post, base_url):
    """Get proper thumbnail URL for social sharing"""
    if post.featured_image:
        if post.featured_image.startswith('http'):
            return post.featured_image
        else:
            return f"{base_url}{post.featured_image}"
    
    # Return default thumbnail or site logo
    return f"{base_url}/static/images/logo.png"

def get_post_url(post, base_url):
    """Get full URL to blog post"""
    return f"{base_url}/blog/post/{post.slug}"

@social_sharing_api_bp.route('/social-sharing/post/<int:post_id>', methods=['GET'])
@login_required
def get_post_sharing_data(post_id):
    """Get social media sharing data for a blog post"""
    try:
        post = BlogPost.query.get_or_404(post_id)
        
        if not post.is_published:
            return jsonify({
                'success': False,
                'error': 'Post nie jest opublikowany'
            }), 400
        
        base_url = request.host_url.rstrip('/')
        
        sharing_data = {
            'post_id': post.id,
            'title': post.title,
            'excerpt': get_post_excerpt(post),
            'thumbnail_url': get_post_thumbnail_url(post, base_url),
            'post_url': get_post_url(post, base_url),
            'author': post.author.first_name if post.author else 'Klub Lepsze Życie'
        }
        
        return jsonify({
            'success': True,
            'sharing_data': sharing_data
        })
        
    except Exception as e:
        logging.error(f"Error getting post sharing data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_sharing_api_bp.route('/social-sharing/generate-links', methods=['POST'])
@login_required
def generate_social_sharing_links():
    """Generate social media sharing links for a blog post"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        
        if not post_id:
            return jsonify({
                'success': False,
                'error': 'ID posta jest wymagane'
            }), 400
        
        post = BlogPost.query.get_or_404(post_id)
        
        if not post.is_published:
            return jsonify({
                'success': False,
                'error': 'Post nie jest opublikowany'
            }), 400
        
        base_url = request.host_url.rstrip('/')
        post_url = get_post_url(post, base_url)
        title = post.title
        excerpt = get_post_excerpt(post)
        thumbnail_url = get_post_thumbnail_url(post, base_url)
        
        # Generate sharing links for different platforms
        sharing_links = {
            'facebook': {
                'name': 'Facebook',
                'icon': 'fab fa-facebook-f',
                'color': '#1877f2',
                'url': f"https://www.facebook.com/sharer/sharer.php?u={quote(post_url)}&quote={quote(title)}"
            },
            'twitter': {
                'name': 'Twitter',
                'icon': 'fab fa-twitter',
                'color': '#1da1f2',
                'url': f"https://twitter.com/intent/tweet?url={quote(post_url)}&text={quote(title)}"
            },
            'linkedin': {
                'name': 'LinkedIn',
                'icon': 'fab fa-linkedin-in',
                'color': '#0077b5',
                'url': f"https://www.linkedin.com/sharing/share-offsite/?url={quote(post_url)}"
            },
            'whatsapp': {
                'name': 'WhatsApp',
                'icon': 'fab fa-whatsapp',
                'color': '#25d366',
                'url': f"https://wa.me/?text={quote(f'{title} - {post_url}')}"
            },
            'telegram': {
                'name': 'Telegram',
                'icon': 'fab fa-telegram-plane',
                'color': '#0088cc',
                'url': f"https://t.me/share/url?url={quote(post_url)}&text={quote(title)}"
            },
            'email': {
                'name': 'Email',
                'icon': 'fas fa-envelope',
                'color': '#6c757d',
                'url': f"mailto:?subject={quote(title)}&body={quote(f'{excerpt}\n\nCzytaj więcej: {post_url}')}"
            }
        }
        
        return jsonify({
            'success': True,
            'sharing_data': {
                'post_id': post.id,
                'title': title,
                'excerpt': excerpt,
                'thumbnail_url': thumbnail_url,
                'post_url': post_url,
                'author': post.author.first_name if post.author else 'Klub Lepsze Życie'
            },
            'sharing_links': sharing_links
        })
        
    except Exception as e:
        logging.error(f"Error generating social sharing links: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_sharing_api_bp.route('/social-sharing/auto-post/<int:post_id>', methods=['POST'])
@login_required
@admin_required_api
def auto_post_to_social_media(post_id):
    """Automatically post to social media platforms (requires admin)"""
    try:
        data = request.get_json()
        platforms = data.get('platforms', [])
        
        if not platforms:
            return jsonify({
                'success': False,
                'error': 'Brak wybranych platform'
            }), 400
        
        post = BlogPost.query.get_or_404(post_id)
        
        if not post.is_published:
            return jsonify({
                'success': False,
                'error': 'Post nie jest opublikowany'
            }), 400
        
        base_url = request.host_url.rstrip('/')
        post_url = get_post_url(post, base_url)
        title = post.title
        excerpt = get_post_excerpt(post)
        
        results = []
        
        # This would require API keys and tokens for each platform
        # For now, we'll return the sharing links that can be used manually
        for platform in platforms:
            if platform == 'facebook':
                # Would require Facebook Graph API
                results.append({
                    'platform': 'facebook',
                    'success': False,
                    'message': 'Automatyczne publikowanie na Facebook wymaga konfiguracji API'
                })
            elif platform == 'twitter':
                # Would require Twitter API v2
                results.append({
                    'platform': 'twitter',
                    'success': False,
                    'message': 'Automatyczne publikowanie na Twitter wymaga konfiguracji API'
                })
            elif platform == 'linkedin':
                # Would require LinkedIn API
                results.append({
                    'platform': 'linkedin',
                    'success': False,
                    'message': 'Automatyczne publikowanie na LinkedIn wymaga konfiguracji API'
                })
        
        return jsonify({
            'success': True,
            'message': 'Automatyczne publikowanie wymaga konfiguracji API dla każdej platformy',
            'results': results,
            'manual_sharing_links': {
                'facebook': f"https://www.facebook.com/sharer/sharer.php?u={quote(post_url)}&quote={quote(title)}",
                'twitter': f"https://twitter.com/intent/tweet?url={quote(post_url)}&text={quote(title)}",
                'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?url={quote(post_url)}"
            }
        })
        
    except Exception as e:
        logging.error(f"Error in auto-posting to social media: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@social_sharing_api_bp.route('/social-sharing/track-share', methods=['POST'])
@login_required
def track_social_share():
    """Track social media shares for analytics"""
    try:
        data = request.get_json()
        post_id = data.get('post_id')
        platform = data.get('platform')
        
        if not post_id or not platform:
            return jsonify({
                'success': False,
                'error': 'ID posta i platforma są wymagane'
            }), 400
        
        post = BlogPost.query.get_or_404(post_id)
        
        # Here you could implement analytics tracking
        # For now, we'll just log the share
        logging.info(f"Social share tracked: Post {post_id} shared on {platform} by user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'Udostępnienie zostało zarejestrowane'
        })
        
    except Exception as e:
        logging.error(f"Error tracking social share: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

