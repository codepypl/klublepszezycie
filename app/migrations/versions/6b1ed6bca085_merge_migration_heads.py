"""merge_migration_heads

Revision ID: 6b1ed6bca085
Revises: ('759870f0f173', '9356897bb38f')
Create Date: 2025-11-22 00:55:39.063328

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b1ed6bca085'
down_revision = ('759870f0f173', '9356897bb38f')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
