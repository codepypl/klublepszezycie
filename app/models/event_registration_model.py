"""
Event registration model
"""
from datetime import datetime
from app.utils.timezone_utils import get_local_datetime
from . import db

class EventRegistration(db.Model):
    """Event registration model for multiple event registrations per user"""
    __tablename__ = 'event_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id', ondelete='CASCADE'), nullable=False)
    registration_date = db.Column(db.DateTime, default=get_local_datetime)
    is_active = db.Column(db.Boolean, default=True)
    registration_source = db.Column(db.String(50), default='website')  # website, admin, api
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('event_registrations', cascade='all, delete', passive_deletes=True))
    event = db.relationship('EventSchedule', backref=db.backref('registrations', cascade='all, delete', passive_deletes=True))
    
    # Unique constraint to prevent duplicate registrations
    __table_args__ = (
        db.UniqueConstraint('user_id', 'event_id', name='unique_user_event_registration'),
    )
    
    def __repr__(self):
        return f'<EventRegistration {self.user_id} -> {self.event_id}>'
    
    @classmethod
    def get_user_registrations(cls, user_id):
        """Get all active registrations for a user"""
        return cls.query.filter_by(user_id=user_id, is_active=True).all()
    
    @classmethod
    def get_event_registrations(cls, event_id):
        """Get all active registrations for an event"""
        return cls.query.filter_by(event_id=event_id, is_active=True).all()
    
    @classmethod
    def is_user_registered(cls, user_id, event_id):
        """Check if user is registered for specific event"""
        return cls.query.filter_by(
            user_id=user_id, 
            event_id=event_id, 
            is_active=True
        ).first() is not None
    
    @classmethod
    def register_user(cls, user_id, event_id, registration_source='website', notes=None):
        """Register user for event"""
        # Check if already registered
        if cls.is_user_registered(user_id, event_id):
            return None, "User already registered for this event"
        
        # Create new registration
        registration = cls(
            user_id=user_id,
            event_id=event_id,
            registration_source=registration_source,
            notes=notes
        )
        
        db.session.add(registration)
        db.session.commit()
        
        return registration, "Registration successful"
    
    @classmethod
    def unregister_user(cls, user_id, event_id):
        """Unregister user from event"""
        registration = cls.query.filter_by(
            user_id=user_id,
            event_id=event_id,
            is_active=True
        ).first()
        
        if registration:
            registration.is_active = False
            db.session.commit()
            return True, "Unregistered successfully"
        
        return False, "Registration not found"
