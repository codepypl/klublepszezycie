from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=True)  # Made nullable for new system
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))  # Full name of the user
    phone = db.Column(db.String(20))  # Phone number
    club_member = db.Column(db.Boolean, default=False)  # Whether user wants to join the club
    is_active = db.Column(db.Boolean, default=True)  # Whether the account is active
    is_admin = db.Column(db.Boolean, default=False)
    is_temporary_password = db.Column(db.Boolean, default=True)  # Whether user needs to change password
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)  # URL for main site
    blog_url = db.Column(db.String(200))  # URL for blog pages (optional)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    blog = db.Column(db.Boolean, default=False)  # True if this menu item should appear on blog pages
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
    order = db.Column(db.Integer, default=0)
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


# Email models removed - will be redesigned from scratch

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
    max_participants = db.Column(db.Integer)  # Maksymalna liczba uczestników
    is_active = db.Column(db.Boolean, default=True)
    is_published = db.Column(db.Boolean, default=False)  # Czy opublikowane na stronie
    is_archived = db.Column(db.Boolean, default=False)  # Czy wydarzenie jest archiwalne (zakończone)
    hero_background = db.Column(db.String(500))  # Ścieżka do zdjęcia/wideo jako tło bannera
    hero_background_type = db.Column(db.String(20), default='image')  # 'image' lub 'video'

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<EventSchedule {self.title} - {self.event_type} - {self.event_date}>'
    
    def is_ended(self):
        """Sprawdza czy wydarzenie się zakończyło"""
        from datetime import datetime
        now = datetime.now()
        
        if self.end_date:
            return now > self.end_date
        else:
            # Jeśli nie ma end_date, sprawdź event_date + 2 godziny
            return now > self.event_date.replace(hour=self.event_date.hour + 2)
    
    def archive(self):
        """Archiwizuje wydarzenie"""
        self.is_archived = True
        self.is_active = False
        self.is_published = False
        return self
    



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


class EventRegistration(db.Model):
    """Zapisy na konkretne wydarzenia"""
    __tablename__ = 'event_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    
    # Status zapisu
    status = db.Column(db.String(20), default='confirmed')  # confirmed, attended, cancelled
    
    # Preferencje powiadomień
    wants_club_news = db.Column(db.Boolean, default=False)  # Czy chce dołączyć do klubu
    notification_preferences = db.Column(db.Text)  # JSON z preferencjami powiadomień
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    event = db.relationship('EventSchedule', backref='registrations')
    
    def __repr__(self):
        return f'<EventRegistration {self.name} - {self.email} - Event {self.event_id}>'


class EventNotification(db.Model):
    """Harmonogram powiadomień o wydarzeniach"""
    __tablename__ = 'event_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=False)
    
    # Typ powiadomienia
    notification_type = db.Column(db.String(20), nullable=False)  # '24h_before', '1h_before', '5min_before'
    
    # Status powiadomienia
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed
    
    # Czas wysłania
    scheduled_at = db.Column(db.DateTime, nullable=False)
    sent_at = db.Column(db.DateTime)
    
    # Szczegóły
    subject = db.Column(db.String(200))
    template_name = db.Column(db.String(100))
    recipient_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    event = db.relationship('EventSchedule', backref='notifications')
    
    def __repr__(self):
        return f'<EventNotification {self.event.title} - {self.notification_type} - {self.scheduled_at}>'


class EventRecipientGroup(db.Model):
    """Grupy odbiorców powiadomień o konkretnych wydarzeniach"""
    __tablename__ = 'event_recipient_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Kryteria grupy
    group_type = db.Column(db.String(20), nullable=False)  # 'event_registrations', 'declined_club', 'custom'
    criteria_config = db.Column(db.Text)  # JSON z konfiguracją kryteriów
    
    # Liczba członków (cache)
    member_count = db.Column(db.Integer, default=0)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    event = db.relationship('EventSchedule', backref='recipient_groups')
    
    def __repr__(self):
        return f'<EventRecipientGroup {self.name} - Event {self.event_id}>'


# Old UserGroup and UserGroupMember models removed - replaced with new email system models


# Additional email models removed - will be redesigned from scratch

# New Email System Models
class EmailTemplate(db.Model):
    """Email templates for the mailing system"""
    __tablename__ = 'email_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    text_content = db.Column(db.Text)  # Plain text version
    template_type = db.Column(db.String(50), default='email')  # welcome, event_reminder, registration_confirmation, campaign
    variables = db.Column(db.Text)  # JSON string of available variables
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailTemplate {self.name}>'

class UserGroup(db.Model):
    """User groups for email campaigns"""
    __tablename__ = 'user_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    group_type = db.Column(db.String(50), nullable=False)  # event_based, club_members, manual
    criteria = db.Column(db.Text)  # JSON with criteria
    is_active = db.Column(db.Boolean, default=True)
    member_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserGroup {self.name} ({self.group_type})>'

class UserGroupMember(db.Model):
    """Members of user groups"""
    __tablename__ = 'user_group_members'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Can be null for manual entries
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100))
    member_type = db.Column(db.String(20), default='manual')  # manual, auto, club_member
    is_active = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    group = db.relationship('UserGroup', backref=db.backref('members', cascade='all, delete-orphan'))
    user = db.relationship('User', backref='group_memberships')
    
    def __repr__(self):
        return f'<UserGroupMember {self.email} in group {self.group_id}>'

class EmailCampaign(db.Model):
    """Email campaigns"""
    __tablename__ = 'email_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'), nullable=True)
    content_variables = db.Column(db.Text)  # JSON with content to insert into template
    recipient_groups = db.Column(db.Text)  # JSON array with group IDs
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, sending, completed, cancelled
    scheduled_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    total_recipients = db.Column(db.Integer, default=0)
    sent_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    template = db.relationship('EmailTemplate', backref='campaigns')
    
    def __repr__(self):
        return f'<EmailCampaign {self.name} ({self.status})>'

class EmailQueue(db.Model):
    """Email queue for processing"""
    __tablename__ = 'email_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    to_email = db.Column(db.String(120), nullable=False)
    to_name = db.Column(db.String(100))
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    text_content = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed, bounced
    scheduled_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'), nullable=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('email_campaigns.id'), nullable=True)
    context = db.Column(db.Text)  # JSON with template variables
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    template = db.relationship('EmailTemplate', backref='queued_emails')
    campaign = db.relationship('EmailCampaign', backref='queued_emails')
    
    def __repr__(self):
        return f'<EmailQueue {self.to_email} - {self.status}>'

class EmailLog(db.Model):
    """Email logs for tracking"""
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='sent')  # sent, failed, bounced
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    error_message = db.Column(db.Text)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'), nullable=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('email_campaigns.id'), nullable=True)
    recipient_data = db.Column(db.Text)  # JSON with recipient info
    
    # Relationships
    template = db.relationship('EmailTemplate', backref='email_logs')
    campaign = db.relationship('EmailCampaign', backref='email_logs')
    
    def __repr__(self):
        return f'<EmailLog {self.email} - {self.status}>'

# Blog Models
class BlogCategory(db.Model):
    """Blog categories with hierarchical structure"""
    __tablename__ = 'blog_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('blog_categories.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = db.relationship('BlogCategory', remote_side=[id], backref='children')
    posts = db.relationship('BlogPost', secondary='blog_post_categories', back_populates='categories')
    
    def __repr__(self):
        return f'<BlogCategory {self.title}>'
    
    @property
    def posts_count(self):
        return len(self.posts)
    
    @property
    def full_path(self):
        """Get full category path (e.g., 'Parent > Child > Subchild')"""
        path = [self.title]
        current = self.parent
        while current:
            path.insert(0, current.title)
            current = current.parent
        return ' > '.join(path)

class BlogTag(db.Model):
    """Blog tags"""
    __tablename__ = 'blog_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')  # Hex color for display
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('BlogPost', secondary='blog_post_tags', back_populates='tags')
    
    def __repr__(self):
        return f'<BlogTag {self.name}>'
    
    @property
    def posts_count(self):
        return len(self.posts)

class BlogPost(db.Model):
    """Blog posts/articles"""
    __tablename__ = 'blog_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    excerpt = db.Column(db.Text)  # Short description
    content = db.Column(db.Text, nullable=False)
    featured_image = db.Column(db.String(200))  # URL to featured image
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # SEO fields
    meta_title = db.Column(db.String(200))
    meta_description = db.Column(db.Text)
    
    # Status and visibility
    status = db.Column(db.String(20), default='draft')  # draft, published, archived
    is_featured = db.Column(db.Boolean, default=False)
    allow_comments = db.Column(db.Boolean, default=True)
    
    # Social sharing
    social_facebook = db.Column(db.Boolean, default=True)
    social_twitter = db.Column(db.Boolean, default=True)
    social_linkedin = db.Column(db.Boolean, default=True)
    social_instagram = db.Column(db.Boolean, default=True)
    
    # Timestamps
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', backref='blog_posts')
    categories = db.relationship('BlogCategory', secondary='blog_post_categories', back_populates='posts')
    tags = db.relationship('BlogTag', secondary='blog_post_tags', back_populates='posts')
    comments = db.relationship('BlogComment', backref='post', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<BlogPost {self.title}>'
    
    @property
    def comments_count(self):
        return self.comments.filter_by(is_approved=True).count()
    
    @property
    def related_posts(self):
        """Get related posts based on tags"""
        if not self.tags:
            return []
        
        # Get posts that share at least one tag
        tag_ids = [tag.id for tag in self.tags]
        related = BlogPost.query.join(blog_post_tags).filter(
            blog_post_tags.c.tag_id.in_(tag_ids),
            BlogPost.id != self.id,
            BlogPost.status == 'published'
        ).distinct().limit(5).all()
        
        return related

class BlogComment(db.Model):
    """Blog comments"""
    __tablename__ = 'blog_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    author_name = db.Column(db.String(100), nullable=False)
    author_email = db.Column(db.String(120), nullable=False)
    author_website = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    
    # Moderation
    is_approved = db.Column(db.Boolean, default=False)
    is_spam = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BlogComment {self.author_name} on {self.post.title}>'

# Association tables for many-to-many relationships
blog_post_categories = db.Table('blog_post_categories',
    db.Column('post_id', db.Integer, db.ForeignKey('blog_posts.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('blog_categories.id'), primary_key=True)
)

blog_post_tags = db.Table('blog_post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('blog_posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('blog_tags.id'), primary_key=True)
)

class FooterSettings(db.Model):
    """Footer settings"""
    __tablename__ = 'footer_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    company_title = db.Column(db.String(200))
    company_description = db.Column(db.Text)
    contact_title = db.Column(db.String(200))
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(50))
    social_title = db.Column(db.String(200))
    company_name = db.Column(db.String(200))
    show_privacy_policy = db.Column(db.Boolean, default=True)
    show_terms = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FooterSettings {self.company_name}>'

class LegalDocument(db.Model):
    """Legal documents (privacy policy, terms, etc.)"""
    __tablename__ = 'legal_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    document_type = db.Column(db.String(50), nullable=False)  # 'privacy_policy', 'terms', etc.
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LegalDocument {self.document_type} - {self.title}>'

class BlogPostImage(db.Model):
    """Images attached to blog posts"""
    __tablename__ = 'blog_post_images'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    image_url = db.Column(db.String(200), nullable=False)  # URL to the image
    alt_text = db.Column(db.String(200))  # Alt text for accessibility
    caption = db.Column(db.Text)  # Optional caption
    order = db.Column(db.Integer, default=0)  # Order of images in the post
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    post = db.relationship('BlogPost', backref='images')
    
    def __repr__(self):
        return f'<BlogPostImage {self.id} - {self.image_url}>'

