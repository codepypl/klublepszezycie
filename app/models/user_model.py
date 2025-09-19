"""
User-related models
"""
from flask_login import UserMixin
from datetime import datetime
from . import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)  # First name
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))  # Phone number
    password_hash = db.Column(db.String(255), nullable=False)
    club_member = db.Column(db.Boolean, default=False)  # Whether user wants to join the club
    is_active = db.Column(db.Boolean, default=True, index=True)  # Whether the account is active
    role = db.Column(db.String(20), default='user', index=True)  # admin, user, ankieter
    account_type = db.Column(db.String(30), default='user', index=True)  # admin, user, ankieter, event_registration
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=True)  # ID of event for event registrations
    group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'), nullable=True)  # ID of group user belongs to
    is_temporary_password = db.Column(db.Boolean, default=True)  # Whether user needs to change password
    created_at = db.Column(db.DateTime, default=lambda: __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now())
    last_login = db.Column(db.DateTime)
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def is_admin_role(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    def is_ankieter_role(self):
        """Check if user has ankieter role"""
        return self.role == 'ankieter'
    
    def is_user_role(self):
        """Check if user has basic user role"""
        return self.role == 'user'
    
    def has_role(self, role_name):
        """Check if user has specific role"""
        if role_name == 'admin':
            return self.is_admin_role()
        return self.role == role_name

    def is_event_registration(self):
        """Check if user is from event registration"""
        return self.account_type == 'event_registration'
    
    def is_club_member_account(self):
        """Check if user is club member (based on club_member boolean field)"""
        return self.club_member
    
    def is_admin_account(self):
        """Check if user is admin account type"""
        return self.account_type == 'admin'
    
    def is_ankieter_account(self):
        """Check if user is ankieter account type"""
        return self.account_type == 'ankieter'

    # Backward-compatible property for legacy code that used a boolean column
    @property
    def is_admin(self):
        return self.is_admin_role()
    
    def __repr__(self):
        return f'<User {self.email}>'

class PasswordResetToken(db.Model):
    """Password reset tokens"""
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_expired(self):
        """Check if token is expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        """Check if token is valid (not expired and not used)"""
        return not self.is_expired() and not self.used
    
    def __repr__(self):
        return f'<PasswordResetToken {self.token[:10]}...>'
