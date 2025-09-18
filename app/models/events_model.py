"""
Event-related models
"""
from datetime import datetime
from . import db

class EventSchedule(db.Model):
    """Event schedule"""
    __tablename__ = 'event_schedule'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    event_type = db.Column(db.String(50))  # Added from database schema
    event_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.Text)
    meeting_link = db.Column(db.String(500))
    location = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    is_published = db.Column(db.Boolean, default=True)
    hero_background = db.Column(db.String(200))  # Added from database schema
    hero_background_type = db.Column(db.String(50))  # Added from database schema
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    max_participants = db.Column(db.Integer)
    is_archived = db.Column(db.Boolean, default=False)
    
    # Relationships
    registrations = db.relationship('EventRegistration', back_populates='event', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def current_participants(self):
        """Get current number of participants"""
        return self.registrations.filter_by(status='confirmed').count()
    
    @property
    def is_full(self):
        """Check if event is full"""
        if self.max_participants is None:
            return False
        return self.current_participants >= self.max_participants
    
    @property
    def spots_remaining(self):
        """Get number of spots remaining"""
        if self.max_participants is None:
            return None
        return max(0, self.max_participants - self.current_participants)
    
    def __repr__(self):
        return f'<EventSchedule {self.title}>'

class EventRegistration(db.Model):
    """Event registrations"""
    __tablename__ = 'event_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    wants_club_news = db.Column(db.Boolean, default=False)  # Added from database schema
    notification_preferences = db.Column(db.Text)  # JSON string for notification preferences
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event = db.relationship('EventSchedule', back_populates='registrations')
    
    def __repr__(self):
        return f'<EventRegistration {self.first_name} for {self.event.title}>'
