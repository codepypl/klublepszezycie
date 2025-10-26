"""add_cascade_delete_to_email_queue_event_id

Revision ID: 97010259728c
Revises: c3202b60b9f3
Create Date: 2025-10-27 00:45:36.710942

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '97010259728c'
down_revision = 'c3202b60b9f3'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the foreign key constraint from email_queue
    with op.batch_alter_table('email_queue', schema=None) as batch_op:
        batch_op.drop_constraint('email_queue_event_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key('email_queue_event_id_fkey', 'event_schedule', ['event_id'], ['id'], ondelete='CASCADE')
    
    # Drop the foreign key constraint from email_logs
    with op.batch_alter_table('email_logs', schema=None) as batch_op:
        batch_op.drop_constraint('email_logs_event_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key('email_logs_event_id_fkey', 'event_schedule', ['event_id'], ['id'], ondelete='CASCADE')


def downgrade():
    # Revert email_queue foreign key to original without CASCADE
    with op.batch_alter_table('email_queue', schema=None) as batch_op:
        batch_op.drop_constraint('email_queue_event_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key('email_queue_event_id_fkey', 'event_schedule', ['event_id'], ['id'])
    
    # Revert email_logs foreign key to original without CASCADE
    with op.batch_alter_table('email_logs', schema=None) as batch_op:
        batch_op.drop_constraint('email_logs_event_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key('email_logs_event_id_fkey', 'event_schedule', ['event_id'], ['id'])
