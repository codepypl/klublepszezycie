#!/usr/bin/env python3
"""
Script to cleanup invalid group memberships (with user_id = None)
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import UserGroupMember, UserGroup, User

def main():
    """Cleanup invalid group memberships"""
    app = create_app()
    
    with app.app_context():
        print("🧹 Cleaning up invalid group memberships...")
        
        try:
            # Find memberships with user_id = None
            invalid_memberships = UserGroupMember.query.filter_by(user_id=None).all()
            
            print(f"📊 Found {len(invalid_memberships)} invalid memberships")
            
            for membership in invalid_memberships:
                group = UserGroup.query.get(membership.group_id)
                group_name = group.name if group else f"Group ID {membership.group_id}"
                print(f"  🗑️  Removing: Membership ID {membership.id} from {group_name}")
                
                # Delete the invalid membership
                from app.models import db
                db.session.delete(membership)
            
            # Commit changes
            db.session.commit()
            
            print(f"✅ Cleaned up {len(invalid_memberships)} invalid memberships")
            
            # Show remaining valid memberships
            valid_memberships = UserGroupMember.query.filter(UserGroupMember.user_id.isnot(None)).all()
            print(f"📊 Remaining valid memberships: {len(valid_memberships)}")
            
            for membership in valid_memberships:
                user = User.query.get(membership.user_id)
                group = UserGroup.query.get(membership.group_id)
                if user and group:
                    print(f"  ✅ {user.email} -> {group.name}")
                else:
                    print(f"  ⚠️  Membership ID {membership.id}: User or Group not found")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {str(e)}")
            from app.models import db
            db.session.rollback()
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
