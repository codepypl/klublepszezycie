"""
Blog API Module - modularized blog functionality
"""

from .posts_api import posts_api_bp
from .categories_api import categories_api_bp
from .tags_api import tags_api_bp
from .comments_api import comments_api_bp
from .media_api import media_api_bp

# Export all blueprints
__all__ = [
    'posts_api_bp',
    'categories_api_bp', 
    'tags_api_bp',
    'comments_api_bp',
    'media_api_bp'
]




