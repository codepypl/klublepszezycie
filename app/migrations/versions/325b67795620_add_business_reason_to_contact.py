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
    # Add business_reason column to crm_contacts
    op.add_column('crm_contacts', sa.Column('business_reason', sa.String(length=50), nullable=True))


def downgrade():
    # Remove business_reason column
    op.drop_column('crm_contacts', 'business_reason')
