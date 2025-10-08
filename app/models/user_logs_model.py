"""
User Logs Model - śledzenie wszystkich akcji użytkowników
"""
from datetime import datetime
from app.utils.timezone_utils import get_local_datetime
from . import db

class UserLogs(db.Model):
    __tablename__ = 'user_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False, index=True)  # 'event_registration', 'event_cancellation', 'login', 'password_change', etc.
    description = db.Column(db.String(255), nullable=False)  # Human readable description
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=True)  # If related to an event
    group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'), nullable=True)  # If related to a group
    extra_data = db.Column(db.JSON, nullable=True)  # Additional data as JSON
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(500), nullable=True)  # Browser/client info
    created_at = db.Column(db.DateTime, default=get_local_datetime, index=True)

    # Relationships
    user = db.relationship('User', backref=db.backref('logs', cascade='all, delete-orphan'), lazy=True)
    event = db.relationship('EventSchedule', backref='user_logs', lazy=True)
    group = db.relationship('UserGroup', backref='user_logs', lazy=True)

    def __repr__(self):
        return f'<UserLogs {self.action_type} for user {self.user_id}>'
    
    @classmethod
    def log_event_registration(cls, user_id, event_id, event_title, ip_address=None, user_agent=None):
        """Log event registration action"""
        log = cls(
            user_id=user_id,
            action_type='event_registration',
            description=f'Zarejestrowano na wydarzenie: {event_title}',
            event_id=event_id,
            extra_data={'event_title': event_title},
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        return log
    
    @classmethod
    def log_event_cancellation(cls, user_id, event_id, event_title, ip_address=None, user_agent=None):
        """Log event cancellation action"""
        log = cls(
            user_id=user_id,
            action_type='event_cancellation',
            description=f'Anulowano rejestrację na wydarzenie: {event_title}',
            event_id=event_id,
            extra_data={'event_title': event_title},
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        return log
    
    @classmethod
    def log_login(cls, user_id, ip_address=None, user_agent=None):
        """Log user login"""
        log = cls(
            user_id=user_id,
            action_type='login',
            description='Logowanie do systemu',
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        return log
    
    @classmethod
    def log_logout(cls, user_id, ip_address=None, user_agent=None):
        """Log user logout"""
        log = cls(
            user_id=user_id,
            action_type='logout',
            description='Wylogowanie z systemu',
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        return log
    
    @classmethod
    def log_password_change(cls, user_id, ip_address=None, user_agent=None):
        """Log password change"""
        log = cls(
            user_id=user_id,
            action_type='password_change',
            description='Zmieniono hasło',
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        return log
    
    @classmethod
    def log_account_creation(cls, user_id, account_type, ip_address=None, user_agent=None):
        """Log account creation"""
        log = cls(
            user_id=user_id,
            action_type='account_creation',
            description=f'Utworzenie konta typu: {account_type}',
            extra_data={'account_type': account_type},
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        return log