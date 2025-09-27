"""merge template versioning

Revision ID: 12e59b307fa2
Revises: template_versioning_001, d1fe377fc0cc
Create Date: 2025-09-27 17:22:48.251065

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '12e59b307fa2'
down_revision = ('template_versioning_001', 'd1fe377fc0cc')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
