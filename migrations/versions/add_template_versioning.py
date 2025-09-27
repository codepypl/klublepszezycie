"""Add template versioning system

Revision ID: template_versioning_001
Revises: d499b730d48a
Create Date: 2025-01-27 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'template_versioning_001'
down_revision = 'd499b730d48a'
branch_labels = None
depends_on = None

def upgrade():
    """Add versioning fields to email_templates table"""
    
    # Add versioning fields to email_templates
    op.add_column('email_templates', sa.Column('version', sa.Integer(), default=1))
    op.add_column('email_templates', sa.Column('parent_template_id', sa.Integer(), nullable=True))
    op.add_column('email_templates', sa.Column('is_edited_copy', sa.Boolean(), default=False))
    op.add_column('email_templates', sa.Column('original_template_name', sa.String(100), nullable=True))
    op.add_column('email_templates', sa.Column('edited_from_default', sa.Boolean(), default=False))
    
    # Add foreign key for parent template
    op.create_foreign_key('fk_email_templates_parent', 'email_templates', 'email_templates', ['parent_template_id'], ['id'])
    
    # Add indexes for better performance
    op.create_index('ix_email_templates_version', 'email_templates', ['version'])
    op.create_index('ix_email_templates_parent', 'email_templates', ['parent_template_id'])
    op.create_index('ix_email_templates_name_version', 'email_templates', ['name', 'version'])
    op.create_index('ix_email_templates_edited_copy', 'email_templates', ['is_edited_copy'])

def downgrade():
    """Remove versioning fields from email_templates table"""
    
    # Drop indexes
    op.drop_index('ix_email_templates_edited_copy', 'email_templates')
    op.drop_index('ix_email_templates_name_version', 'email_templates')
    op.drop_index('ix_email_templates_parent', 'email_templates')
    op.drop_index('ix_email_templates_version', 'email_templates')
    
    # Drop foreign key
    op.drop_constraint('fk_email_templates_parent', 'email_templates', type_='foreignkey')
    
    # Drop columns
    op.drop_column('email_templates', 'edited_from_default')
    op.drop_column('email_templates', 'original_template_name')
    op.drop_column('email_templates', 'is_edited_copy')
    op.drop_column('email_templates', 'parent_template_id')
    op.drop_column('email_templates', 'version')
