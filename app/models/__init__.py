"""
Models package - organized by functionality
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
import json

# Initialize database
db = SQLAlchemy()

# Import all models
from .user_model import User, PasswordResetToken
from .content_model import MenuItem, Section, BenefitItem, Testimonial, SocialLink, FAQ
from .events_model import EventSchedule, EventRegistration
from .email_model import EmailTemplate, DefaultEmailTemplate, UserGroup, UserGroupMember, EmailCampaign, EmailQueue, EmailLog
from .blog_model import BlogCategory, BlogTag, BlogPost, BlogComment, BlogPostImage
from .seo_model import SEOSettings, FooterSettings, LegalDocument

# Association tables
from .associations_model import blog_post_categories, blog_post_tags

__all__ = [
    'db',
    'User',
    'PasswordResetToken',
    'MenuItem',
    'Section',
    'BenefitItem',
    'Testimonial',
    'SocialLink',
    'FAQ',
    'EventSchedule',
    'EventRegistration',
    'EmailTemplate',
    'DefaultEmailTemplate',
    'UserGroup',
    'UserGroupMember',
    'EmailCampaign',
    'EmailQueue',
    'EmailLog',
    'BlogCategory',
    'BlogTag',
    'BlogPost',
    'BlogComment',
    'BlogPostImage',
    'SEOSettings',
    'FooterSettings',
    'LegalDocument',
    'blog_post_categories',
    'blog_post_tags'
]
