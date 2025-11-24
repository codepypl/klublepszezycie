"""Add sent_by_user_id to EmailLog and EmailQueue

Revision ID: f1a2b3c4d5e6
Revises: a8a1f342d409
Create Date: 2025-11-24 15:05:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'a8a1f342d409'
branch_labels = None
depends_on = None


def upgrade():
    # Sprawdź czy tabele istnieją
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Dodaj sent_by_user_id do email_logs
    if 'email_logs' in existing_tables:
        existing_columns = [col['name'] for col in inspector.get_columns('email_logs')]
        if 'sent_by_user_id' not in existing_columns:
            with op.batch_alter_table('email_logs', schema=None) as batch_op:
                batch_op.add_column(sa.Column('sent_by_user_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key('email_logs_sent_by_user_id_fkey', 'users', ['sent_by_user_id'], ['id'])
    
    # Dodaj sent_by_user_id do email_queue
    if 'email_queue' in existing_tables:
        existing_columns = [col['name'] for col in inspector.get_columns('email_queue')]
        if 'sent_by_user_id' not in existing_columns:
            with op.batch_alter_table('email_queue', schema=None) as batch_op:
                batch_op.add_column(sa.Column('sent_by_user_id', sa.Integer(), nullable=True))
                batch_op.create_foreign_key('email_queue_sent_by_user_id_fkey', 'users', ['sent_by_user_id'], ['id'])


def downgrade():
    # Sprawdź czy tabele istnieją
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Usuń sent_by_user_id z email_logs
    if 'email_logs' in existing_tables:
        existing_columns = [col['name'] for col in inspector.get_columns('email_logs')]
        if 'sent_by_user_id' in existing_columns:
            with op.batch_alter_table('email_logs', schema=None) as batch_op:
                batch_op.drop_constraint('email_logs_sent_by_user_id_fkey', type_='foreignkey')
                batch_op.drop_column('sent_by_user_id')
    
    # Usuń sent_by_user_id z email_queue
    if 'email_queue' in existing_tables:
        existing_columns = [col['name'] for col in inspector.get_columns('email_queue')]
        if 'sent_by_user_id' in existing_columns:
            with op.batch_alter_table('email_queue', schema=None) as batch_op:
                batch_op.drop_constraint('email_queue_sent_by_user_id_fkey', type_='foreignkey')
                batch_op.drop_column('sent_by_user_id')

