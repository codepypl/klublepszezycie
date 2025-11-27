"""add_event_link_click_tracking

Revision ID: 1ff627f925d2
Revises: ee4aa8a379c5
Create Date: 2025-11-28 00:01:53.778279

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1ff627f925d2'
down_revision = 'ee4aa8a379c5'
branch_labels = None
depends_on = None


def upgrade():
    # Create event_link_clicks table
    op.create_table('event_link_clicks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('email_log_id', sa.Integer(), nullable=True),
        sa.Column('click_token', sa.String(length=255), nullable=False),
        sa.Column('clicked_at', sa.DateTime(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('participation_recorded', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['email_log_id'], ['email_logs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['event_id'], ['event_schedule.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('click_token', name='unique_click_token')
    )
    
    # Create indexes
    op.create_index(op.f('ix_event_link_clicks_click_token'), 'event_link_clicks', ['click_token'], unique=False)
    op.create_index(op.f('ix_event_link_clicks_clicked_at'), 'event_link_clicks', ['clicked_at'], unique=False)
    op.create_index(op.f('ix_event_link_clicks_created_at'), 'event_link_clicks', ['created_at'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_event_link_clicks_created_at'), table_name='event_link_clicks')
    op.drop_index(op.f('ix_event_link_clicks_clicked_at'), table_name='event_link_clicks')
    op.drop_index(op.f('ix_event_link_clicks_click_token'), table_name='event_link_clicks')
    
    # Drop table
    op.drop_table('event_link_clicks')
