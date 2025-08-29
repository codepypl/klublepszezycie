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
    order = db.Column(db.Integer, default=0)
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

class EmailSchedule(db.Model):
    __tablename__ = 'email_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'), nullable=False)
    
    # Kiedy (kryteria)
    trigger_type = db.Column(db.String(50), nullable=False)  # 'user_activation', 'event_registration', 'event_reminder', 'manual', 'scheduled'
    trigger_conditions = db.Column(db.Text)  # JSON z warunkami
    
    # Do kogo (odbiorcy)
    recipient_type = db.Column(db.String(20), nullable=False)  # 'user', 'admin', 'group', 'all'
    recipient_emails = db.Column(db.Text)  # JSON array z konkretnymi emailami
    recipient_group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'))
    
    # Data wysłania
    send_type = db.Column(db.String(20), default='immediate')  # 'immediate', 'scheduled'
    scheduled_at = db.Column(db.DateTime)
    
    # Status
    status = db.Column(db.String(20), default='active')  # 'active', 'paused', 'cancelled'
    last_sent = db.Column(db.DateTime)
    sent_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    template = db.relationship('EmailTemplate', backref='schedules')
    recipient_group = db.relationship('UserGroup', backref='email_schedules')

# Stary model CustomEmailCampaign został usunięty - zastąpiony przez nowy system

# Stary model EmailRecipientGroup został usunięty - zastąpiony przez nowy system

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
    hero_background = db.Column(db.String(500))  # Ścieżka do zdjęcia/wideo jako tło bannera
    hero_background_type = db.Column(db.String(20), default='image')  # 'image' lub 'video'

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


class UserGroup(db.Model):
    """Grupy użytkowników - podstawowy model dla grupowania"""
    __tablename__ = 'user_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Typ grupy
    group_type = db.Column(db.String(50), nullable=False)  # 'manual', 'event_based', 'dynamic'
    
    # Kryteria grupy (JSON)
    criteria = db.Column(db.Text)  # JSON z kryteriami
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Liczba członków (cache)
    member_count = db.Column(db.Integer, default=0)
    
    # Relacje
    members = db.relationship('UserGroupMember', backref='group', cascade='all, delete-orphan')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserGroup {self.name} ({self.group_type})>'
    
    def update_member_count(self):
        """Aktualizuje liczbę członków grupy"""
        self.member_count = len([m for m in self.members if m.is_active])
        return self.member_count


class UserGroupMember(db.Model):
    """Członkowie grup użytkowników"""
    __tablename__ = 'user_group_members'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'), nullable=False)
    
    # Typ członka
    member_type = db.Column(db.String(50), nullable=False)  # 'email', 'registration', 'event_registration'
    
    # Dane członka
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100))
    
    # Dodatkowe dane (JSON)
    member_metadata = db.Column(db.Text)  # JSON z dodatkowymi danymi
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserGroupMember {self.email} in group {self.group_id}>'


class EmailCampaign(db.Model):
    """Kampanie emailowe - mailing celowany"""
    __tablename__ = 'email_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    
    # Treść emaila
    html_content = db.Column(db.Text)
    text_content = db.Column(db.Text)
    
    # Odbiorcy
    recipient_groups = db.Column(db.Text)  # JSON array z ID grup
    custom_emails = db.Column(db.Text)  # JSON array z dodatkowymi emailami
    
    # Status
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, sending, completed, cancelled
    
    # Planowanie
    send_type = db.Column(db.String(20), default='immediate')  # immediate, scheduled
    scheduled_at = db.Column(db.DateTime)
    
    # Statystyki
    total_recipients = db.Column(db.Integer, default=0)
    sent_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<EmailCampaign {self.name} ({self.status})>'


class EmailAutomation(db.Model):
    """Automatyzacje emailowe - mailing automatyczny"""
    __tablename__ = 'email_automations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Typ automatyzacji
    automation_type = db.Column(db.String(50), nullable=False)  # 'welcome', 'event_reminder', 'newsletter'
    
    # Szablon
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    
    # Warunki uruchomienia
    trigger_conditions = db.Column(db.Text)  # JSON z warunkami
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    template = db.relationship('EmailTemplate', backref='automations')
    
    def __repr__(self):
        return f'<EmailAutomation {self.name} ({self.automation_type})>'


class EmailAutomationLog(db.Model):
    """Logi automatyzacji emailowych"""
    __tablename__ = 'email_automation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    automation_id = db.Column(db.Integer, db.ForeignKey('email_automations.id'), nullable=False)
    
    # Szczegóły wykonania
    execution_type = db.Column(db.String(50), nullable=False)  # 'triggered', 'scheduled', 'manual'
    recipient_count = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    
    # Status
    status = db.Column(db.String(20), default='running')  # running, completed, failed
    
    # Szczegóły
    details = db.Column(db.Text)  # JSON z szczegółami
    
    # Timestamps
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relacje
    automation = db.relationship('EmailAutomation', backref='logs')
    
    def __repr__(self):
        return f'<EmailAutomationLog {self.automation.name} ({self.status})>'


class EventEmailSchedule(db.Model):
    """Harmonogram emaili dla wydarzeń"""
    __tablename__ = 'event_email_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=False)
    
    # Typ powiadomienia
    notification_type = db.Column(db.String(50), nullable=False)  # '24h_before', '1h_before', '5min_before'
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, sent, failed, cancelled
    
    # Planowanie
    scheduled_at = db.Column(db.DateTime, nullable=False)
    sent_at = db.Column(db.DateTime)
    
    # Odbiorcy
    recipient_group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'))
    
    # Szablon
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    
    # Statystyki
    recipient_count = db.Column(db.Integer, default=0)
    sent_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    event = db.relationship('EventSchedule', backref='email_schedules')
    recipient_group = db.relationship('UserGroup', backref='event_schedules')
    template = db.relationship('EmailTemplate', backref='event_schedules')
    
    def __repr__(self):
        return f'<EventEmailSchedule {self.event.title} - {self.notification_type}>'

