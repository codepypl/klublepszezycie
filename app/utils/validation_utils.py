"""
Validation utility functions
"""
import os
import re
import unicodedata
from werkzeug.utils import secure_filename
from datetime import datetime

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'mov'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_type(file):
    """Validate uploaded file type and size"""
    if not file or file.filename == '':
        return False, "Nie wybrano pliku"
    
    if not allowed_file(file.filename):
        return False, f"Nieprawidłowy typ pliku. Dozwolone: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size (50MB max)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > 50 * 1024 * 1024:  # 50MB
        return False, "Plik jest za duży. Maksymalny rozmiar: 50MB"
    
    return True, "OK"

def validate_event_date(event_date_str):
    """Validate event date string"""
    try:
        # Try parsing the date string
        event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
        
        # Check if date is in the future
        from .timezone import get_local_now
        now = get_local_now()
        
        if event_date.date() < now.date():
            return False, "Data wydarzenia nie może być w przeszłości"
        
        return True, event_date
    except ValueError:
        return False, "Nieprawidłowy format daty. Użyj YYYY-MM-DD"
    except Exception as e:
        return False, f"Błąd walidacji daty: {str(e)}"

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    # Check if it has 9 digits (Polish phone number)
    return len(digits_only) == 9

def validate_blog_post(data):
    """Validate blog post data"""
    errors = []
    
    # Required fields
    if not data.get('title') or not data['title'].strip():
        errors.append('Tytuł jest wymagany')
    
    if not data.get('content') or not data['content'].strip():
        errors.append('Treść jest wymagana')
    
    if not data.get('slug') or not data['slug'].strip():
        errors.append('Slug jest wymagany')
    
    # Validate slug format
    if data.get('slug'):
        slug = data['slug'].strip()
        if not re.match(r'^[a-z0-9-]+$', slug):
            errors.append('Slug może zawierać tylko małe litery, cyfry i myślniki')
    
    # Validate status
    if data.get('status') and data['status'] not in ['draft', 'published', 'archived']:
        errors.append('Nieprawidłowy status artykułu')
    
    # Validate allow_comments
    if 'allow_comments' in data:
        if not isinstance(data['allow_comments'], bool):
            try:
                data['allow_comments'] = str(data['allow_comments']).lower() == 'true'
            except:
                errors.append('Nieprawidłowa wartość dla komentarzy')
    
    return len(errors) == 0, errors

def validate_blog_categories(categories_data):
    """Validate blog categories data"""
    if not categories_data:
        return True, []
    
    # Check if it's already a list (parsed JSON) or needs parsing
    if isinstance(categories_data, list):
        categories = categories_data
    else:
        try:
            import json
            categories = json.loads(categories_data)
        except:
            return False, ['Nieprawidłowy format kategorii']
    
    if not isinstance(categories, list):
        return False, ['Kategorie muszą być listą']
    
    for cat_id in categories:
        if not isinstance(cat_id, int) or cat_id <= 0:
            return False, ['Nieprawidłowe ID kategorii']
    
    return True, []

def validate_blog_tags(tags_data):
    """Validate blog tags data"""
    if not tags_data:
        return True, []
    
    # Check if it's already a list (parsed JSON) or needs parsing
    if isinstance(tags_data, list):
        tags = tags_data
    else:
        try:
            import json
            tags = json.loads(tags_data)
        except:
            return False, ['Nieprawidłowy format tagów']
    
    if not isinstance(tags, list):
        return False, ['Tagi muszą być listą']
    
    for tag_name in tags:
        if not isinstance(tag_name, str) or not tag_name.strip():
            return False, ['Nieprawidłowa nazwa tagu']
    
    return True, []

def validate_featured_image(file):
    """Validate featured image upload"""
    if not file or file.filename == '':
        return True, None  # No file is OK
    
    # Check file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    if not allowed_file(file.filename):
        return False, f'Nieprawidłowy format pliku. Dozwolone: {", ".join(allowed_extensions)}'
    
    # Check file size (16MB max)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > 16 * 1024 * 1024:  # 16MB
        return False, 'Plik jest za duży. Maksymalny rozmiar: 16MB'
    
    return True, None

def create_slug(text, max_length=200):
    """
    Create a URL-friendly slug from text
    
    Args:
        text (str): Input text to convert to slug
        max_length (int): Maximum length of the slug
    
    Returns:
        str: URL-friendly slug
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove accents and special characters
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    
    # Replace spaces and special characters with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Truncate to max_length
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text

def generate_unique_slug(text, model_class, field_name='slug', exclude_id=None, max_length=200):
    """
    Generate a unique slug for a model
    
    Args:
        text (str): Input text to convert to slug
        model_class: SQLAlchemy model class
        field_name (str): Name of the slug field in the model
        exclude_id (int): ID to exclude from uniqueness check (for updates)
        max_length (int): Maximum length of the slug
    
    Returns:
        str: Unique slug
    """
    base_slug = create_slug(text, max_length)
    slug = base_slug
    counter = 1
    
    while True:
        # Check if slug exists
        query = model_class.query.filter(getattr(model_class, field_name) == slug)
        if exclude_id:
            query = query.filter(model_class.id != exclude_id)
        
        if not query.first():
            break
        
        # Add counter to make it unique
        counter += 1
        slug = f"{base_slug}-{counter}"
        
        # Prevent infinite loop
        if counter > 1000:
            import uuid
            slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
            break
    
    return slug

