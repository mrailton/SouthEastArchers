"""Add qualification_detail to users table

Revision ID: a1b2c3d4e5f6
Revises: c91a55e5475d
Create Date: 2026-02-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c91a55e5475d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('qualification_detail', sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column('users', 'qualification_detail')

