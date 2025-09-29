"""
Add reminders_scheduled column to event_schedule table

Revision ID: add_reminders_scheduled
Revises: 
Create Date: 2025-09-29 11:07:10.225

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_reminders_scheduled'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add reminders_scheduled column to event_schedule table
    op.add_column('event_schedule', sa.Column('reminders_scheduled', sa.Boolean(), nullable=True, default=False))
    
    # Set default value for existing records
    op.execute("UPDATE event_schedule SET reminders_scheduled = FALSE WHERE reminders_scheduled IS NULL")
    
    # Make column NOT NULL after setting default values
    op.alter_column('event_schedule', 'reminders_scheduled', nullable=False, default=False)

def downgrade():
    # Remove reminders_scheduled column
    op.drop_column('event_schedule', 'reminders_scheduled')
