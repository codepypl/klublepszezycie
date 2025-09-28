"""
User Groups models
"""
from datetime import datetime
from . import db

class UserGroup(db.Model):
    """User groups for email campaigns"""
    __tablename__ = 'user_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    group_type = db.Column(db.String(50), default='manual')  # manual, automatic, event, event_based
    event_id = db.Column(db.Integer, db.ForeignKey('event_schedule.id'), nullable=True)  # ID of event for event groups
    criteria = db.Column(db.Text)  # JSON string for automatic group criteria
    is_active = db.Column(db.Boolean, default=True)
    member_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now())
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now(), onupdate=lambda: __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now())
    
    # Relationships
    members = db.relationship('UserGroupMember', backref='group', lazy='dynamic', cascade='all, delete-orphan')
    event = db.relationship('EventSchedule', backref='user_groups')
    
    def __repr__(self):
        return f'<UserGroup {self.name}>'

class UserGroupMember(db.Model):
    """User group memberships"""
    __tablename__ = 'user_group_members'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('user_groups.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Can be null for external members
    member_type = db.Column(db.String(50), default='user')  # user, external
    email = db.Column(db.String(120))  # For external members
    name = db.Column(db.String(120))  # For external members
    member_metadata = db.Column(db.Text)  # JSON string for additional member data
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now())
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now(), onupdate=lambda: __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now())
    joined_at = db.Column(db.DateTime(timezone=True), default=lambda: __import__('app.utils.timezone_utils', fromlist=['get_local_now']).get_local_now())
    
    # Relationships
    user = db.relationship('User', backref='group_memberships')
    
    def __repr__(self):
        if self.user:
            return f'<UserGroupMember {self.user.email} in {self.group.name}>'
        else:
            return f'<UserGroupMember {self.email} in {self.group.name}>'
