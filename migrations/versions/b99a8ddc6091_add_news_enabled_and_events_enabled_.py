"""Add news_enabled and events_enabled feature toggles to application_settings

Revision ID: b99a8ddc6091
Revises: c3d4e5f6a7b8
Create Date: 2026-02-25 17:20:17.238196

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b99a8ddc6091'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('application_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('news_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('events_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')))


def downgrade():
    with op.batch_alter_table('application_settings', schema=None) as batch_op:
        batch_op.drop_column('events_enabled')
        batch_op.drop_column('news_enabled')
