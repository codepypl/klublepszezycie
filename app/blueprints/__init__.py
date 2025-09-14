# Blueprints module
from .public import public_bp
from .admin import admin_bp
from .api import api_bp
from .auth import auth_bp
from .blog import blog_bp
from .seo import seo_bp
from .social import social_bp
from .events import events_bp
from .users import users_bp
from .footer import footer_bp
from .email_api import email_api_bp
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'crm', 'admin'))
from ankieter import ankieter_bp

__all__ = ['public_bp', 'admin_bp', 'api_bp', 'auth_bp', 'blog_bp', 'seo_bp', 'social_bp', 'events_bp', 'users_bp', 'footer_bp', 'email_api_bp', 'ankieter_bp']
