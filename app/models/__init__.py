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
from .events_model import EventSchedule
from .event_registration_model import EventRegistration
from .email_model import EmailTemplate, EmailCampaign, EmailQueue, EmailLog, EmailReminder
from .user_groups_model import UserGroup, UserGroupMember
from .blog_model import BlogCategory, BlogTag, BlogPost, BlogComment, BlogPostImage
from .seo_model import SEOSettings, FooterSettings, LegalDocument
from .user_logs_model import UserLogs
from .user_history_model import UserHistory
from .stats_model import Stats
from .system_logs_model import SystemLog
from .crm_model import Campaign, Contact, Call, BlacklistEntry, ImportFile, ImportRecord
# TaskQueue usunięty - niepotrzebny

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
    'UserGroup',
    'UserGroupMember',
    'EmailCampaign',
    'EmailQueue',
    'EmailLog',
    'EmailReminder',
    'BlogCategory',
    'BlogTag',
    'BlogPost',
    'BlogComment',
    'BlogPostImage',
    'SEOSettings',
    'FooterSettings',
    'LegalDocument',
    'UserLogs',
    'UserHistory',
    'Stats',
    'SystemLog',
    'Campaign',
    'Contact',
    'Call',
    'BlacklistEntry',
    'ImportFile',
    'ImportRecord',
    # 'TaskQueue',  # Usunięty
    'SocialMediaConfig',
    'SocialMediaPost',
    'AutoPostingQueue',
    'blog_post_categories',
    'blog_post_tags'
]
