"""
Event-related models
"""
from datetime import datetime
from app.utils.timezone_utils import get_local_datetime
from . import db

class EventSchedule(db.Model):
    """Event schedule"""
    __tablename__ = 'event_schedule'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=True, index=True)  # SEO-friendly URL
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
    created_at = db.Column(db.DateTime, default=get_local_datetime)
    updated_at = db.Column(db.DateTime, default=get_local_datetime, onupdate=get_local_datetime)
    max_participants = db.Column(db.Integer)
    is_archived = db.Column(db.Boolean, default=False)
    reminders_scheduled = db.Column(db.Boolean, default=False)  # Flaga zabezpieczająca przed duplikatami
    
    # Relationships - using EventRegistration model for registrations
    # registered_users = db.relationship('User', backref='registered_event', lazy=True, foreign_keys='User.event_id')
    
    @property
    def current_participants(self):
        """Get current number of participants"""
        from .event_registration_model import EventRegistration
        return EventRegistration.query.filter_by(
            event_id=self.id,
            is_active=True
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
    
    def generate_slug(self):
        """Generuje unikalny slug dla wydarzenia"""
        from app.utils.blog_utils import generate_unique_slug
        
        if not self.slug:
            # Użyj utility do generowania sluga (usuwa polskie znaki, dodaje ID dla unikalności)
            base_slug = generate_unique_slug(self.title, EventSchedule, existing_id=self.id)
            self.slug = base_slug
        
        return self.slug
    
    def is_ended(self):
        """Check if event has ended - improved with debugging"""
        from app.utils.timezone_utils import get_local_now
        
        now = get_local_now().replace(tzinfo=None)
        
        if not self.end_date:
            # If no end_date, consider event ended if event_date has passed
            is_ended = now > self.event_date
            print(f"🔍 Event {self.id} ({self.title}): No end_date, checking event_date {self.event_date} vs now {now} = {is_ended}")
            return is_ended
        else:
            # If has end_date, check if current time is past end_date
            is_ended = now > self.end_date
            print(f"🔍 Event {self.id} ({self.title}): Checking end_date {self.end_date} vs now {now} = {is_ended}")
            return is_ended
    
    def archive(self):
        """Archive the event and clean up related groups - improved version"""
        try:
            print(f"🏁 Rozpoczynam archiwizację wydarzenia: {self.title} (ID: {self.id})")
            
            # Step 1: Remove all users from event groups first
            from app.services.group_manager import GroupManager
            from app.models.user_groups_model import UserGroup, UserGroupMember
            
            group_manager = GroupManager()
            
            # Find all event-based groups for this event
            event_groups = UserGroup.query.filter_by(
                event_id=self.id,
                group_type='event_based'
            ).all()
            
            total_members_removed = 0
            for group in event_groups:
                print(f"📦 Przetwarzam grupę: {group.name} (ID: {group.id})")
                
                # Count members before removal
                members_before = group.members.count()
                print(f"   👥 Członków przed usunięciem: {members_before}")
                
                # Remove all members from this group
                removed_count = UserGroupMember.query.filter_by(
                    group_id=group.id,
                    is_active=True
                ).delete(synchronize_session=False)
                
                total_members_removed += removed_count
                print(f"   ✅ Usunięto {removed_count} członków z grupy")
                
                # Update member count
                group.member_count = 0
            
            print(f"👥 Łącznie usunięto {total_members_removed} członków ze wszystkich grup wydarzenia")
            
            # Step 2: Delete the event groups
            groups_deleted = 0
            for group in event_groups:
                print(f"🗑️ Usuwam grupę: {group.name} (ID: {group.id})")
                db.session.delete(group)
                groups_deleted += 1
            
            print(f"🗑️ Usunięto {groups_deleted} grup wydarzenia")
            
            # Step 3: Archive the event itself
            self.is_archived = True
            self.is_active = False
            self.is_published = False  # Unpublish archived events
            
            print(f"📦 Wydarzenie zarchiwizowane: is_archived={self.is_archived}, is_active={self.is_active}, is_published={self.is_published}")
            
            # Commit all changes
            db.session.commit()
            
            message = f"Wydarzenie '{self.title}' zostało zarchiwizowane. Usunięto {total_members_removed} członków z {groups_deleted} grup."
            print(f"✅ {message}")
            
            return True, message
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Błąd archiwizacji wydarzenia '{self.title}': {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def __repr__(self):
        return f'<EventSchedule {self.title}>'

