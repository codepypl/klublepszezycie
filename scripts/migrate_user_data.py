#!/usr/bin/env python3
"""
Script to migrate existing user data to new structure
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import User, UserLogs, UserHistory, EventSchedule

def main():
    """Migrate existing user data to new structure"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Migrating existing user data to new structure...")
        
        try:
            # Get all users with event registrations
            event_users = User.query.filter_by(account_type='event_registration').all()
            
            print(f"📊 Found {len(event_users)} users with event registrations")
            
            migrated_count = 0
            
            for user in event_users:
                if user.event_id:
                    # Get the event
                    event = EventSchedule.query.get(user.event_id)
                    if event:
                        # Check if already exists in UserHistory
                        existing_history = UserHistory.query.filter_by(
                            user_id=user.id,
                            event_id=user.event_id
                        ).first()
                        
                        if not existing_history:
                            # Create new UserHistory entry
                            UserHistory.log_event_registration(
                                user_id=user.id,
                                event_id=user.event_id,
                                was_club_member=user.club_member or False,
                                notes=f'Migrated from old system - registered as {user.account_type}'
                            )
                            migrated_count += 1
                            print(f"✅ Migrated user {user.id} - event {user.event_id}")
                        else:
                            print(f"⏭️  User {user.id} - event {user.event_id} already exists")
                    else:
                        print(f"⚠️  Event {user.event_id} not found for user {user.id}")
            
            # Commit all changes
            from app.models import db
            db.session.commit()
            
            print(f"\n🎉 Migration completed successfully!")
            print(f"📈 Migrated {migrated_count} user-event registrations")
            
            # Show statistics
            total_user_history = UserHistory.query.count()
            total_user_logs = UserLogs.query.count()
            
            print(f"\n📊 Final Statistics:")
            print(f"  UserHistory entries: {total_user_history}")
            print(f"  UserLogs entries: {total_user_logs}")
            
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            from app.models import db
            db.session.rollback()
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
