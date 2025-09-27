"""
SEO business logic controller
"""
from flask import request
from flask_login import login_required, current_user
from app.models import db, SEOSettings
from datetime import datetime

class SEOController:
    """SEO business logic controller"""
    
    @staticmethod
    def get_seo_settings():
        """Get all SEO settings"""
        try:
            settings = SEOSettings.query.order_by(SEOSettings.page_type.asc()).all()
            return {
                'success': True,
                'settings': settings
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'settings': []
            }
    
    @staticmethod
    def get_seo_setting(setting_id):
        """Get single SEO setting"""
        try:
            setting = SEOSettings.query.get(setting_id)
            if not setting:
                return {
                    'success': False,
                    'error': 'Ustawienie SEO nie zostało znalezione',
                    'setting': None
                }
            
            return {
                'success': True,
                'setting': setting
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'setting': None
            }
    
    @staticmethod
    def create_seo_setting(page_type, title, description, keywords, og_title=None, og_description=None, og_image=None):
        """Create new SEO setting"""
        try:
            if not all([page_type, title, description]):
                return {
                    'success': False,
                    'error': 'Typ strony, tytuł i opis są wymagane'
                }
            
            # Check if page_type already exists
            existing = SEOSettings.query.filter_by(page_type=page_type).first()
            if existing:
                return {
                    'success': False,
                    'error': 'Ustawienia SEO dla tego typu strony już istnieją'
                }
            
            seo = SEOSettings(
                page_type=page_type,
                title=title,
                description=description,
                keywords=keywords,
                og_title=og_title,
                og_description=og_description,
                og_image=og_image,
                created_by=current_user.id
            )
            
            db.session.add(seo)
            db.session.commit()
            
            return {
                'success': True,
                'setting': seo,
                'message': 'Ustawienia SEO zostały utworzone pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def update_seo_setting(setting_id, page_type, title, description, keywords, og_title=None, og_description=None, og_image=None):
        """Update SEO setting"""
        try:
            setting = SEOSettings.query.get(setting_id)
            if not setting:
                return {
                    'success': False,
                    'error': 'Ustawienie SEO nie zostało znalezione'
                }
            
            # Check if page_type is taken by another setting
            existing = SEOSettings.query.filter(
                SEOSettings.page_type == page_type,
                SEOSettings.id != setting_id
            ).first()
            if existing:
                return {
                    'success': False,
                    'error': 'Ustawienia SEO dla tego typu strony już istnieją'
                }
            
            setting.page_type = page_type
            setting.title = title
            setting.description = description
            setting.keywords = keywords
            setting.og_title = og_title
            setting.og_description = og_description
            setting.og_image = og_image
            setting.updated_at = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
            
            db.session.commit()
            
            return {
                'success': True,
                'setting': setting,
                'message': 'Ustawienia SEO zostały zaktualizowane pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def delete_seo_setting(setting_id):
        """Delete SEO setting"""
        try:
            setting = SEOSettings.query.get(setting_id)
            if not setting:
                return {
                    'success': False,
                    'error': 'Ustawienie SEO nie zostało znalezione'
                }
            
            db.session.delete(setting)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Ustawienia SEO zostały usunięte pomyślnie'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def get_seo_for_page(page_type):
        """Get SEO settings for specific page type"""
        try:
            setting = SEOSettings.query.filter_by(page_type=page_type).first()
            if not setting:
                return {
                    'success': False,
                    'error': 'Ustawienia SEO dla tej strony nie zostały znalezione',
                    'setting': None
                }
            
            return {
                'success': True,
                'setting': setting
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'setting': None
            }
