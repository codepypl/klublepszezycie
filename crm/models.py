"""
CRM models for phone call management
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models import db
from app.utils.timezone import get_local_datetime
from datetime import datetime, timedelta

class Contact(db.Model):
    """Contact model for CRM system"""
    __tablename__ = 'crm_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    company = db.Column(db.String(200))
    source_file = db.Column(db.String(200))  # Name of imported file
    notes = db.Column(db.Text)
    tags = db.Column(db.Text)  # JSON string with tags
    is_active = db.Column(db.Boolean, default=True)
    is_blacklisted = db.Column(db.Boolean, default=False)  # Blacklisted numbers
    call_attempts = db.Column(db.Integer, default=0)  # Number of call attempts
    max_call_attempts = db.Column(db.Integer, default=3)  # Max attempts before blacklisting
    assigned_ankieter_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Assigned ankieter
    last_call_date = db.Column(db.DateTime)  # Last call attempt
    created_at = db.Column(db.DateTime, default=get_local_datetime)
    updated_at = db.Column(db.DateTime, default=get_local_datetime, onupdate=get_local_datetime)
    
    # Relationships
    calls = db.relationship('Call', backref='contact', cascade='all, delete-orphan')
    assigned_ankieter = db.relationship('User', backref='assigned_contacts')
    
    def __repr__(self):
        return f'<Contact {self.name} ({self.phone})>'
    
    def get_tags(self):
        """Get tags as list"""
        import json
        if self.tags:
            try:
                return json.loads(self.tags)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    def set_tags(self, tags_list):
        """Set tags from list"""
        import json
        self.tags = json.dumps(tags_list) if tags_list else None
    
    def add_tag(self, tag):
        """Add single tag"""
        tags = self.get_tags()
        if tag not in tags:
            tags.append(tag)
            self.set_tags(tags)
    
    def remove_tag(self, tag):
        """Remove single tag"""
        tags = self.get_tags()
        if tag in tags:
            tags.remove(tag)
            self.set_tags(tags)
    
    def can_be_called(self):
        """Check if contact can be called (not blacklisted and within attempt limit)"""
        if self.is_blacklisted:
            return False
        if self.call_attempts >= self.max_call_attempts:
            return False
        return True

class Call(db.Model):
    """Call model for tracking phone calls"""
    __tablename__ = 'crm_calls'
    
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('crm_contacts.id'), nullable=False)
    ankieter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    call_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), nullable=False)  # lead, rejection, callback, no_answer, busy, wrong_number
    priority = db.Column(db.String(20), default='low')  # high, medium, low
    notes = db.Column(db.Text)
    next_call_date = db.Column(db.DateTime)  # For callback scheduling
    duration_minutes = db.Column(db.Integer)  # Call duration in minutes
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'))  # Event for lead registration
    is_lead_registered = db.Column(db.Boolean, default=False)  # Whether lead was registered for event
    created_at = db.Column(db.DateTime, default=get_local_datetime)
    updated_at = db.Column(db.DateTime, default=get_local_datetime, onupdate=get_local_datetime)
    
    # Relationships
    ankieter = db.relationship('User', backref='calls')
    event = db.relationship('EventSchedule', backref='crm_calls')
    
    def __repr__(self):
        return f'<Call {self.contact.name} - {self.status}>'
    
    def is_lead_status(self):
        """Check if call resulted in a lead"""
        return self.status == 'lead'
    
    def is_rejection_status(self):
        """Check if call resulted in rejection"""
        return self.status == 'rejection'
    
    def is_callback_status(self):
        """Check if call needs callback"""
        return self.status == 'callback'

class CallQueue(db.Model):
    """Call queue for managing call priorities"""
    __tablename__ = 'crm_call_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey('crm_contacts.id'), nullable=False)
    ankieter_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Assigned ankieter
    priority = db.Column(db.String(20), nullable=False)  # high, medium, low
    scheduled_date = db.Column(db.DateTime)  # When to call
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    queue_type = db.Column(db.String(20), default='new')  # new, callback, retry
    created_at = db.Column(db.DateTime, default=get_local_datetime)
    updated_at = db.Column(db.DateTime, default=get_local_datetime, onupdate=get_local_datetime)
    
    # Relationships
    contact = db.relationship('Contact', backref='queue_entries')
    ankieter = db.relationship('User', backref='queue_assignments')
    
    def __repr__(self):
        return f'<CallQueue {self.contact.name} - {self.priority}>'
    
    def is_high_priority(self):
        """Check if this is high priority (callbacks)"""
        return self.priority == 'high'
    
    def is_medium_priority(self):
        """Check if this is medium priority (leads)"""
        return self.priority == 'medium'
    
    def is_low_priority(self):
        """Check if this is low priority (new contacts)"""
        return self.priority == 'low'
    
    def is_callback(self):
        """Check if this is a callback"""
        return self.queue_type == 'callback'
    
    def is_retry(self):
        """Check if this is a retry"""
        return self.queue_type == 'retry'

class BlacklistEntry(db.Model):
    """Blacklist for phone numbers that should not be called"""
    __tablename__ = 'crm_blacklist'
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False, unique=True)
    reason = db.Column(db.String(200))  # Reason for blacklisting
    blacklisted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('crm_contacts.id'))  # Original contact
    is_active = db.Column(db.Boolean, default=True)  # Can be reactivated by admin
    created_at = db.Column(db.DateTime, default=get_local_datetime)
    updated_at = db.Column(db.DateTime, default=get_local_datetime, onupdate=get_local_datetime)
    
    # Relationships
    blacklister = db.relationship('User', backref='blacklist_entries')
    contact = db.relationship('Contact', backref='blacklist_entry')
    
    def __repr__(self):
        return f'<BlacklistEntry {self.phone} - {self.reason}>'

class ImportLog(db.Model):
    """Log for file imports"""
    __tablename__ = 'crm_import_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    file_size = db.Column(db.Integer)
    rows_imported = db.Column(db.Integer, default=0)
    rows_skipped = db.Column(db.Integer, default=0)
    import_status = db.Column(db.String(20), default='processing')  # processing, completed, failed
    error_message = db.Column(db.Text)
    imported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=get_local_datetime)
    
    # Relationships
    importer = db.relationship('User', backref='import_logs')
    
    def __repr__(self):
        return f'<ImportLog {self.filename} - {self.import_status}>'
