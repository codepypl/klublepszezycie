"""
Event Link Click Tracking Model
Śledzi kliknięcia w linki wydarzeń wysyłane mailem
"""
from datetime import datetime
from app.utils.timezone_utils import get_local_datetime
from . import db

class EventLinkClick(db.Model):
    """Model do śledzenia kliknięć w linki wydarzeń"""
    __tablename__ = 'event_link_clicks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id', ondelete='CASCADE'), nullable=False)
    email_log_id = db.Column(db.Integer, db.ForeignKey('email_logs.id', ondelete='SET NULL'), nullable=True)
    click_token = db.Column(db.String(255), unique=True, nullable=False, index=True)  # Unikalny token dla linku
    clicked_at = db.Column(db.DateTime, default=get_local_datetime, nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    participation_recorded = db.Column(db.Boolean, default=False)  # Czy zapisano uczestnictwo w UserHistory
    created_at = db.Column(db.DateTime, default=get_local_datetime, index=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('event_link_clicks', cascade='all, delete-orphan'))
    event = db.relationship('EventSchedule', backref='link_clicks')
    email_log = db.relationship('EmailLog', backref='event_link_clicks')
    
    # Unique constraint - jeden token może być użyty tylko raz
    __table_args__ = (
        db.UniqueConstraint('click_token', name='unique_click_token'),
    )
    
    def __repr__(self):
        return f'<EventLinkClick user_id={self.user_id} event_id={self.event_id} clicked_at={self.clicked_at}>'
    
    @classmethod
    def record_click(cls, user_id, event_id, click_token, email_log_id=None, ip_address=None, user_agent=None):
        """Zapisuje kliknięcie w link wydarzenia"""
        # Sprawdź czy token nie został już użyty
        existing = cls.query.filter_by(click_token=click_token).first()
        if existing:
            return existing, "Token already used"
        
        click = cls(
            user_id=user_id,
            event_id=event_id,
            email_log_id=email_log_id,
            click_token=click_token,
            ip_address=ip_address,
            user_agent=user_agent,
            clicked_at=get_local_datetime()
        )
        
        db.session.add(click)
        return click, "Click recorded"
    
    @classmethod
    def has_user_clicked_event_link(cls, user_id, event_id):
        """Sprawdza czy użytkownik kliknął w link wydarzenia"""
        return cls.query.filter_by(
            user_id=user_id,
            event_id=event_id
        ).first() is not None
    
    @classmethod
    def get_event_clicks(cls, event_id):
        """Pobiera wszystkie kliknięcia dla wydarzenia"""
        return cls.query.filter_by(event_id=event_id).order_by(cls.clicked_at.desc()).all()
    
    @classmethod
    def get_user_clicks(cls, user_id):
        """Pobiera wszystkie kliknięcia użytkownika"""
        return cls.query.filter_by(user_id=user_id).order_by(cls.clicked_at.desc()).all()


