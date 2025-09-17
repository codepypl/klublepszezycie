"""
SEO API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.models import SEOSettings, db
from app.utils.auth_utils import admin_required
import logging

seo_api_bp = Blueprint('seo_api', __name__)

@seo_api_bp.route('/seo', methods=['GET', 'POST'])
@login_required
def api_seo():
    """SEO settings API"""
    if request.method == 'GET':
        try:
            seo_settings = SEOSettings.query.filter_by(is_active=True).all()
            return jsonify({
                'success': True,
                'seo_settings': [{
                    'id': seo.id,
                    'page_type': seo.page_type,
                    'title': seo.title,
                    'description': seo.description,
                    'keywords': seo.keywords,
                    'og_title': seo.og_title,
                    'og_description': seo.og_description,
                    'og_image': seo.og_image,
                    'is_active': seo.is_active,
                    'created_at': seo.created_at.isoformat() if seo.created_at else None,
                    'updated_at': seo.updated_at.isoformat() if seo.updated_at else None
                } for seo in seo_settings]
            })
        except Exception as e:
            logging.error(f"Error getting SEO settings: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            seo = SEOSettings(
                page_type=data['page_type'],
                title=data['title'],
                description=data.get('description', ''),
                keywords=data.get('keywords', ''),
                og_title=data.get('og_title', ''),
                og_description=data.get('og_description', ''),
                og_image=data.get('og_image', ''),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(seo)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'SEO settings created successfully',
                'seo': {
                    'id': seo.id,
                    'page_type': seo.page_type,
                    'title': seo.title,
                    'description': seo.description,
                    'keywords': seo.keywords,
                    'og_title': seo.og_title,
                    'og_description': seo.og_description,
                    'og_image': seo.og_image,
                    'is_active': seo.is_active
                }
            })
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating SEO settings: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

@seo_api_bp.route('/seo/<int:seo_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_seo_setting(seo_id):
    """Individual SEO setting API"""
    seo = SEOSettings.query.get_or_404(seo_id)
    
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'seo': {
                    'id': seo.id,
                    'page_type': seo.page_type,
                    'title': seo.title,
                    'description': seo.description,
                    'keywords': seo.keywords,
                    'og_title': seo.og_title,
                    'og_description': seo.og_description,
                    'og_image': seo.og_image,
                    'is_active': seo.is_active,
                    'created_at': seo.created_at.isoformat() if seo.created_at else None,
                    'updated_at': seo.updated_at.isoformat() if seo.updated_at else None
                }
            })
        
        elif request.method == 'PUT':
            data = request.get_json()
            
            if 'page_type' in data:
                seo.page_type = data['page_type']
            if 'title' in data:
                seo.title = data['title']
            if 'description' in data:
                seo.description = data['description']
            if 'keywords' in data:
                seo.keywords = data['keywords']
            if 'og_title' in data:
                seo.og_title = data['og_title']
            if 'og_description' in data:
                seo.og_description = data['og_description']
            if 'og_image' in data:
                seo.og_image = data['og_image']
            if 'is_active' in data:
                seo.is_active = data['is_active']
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'SEO settings updated successfully'
            })
        
        elif request.method == 'DELETE':
            db.session.delete(seo)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'SEO settings deleted successfully'
            })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error with SEO setting {seo_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@seo_api_bp.route('/seo/blog/post/<int:post_id>')
def api_seo_blog_post(post_id):
    """Get SEO settings for blog post"""
    try:
        from app.models import BlogPost
        post = BlogPost.query.get_or_404(post_id)
        
        # Get SEO settings for blog posts
        seo = SEOSettings.query.filter_by(page_type='blog_post', is_active=True).first()
        
        return jsonify({
            'success': True,
            'seo': {
                'title': seo.title if seo else post.title,
                'description': seo.description if seo else post.excerpt,
                'keywords': seo.keywords if seo else '',
                'og_title': seo.og_title if seo else post.title,
                'og_description': seo.og_description if seo else post.excerpt,
                'og_image': seo.og_image if seo else post.featured_image
            }
        })
    except Exception as e:
        logging.error(f"Error getting SEO for blog post {post_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@seo_api_bp.route('/seo/blog/category/<slug>')
def api_seo_blog_category(slug):
    """Get SEO settings for blog category"""
    try:
        from app.models import BlogCategory
        category = BlogCategory.query.filter_by(slug=slug, is_active=True).first_or_404()
        
        # Get SEO settings for blog categories
        seo = SEOSettings.query.filter_by(page_type='blog_category', is_active=True).first()
        
        return jsonify({
            'success': True,
            'seo': {
                'title': seo.title if seo else category.title,
                'description': seo.description if seo else category.description,
                'keywords': seo.keywords if seo else '',
                'og_title': seo.og_title if seo else category.title,
                'og_description': seo.og_description if seo else category.description,
                'og_image': seo.og_image if seo else ''
            }
        })
    except Exception as e:
        logging.error(f"Error getting SEO for blog category {slug}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@seo_api_bp.route('/seo/blog/tag/<slug>')
def api_seo_blog_tag(slug):
    """Get SEO settings for blog tag"""
    try:
        from app.models import BlogTag
        tag = BlogTag.query.filter_by(slug=slug).first_or_404()
        
        # Get SEO settings for blog tags
        seo = SEOSettings.query.filter_by(page_type='blog_tag', is_active=True).first()
        
        return jsonify({
            'success': True,
            'seo': {
                'title': seo.title if seo else f"Tagi: {tag.name}",
                'description': seo.description if seo else f"Artykuły z tagiem {tag.name}",
                'keywords': seo.keywords if seo else tag.name,
                'og_title': seo.og_title if seo else f"Tagi: {tag.name}",
                'og_description': seo.og_description if seo else f"Artykuły z tagiem {tag.name}",
                'og_image': seo.og_image if seo else ''
            }
        })
    except Exception as e:
        logging.error(f"Error getting SEO for blog tag {slug}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@seo_api_bp.route('/seo/event/<int:event_id>')
def api_seo_event(event_id):
    """Get SEO settings for event"""
    try:
        from app.models import EventSchedule
        event = EventSchedule.query.get_or_404(event_id)
        
        # Get SEO settings for events
        seo = SEOSettings.query.filter_by(page_type='event', is_active=True).first()
        
        return jsonify({
            'success': True,
            'seo': {
                'title': seo.title if seo else event.title,
                'description': seo.description if seo else event.description,
                'keywords': seo.keywords if seo else '',
                'og_title': seo.og_title if seo else event.title,
                'og_description': seo.og_description if seo else event.description,
                'og_image': seo.og_image if seo else ''
            }
        })
    except Exception as e:
        logging.error(f"Error getting SEO for event {event_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@seo_api_bp.route('/seo/section/<int:section_id>')
def api_seo_section(section_id):
    """Get SEO settings for section"""
    try:
        from app.models import Section
        section = Section.query.get_or_404(section_id)
        
        # Get SEO settings for sections
        seo = SEOSettings.query.filter_by(page_type='section', is_active=True).first()
        
        return jsonify({
            'success': True,
            'seo': {
                'title': seo.title if seo else section.title,
                'description': seo.description if seo else section.content,
                'keywords': seo.keywords if seo else '',
                'og_title': seo.og_title if seo else section.title,
                'og_description': seo.og_description if seo else section.content,
                'og_image': seo.og_image if seo else ''
            }
        })
    except Exception as e:
        logging.error(f"Error getting SEO for section {section_id}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@seo_api_bp.route('/seo/page-types')
@login_required
def api_seo_page_types():
    """Get available page types for SEO"""
    try:
        page_types = [
            {'value': 'home', 'label': 'Strona główna'},
            {'value': 'about', 'label': 'O nas'},
            {'value': 'contact', 'label': 'Kontakt'},
            {'value': 'blog', 'label': 'Blog'},
            {'value': 'blog_post', 'label': 'Artykuł bloga'},
            {'value': 'blog_category', 'label': 'Kategoria bloga'},
            {'value': 'blog_tag', 'label': 'Tag bloga'},
            {'value': 'event', 'label': 'Wydarzenie'},
            {'value': 'section', 'label': 'Sekcja'},
            {'value': 'testimonials', 'label': 'Opinie'},
            {'value': 'faq', 'label': 'FAQ'},
            {'value': 'benefits', 'label': 'Korzyści'}
        ]
        
        return jsonify({
            'success': True,
            'page_types': page_types
        })
    except Exception as e:
        logging.error(f"Error getting page types: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@seo_api_bp.route('/seo/auto-generate', methods=['POST'])
@login_required
@admin_required
def api_seo_auto_generate():
    """Auto-generate SEO settings for page type"""
    try:
        data = request.get_json()
        page_type = data.get('page_type')
        
        if not page_type:
            return jsonify({'success': False, 'message': 'Page type is required'}), 400
        
        # This would need to be implemented based on your specific logic
        # for auto-generating SEO content
        return jsonify({
            'success': True,
            'message': 'SEO settings auto-generated successfully',
            'seo': {
                'title': f'Auto-generated title for {page_type}',
                'description': f'Auto-generated description for {page_type}',
                'keywords': f'auto, generated, {page_type}'
            }
        })
    except Exception as e:
        logging.error(f"Error auto-generating SEO: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@seo_api_bp.route('/seo/page/<page_type>')
def api_seo_page(page_type):
    """Get SEO settings for specific page type"""
    try:
        seo = SEOSettings.query.filter_by(page_type=page_type, is_active=True).first()
        
        if not seo:
            return jsonify({
                'success': True,
                'seo': {
                    'title': f'Default title for {page_type}',
                    'description': f'Default description for {page_type}',
                    'keywords': '',
                    'og_title': f'Default OG title for {page_type}',
                    'og_description': f'Default OG description for {page_type}',
                    'og_image': ''
                }
            })
        
        return jsonify({
            'success': True,
            'seo': {
                'title': seo.title,
                'description': seo.description,
                'keywords': seo.keywords,
                'og_title': seo.og_title,
                'og_description': seo.og_description,
                'og_image': seo.og_image
            }
        })
    except Exception as e:
        logging.error(f"Error getting SEO for page type {page_type}: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500
