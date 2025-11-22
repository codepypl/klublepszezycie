"""add_business_reason_to_contact

Revision ID: 325b67795620
Revises: 871d187c04c0
Create Date: 2025-10-10 13:24:23.681058

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '325b67795620'
down_revision = '871d187c04c0'
branch_labels = None
depends_on = None


def upgrade():
    # Add business_reason column to crm_contacts (only if it doesn't exist)
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    
    if 'crm_contacts' in existing_tables:
        existing_columns = [col['name'] for col in inspector.get_columns('crm_contacts')]
        if 'business_reason' not in existing_columns:
            op.add_column('crm_contacts', sa.Column('business_reason', sa.String(length=50), nullable=True))


def downgrade():
    # Remove business_reason column (only if table exists)
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    
    if 'crm_contacts' in existing_tables:
        existing_columns = [col['name'] for col in inspector.get_columns('crm_contacts')]
        if 'business_reason' in existing_columns:
            op.drop_column('crm_contacts', 'business_reason')
