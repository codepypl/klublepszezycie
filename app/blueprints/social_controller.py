"""
Social Media business logic controller
"""
from flask import request, jsonify
from flask_login import login_required, current_user
from app.models import db, SocialLink
import re

class SocialController:
    """Social Media business logic controller"""
    
    @staticmethod
    def get_social_links():
        """Get all social media links"""
        try:
            links = SocialLink.query.order_by(SocialLink.order.asc()).all()
            return {
                'success': True,
                'links': links
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'links': []
            }
    
    @staticmethod
    def get_social_link(link_id):
        """Get single social media link"""
        try:
            link = SocialLink.query.get(link_id)
            if not link:
                return {
                    'success': False,
                    'error': 'Link nie został znaleziony',
                    'link': None
                }
            
            return {
                'success': True,
                'link': link
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'link': None
            }
    
    @staticmethod
    def create_social_link(platform, url, icon_class, is_active=True, order=0):
        """Create new social media link"""
        try:
            if not all([platform, url, icon_class]):
                return {
                    'success': False,
                    'error': 'Platforma, URL i klasa ikony są wymagane'
                }
            
            # Validate URL format
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(url):
                return {
                    'success': False,
                    'error': 'Nieprawidłowy format URL'
                }
            
            # Check if platform already exists
            existing = SocialLink.query.filter_by(platform=platform).first()
            if existing:
                return {
                    'success': False,
                    'error': 'Link dla tej platformy już istnieje'
                }
            
            link = SocialLink(
                platform=platform,
                url=url,
                icon_class=icon_class,
                is_active=is_active,
                order=order
            )
            
            db.session.add(link)
            db.session.commit()
            
            return {
                'success': True,
                'link': link,
                'message': 'Link został utworzony pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_social_link(link_id, platform, url, icon_class, is_active=True, order=0):
        """Update social media link"""
        try:
            link = SocialLink.query.get(link_id)
            if not link:
                return {
                    'success': False,
                    'error': 'Link nie został znaleziony'
                }
            
            # Validate URL format
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(url):
                return {
                    'success': False,
                    'error': 'Nieprawidłowy format URL'
                }
            
            # Check if platform is taken by another link
            existing = SocialLink.query.filter(
                SocialLink.platform == platform,
                SocialLink.id != link_id
            ).first()
            if existing:
                return {
                    'success': False,
                    'error': 'Link dla tej platformy już istnieje'
                }
            
            link.platform = platform
            link.url = url
            link.icon_class = icon_class
            link.is_active = is_active
            link.order = order
            
            db.session.commit()
            
            return {
                'success': True,
                'link': link,
                'message': 'Link został zaktualizowany pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def delete_social_link(link_id):
        """Delete social media link"""
        try:
            link = SocialLink.query.get(link_id)
            if not link:
                return {
                    'success': False,
                    'error': 'Link nie został znaleziony'
                }
            
            db.session.delete(link)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Link został usunięty pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def toggle_social_link_status(link_id):
        """Toggle social media link active status"""
        try:
            link = SocialLink.query.get(link_id)
            if not link:
                return {
                    'success': False,
                    'error': 'Link nie został znaleziony'
                }
            
            link.is_active = not link.is_active
            db.session.commit()
            
            return {
                'success': True,
                'link': link,
                'message': f'Link został {"aktywowany" if link.is_active else "deaktywowany"}'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def reorder_social_links(link_orders):
        """Reorder social media links"""
        try:
            for link_id, order in link_orders.items():
                link = SocialLink.query.get(link_id)
                if link:
                    link.order = order
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Kolejność linków została zaktualizowana'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
