"""optimize_account_types_remove_club_member

Revision ID: 7b4dd244edb2
Revises: 8a4291b8153b
Create Date: 2025-09-19 06:01:17.974503

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b4dd244edb2'
down_revision = '8a4291b8153b'
branch_labels = None
depends_on = None


def upgrade():
    # Get database connection
    connection = op.get_bind()
    
    print("🔄 Optimizing account types - removing club_member type...")
    
    # Update all users with account_type='club_member' to 'user'
    # Club membership is now tracked by the club_member boolean field
    connection.execute(sa.text("""
        UPDATE users 
        SET account_type = 'user'
        WHERE account_type = 'club_member'
    """))
    
    print("✅ Updated club_member account types to user")
    print("✅ Club membership is now tracked by club_member boolean field")
    print("✅ Account types simplified to: user, ankieter, admin, event_registration")


def downgrade():
    # Get database connection
    connection = op.get_bind()
    
    print("🔄 Reverting account types optimization...")
    
    # Restore club_member account type for users who are club members
    connection.execute(sa.text("""
        UPDATE users 
        SET account_type = 'club_member'
        WHERE club_member = true AND account_type = 'user'
    """))
    
    print("✅ Restored club_member account types")
