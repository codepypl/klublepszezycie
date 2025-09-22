"""
Email-related models
"""
from datetime import datetime
from . import db

class EmailTemplate(db.Model):
    """Email templates"""
    __tablename__ = 'email_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text)
    text_content = db.Column(db.Text)
    template_type = db.Column(db.String(50), default='html')  # html, text
    variables = db.Column(db.Text)  # JSON string of template variables
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)  # Whether this is a default template
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EmailTemplate {self.name}>'

class DefaultEmailTemplate(db.Model):
    """Default email templates stored in database"""
    __tablename__ = 'default_email_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    template_type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text)
    text_content = db.Column(db.Text)
    variables = db.Column(db.Text)  # JSON string of template variables with descriptions
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<DefaultEmailTemplate {self.name}>'

class UserGroup(db.Model):
    """User groups for email campaigns"""
    __tablename__ = 'user_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    group_type = db.Column(db.String(50), default='manual')  # manual, automatic, event, event_based
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=True)  # ID of event for event groups
    criteria = db.Column(db.Text)  # JSON string for automatic group criteria
    is_active = db.Column(db.Boolean, default=True)
    member_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = db.relationship('UserGroupMember', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<UserGroup {self.name}>'

class UserGroupMember(db.Model):
    """User group memberships"""
    __tablename__ = 'user_group_members'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Can be null for external members
    member_type = db.Column(db.String(50), default='user')  # user, external
    email = db.Column(db.String(120))  # For external members
    name = db.Column(db.String(120))  # For external members
    member_metadata = db.Column(db.Text)  # JSON string for additional member data
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='group_memberships')
    
    def __repr__(self):
        if self.user:
            return f'<UserGroupMember {self.user.email} in {self.group.name}>'
        else:
            return f'<UserGroupMember {self.email} in {self.group.name}>'

class EmailCampaign(db.Model):
    """Email campaigns"""
    __tablename__ = 'email_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text)
    text_content = db.Column(db.Text)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'), nullable=True)
    recipient_groups = db.Column(db.Text)  # JSON string of group IDs
    custom_emails = db.Column(db.Text)  # JSON string of custom email addresses
    recipient_users = db.Column(db.Text)  # JSON string of user IDs
    recipient_type = db.Column(db.String(20), default='groups')  # groups, users, custom
    content_variables = db.Column(db.Text)  # JSON string of template variables
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, sending, sent, cancelled
    send_type = db.Column(db.String(20), default='immediate')  # immediate, scheduled
    scheduled_at = db.Column(db.DateTime)
    sent_at = db.Column(db.DateTime)
    total_recipients = db.Column(db.Integer, default=0)
    sent_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    template = db.relationship('EmailTemplate', backref='campaigns')
    queue_items = db.relationship('EmailQueue', back_populates='email_campaign', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<EmailCampaign {self.name}>'

class EmailQueue(db.Model):
    """Email queue for sending"""
    __tablename__ = 'email_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('email_campaigns.id'), nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'), nullable=True)
    to_email = db.Column(db.String(120), nullable=False)
    to_name = db.Column(db.String(120))
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text)
    text_content = db.Column(db.Text)
    context = db.Column(db.Text)  # JSON string for template variables
    status = db.Column(db.String(20), default='pending')  # pending, sending, sent, failed, cancelled
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    scheduled_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    email_campaign = db.relationship('EmailCampaign', back_populates='queue_items')
    template = db.relationship('EmailTemplate', backref='email_queue_items')
    
    def __repr__(self):
        return f'<EmailQueue {self.to_email} - {self.status}>'

class EmailLog(db.Model):
    """Email sending logs"""
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # sent, failed, bounced, opened, clicked
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    campaign_id = db.Column(db.Integer, db.ForeignKey('email_campaigns.id'), nullable=True)
    recipient_data = db.Column(db.Text)  # JSON string of recipient information
    
    # Relationships
    template = db.relationship('EmailTemplate', backref='email_logs')
    campaign = db.relationship('EmailCampaign', backref='email_logs')
    
    def __repr__(self):
        return f'<EmailLog {self.email} - {self.status}>'

class EmailReminderSent(db.Model):
    """Tracks sent email reminders to prevent duplicates"""
    __tablename__ = 'email_reminders_sent'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_email = db.Column(db.String(120), nullable=False)  # Email address
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedules.id'), nullable=False)
    reminder_type = db.Column(db.String(20), nullable=False)  # '24h', '1h', '5min'
    template_name = db.Column(db.String(100), nullable=False)  # 'event_reminder_24h', etc.
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='sent_reminders')
    event = db.relationship('EventSchedule', backref='sent_reminders')
    
    # Unique constraint to prevent duplicates
    __table_args__ = (
        db.UniqueConstraint('user_email', 'event_id', 'reminder_type', name='unique_reminder_per_user_event'),
    )
    
    def __repr__(self):
        return f'<EmailReminderSent {self.user_email} - {self.event_id} - {self.reminder_type}>'
