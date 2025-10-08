"""
SEO and legal document models
"""
from datetime import datetime
from app.utils.timezone_utils import get_local_datetime
from . import db

class SEOSettings(db.Model):
    """SEO Settings for different page types"""
    __tablename__ = 'seo_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    page_type = db.Column(db.String(50), unique=True, nullable=False)  # home, blog, event, etc.
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    keywords = db.Column(db.Text)  # Changed from String(500) to Text to match database
    og_title = db.Column(db.String(200))
    og_description = db.Column(db.Text)
    og_image = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_local_datetime)
    updated_at = db.Column(db.DateTime, default=get_local_datetime, onupdate=get_local_datetime)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)  # Added from database schema
    
    def __repr__(self):
        return f'<SEOSettings {self.page_type}>'

class FooterSettings(db.Model):
    """Footer settings"""
    __tablename__ = 'footer_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    company_title = db.Column(db.String(100))
    company_description = db.Column(db.Text)
    contact_title = db.Column(db.String(100))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(20))
    social_title = db.Column(db.String(100))
    company_name = db.Column(db.String(100))
    show_privacy_policy = db.Column(db.Boolean, default=True)
    show_terms = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_local_datetime)
    updated_at = db.Column(db.DateTime, default=get_local_datetime, onupdate=get_local_datetime)
    
    def __repr__(self):
        return f'<FooterSettings {self.company_name}>'

class LegalDocument(db.Model):
    """Legal documents (privacy policy, terms)"""
    __tablename__ = 'legal_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(50), unique=True, nullable=False)  # privacy_policy, terms_of_service, etc.
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=get_local_datetime)
    updated_at = db.Column(db.DateTime, default=get_local_datetime, onupdate=get_local_datetime)
    
    def __repr__(self):
        return f'<LegalDocument {self.document_type}>'
