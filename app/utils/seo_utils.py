"""
SEO Utilities - funkcje pomocnicze do zarządzania SEO
"""
from flask import current_app
from app.models import db, BlogPost, BlogCategory, BlogTag, EventSchedule, Section, MenuItem, SEOSettings
from datetime import datetime
import json
import re

class SEOManager:
    """Manager do zarządzania SEO dla różnych typów stron"""
    
    @staticmethod
    def get_seo_settings(page_type, fallback_to_default=True):
        """
        Pobierz ustawienia SEO dla danego typu strony
        
        Args:
            page_type (str): Typ strony (home, about, blog_post, etc.)
            fallback_to_default (bool): Czy używać domyślnych ustawień jeśli nie ma SEO
            
        Returns:
            dict: Ustawienia SEO lub None
        """
        try:
            seo = SEOSettings.query.filter_by(page_type=page_type, is_active=True).first()
            
            if seo:
                return {
                    'page_title': seo.page_title,
                    'meta_description': seo.meta_description,
                    'meta_keywords': seo.meta_keywords,
                    'og_title': seo.og_title,
                    'og_description': seo.og_description,
                    'og_image': seo.og_image,
                    'og_type': seo.og_type,
                    'twitter_card': seo.twitter_card,
                    'twitter_title': seo.twitter_title,
                    'twitter_description': seo.twitter_description,
                    'twitter_image': seo.twitter_image,
                    'canonical_url': seo.canonical_url,
                    'structured_data': json.loads(seo.structured_data) if seo.structured_data else None
                }
            
            # Fallback do domyślnych ustawień
            if fallback_to_default:
                return SEOManager.get_default_seo_settings()
                
            return None
            
        except Exception as e:
            current_app.logger.error(f"Error getting SEO settings for {page_type}: {str(e)}")
            return SEOManager.get_default_seo_settings()
    
    @staticmethod
    def get_default_seo_settings():
        """Pobierz domyślne ustawienia SEO"""
        return {
            'page_title': 'Klub Lepsze Życie - Rozwój osobisty i biznesowy',
            'meta_description': 'Klub Lepsze Życie - miejsce gdzie rozwijasz się osobisto i biznesowo. Dołącz do naszej społeczności i odkryj swój potencjał.',
            'meta_keywords': 'rozwój osobisty, biznes, coaching, mentoring, szkolenia',
            'og_title': 'Klub Lepsze Życie',
            'og_description': 'Klub Lepsze Życie - miejsce gdzie rozwijasz się osobisto i biznesowo.',
            'og_image': '/static/images/hero/hero-bg.jpg',
            'og_type': 'website',
            'twitter_card': 'summary_large_image',
            'twitter_title': 'Klub Lepsze Życie',
            'twitter_description': 'Klub Lepsze Życie - miejsce gdzie rozwijasz się osobisto i biznesowo.',
            'twitter_image': '/static/images/hero/hero-bg.jpg',
            'canonical_url': None,
            'structured_data': None
        }
    
    @staticmethod
    def generate_blog_post_seo(post):
        """Generuj SEO dla wpisu bloga"""
        if not post:
            return SEOManager.get_default_seo_settings()
        
        # Użyj meta tagów z posta jeśli istnieją
        if post.meta_title and post.meta_description:
            return {
                'page_title': post.meta_title,
                'meta_description': post.meta_description,
                'meta_keywords': ', '.join([tag.name for tag in post.tags]) if post.tags else None,
                'og_title': post.meta_title,
                'og_description': post.meta_description,
                'og_image': post.featured_image if post.featured_image else '/static/images/hero/hero-bg.jpg',
                'og_type': 'article',
                'twitter_card': 'summary_large_image',
                'twitter_title': post.meta_title,
                'twitter_description': post.meta_description,
                'twitter_image': post.featured_image if post.featured_image else '/static/images/hero/hero-bg.jpg',
                'canonical_url': None,
                'structured_data': SEOManager.generate_article_schema(post)
            }
        
        # Generuj automatycznie
        title = f"{post.title} - Klub Lepsze Życie"
        description = post.excerpt or post.content[:160].strip() + '...' if len(post.content) > 160 else post.content.strip()
        
        return {
            'page_title': title,
            'meta_description': description,
            'meta_keywords': ', '.join([tag.name for tag in post.tags]) if post.tags else None,
            'og_title': post.title,
            'og_description': description,
            'og_image': post.featured_image if post.featured_image else '/static/images/hero/hero-bg.jpg',
            'og_type': 'article',
            'twitter_card': 'summary_large_image',
            'twitter_title': post.title,
            'twitter_description': description,
            'twitter_image': post.featured_image if post.featured_image else '/static/images/hero/hero-bg.jpg',
            'canonical_url': None,
            'structured_data': SEOManager.generate_article_schema(post)
        }
    
    @staticmethod
    def generate_blog_category_seo(category):
        """Generuj SEO dla kategorii bloga"""
        if not category:
            return SEOManager.get_default_seo_settings()
        
        # Sprawdź czy istnieją ustawienia SEO dla tej kategorii
        seo = SEOManager.get_seo_settings(f'blog_category_{category.slug}', fallback_to_default=False)
        if seo:
            return seo
        
        # Generuj automatycznie
        title = f"Kategoria: {category.title} - Klub Lepsze Życie"
        description = category.description or f"Artykuły z kategorii {category.title} na blogu Klub Lepsze Życie."
        
        return {
            'page_title': title,
            'meta_description': description,
            'meta_keywords': f"{category.title}, blog, artykuły, klub lepsze życie",
            'og_title': f"Kategoria: {category.title}",
            'og_description': description,
            'og_image': '/static/images/hero/hero-bg.jpg',
            'og_type': 'website',
            'twitter_card': 'summary_large_image',
            'twitter_title': f"Kategoria: {category.title}",
            'twitter_description': description,
            'twitter_image': '/static/images/hero/hero-bg.jpg',
            'canonical_url': None,
            'structured_data': None
        }
    
    @staticmethod
    def generate_blog_tag_seo(tag):
        """Generuj SEO dla tagu bloga"""
        if not tag:
            return SEOManager.get_default_seo_settings()
        
        # Sprawdź czy istnieją ustawienia SEO dla tego tagu
        seo = SEOManager.get_seo_settings(f'blog_tag_{tag.slug}', fallback_to_default=False)
        if seo:
            return seo
        
        # Generuj automatycznie
        title = f"Tag: {tag.name} - Klub Lepsze Życie"
        description = f"Artykuły oznaczone tagiem {tag.name} na blogu Klub Lepsze Życie."
        
        return {
            'page_title': title,
            'meta_description': description,
            'meta_keywords': f"{tag.name}, blog, artykuły, klub lepsze życie",
            'og_title': f"Tag: {tag.name}",
            'og_description': description,
            'og_image': '/static/images/hero/hero-bg.jpg',
            'og_type': 'website',
            'twitter_card': 'summary_large_image',
            'twitter_title': f"Tag: {tag.name}",
            'twitter_description': description,
            'twitter_image': '/static/images/hero/hero-bg.jpg',
            'canonical_url': None,
            'structured_data': None
        }
    
    @staticmethod
    def generate_event_seo(event):
        """Generuj SEO dla wydarzenia"""
        if not event:
            return SEOManager.get_default_seo_settings()
        
        # Sprawdź czy istnieją ustawienia SEO dla tego wydarzenia
        seo = SEOManager.get_seo_settings(f'event_{event.id}', fallback_to_default=False)
        if seo:
            return seo
        
        # Generuj automatycznie
        title = f"{event.title} - Klub Lepsze Życie"
        description = event.description[:160].strip() + '...' if event.description and len(event.description) > 160 else (event.description or f"Wydarzenie: {event.title}")
        
        return {
            'page_title': title,
            'meta_description': description,
            'meta_keywords': f"{event.title}, wydarzenie, {event.event_type}, klub lepsze życie",
            'og_title': event.title,
            'og_description': description,
            'og_image': event.hero_background if event.hero_background else '/static/images/hero/hero-bg.jpg',
            'og_type': 'event',
            'twitter_card': 'summary_large_image',
            'twitter_title': event.title,
            'twitter_description': description,
            'twitter_image': event.hero_background if event.hero_background else '/static/images/hero/hero-bg.jpg',
            'canonical_url': None,
            'structured_data': SEOManager.generate_event_schema(event)
        }
    
    @staticmethod
    def generate_section_seo(section):
        """Generuj SEO dla sekcji"""
        if not section:
            return SEOManager.get_default_seo_settings()
        
        # Sprawdź czy istnieją ustawienia SEO dla tej sekcji
        seo = SEOManager.get_seo_settings(f'section_{section.id}', fallback_to_default=False)
        if seo:
            return seo
        
        # Generuj automatycznie
        title = f"{section.title} - Klub Lepsze Życie"
        description = section.description[:160].strip() + '...' if section.description and len(section.description) > 160 else (section.description or f"Sekcja: {section.title}")
        
        return {
            'page_title': title,
            'meta_description': description,
            'meta_keywords': f"{section.title}, sekcja, klub lepsze życie",
            'og_title': section.title,
            'og_description': description,
            'og_image': '/static/images/hero/hero-bg.jpg',
            'og_type': 'website',
            'twitter_card': 'summary_large_image',
            'twitter_title': section.title,
            'twitter_description': description,
            'twitter_image': '/static/images/hero/hero-bg.jpg',
            'canonical_url': None,
            'structured_data': None
        }
    
    @staticmethod
    def generate_article_schema(post):
        """Generuj schema.org dla artykułu"""
        if not post:
            return None
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": post.title,
            "description": post.meta_description or post.excerpt or post.content[:160],
            "author": {
                "@type": "Person",
                "name": post.author.name or post.author.email
            },
            "publisher": {
                "@type": "Organization",
                "name": "Klub Lepsze Życie",
                "logo": {
                    "@type": "ImageObject",
                    "url": "/static/images/logo.png"
                }
            },
            "datePublished": post.published_at.isoformat() if post.published_at else post.created_at.isoformat(),
            "dateModified": post.updated_at.isoformat() if post.updated_at else post.created_at.isoformat()
        }
        
        if post.featured_image:
            schema["image"] = {
                "@type": "ImageObject",
                "url": post.featured_image
            }
        
        if post.categories:
            schema["articleSection"] = [cat.title for cat in post.categories]
        
        if post.tags:
            schema["keywords"] = [tag.name for tag in post.tags]
        
        return schema
    
    @staticmethod
    def generate_event_schema(event):
        """Generuj schema.org dla wydarzenia"""
        if not event:
            return None
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": event.title,
            "description": event.description or f"Wydarzenie: {event.title}",
            "startDate": event.event_date.isoformat(),
            "organizer": {
                "@type": "Organization",
                "name": "Klub Lepsze Życie"
            }
        }
        
        if event.end_date:
            schema["endDate"] = event.end_date.isoformat()
        
        if event.location:
            schema["location"] = {
                "@type": "Place",
                "name": event.location
            }
        
        return schema
    
    @staticmethod
    def create_or_update_seo(page_type, seo_data):
        """Utwórz lub zaktualizuj ustawienia SEO"""
        try:
            seo = SEOSettings.query.filter_by(page_type=page_type).first()
            
            if seo:
                # Aktualizuj istniejące
                for key, value in seo_data.items():
                    if hasattr(seo, key):
                        setattr(seo, key, value)
                seo.updated_at = datetime.utcnow()
            else:
                # Utwórz nowe
                seo = SEOSettings(
                    page_type=page_type,
                    **seo_data
                )
                db.session.add(seo)
            
            db.session.commit()
            return seo
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating/updating SEO for {page_type}: {str(e)}")
            return None
    
    @staticmethod
    def get_available_page_types():
        """Pobierz listę dostępnych typów stron"""
        return [
            # Podstawowe strony
            {'value': 'home', 'label': 'Strona Główna'},
            {'value': 'about', 'label': 'O Nas'},
            {'value': 'benefits', 'label': 'Korzyści'},
            {'value': 'testimonials', 'label': 'Opinie'},
            {'value': 'contact', 'label': 'Kontakt'},
            
            # Blog
            {'value': 'blog_home', 'label': 'Strona Główna Blogu'},
            {'value': 'blog_search', 'label': 'Wyszukiwanie w Blogu'},
            
            # Użytkownik
            {'value': 'login', 'label': 'Logowanie'},
            {'value': 'profile', 'label': 'Profil użytkownika'},
            {'value': 'change_password', 'label': 'Zmiana hasła'},
            
            # Błędy
            {'value': '404', 'label': 'Strona 404'},
            
            # Admin
            {'value': 'admin', 'label': 'Panel Administratora'},
            
            # Dynamiczne typy (będą tworzone automatycznie)
            {'value': 'blog_category', 'label': 'Kategoria Blogu'},
            {'value': 'blog_tag', 'label': 'Tag Blogu'},
            {'value': 'blog_post', 'label': 'Wpis Blogu'},
            {'value': 'event', 'label': 'Wydarzenie'},
            {'value': 'section', 'label': 'Sekcja'},
            {'value': 'menu_item', 'label': 'Element Menu'}
        ]
