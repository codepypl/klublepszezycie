"""
Routes package - organized by functionality
"""
from .public_route import public_bp
from .admin_route import admin_bp
from .auth_route import auth_bp
from .blog_route import blog_bp, blog_admin_bp
from .seo_route import seo_bp
from .social_route import social_bp
from .events_route import events_bp
from .users_route import users_bp
from .footer_route import footer_bp
from .crm_routes import crm_bp
from .ankieter_routes import ankieter_bp

__all__ = [
    'public_bp',
    'admin_bp',
    'auth_bp',
    'blog_bp',
    'blog_admin_bp',
    'seo_bp',
    'social_bp',
    'events_bp',
    'users_bp',
    'footer_bp',
    'crm_bp',
    'ankieter_bp'
]