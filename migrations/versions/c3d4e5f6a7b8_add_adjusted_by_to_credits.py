"""Add adjusted_by_id to credits table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-24 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('credits', sa.Column('adjusted_by_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_credits_adjusted_by', 'credits', 'users', ['adjusted_by_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_credits_adjusted_by', 'credits', type_='foreignkey')
    op.drop_column('credits', 'adjusted_by_id')

