"""
CRM models for phone call management
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.models import db
# Import moved to avoid circular dependency
from datetime import datetime, timedelta

class Campaign(db.Model):
    """Campaign model for CRM system"""
    __tablename__ = 'crm_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    script_content = db.Column(db.Text)  # Call script content
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    import_files = db.relationship('ImportFile', backref='campaign', lazy='dynamic')
    contacts = db.relationship('Contact', backref='campaign', lazy='dynamic')
    calls = db.relationship('Call', backref='campaign', lazy='dynamic')
    
    def __repr__(self):
        return f'<Campaign {self.name}>'


class Contact(db.Model):
    """Contact model for CRM system"""
    __tablename__ = 'crm_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    company = db.Column(db.String(200))
    source_file = db.Column(db.String(200))  # Name of imported file
    import_file_id = db.Column(db.Integer, db.ForeignKey('crm_import_files.id', ondelete='SET NULL'))  # Link to import file
    campaign_id = db.Column(db.Integer, db.ForeignKey('crm_campaigns.id', ondelete='SET NULL'))  # Link to campaign
    notes = db.Column(db.Text)
    tags = db.Column(db.Text)  # JSON string with tags
    is_active = db.Column(db.Boolean, default=True)
    is_blacklisted = db.Column(db.Boolean, default=False)  # Blacklisted numbers
    call_attempts = db.Column(db.Integer, default=0)  # Number of call attempts
    max_call_attempts = db.Column(db.Integer, default=3)  # Max attempts before blacklisting
    assigned_ankieter_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))  # Assigned ankieter
    last_call_date = db.Column(db.DateTime)  # Last call attempt
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    calls = db.relationship('Call', backref='contact', cascade='all, delete-orphan')
    assigned_ankieter = db.relationship('User', backref='assigned_contacts')
    import_file = db.relationship('ImportFile', backref='contacts')
    
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
    ankieter_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('crm_campaigns.id', ondelete='SET NULL'))  # Link to campaign
    call_date = db.Column(db.DateTime, nullable=False)
    call_start_time = db.Column(db.DateTime)  # When call actually started
    call_end_time = db.Column(db.DateTime)  # When call ended
    status = db.Column(db.String(50), nullable=False)  # lead, rejection, callback, no_answer, busy, wrong_number
    priority = db.Column(db.String(20), default='low')  # high, medium, low
    notes = db.Column(db.Text)
    next_call_date = db.Column(db.DateTime)  # For callback scheduling
    duration_minutes = db.Column(db.Integer)  # Call duration in minutes
    duration_seconds = db.Column(db.Integer)  # Call duration in seconds for precise tracking
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'))  # Event for lead registration
    is_lead_registered = db.Column(db.Boolean, default=False)  # Whether lead was registered for event
    
    # Queue management fields (moved from CallQueue)
    queue_status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    queue_type = db.Column(db.String(20), default='new')  # new, callback, retry
    scheduled_date = db.Column(db.DateTime)  # When to call
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    
    # Queue management methods (moved from CallQueue)
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

# Call Queue removed - functionality moved to Call model

class BlacklistEntry(db.Model):
    """Blacklist for phone numbers that should not be called"""
    __tablename__ = 'crm_blacklist'
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    reason = db.Column(db.String(200))  # Reason for blacklisting
    campaign_id = db.Column(db.Integer, db.ForeignKey('crm_campaigns.id', ondelete='SET NULL'), nullable=True)  # NULL = global blacklist
    blacklisted_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('crm_contacts.id'))  # Original contact
    is_active = db.Column(db.Boolean, default=True)  # Can be reactivated by admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    campaign = db.relationship('Campaign', backref='blacklist_entries')
    blacklister = db.relationship('User', backref='blacklist_entries')
    contact = db.relationship('Contact', backref='blacklist_entry')
    
    def __repr__(self):
        return f'<BlacklistEntry {self.phone} - {self.reason}>'
    
    @staticmethod
    def is_blacklisted(phone, campaign_id=None):
        """Check if phone number is blacklisted globally or for specific campaign"""
# Import Log removed - functionality moved to ImportFile

class ImportFile(db.Model):
    """Raw import file data storage"""
    __tablename__ = 'crm_import_files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)  # Full path to file on disk
    file_size = db.Column(db.Integer)  # File size in bytes
    file_type = db.Column(db.String(10), nullable=False)  # xlsx, xls, csv
    csv_separator = db.Column(db.String(5), default=',')  # CSV separator character
    imported_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('crm_campaigns.id', ondelete='SET NULL'))  # Link to campaign
    import_status = db.Column(db.String(20), default='uploaded')  # uploaded, processing, completed, failed
    is_active = db.Column(db.Boolean, default=False)  # Whether this import container is active for ankieter
    total_rows = db.Column(db.Integer, default=0)
    processed_rows = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    # Relationships
    importer = db.relationship('User', backref='import_files')
    raw_records = db.relationship('ImportRecord', backref='import_file', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ImportFile {self.filename} ({self.import_status})>'

class ImportRecord(db.Model):
    """Individual record from imported file"""
    __tablename__ = 'crm_import_records'
    
    id = db.Column(db.Integer, primary_key=True)
    import_file_id = db.Column(db.Integer, db.ForeignKey('crm_import_files.id'), nullable=False)
    row_number = db.Column(db.Integer, nullable=False)  # Row number in original file
    raw_data = db.Column(db.Text, nullable=False)  # JSON string with all column data
    processed = db.Column(db.Boolean, default=False)  # Whether record was processed into Contact
    contact_id = db.Column(db.Integer, db.ForeignKey('crm_contacts.id'))  # Link to created contact
    error_message = db.Column(db.Text)  # Error during processing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    contact = db.relationship('Contact', backref='import_record')
    
    def __repr__(self):
        return f'<ImportRecord {self.row_number} from {self.import_file_id}>'
    
    def get_raw_data(self):
        """Get raw data as dictionary"""
        import json
        if self.raw_data:
            try:
                return json.loads(self.raw_data)
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def set_raw_data(self, data_dict):
        """Set raw data from dictionary"""
        import json
        self.raw_data = json.dumps(data_dict, ensure_ascii=False)
