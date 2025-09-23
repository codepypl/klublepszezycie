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
    
    def is_ended(self):
        """Check if event has ended"""
        if not self.end_date:
            # If no end_date, consider event ended if event_date has passed
            from app.utils.timezone_utils import get_local_now
            now = get_local_now().replace(tzinfo=None)
            return now > self.event_date
        else:
            from app.utils.timezone_utils import get_local_now
            now = get_local_now().replace(tzinfo=None)
            return now > self.end_date
    
    def archive(self):
        """Archive the event and clean up related groups"""
        try:
            # Archive the event
            self.is_archived = True
            self.is_active = False
            
            # Clean up related groups
            from app.services.group_manager import GroupManager
            group_manager = GroupManager()
            
            # Remove all users from event groups
            success, message = group_manager.cleanup_event_groups(self.id)
            if success:
                print(f"✅ Wyczyściono grupy dla wydarzenia: {self.title}")
            else:
                print(f"❌ Błąd czyszczenia grup dla wydarzenia {self.title}: {message}")
            
            # Delete event groups
            success, message = group_manager.delete_event_groups(self.id)
            if success:
                print(f"✅ Usunięto grupy dla wydarzenia: {self.title}")
            else:
                print(f"❌ Błąd usuwania grup dla wydarzenia {self.title}: {message}")
            
            return True, "Wydarzenie zostało zarchiwizowane"
            
        except Exception as e:
            return False, f"Błąd archiwizacji wydarzenia: {str(e)}"
    
    def __repr__(self):
        return f'<EventSchedule {self.title}>'

