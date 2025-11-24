"""Merge sent_by_user_id and 68f474826a4c heads

Revision ID: ee4aa8a379c5
Revises: 68f474826a4c, f1a2b3c4d5e6
Create Date: 2025-11-24 15:08:55.301006

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee4aa8a379c5'
down_revision = ('68f474826a4c', 'f1a2b3c4d5e6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
