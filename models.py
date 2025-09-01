from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    phone = db.Column(db.String(20))
    club_member = db.Column(db.Boolean, default=False)
    is_temporary_password = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<MenuItem {self.title}>'

class Section(db.Model):
    __tablename__ = 'sections'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Section {self.name}>'

class BenefitItem(db.Model):
    __tablename__ = 'benefit_items'
    
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    icon = db.Column(db.String(100))
    image = db.Column(db.String(200))
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    section = db.relationship('Section', backref='benefit_items')
    
    def __repr__(self):
        return f'<BenefitItem {self.title}>'

class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    
    id = db.Column(db.Integer, primary_key=True)
    author_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    member_since = db.Column(db.String(20))
    rating = db.Column(db.Integer, default=5)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Testimonial {self.name}>'

class SocialLink(db.Model):
    __tablename__ = 'social_links'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    icon = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SocialLink {self.platform}>'

class Registration(db.Model):
    __tablename__ = 'registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    presentation_date = db.Column(db.DateTime)
    status = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Registration {self.name}>'

class FAQ(db.Model):
    __tablename__ = 'faqs'
    
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(500), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FAQ {self.question[:50]}...>'

class SEOSettings(db.Model):
    __tablename__ = 'seo_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    page_type = db.Column(db.String(50), nullable=False)
    page_title = db.Column(db.String(60), nullable=False)
    meta_description = db.Column(db.String(160), nullable=False)
    meta_keywords = db.Column(db.String(200))
    og_title = db.Column(db.String(60))
    og_description = db.Column(db.String(160))
    og_image = db.Column(db.String(200))
    og_type = db.Column(db.String(20))
    twitter_card = db.Column(db.String(20))
    twitter_title = db.Column(db.String(60))
    twitter_description = db.Column(db.String(160))
    twitter_image = db.Column(db.String(200))
    canonical_url = db.Column(db.String(200))
    structured_data = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SEOSettings {self.page}>'

class EventSchedule(db.Model):
    __tablename__ = 'event_schedule'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    event_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    description = db.Column(db.Text)
    meeting_link = db.Column(db.String(500))
    location = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    is_published = db.Column(db.Boolean, default=False)
    hero_background = db.Column(db.String(500))
    hero_background_type = db.Column(db.String(20), default='image')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EventSchedule {self.title} - {self.event_type} - {self.event_date}>'

class EventRegistration(db.Model):
    __tablename__ = 'event_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='confirmed')
    wants_club_news = db.Column(db.Boolean, default=False)
    notification_preferences = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    event = db.relationship('EventSchedule', backref='registrations')
    
    def __repr__(self):
        return f'<EventRegistration {self.name} - {self.email} - Event {self.event_id}>'

class EventNotification(db.Model):
    __tablename__ = 'event_notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=False)
    notification_type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='pending')
    scheduled_at = db.Column(db.DateTime, nullable=False)
    sent_at = db.Column(db.DateTime)
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
    __tablename__ = 'event_recipient_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    group_type = db.Column(db.String(20), nullable=False)
    criteria_config = db.Column(db.Text)
    member_count = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    event = db.relationship('EventSchedule', backref='recipient_groups')
    
    def __repr__(self):
        return f'<EventRecipientGroup {self.group_name} for Event {self.event_id}>'

class EventEmailSchedule(db.Model):
    __tablename__ = 'event_email_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pending')
    scheduled_at = db.Column(db.DateTime, nullable=False)
    sent_at = db.Column(db.DateTime)
    recipient_group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'))
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    recipient_count = db.Column(db.Integer, default=0)
    sent_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    event = db.relationship('EventSchedule', backref=db.backref('email_schedules', cascade='all, delete-orphan'))
    recipient_group = db.relationship('UserGroup', backref='event_schedules')
    template = db.relationship('EmailTemplate', backref='event_schedules')
    
    def __repr__(self):
        return f'<EventEmailSchedule {self.event.title} - {self.notification_type}>'

class Page(db.Model):
    __tablename__ = 'pages'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    meta_description = db.Column(db.String(300))
    meta_keywords = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    is_published = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    order = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Page {self.title}>'

class EmailTemplate(db.Model):
    __tablename__ = 'email_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text)
    text_content = db.Column(db.Text)
    template_type = db.Column(db.String(100))
    variables = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailTemplate {self.name}>'

class EmailSubscription(db.Model):
    __tablename__ = 'email_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    subscription_type = db.Column(db.String(50))
    unsubscribe_token = db.Column(db.String(255), nullable=False)
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
    status = db.Column(db.String(20))
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<EmailLog {self.email} - {self.status}>'

class EmailSchedule(db.Model):
    __tablename__ = 'email_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    trigger_type = db.Column(db.String(50), nullable=False)
    trigger_conditions = db.Column(db.Text)
    recipient_type = db.Column(db.String(20), nullable=False)
    recipient_emails = db.Column(db.Text)
    recipient_group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'))
    send_type = db.Column(db.String(50), nullable=False)
    scheduled_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    last_sent = db.Column(db.DateTime)
    sent_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    template = db.relationship('EmailTemplate', backref='schedules')
    recipient_group = db.relationship('UserGroup', backref='email_schedules')
    
    def __repr__(self):
        return f'<EmailSchedule {self.name}>'

class UserGroup(db.Model):
    __tablename__ = 'user_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    group_type = db.Column(db.String(50), default='general')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserGroup {self.name}>'

class UserGroupMember(db.Model):
    __tablename__ = 'user_group_members'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(100))
    member_type = db.Column(db.String(50), default='user')
    member_metadata = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    group = db.relationship('UserGroup', backref='members')
    
    def __repr__(self):
        return f'<UserGroupMember {self.email} in {self.group.name}>'

class EmailCampaign(db.Model):
    __tablename__ = 'email_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text)
    text_content = db.Column(db.Text)
    recipient_groups = db.Column(db.Text)
    custom_emails = db.Column(db.Text)
    status = db.Column(db.String(20))
    send_type = db.Column(db.String(20))
    scheduled_at = db.Column(db.DateTime)
    total_recipients = db.Column(db.Integer)
    sent_count = db.Column(db.Integer)
    failed_count = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<EmailCampaign {self.name} - {self.status}>'

class EmailAutomation(db.Model):
    __tablename__ = 'email_automations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    automation_type = db.Column(db.String(50), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'))
    trigger_conditions = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacje
    template = db.relationship('EmailTemplate', backref='automations')
    
    def __repr__(self):
        return f'<EmailAutomation {self.name} ({self.automation_type})>'

class EmailAutomationLog(db.Model):
    __tablename__ = 'email_automation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    automation_id = db.Column(db.Integer, db.ForeignKey('email_automations.id'), nullable=False)
    execution_type = db.Column(db.String(50), nullable=False)
    recipient_count = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='running')
    details = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Relacje
    automation = db.relationship('EmailAutomation', backref='logs')
    
    def __repr__(self):
        return f'<EmailAutomationLog {self.automation.name} ({self.status})>'

class PresentationSchedule(db.Model):
    __tablename__ = 'presentation_schedule'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    next_presentation_date = db.Column(db.DateTime, nullable=False)
    custom_text = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PresentationSchedule {self.title}>'
