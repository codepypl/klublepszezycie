from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Section(db.Model):
    __tablename__ = 'sections'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    title = db.Column(db.String(200))
    subtitle = db.Column(db.Text)
    content = db.Column(db.Text)
    background_image = db.Column(db.String(200))
    # Additional fields for About section
    pillars_data = db.Column(db.Text)  # JSON string for pillar items
    final_text = db.Column(db.Text)    # Final text in About section
    floating_cards_data = db.Column(db.Text)  # JSON string for floating cards
    # New fields for enabling/disabling features
    enable_pillars = db.Column(db.Boolean, default=False)
    enable_floating_cards = db.Column(db.Boolean, default=False)
    pillars_count = db.Column(db.Integer, default=4)  # Default number of pillars
    floating_cards_count = db.Column(db.Integer, default=3)  # Default number of floating cards
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BenefitItem(db.Model):
    __tablename__ = 'benefit_items'
    
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100))
    image = db.Column(db.String(200))
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    section = db.relationship('Section', backref='benefit_items')

class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    
    id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    member_since = db.Column(db.String(20))
    rating = db.Column(db.Integer, default=5)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SocialLink(db.Model):
    __tablename__ = 'social_links'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(100))
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Registration(db.Model):
    __tablename__ = 'registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    presentation_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, attended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Page(db.Model):
    __tablename__ = 'pages'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    content = db.Column(db.Text)  # HTML content from WYSIWYG editor
    meta_description = db.Column(db.String(300))
    meta_keywords = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    is_published = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Page {self.title}>'

class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    text_content = db.Column(db.Text)  # Plain text version
    template_type = db.Column(db.String(50), nullable=False)  # welcome, reminder, newsletter, etc.
    variables = db.Column(db.Text)  # JSON string of available variables
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailTemplate {self.name}>'

class EmailSubscription(db.Model):
    __tablename__ = 'email_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    subscription_type = db.Column(db.String(50), default='all')  # all, reminders, newsletter, etc.
    unsubscribe_token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailSubscription {self.email}>'

class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    subject = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='sent')  # sent, failed, bounced
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    template = db.relationship('EmailTemplate', backref='email_logs')
    
    def __repr__(self):
        return f'<EmailLog {self.email} - {self.subject}>'

class FAQ(db.Model):
    __tablename__ = 'faqs'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SEOSettings(db.Model):
    __tablename__ = 'seo_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    page_type = db.Column(db.String(50), nullable=False, unique=True)  # 'home', 'about', 'benefits', etc.
    page_title = db.Column(db.String(60), nullable=False)
    meta_description = db.Column(db.String(160), nullable=False)
    meta_keywords = db.Column(db.String(200))
    og_title = db.Column(db.String(60))
    og_description = db.Column(db.String(160))
    og_image = db.Column(db.String(200))
    og_type = db.Column(db.String(20), default='website')
    twitter_card = db.Column(db.String(20), default='summary_large_image')
    twitter_title = db.Column(db.String(60))
    twitter_description = db.Column(db.String(160))
    twitter_image = db.Column(db.String(200))
    canonical_url = db.Column(db.String(200))
    structured_data = db.Column(db.Text)  # JSON-LD schema
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EventSchedule(db.Model):
    __tablename__ = 'event_schedule'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # Prezentacja, Webinar, Spotkanie, Event, Inne
    event_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)  # Data zakończenia wydarzenia
    description = db.Column(db.Text)  # Opis wydarzenia z edytora WYSIWYG
    meeting_link = db.Column(db.String(500))  # Link do spotkania
    location = db.Column(db.String(200))  # Lokalizacja wydarzenia
    is_active = db.Column(db.Boolean, default=True)
    is_published = db.Column(db.Boolean, default=False)  # Czy opublikowane na stronie

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<EventSchedule {self.title} - {self.event_type} - {self.event_date}>'
    



class PresentationSchedule(db.Model):
    __tablename__ = 'presentation_schedule'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    next_presentation_date = db.Column(db.DateTime, nullable=False)
    custom_text = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PresentationSchedule {self.title} - {self.next_presentation_date}>'

