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
    
    # Relationships - now using User model for registrations
    registered_users = db.relationship('User', backref='registered_event', lazy=True, foreign_keys='User.event_id')
    
    @property
    def current_participants(self):
        """Get current number of participants"""
        from .user_model import User
        return User.query.filter_by(
            event_id=self.id,
            account_type='event_registration'
        ).count()
    
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

