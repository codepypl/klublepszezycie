"""
User History Model - historia uczestnictwa w wydarzeniach
"""
from datetime import datetime
from . import db

class UserHistory(db.Model):
    __tablename__ = 'user_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=False)
    registration_type = db.Column(db.String(20), nullable=False, default='registration')  # 'registration', 'participation'
    was_club_member = db.Column(db.Boolean, nullable=False, default=False)  # Czy był członkiem klubu podczas wydarzenia
    registration_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    participation_date = db.Column(db.DateTime, nullable=True)  # Data rzeczywistego uczestnictwa
    status = db.Column(db.String(20), nullable=False, default='registered')  # 'registered', 'participated', 'cancelled', 'no_show'
    notes = db.Column(db.Text, nullable=True)  # Dodatkowe notatki
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('event_history', cascade='all, delete-orphan'), lazy=True)
    event = db.relationship('EventSchedule', backref='participants_history', lazy=True)
    
    # Unique constraint - user can only have one history entry per event
    __table_args__ = (
        db.UniqueConstraint('user_id', 'event_id', name='_unique_user_event_history'),
    )
    
    def __repr__(self):
        return f'<UserHistory user {self.user_id} - event {self.event_id} ({self.status})>'
    
    @classmethod
    def log_event_registration(cls, user_id, event_id, was_club_member=False, notes=None):
        """Log event registration in user history"""
        history = cls(
            user_id=user_id,
            event_id=event_id,
            registration_type='registration',
            was_club_member=was_club_member,
            status='registered',
            notes=notes
        )
        db.session.add(history)
        return history
    
    @classmethod
    def log_event_participation(cls, user_id, event_id, was_club_member=False, notes=None):
        """Log actual event participation"""
        history = cls(
            user_id=user_id,
            event_id=event_id,
            registration_type='participation',
            was_club_member=was_club_member,
            participation_date=__import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now(),
            status='participated',
            notes=notes
        )
        db.session.add(history)
        return history
    
    @classmethod
    def update_registration_status(cls, user_id, event_id, status, notes=None):
        """Update registration status"""
        history = cls.query.filter_by(user_id=user_id, event_id=event_id).first()
        if history:
            history.status = status
            if notes:
                history.notes = notes
            if status == 'participated':
                history.participation_date = __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now()
            return history
        return None
    
    @classmethod
    def get_user_event_history(cls, user_id, include_club_events=True):
        """Get user's complete event history"""
        query = cls.query.filter_by(user_id=user_id)
        if not include_club_events:
            query = query.filter_by(was_club_member=False)
        return query.order_by(cls.registration_date.desc()).all()
    
    @classmethod
    def get_event_participants_history(cls, event_id):
        """Get all participants history for an event"""
        return cls.query.filter_by(event_id=event_id).order_by(cls.registration_date.asc()).all()
    
    @classmethod
    def get_club_member_participation_stats(cls, user_id):
        """Get statistics for club member participation"""
        from .user_model import User
        user = User.query.get(user_id)
        if not user or not user.club_member:
            return None
            
        total_events = cls.query.filter_by(user_id=user_id, was_club_member=True).count()
        participated = cls.query.filter_by(user_id=user_id, was_club_member=True, status='participated').count()
        registered = cls.query.filter_by(user_id=user_id, was_club_member=True, status='registered').count()
        cancelled = cls.query.filter_by(user_id=user_id, was_club_member=True, status='cancelled').count()
        no_show = cls.query.filter_by(user_id=user_id, was_club_member=True, status='no_show').count()
        
        return {
            'total_events': total_events,
            'participated': participated,
            'registered': registered,
            'cancelled': cancelled,
            'no_show': no_show,
            'participation_rate': (participated / total_events * 100) if total_events > 0 else 0
        }
    
    @classmethod
    def get_non_club_member_registrations(cls, user_id):
        """Get registrations when user was not a club member"""
        return cls.query.filter_by(user_id=user_id, was_club_member=False).order_by(cls.registration_date.desc()).all()