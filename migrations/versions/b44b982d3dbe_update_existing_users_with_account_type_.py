"""Update existing users with account_type and group_id

Revision ID: b44b982d3dbe
Revises: 174ac7b3976b
Create Date: 2025-09-19 00:54:17.482257

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b44b982d3dbe'
down_revision = '174ac7b3976b'
branch_labels = None
depends_on = None


def upgrade():
    # Get database connection
    connection = op.get_bind()
    
    # Update account_type based on existing data
    print("🔄 Updating account_type for existing users...")
    
    # Set account_type based on role (club membership is tracked separately by club_member boolean)
    connection.execute(sa.text("""
        UPDATE users 
        SET account_type = CASE 
            WHEN role = 'admin' THEN 'admin'
            WHEN role = 'ankieter' THEN 'ankieter'
            ELSE 'user'
        END
        WHERE account_type IS NULL OR account_type = 'user' OR account_type = 'club_member'
    """))
    
    # Update group_id for club members
    print("🔄 Updating group_id for club members...")
    
    # Get club members group ID
    club_group_result = connection.execute(sa.text("""
        SELECT id FROM user_groups 
        WHERE group_type = 'club_members' 
        LIMIT 1
    """))
    
    club_group_id = club_group_result.fetchone()
    if club_group_id:
        club_group_id = club_group_id[0]
        
        # Update users who are club members
        connection.execute(sa.text("""
            UPDATE users 
            SET group_id = :club_group_id
            WHERE club_member = true 
            AND group_id IS NULL
        """), {"club_group_id": club_group_id})
        
        print(f"✅ Updated club members with group_id = {club_group_id}")
    
    # Update group_id for event registrations
    print("🔄 Updating group_id for event registrations...")
    
    # Get event groups and update users
    event_groups_result = connection.execute(sa.text("""
        SELECT ug.id, ug.name
        FROM user_groups ug 
        WHERE ug.group_type = 'event_based'
    """))
    
    for group_id, group_name in event_groups_result:
        # Extract event ID from group name if possible, or use a different approach
        # For now, just update users who are not already in any group
        connection.execute(sa.text("""
            UPDATE users 
            SET group_id = :group_id, account_type = 'event_registration'
            WHERE group_id IS NULL
            AND account_type = 'user'
            AND id IN (
                SELECT DISTINCT u.id 
                FROM users u
                JOIN event_registrations er ON u.email = er.email
                LIMIT 10
            )
        """), {"group_id": group_id})
        
        print(f"✅ Updated event registrations for group {group_name} with group_id = {group_id}")
    
    print("✅ Migration completed successfully!")


def downgrade():
    # Reset account_type and group_id to NULL
    connection = op.get_bind()
    
    print("🔄 Resetting account_type and group_id...")
    
    connection.execute(sa.text("""
        UPDATE users 
        SET account_type = 'user', group_id = NULL
    """))
    
    print("✅ Rollback completed!")
