"""
API package
"""
# Main API blueprint not needed - individual API modules are imported separately
from .email_api import email_bp
from .users_api import users_api_bp
from .testimonials_api import testimonials_api_bp
from .sections_api import sections_api_bp
from .menu_api import menu_api_bp
from .faq_api import faq_api_bp
from .benefits_api import benefits_api_bp
from .events_api import events_api_bp
from .blog_api import blog_api_bp
from .seo_api import seo_api_bp
from .social_api import social_api_bp

__all__ = [
    'email_bp',
    'users_api_bp',
    'testimonials_api_bp',
    'sections_api_bp',
    'menu_api_bp',
    'faq_api_bp',
    'benefits_api_bp',
    'events_api_bp',
    'blog_api_bp',
    'seo_api_bp',
    'social_api_bp'
]
