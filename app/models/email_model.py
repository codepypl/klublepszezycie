"""
Email-related models
"""
import hashlib
from datetime import datetime
from . import db

class EmailTemplate(db.Model):
    """Email templates with versioning support"""
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
    
    # Versioning fields
    version = db.Column(db.Integer, default=1)
    parent_template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'), nullable=True)
    is_edited_copy = db.Column(db.Boolean, default=False)
    original_template_name = db.Column(db.String(100), nullable=True)
    edited_from_default = db.Column(db.Boolean, default=False)
    
    # Relationships
    parent_template = db.relationship('EmailTemplate', remote_side=[id], backref='child_versions')
    
    def __repr__(self):
        return f'<EmailTemplate {self.name} v{self.version}>'
    
    def create_version(self, user_changes=None):
        """Create a new version of this template"""
        new_version = EmailTemplate(
            name=self.name,
            subject=self.subject,
            html_content=self.html_content,
            text_content=self.text_content,
            template_type=self.template_type,
            variables=self.variables,
            description=self.description,
            is_active=self.is_active,
            is_default=False,  # New versions are never default by default
            parent_template_id=self.id,
            is_edited_copy=True,
            original_template_name=self.original_template_name or self.name,
            edited_from_default=self.is_default,
            version=self.get_next_version_number()
        )
        
        # Apply user changes if provided
        if user_changes:
            for key, value in user_changes.items():
                if hasattr(new_version, key):
                    setattr(new_version, key, value)
        
        db.session.add(new_version)
        db.session.commit()
        return new_version
    
    def get_next_version_number(self):
        """Get the next version number for this template"""
        max_version = db.session.query(db.func.max(EmailTemplate.version))\
            .filter_by(name=self.name)\
            .scalar()
        return (max_version or 0) + 1
    
    def get_all_versions(self):
        """Get all versions of this template"""
        return EmailTemplate.query.filter_by(name=self.name)\
            .order_by(EmailTemplate.version.desc()).all()
    
    def get_latest_version(self):
        """Get the latest version of this template"""
        return EmailTemplate.query.filter_by(name=self.name)\
            .order_by(EmailTemplate.version.desc()).first()
    
    def restore_to_version(self, version_number):
        """Restore this template to a specific version"""
        target_version = EmailTemplate.query.filter_by(
            name=self.name, 
            version=version_number
        ).first()
        
        if not target_version:
            return False, f"Version {version_number} not found"
        
        # Copy content from target version
        self.subject = target_version.subject
        self.html_content = target_version.html_content
        self.text_content = target_version.text_content
        self.template_type = target_version.template_type
        self.variables = target_version.variables
        self.description = target_version.description
        
        db.session.commit()
        return True, f"Restored to version {version_number}"
    
    def make_default(self):
        """Make this template the default template"""
        if not self.original_template_name:
            return False, "Cannot make template default - no original template name"
        
        # Update the default template
        default_template = DefaultEmailTemplate.query.filter_by(
            name=self.original_template_name
        ).first()
        
        if default_template:
            default_template.subject = self.subject
            default_template.html_content = self.html_content
            default_template.text_content = self.text_content
            default_template.template_type = self.template_type
            default_template.variables = self.variables
            default_template.description = self.description
            default_template.updated_at = datetime.utcnow()
        
        # Mark this as default
        self.is_default = True
        db.session.commit()
        
        return True, f"Template '{self.original_template_name}' updated as default"
    
    @classmethod
    def create_from_default(cls, template_name):
        """Create an edited copy from a default template"""
        default_template = DefaultEmailTemplate.query.filter_by(name=template_name).first()
        
        if not default_template:
            return None, f"Default template '{template_name}' not found"
        
        # Create new template as edited copy
        new_template = cls(
            name=f"{template_name}_edited_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            subject=default_template.subject,
            html_content=default_template.html_content,
            text_content=default_template.text_content,
            template_type=default_template.template_type,
            variables=default_template.variables,
            description=default_template.description,
            is_active=True,
            is_default=False,
            is_edited_copy=True,
            original_template_name=template_name,
            edited_from_default=True,
            version=1
        )
        
        db.session.add(new_template)
        db.session.commit()
        
        return new_template, f"Created edited copy of '{template_name}'"
    
    @classmethod
    def get_active_template(cls, template_name):
        """Get the active (non-default) template for a given name"""
        return cls.query.filter_by(
            name=template_name,
            is_default=False,
            is_active=True
        ).first()
    
    @classmethod
    def get_default_or_active(cls, template_name):
        """Get default template or active edited version"""
        # First try to get active edited version
        active_template = cls.get_active_template(template_name)
        if active_template:
            return active_template
        
        # If no active version, get from default templates
        default_template = DefaultEmailTemplate.query.filter_by(name=template_name).first()
        
        if default_template:
            # Create a temporary template object for compatibility
            temp_template = cls(
                name=template_name,
                subject=default_template.subject,
                html_content=default_template.html_content,
                text_content=default_template.text_content,
                template_type=default_template.template_type,
                variables=default_template.variables,
                description=default_template.description,
                is_default=True,
                is_active=True
            )
            return temp_template
        
        return None

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
    recipient_email = db.Column(db.String(120), nullable=False)  # Changed from to_email
    recipient_name = db.Column(db.String(120))  # Changed from to_name
    template_name = db.Column(db.String(100))  # Template name for new system
    subject = db.Column(db.String(200), nullable=False)
    html_content = db.Column(db.Text)
    text_content = db.Column(db.Text)
    context = db.Column(db.Text)  # JSON string for template variables
    status = db.Column(db.String(20), default='pending')  # pending, sending, sent, failed, cancelled
    priority = db.Column(db.Integer, default=2)  # Priority: 1=high, 2=normal, 3=low
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    scheduled_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Duplicate prevention fields
    content_hash = db.Column(db.String(64), nullable=False, index=True)  # Hash of email content for duplicate detection
    duplicate_check_key = db.Column(db.String(255), nullable=True, index=True)  # Custom key for duplicate checking
    
    # Indexes for duplicate detection
    __table_args__ = (
        db.Index('ix_email_queue_duplicate_pending', 'recipient_email', 'subject', 'status'),
        db.Index('ix_email_queue_campaign_duplicate', 'recipient_email', 'campaign_id', 'content_hash'),
        db.Index('ix_email_queue_custom_key', 'duplicate_check_key'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Generate content hash if not provided
        if not self.content_hash:
            self.content_hash = self._generate_content_hash()
    
    def _generate_content_hash(self):
        """Generate hash for duplicate detection"""
        content = f"{self.recipient_email}|{self.subject}|{self.html_content or ''}|{self.text_content or ''}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _generate_content_hash_static(recipient_email, subject, html_content, text_content):
        """Generate hash for duplicate detection (static method)"""
        content = f"{recipient_email}|{subject}|{html_content or ''}|{text_content or ''}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    @classmethod
    def check_duplicate(cls, recipient_email, subject, campaign_id=None, html_content=None, text_content=None, duplicate_check_key=None):
        """
        Check if a similar email already exists in the queue
        
        Args:
            recipient_email: Email address
            subject: Email subject
            campaign_id: Campaign ID (optional)
            html_content: HTML content (optional)
            text_content: Text content (optional)
            duplicate_check_key: Custom duplicate check key (optional)
            
        Returns:
            EmailQueue object if duplicate found, None otherwise
        """
        # Check by custom key first (most specific)
        if duplicate_check_key:
            existing = cls.query.filter_by(
                duplicate_check_key=duplicate_check_key,
                status='pending'
            ).first()
            if existing:
                return existing
        
        # Check by campaign and recipient
        if campaign_id:
            # Generate content hash for comparison
            content = f"{recipient_email}|{subject}|{html_content or ''}|{text_content or ''}"
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            existing = cls.query.filter_by(
                recipient_email=recipient_email,
                campaign_id=campaign_id,
                content_hash=content_hash,
                status='pending'
            ).first()
            if existing:
                return existing
        
        # Check by recipient and subject (for non-campaign emails)
        # Only if no campaign_id and no custom key
        if not campaign_id and not duplicate_check_key:
            existing = cls.query.filter_by(
                recipient_email=recipient_email,
                subject=subject,
                status='pending'
            ).first()
            
            if existing:
                # Check if content is the same
                existing_content_hash = existing.content_hash
                new_content_hash = cls._generate_content_hash_static(
                    recipient_email, subject, html_content, text_content
                )
                
                if existing_content_hash == new_content_hash:
                    return existing
        
        return None
    
    # Backward compatibility properties
    @property
    def to_email(self):
        return self.recipient_email
    
    @to_email.setter
    def to_email(self, value):
        self.recipient_email = value
    
    @property
    def to_name(self):
        return self.recipient_name
    
    @to_name.setter
    def to_name(self, value):
        self.recipient_name = value
    
    # Relationships
    email_campaign = db.relationship('EmailCampaign', back_populates='queue_items')
    template = db.relationship('EmailTemplate', backref='email_queue_items')
    
    def __repr__(self):
        return f'<EmailQueue {self.to_email} - {self.status}>'

class EmailReminder(db.Model):
    """Email reminders tracking"""
    __tablename__ = 'email_reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    event_id = db.Column(db.Integer, nullable=False)
    reminder_type = db.Column(db.String(20), nullable=False)  # '24h', '1h', '5min'
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    email_queue_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Unique constraint to prevent duplicates
    __table_args__ = (
        db.UniqueConstraint('user_id', 'event_id', 'reminder_type', name='uq_email_reminder'),
    )
    
    def __repr__(self):
        return f'<EmailReminder user_id={self.user_id} event_id={self.event_id} type={self.reminder_type}>'

class EmailLog(db.Model):
    """Email sending logs"""
    __tablename__ = 'email_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('email_templates.id'), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # sent, failed, bounced, opened, clicked
    error_message = db.Column(db.Text)
    sent_at = db.Column(db.DateTime, default=lambda: __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now())
    campaign_id = db.Column(db.Integer, db.ForeignKey('email_campaigns.id'), nullable=True)
    recipient_data = db.Column(db.Text)  # JSON string of recipient information
    
    # Relationships
    template = db.relationship('EmailTemplate', backref='email_logs')
    campaign = db.relationship('EmailCampaign', backref='email_logs')
    
    def __repr__(self):
        return f'<EmailLog {self.email} - {self.status}>'

