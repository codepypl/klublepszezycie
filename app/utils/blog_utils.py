"""
Blog utilities - helper functions for blog functionality
"""
from flask import url_for
from app.models import BlogCategory, BlogPost
import logging

def generate_blog_link(link_data):
    """
    Generuje link do bloga na podstawie konfiguracji linku
    
    Args:
        link_data (dict or str): Konfiguracja linku:
            - dict z polami: type, value
            - str w formacie "type:value" (np. "category:slug", "post:slug")
    
    Returns:
        str: URL do odpowiedniej strony bloga lub None jeśli błąd
    """
    if not link_data:
        return None
    
    # Handle string format from JavaScript (e.g., "category:slug", "post:slug")
    if isinstance(link_data, str):
        if ':' in link_data:
            link_type, value = link_data.split(':', 1)
        else:
            # Handle simple values like "blog_index"
            link_type = link_data
            value = None
    elif isinstance(link_data, dict):
        link_type = link_data.get('type')
        value = link_data.get('value')
    else:
        return None
    
    if not link_type:
        return None
    
    try:
        if link_type == 'menu':
            # Link do menu głównego (np. #blog)
            return f"#{value}" if value else None
        
        elif link_type == 'category':
            # Link do kategorii bloga
            if not value:
                return None
            category = BlogCategory.query.filter_by(slug=value, is_active=True).first()
            if category:
                return url_for('blog.category_detail', slug=value)
        
        elif link_type == 'subcategory':
            # Link do podkategorii bloga (podkategorie to też kategorie z parent_id)
            if not value:
                return None
            subcategory = BlogCategory.query.filter_by(slug=value, is_active=True).first()
            if subcategory:
                return url_for('blog.category_detail', slug=value)
        
        elif link_type == 'post':
            # Link do konkretnego posta
            if not value:
                return None
            post = BlogPost.query.filter_by(slug=value, status='published').first()
            if post:
                # Use new URL structure with category
                if post.categories:
                    primary_category = post.categories[0]
                    if primary_category.parent:
                        return url_for('blog.post_detail_with_category', 
                                     category_slug=primary_category.slug, 
                                     post_slug=value)
                    else:
                        return url_for('blog.post_detail_with_category', 
                                     category_slug=primary_category.slug, 
                                     post_slug=value)
                else:
                    return url_for('blog.post_detail', slug=value)
        
        elif link_type == 'blog_index':
            # Link do głównej strony bloga
            return url_for('blog.index')
        
    except Exception as e:
        logging.error(f"Error generating blog link: {str(e)}")
        return None
    
    return None

def get_blog_categories_for_select():
    """
    Pobiera kategorie bloga w formacie odpowiednim dla selectów w formularzach
    
    Returns:
        list: Lista kategorii z pełną ścieżką (np. "Parent > Child > Subchild")
    """
    try:
        categories = BlogCategory.query.filter_by(is_active=True).order_by(BlogCategory.sort_order).all()
        result = []
        
        for category in categories:
            result.append({
                'id': category.id,
                'slug': category.slug,
                'title': category.full_path,
                'value': category.slug
            })
        
        return result
    except Exception as e:
        logging.error(f"Error getting blog categories for select: {str(e)}")
        return []

def get_blog_posts_for_select():
    """
    Pobiera opublikowane posty bloga w formacie odpowiednim dla selectów w formularzach
    
    Returns:
        list: Lista postów z tytułem i slugiem
    """
    try:
        posts = BlogPost.query.filter_by(status='published').order_by(BlogPost.published_at.desc()).all()
        result = []
        
        for post in posts:
            result.append({
                'id': post.id,
                'slug': post.slug,
                'title': post.title,
                'value': post.slug
            })
        
        return result
    except Exception as e:
        logging.error(f"Error getting blog posts for select: {str(e)}")
        return []

def validate_blog_link_data(link_data):
    """
    Waliduje dane linku do bloga
    
    Args:
        link_data (dict): Dane linku do walidacji
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not link_data or not isinstance(link_data, dict):
        return False, "Dane linku są nieprawidłowe"
    
    link_type = link_data.get('type')
    value = link_data.get('value')
    
    if not link_type:
        return False, "Typ linku jest wymagany"
    
    if not value:
        return False, "Wartość linku jest wymagana"
    
    valid_types = ['menu', 'category', 'subcategory', 'post', 'blog_index']
    if link_type not in valid_types:
        return False, f"Nieprawidłowy typ linku. Dozwolone: {', '.join(valid_types)}"
    
    # Sprawdź czy kategoria/post istnieje (jeśli to nie jest menu lub blog_index)
    if link_type in ['category', 'subcategory']:
        category = BlogCategory.query.filter_by(slug=value, is_active=True).first()
        if not category:
            return False, f"Kategoria '{value}' nie została znaleziona"
    
    elif link_type == 'post':
        post = BlogPost.query.filter_by(slug=value, status='published').first()
        if not post:
            return False, f"Post '{value}' nie został znaleziony"
    
    return True, None
