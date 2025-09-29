"""Add reminders_scheduled column to event_schedule

Revision ID: 1741a81db96b
Revises: 4eb519cd831c
Create Date: 2025-09-29 11:54:52.377898

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1741a81db96b'
down_revision = '4eb519cd831c'
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
